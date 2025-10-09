from functools import wraps
from typing import Callable, TypeVar, Any
from graphql import GraphQLError
from backend.core.errors import BaseAPIError, AuthenticationError
from backend.core.db.session import transaction_context
from backend.core.logger import get_logger

logger = get_logger("decorators")

T = TypeVar("T")

def with_transaction(isolation_level: str = None):
    """
    Decorator that wraps a function with database transaction management
    
    Args:
        isolation_level: Optional SQLAlchemy isolation level
    """
    return transaction_context(isolation_level)


def handle_graphql_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for consistent GraphQL error handling
    
    Converts various error types to GraphQL-compliant error responses
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except AuthenticationError as e:
            logger.warning(f"Authentication error: {str(e)}")
            raise GraphQLError(
                message=str(e),
                extensions={
                    "code": e.code,
                    "category": "authentication"
                }
            )
        except BaseAPIError as e:
            logger.error(f"API error: {str(e)}")
            raise GraphQLError(
                message=str(e),
                extensions={
                    "code": e.code,
                    "category": "api"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise GraphQLError(
                message="An unexpected error occurred",
                extensions={
                    "code": "INTERNAL_SERVER_ERROR",
                    "category": "internal"
                }
            )
    return wrapper