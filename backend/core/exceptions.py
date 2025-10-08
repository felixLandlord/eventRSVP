from typing import Optional


class BaseError(Exception):
    """Base exception class for custom application errors"""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(BaseError):
    """Exception raised for authentication related errors"""
    def __init__(
        self, 
        message: str = "Authentication failed", 
        code: str = "AUTH_ERROR",
        original_error: Optional[Exception] = None
    ):
        super().__init__(message=message, code=code)
        self.original_error = original_error

    def to_dict(self) -> dict:
        """Convert error to dictionary format for API responses"""
        return {
            "message": self.message,
            "code": self.code,
            "type": "authentication_error"
        }


class DatabaseError(BaseError):
    """Exception raised for database related errors"""
    def __init__(
        self,
        message: str = "Database operation failed",
        code: str = "DB_ERROR",
        original_error: Optional[Exception] = None
    ):
        super().__init__(message=message, code=code)
        self.original_error = original_error

    def to_dict(self) -> dict:
        """Convert error to dictionary format for API responses"""
        return {
            "message": self.message,
            "code": self.code,
            "type": "database_error"
        }


class EmailError(BaseError):
    """Exception raised for email service related errors"""
    def __init__(
        self,
        message: str = "Email operation failed",
        code: str = "EMAIL_ERROR",
        original_error: Optional[Exception] = None
    ):
        super().__init__(message=message, code=code)
        self.original_error = original_error

    def to_dict(self) -> dict:
        """Convert error to dictionary format for API responses"""
        return {
            "message": self.message,
            "code": self.code,
            "type": "email_error"
        }


# Common error codes
AUTH_CODES = {
    "TOKEN_EXPIRED": "AUTH_001",
    "INVALID_TOKEN": "AUTH_002",
    "MISSING_TOKEN": "AUTH_003",
    "INVALID_CREDENTIALS": "AUTH_004"
}

DB_CODES = {
    "CONNECTION_ERROR": "DB_001",
    "TRANSACTION_ERROR": "DB_002",
    "INTEGRITY_ERROR": "DB_003",
    "QUERY_ERROR": "DB_004"
}

EMAIL_CODES = {
    "SMTP_ERROR": "EMAIL_001",
    "TEMPLATE_ERROR": "EMAIL_002",
    "INVALID_RECIPIENT": "EMAIL_003",
    "CONNECTION_ERROR": "EMAIL_004"
}