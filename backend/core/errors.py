class BaseAPIError(Exception):
    """Base class for API errors"""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.message = message
        self.code = code


class AuthenticationError(BaseAPIError):
    """Authentication related errors"""
    def __init__(self, message: str, code: str = "AUTHENTICATION_ERROR"):
        super().__init__(message=message, code=code)


class EmailServiceError(BaseAPIError):
    """Email service related errors"""
    def __init__(self, message: str, code: str = "EMAIL_SERVICE_ERROR"):
        super().__init__(message=message, code=code)