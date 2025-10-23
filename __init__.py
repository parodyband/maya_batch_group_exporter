"""
Maya Batch Exporter
A tool for managing export groups and batch exporting with FBX settings.

Refactored to follow SOLID principles with proper dependency injection,
separation of concerns, and testable architecture.
"""

from .ui.main_window import show_batch_exporter
from .container import get_container, reset_container

__version__ = "2.0.0"
__all__ = ["show_batch_exporter", "get_container", "reset_container"]

