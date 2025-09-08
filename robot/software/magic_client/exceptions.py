class MagicClientError(Exception):
    """Base exception for magic client errors"""
    pass

class AuthenticationError(MagicClientError):
    """Raised when authentication fails"""
    pass

class NotFoundError(MagicClientError):
    """Raised when a resource is not found"""
    pass

class ValidationError(MagicClientError):
    """Raised when request validation fails"""
    pass
