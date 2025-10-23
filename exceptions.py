"""
Custom Exception Hierarchy
Defines all custom exceptions for the batch exporter.
"""


class ExporterError(Exception):
    """Base exception for all batch exporter errors."""
    pass


class ValidationError(ExporterError):
    """Raised when input validation fails."""
    pass


class ExportError(ExporterError):
    """Raised when an export operation fails."""
    pass


class DataPersistenceError(ExporterError):
    """Raised when saving or loading configuration fails."""
    pass


class MayaOperationError(ExporterError):
    """Raised when a Maya operation fails."""
    pass


class SetNotFoundError(MayaOperationError):
    """Raised when a Maya set cannot be found."""
    pass


class PluginError(ExporterError):
    """Raised when plugin loading fails."""
    pass

