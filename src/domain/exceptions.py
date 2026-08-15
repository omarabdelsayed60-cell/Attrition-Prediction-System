"""
Domain Exceptions Hierarchy
Centralized custom exceptions for enterprise error handling.
"""

class AttritionSystemException(Exception):
    """Base exception class for all enterprise application errors."""
    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details

class ModelNotFoundError(AttritionSystemException):
    """Raised when trained model or preprocessor artifacts cannot be found on disk."""
    pass

class ModelInferenceError(AttritionSystemException):
    """Raised when model prediction or SHAP explainer fails during calculation."""
    pass

class InvalidEmployeeDataError(AttritionSystemException):
    """Raised when input employee feature values violate schema constraints or business rules."""
    pass

class DatabaseConnectionError(AttritionSystemException):
    """Raised when SQL Server or SQLite database session initialization fails."""
    pass

class ResourceNotFoundError(AttritionSystemException):
    """Raised when requesting a non-existent database entity (e.g., missing Employee ID)."""
    pass

class BatchProcessingError(AttritionSystemException):
    """Raised when batch prediction processing encounters invalid file formats or parsing errors."""
    pass
