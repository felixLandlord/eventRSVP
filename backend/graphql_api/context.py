from typing import Optional
from fastapi import Request
from backend.services.auth_service import AuthService
from backend.graphql_api.types import UserType
from jwt import PyJWTError as JWTError
from backend.core.logger import get_logger

logger = get_logger("graphql_context")


async def get_context_value(request: Request):
    """
    Builds the GraphQL context for each request:
    - Always includes the `request` object
    - Extracts Bearer token from Authorization header
    - Validates token and fetches current user
    - Injects `token` and `current_user` into context
    """
    token: Optional[str] = None
    current_user: Optional[UserType] = None

    auth_header: Optional[str] = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            current_user = await AuthService.get_current_user(token)
        except JWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Context error: {str(e)}")

    return {"request": request, "token": token, "current_user": current_user}
