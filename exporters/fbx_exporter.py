"""
FBX Exporter
Handles FBX export operations using Maya API facade.
"""

import os
from typing import Dict, Any
from .base import Exporter, ExportSettings
from ..types import ExportGroupDict, FBXSettingsDict
from ..maya_facade import MayaSceneInterface
from ..exceptions import ExportError, PluginError, ValidationError
from ..validators import PathValidator
from ..constants import FBX_EXTENSION
from ..logger import get_logger

logger = get_logger(__name__)


class FBXSettings(ExportSettings):
    """FBX export settings."""
    
    def __init__(self, settings_dict: FBXSettingsDict):
        """
        Initialize FBX settings.
        
        Args:
            settings_dict: Settings dictionary
        """
        self.up_axis = settings_dict.get("up_axis", "Y")
        self.triangulate = settings_dict.get("triangulate", False)
        self.convert_unit = settings_dict.get("convert_unit", "cm")
        self.export_directory = settings_dict.get("export_directory", "")
        self.file_prefix = settings_dict.get("file_prefix", "")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "up_axis": self.up_axis,
            "triangulate": self.triangulate,
            "convert_unit": self.convert_unit,
            "export_directory": self.export_directory,
            "file_prefix": self.file_prefix,
        }
    
    def validate(self) -> None:
        """
        Validate FBX settings.
        
        Raises:
            ValidationError: If settings are invalid
        """
        if self.up_axis not in ["Y", "Z"]:
            raise ValidationError(f"Invalid up axis: {self.up_axis}")
        
        if self.convert_unit not in ["cm", "m", "mm", "in", "ft"]:
            raise ValidationError(f"Invalid unit: {self.convert_unit}")
        
        if not self.export_directory:
            raise ValidationError("Export directory is not set")
        
        # Validate directory path
        PathValidator.validate_directory(self.export_directory, must_exist=False)


class FBXExporter(Exporter):
    """Exporter for FBX format."""
    
    def __init__(self, maya_scene: MayaSceneInterface):
        """
        Initialize the FBX exporter.
        
        Args:
            maya_scene: Maya scene interface
        """
        self.maya_scene = maya_scene
        self._ensure_plugin_loaded()
    
    def _ensure_plugin_loaded(self) -> None:
        """
        Ensure FBX plugin is loaded.
        
        Raises:
            PluginError: If plugin cannot be loaded
        """
        try:
            if not self.maya_scene.is_plugin_loaded("fbxmaya"):
                self.maya_scene.load_plugin("fbxmaya")
                logger.info("Loaded FBX plugin")
        except Exception as e:
            raise PluginError(f"Could not load FBX plugin: {e}")
    
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Apply FBX export settings using MEL commands.
        
        Args:
            settings: FBX settings dictionary
            
        Returns:
            True if successful
        """
        try:
            fbx_settings = FBXSettings(settings)
            fbx_settings.validate()
            
            # Reset to defaults first
            self.maya_scene.eval_mel('FBXResetExport')
            
            # Apply up axis
            self.maya_scene.eval_mel(f'FBXExportUpAxis {fbx_settings.up_axis}')
            
            # Apply triangulate
            value = "true" if fbx_settings.triangulate else "false"
            self.maya_scene.eval_mel(f'FBXExportTriangulate -v {value}')
            
            # Apply unit conversion
            self.maya_scene.eval_mel(f'FBXExportConvertUnitString "{fbx_settings.convert_unit}"')
            
            logger.debug("Applied FBX settings")
            return True
            
        except ValidationError as e:
            logger.error(f"Invalid FBX settings: {e}")
            return False
        except Exception as e:
            logger.error(f"Error applying FBX settings: {e}")
            return False
    
    def export_group(self, group: ExportGroupDict, settings: Dict[str, Any]) -> tuple[bool, str]:
        """
        Export a single group with the given FBX settings.
        
        Args:
            group: Export group data
            settings: FBX settings dictionary
            
        Returns:
            Tuple of (success, message)
        """
        name = group.get("name", "untitled")
        set_name = group.get("set_name")
        
        try:
            # Validate settings
            fbx_settings = FBXSettings(settings)
            fbx_settings.validate()
            
        except ValidationError as e:
            msg = f"Invalid settings: {e}"
            logger.error(msg)
            return False, msg
        
        # Check if set exists
        if not set_name or not self.maya_scene.object_exists(set_name):
            msg = f"Export set does not exist for '{name}'"
            logger.error(msg)
            return False, msg
        
        # Get set members
        set_members = self.maya_scene.get_set_members(set_name)
        
        if not set_members:
            msg = f"No objects in group '{name}'"
            logger.warning(msg)
            return False, msg
        
        # Build export path
        filename = f"{fbx_settings.file_prefix}{name}{FBX_EXTENSION}"
        export_path = os.path.join(fbx_settings.export_directory, filename)
        
        # Ensure directory exists
        if not os.path.exists(fbx_settings.export_directory):
            try:
                os.makedirs(fbx_settings.export_directory)
                logger.info(f"Created directory: {fbx_settings.export_directory}")
            except Exception as e:
                msg = f"Could not create directory '{fbx_settings.export_directory}': {e}"
                logger.error(msg)
                return False, msg
        
        # Save current selection
        previous_selection = self.maya_scene.get_selection()
        
        try:
            # Apply FBX settings
            if not self.apply_settings(settings):
                raise ExportError("Failed to apply FBX settings")
            
            # Select objects to export
            self.maya_scene.select(set_members, replace=True)
            
            # Export using MEL
            self.maya_scene.eval_mel(f'FBXExport -f "{export_path}" -s')
            
            # Restore selection
            if previous_selection:
                self.maya_scene.select(previous_selection, replace=True)
            else:
                self.maya_scene.select(clear=True)
            
            msg = f"Exported '{name}' to {export_path}"
            logger.info(msg)
            return True, msg
            
        except Exception as e:
            # Restore selection on error
            try:
                if previous_selection:
                    self.maya_scene.select(previous_selection, replace=True)
                else:
                    self.maya_scene.select(clear=True)
            except Exception as restore_error:
                logger.warning(f"Failed to restore selection after export error: {restore_error}")
            
            msg = f"Error exporting group '{name}': {e}"
            logger.error(msg)
            return False, msg

