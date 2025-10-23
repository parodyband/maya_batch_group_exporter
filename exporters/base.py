"""
Base Exporter Classes
Abstract interfaces for exporters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from ..types import ExportGroupDict, FBXSettingsDict


class ExportSettings(ABC):
    """Abstract base class for export settings."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary representation.
        
        Returns:
            Settings as dictionary
        """
        pass
    
    @abstractmethod
    def validate(self) -> None:
        """
        Validate the settings.
        
        Raises:
            ValidationError: If settings are invalid
        """
        pass


class Exporter(ABC):
    """Abstract base class for exporters."""
    
    @abstractmethod
    def export_group(self, group: ExportGroupDict, settings: Dict[str, Any]) -> tuple[bool, str]:
        """
        Export a single group.
        
        Args:
            group: Export group data
            settings: Export settings
            
        Returns:
            Tuple of (success, message)
        """
        pass
    
    @abstractmethod
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Apply export settings.
        
        Args:
            settings: Export settings to apply
            
        Returns:
            True if successful
        """
        pass

