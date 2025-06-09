# exceptions.py - Custom exception classes for FastAPI application
# Defines domain-specific exceptions for error handling.


class DatabaseError(Exception):
    """Wrapper for database operation failures."""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class ConflictError(Exception):
    """Raised when resource constraints are violated."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class NotFoundError(Exception):
    """Raised when a requested resource doesn't exist."""
    def __init__(self, message: str, resource_type: str = None):
        self.message = message
        self.resource_type = resource_type
        super().__init__(self.message)


class ValidationError(Exception):
    """Raised when data validation fails."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)


class AuthorizationError(Exception):
    """Raised when user lacks required permissions."""
    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message
        super().__init__(self.message)


class PermissionError(Exception):
    """Raised when a user does not have permission to perform an action."""
    def __init__(self, message: str = "Permission denied"):
        self.message = message
        super().__init__(self.message)
