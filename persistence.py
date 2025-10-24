"""
Configuration Persistence
Handles saving and loading export configurations to/from JSON files.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Optional
from .types import ExportDataDict
from .constants import (
    EXPORT_GROUPS_SUFFIX, JSON_EXTENSION, UNTITLED_SCENE_FILENAME,
    DEFAULT_UP_AXIS, DEFAULT_TRIANGULATE, DEFAULT_CONVERT_UNIT,
    DEFAULT_EXPORT_DIRECTORY, DEFAULT_FILE_PREFIX
)
from .exceptions import DataPersistenceError, ValidationError
from .validators import PathValidator
from .logger import get_logger

logger = get_logger(__name__)


class ConfigRepository(ABC):
    """Abstract interface for configuration persistence."""
    
    @abstractmethod
    def save(self, data: ExportDataDict, file_path: str) -> None:
        """
        Save configuration data to a file.
        
        Args:
            data: Export configuration data
            file_path: Path to save the file
            
        Raises:
            DataPersistenceError: If save fails
        """
        pass
    
    @abstractmethod
    def load(self, file_path: str) -> ExportDataDict:
        """
        Load configuration data from a file.
        
        Args:
            file_path: Path to load from
            
        Returns:
            Export configuration data
            
        Raises:
            DataPersistenceError: If load fails
        """
        pass
    
    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """
        Check if a configuration file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists
        """
        pass


class JsonConfigRepository(ConfigRepository):
    """JSON-based configuration persistence."""
    
    def save(self, data: ExportDataDict, file_path: str) -> None:
        """
        Save configuration data to a JSON file.
        
        Args:
            data: Export configuration data
            file_path: Path to save the file
            
        Raises:
            DataPersistenceError: If save fails
            ValidationError: If file path is invalid
        """
        try:
            # Validate path
            file_path = PathValidator.validate_file_path(
                file_path, 
                must_exist=False, 
                extensions=[JSON_EXTENSION]
            )
            
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    logger.info(f"Created directory: {directory}")
                except Exception as e:
                    raise DataPersistenceError(f"Failed to create directory '{directory}': {e}")
            
            # Check if path is writable
            if not PathValidator.is_path_writable(file_path):
                raise DataPersistenceError(f"Path is not writable: {file_path}")
            
            # Write JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            
            logger.info(f"Saved configuration to: {file_path}")
            
        except ValidationError:
            raise
        except DataPersistenceError:
            raise
        except Exception as e:
            raise DataPersistenceError(f"Failed to save configuration: {e}")
    
    def load(self, file_path: str) -> ExportDataDict:
        """
        Load configuration data from a JSON file.
        
        Args:
            file_path: Path to load from
            
        Returns:
            Export configuration data
            
        Raises:
            DataPersistenceError: If load fails
            ValidationError: If file path is invalid
        """
        try:
            # Validate path
            file_path = PathValidator.validate_file_path(
                file_path,
                must_exist=True,
                extensions=[JSON_EXTENSION]
            )
            
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Strict validation - no backwards compatibility
            if not isinstance(data, dict):
                raise DataPersistenceError("Invalid configuration format: expected dictionary")
            
            if "export_groups" not in data:
                raise DataPersistenceError("Invalid configuration: missing 'export_groups' field")
            
            if "fbx_settings" not in data:
                raise DataPersistenceError("Invalid configuration: missing 'fbx_settings' field")
            
            # Validate required settings fields
            required_settings = ["up_axis", "triangulate", "convert_unit", "export_directory", "file_prefix"]
            missing_fields = [field for field in required_settings if field not in data["fbx_settings"]]
            if missing_fields:
                raise DataPersistenceError(f"Invalid configuration: missing FBX settings fields: {missing_fields}")
            
            # expanded_groups is optional (for backwards compatibility with newly created files)
            if "expanded_groups" not in data:
                data["expanded_groups"] = []
            
            logger.info(f"Loaded configuration from: {file_path}")
            return data
            
        except ValidationError:
            raise
        except DataPersistenceError:
            raise
        except json.JSONDecodeError as e:
            raise DataPersistenceError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise DataPersistenceError(f"Failed to load configuration: {e}")
    
    def exists(self, file_path: str) -> bool:
        """
        Check if a configuration file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists
        """
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    @staticmethod
    def _get_default_fbx_settings() -> dict:
        """Get default FBX settings."""
        return {
            "up_axis": DEFAULT_UP_AXIS,
            "triangulate": DEFAULT_TRIANGULATE,
            "convert_unit": DEFAULT_CONVERT_UNIT,
            "export_directory": DEFAULT_EXPORT_DIRECTORY,
            "file_prefix": DEFAULT_FILE_PREFIX,
        }


class ConfigPathResolver:
    """Resolves configuration file paths based on Maya scene."""
    
    def __init__(self, maya_scene):
        """
        Initialize the path resolver.
        
        Args:
            maya_scene: Maya scene interface
        """
        self.maya_scene = maya_scene
    
    def get_default_config_path(self) -> str:
        """
        Get the default configuration file path based on current Maya scene.
        
        Returns:
            Default JSON file path
        """
        scene_path = self.maya_scene.get_scene_name()
        
        if scene_path:
            # Use scene name + suffix
            base_name = os.path.splitext(scene_path)[0]
            json_path = base_name + EXPORT_GROUPS_SUFFIX + JSON_EXTENSION
        else:
            # Untitled scene - save to home directory
            json_path = os.path.join(
                os.path.expanduser("~"),
                UNTITLED_SCENE_FILENAME
            )
        
        logger.debug(f"Default config path: {json_path}")
        return json_path

