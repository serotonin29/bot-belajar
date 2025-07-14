class OpenNotebookException(Exception):
    """Base exception for Open Notebook."""
    pass


class NotFoundError(OpenNotebookException):
    """Raised when a requested object is not found."""
    pass


class InvalidInputError(OpenNotebookException):
    """Raised when input data is invalid."""
    pass


class DatabaseOperationError(OpenNotebookException):
    """Raised when a database operation fails."""
    pass


class UnsupportedTypeException(OpenNotebookException):
    """Raised when an unsupported content type is encountered."""
    pass
