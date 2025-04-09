class BaseTaskiqAiopgError(Exception):
    """Base error for all possible exception in the lib."""


class DatabaseConnectionError(BaseTaskiqAiopgError):
    """Error if cannot connect to PostgreSQL."""


class ResultIsMissingError(BaseTaskiqAiopgError):
    """Error if cannot retrieve result from PostgreSQL."""
