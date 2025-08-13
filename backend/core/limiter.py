from typing import Optional, Callable, Any, cast
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from functools import wraps
import inspect

from backend.core.config import settings
from backend.core.logger import get_logger
import logging

logger: logging.Logger = get_logger("rate_limiter")


def get_client_ip(request: Request) -> str:
    """Get client IP address for rate limiting"""
    forwarded_ip: Optional[str] = request.headers.get("X-Forwarded-For")
    if forwarded_ip:
        client_ip: str = forwarded_ip.split(",")[0].strip()
    else:
        client_ip: str = get_remote_address(request)

    logger.debug(f"Client IP for rate limiting: {client_ip}")
    return client_ip


class CustomLimiter:
    """Custom rate limiter wrapper that can be disabled and supports GraphQL"""

    def __init__(self):
        self.enabled: bool = getattr(settings, "RATE_LIMITING_ENABLED", True)
        self.limiter: Optional[Limiter] = None

        if self.enabled:
            self.limiter = Limiter(
                key_func=get_client_ip,
                storage_uri=getattr(settings, "RATE_LIMIT_STORAGE_URI", "memory://"),
                default_limits=getattr(settings, "RATE_LIMIT_DEFAULT", ["100/minute"]),
            )
            logger.info("Rate limiting enabled")
        else:
            logger.info("Rate limiting disabled")

    def limit(self, rate: str) -> Callable:
        """Apply rate limit decorator (supports FastAPI + GraphQL)"""

        def decorator(func: Callable) -> Callable:
            if not self.enabled or self.limiter is None:
                return func

            sig = inspect.signature(func)
            params = list(sig.parameters.keys())

            # Case 1: Normal FastAPI endpoint with request/websocket param
            if "request" in params or "websocket" in params:
                return self.limiter.limit(rate)(func)

            # Case 2: GraphQL resolver (no request param)
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                request: Optional[Request] = None
                try:
                    info = args[1] if len(args) > 1 else kwargs.get("info")
                    if info and hasattr(info, "context"):
                        request = info.context.get("request")  # type: ignore

                    if not isinstance(request, Request):
                        logger.error(
                            "Request object missing in GraphQL context — skipping rate limit"
                        )
                        return await func(*args, **kwargs)

                    if self.limiter:
                        wrapped = self.limiter.limit(rate)(lambda: None)
                        wrapped()

                except RateLimitExceeded as e:
                    logger.warning(
                        f"Rate limit exceeded for {get_client_ip(cast(Request, request))}: {e.detail}"
                    )
                    raise e

                return await func(*args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                request: Optional[Request] = None
                try:
                    info = args[1] if len(args) > 1 else kwargs.get("info")
                    if info and hasattr(info, "context"):
                        request = info.context.get("request")  # type: ignore

                    if not isinstance(request, Request):
                        logger.error(
                            "Request object missing in GraphQL context — skipping rate limit"
                        )
                        return func(*args, **kwargs)

                    if self.limiter:
                        wrapped = self.limiter.limit(rate)(lambda: None)
                        wrapped()

                except RateLimitExceeded as e:
                    logger.warning(
                        f"Rate limit exceeded for {get_client_ip(cast(Request, request))}: {e.detail}"
                    )
                    raise e

                return func(*args, **kwargs)

            return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def get_limiter(self) -> Optional[Limiter]:
        """Get the underlying limiter instance"""
        return self.limiter if self.enabled else None


limiter: CustomLimiter = CustomLimiter()


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom rate limit exceeded handler"""
    logger.warning(f"Rate limit exceeded for {get_client_ip(request)}: {exc.detail}")

    retry_after: Optional[int] = getattr(exc, "retry_after", None)
    retry_after_str = str(retry_after) if retry_after is not None else "60"

    response: Response = Response(
        content=f"Rate limit exceeded: {exc.detail}",
        status_code=429,
        headers={
            "Content-Type": "application/json",
            "Retry-After": retry_after_str,
        },
    )
    return response


def setup_rate_limiting(app):
    """Setup rate limiting for FastAPI app"""
    if limiter.enabled and limiter.get_limiter():
        app.state.limiter = limiter.get_limiter()
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
        logger.info("Rate limiting setup completed")
    else:
        logger.info("Rate limiting setup skipped (disabled)")


RATE_LIMITS: dict = {
    "general": "60/minute",
    "query_hello": "30/minute",
    "query_me": "20/minute",
    "query_get_events": "60/minute",
    "query_get_event": "60/minute",
    "query_get_my_events": "30/minute",
    "query_get_my_rsvps": "30/minute",
    "query_get_event_attendees": "20/minute",
    "query_get_event_analytics": "10/minute",
    "mutation_register": "5/minute",
    "mutation_login": "10/minute",
    "mutation_create_event": "10/minute",
    "mutation_update_event": "10/minute",
    "mutation_delete_event": "5/minute",
    "mutation_create_rsvp": "20/minute",
    "mutation_cancel_rsvp": "20/minute",
    "mutation_check_in_attendee": "30/minute",
    "mutation_verify_email": "5/minute",
    "mutation_resend_email_otp": "3/minute",
    "mutation_forgot_password": "5/minute",
    "mutation_reset_password": "5/minute",
    "mutation_change_password": "5/minute",
    "mutation_delete_account": "2/minute",
    "mutation_refresh_tokens": "20/minute",
    "mutation_validate_qr_code": "30/minute",
}
