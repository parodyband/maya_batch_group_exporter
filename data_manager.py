"""
Data Manager (Refactored)
Orchestrates export group operations using composition.
"""

from typing import List, Optional
from .types import ExportGroupDict, FBXSettingsDict, ExportDataDict
from .maya_facade import MayaSceneInterface
from .set_manager import SetManager
from .persistence import ConfigRepository, ConfigPathResolver
from .validators import NameValidator
from .constants import (
    DEFAULT_UP_AXIS, DEFAULT_TRIANGULATE, DEFAULT_CONVERT_UNIT,
    DEFAULT_EXPORT_DIRECTORY, DEFAULT_FILE_PREFIX, SET_PREFIX
)
from .exceptions import ValidationError
from .logger import get_logger

logger = get_logger(__name__)


class DataManager:
    """
    Manages export groups and settings using composition pattern.
    Delegates to specialized classes for set operations and persistence.
    """
    
    def __init__(self, 
                 maya_scene: MayaSceneInterface,
                 set_manager: SetManager,
                 config_repository: ConfigRepository,
                 path_resolver: ConfigPathResolver):
        """
        Initialize the DataManager.
        
        Args:
            maya_scene: Maya scene interface
            set_manager: Manager for Maya sets
            config_repository: Repository for config persistence
            path_resolver: Resolver for config file paths
        """
        self.maya_scene = maya_scene
        self.set_manager = set_manager
        self.config_repository = config_repository
        self.path_resolver = path_resolver
        
        self.data: ExportDataDict = {
            "export_groups": [],
            "fbx_settings": self._get_default_fbx_settings(),
            "expanded_groups": []
        }
        self.group_order: List[str] = []  # Track desired order by set_name
    
    def _get_default_fbx_settings(self) -> FBXSettingsDict:
        """Get default FBX settings."""
        return {
            "up_axis": DEFAULT_UP_AXIS,
            "triangulate": DEFAULT_TRIANGULATE,
            "convert_unit": DEFAULT_CONVERT_UNIT,
            "export_directory": DEFAULT_EXPORT_DIRECTORY,
            "file_prefix": DEFAULT_FILE_PREFIX,
        }
    
    def sync_from_scene(self) -> None:
        """Synchronize data structure from Maya sets in the scene."""
        try:
            export_sets = self.set_manager.list_export_sets()
            
            # Build groups from sets
            groups_dict = {}
            for set_name in export_sets:
                if self.maya_scene.object_exists(set_name):
                    display_name = set_name[len(SET_PREFIX):]
                    group: ExportGroupDict = {
                        "name": display_name,
                        "set_name": set_name
                    }
                    groups_dict[set_name] = group
            
            # Update group_order to include any new sets
            for set_name in groups_dict:
                if set_name not in self.group_order:
                    self.group_order.append(set_name)
            
            # Remove deleted sets from order
            self.group_order = [s for s in self.group_order if s in groups_dict]
            
            # Build final list in the correct order
            self.data["export_groups"] = []
            for set_name in self.group_order:
                if set_name in groups_dict:
                    self.data["export_groups"].append(groups_dict[set_name])
            
            logger.debug(f"Synced {len(self.data['export_groups'])} groups from scene")
        except Exception as e:
            logger.error(f"Error syncing data from scene: {e}")
    
    def get_json_path(self) -> str:
        """Get the default JSON file path based on current Maya scene."""
        return self.path_resolver.get_default_config_path()
    
    def save_to_file(self, file_path: Optional[str] = None) -> tuple[bool, str]:
        """
        Save export groups and settings to JSON file.
        
        Args:
            file_path: Optional custom file path
            
        Returns:
            Tuple of (success, message)
        """
        if file_path is None:
            file_path = self.get_json_path()
        
        self.sync_from_scene()
        
        try:
            self.config_repository.save(self.data, file_path)
            return True, file_path
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False, str(e)
    
    def load_from_file(self, file_path: Optional[str] = None) -> tuple[bool, str]:
        """
        Load export groups and settings from JSON file.
        
        Args:
            file_path: Optional custom file path
            
        Returns:
            Tuple of (success, message)
        """
        if file_path is None:
            file_path = self.get_json_path()
        
        if not self.config_repository.exists(file_path):
            return False, "File does not exist"
        
        try:
            loaded_data = self.config_repository.load(file_path)
            
            # Update FBX settings
            self.data["fbx_settings"] = loaded_data["fbx_settings"]
            
            # Create sets from loaded data
            self._create_sets_from_data(loaded_data.get("export_groups", []))
            
            # Sync to get current state
            self.sync_from_scene()
            
            return True, file_path
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False, str(e)
    
    def _create_sets_from_data(self, groups_data: List[ExportGroupDict]) -> None:
        """
        Create or update Maya sets from loaded JSON data.
        
        Args:
            groups_data: List of export group data
        """
        for group_data in groups_data:
            set_name = group_data.get("set_name")
            display_name = group_data.get("name", "untitled")
            
            if not set_name:
                set_name = self.set_manager.get_unique_set_name(display_name)
            
            if not self.maya_scene.object_exists(set_name):
                try:
                    self.set_manager.create_set(display_name)
                except Exception as e:
                    logger.warning(f"Failed to create set for '{display_name}': {e}")
    
    def add_export_group(self, name: str) -> Optional[int]:
        """
        Add a new export group as a Maya set.
        
        Args:
            name: Name for the export group
            
        Returns:
            Index of the new group, or None if failed
        """
        try:
            # Validate name
            name = NameValidator.validate_group_name(name)
            
            # Create set
            set_name = self.set_manager.create_set(name)
            
            # Sync and find index
            self.sync_from_scene()
            
            for i, group in enumerate(self.data["export_groups"]):
                if group["set_name"] == set_name:
                    return i
            
            return len(self.data["export_groups"]) - 1
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to add export group: {e}")
            return None
    
    def remove_export_group(self, index: int) -> bool:
        """
        Remove an export group by index.
        
        Args:
            index: Index of the group to remove
            
        Returns:
            True if successful
        """
        if 0 <= index < len(self.data["export_groups"]):
            group = self.data["export_groups"][index]
            set_name = group.get("set_name")
            
            if set_name:
                try:
                    self.set_manager.delete_set(set_name)
                except Exception as e:
                    logger.error(f"Failed to delete set: {e}")
                    return False
            
            self.sync_from_scene()
            return True
        return False
    
    def update_export_group(self, index: int, name: Optional[str] = None) -> bool:
        """
        Update an export group.
        
        Args:
            index: Index of the group to update
            name: Optional new name
            
        Returns:
            True if successful
        """
        if 0 <= index < len(self.data["export_groups"]):
            group = self.data["export_groups"][index]
            set_name = group.get("set_name")
            
            if not set_name or not self.maya_scene.object_exists(set_name):
                return False
            
            if name is not None:
                try:
                    # Validate name
                    name = NameValidator.validate_group_name(name)
                    
                    # Rename set
                    self.set_manager.rename_set(set_name, name)
                except ValidationError as e:
                    logger.error(f"Validation error: {e}")
                    return False
                except Exception as e:
                    logger.error(f"Failed to rename group: {e}")
                    return False
            
            self.sync_from_scene()
            return True
        return False
    
    def get_export_group(self, index: int) -> Optional[ExportGroupDict]:
        """
        Get an export group by index.
        
        Args:
            index: Index of the group
            
        Returns:
            Export group data, or None if not found
        """
        self.sync_from_scene()
        if 0 <= index < len(self.data["export_groups"]):
            return self.data["export_groups"][index]
        return None
    
    def get_all_export_groups(self) -> List[ExportGroupDict]:
        """
        Get all export groups.
        
        Returns:
            List of export group data
        """
        self.sync_from_scene()
        return self.data["export_groups"]
    
    def get_set_objects(self, set_name: str) -> List[str]:
        """
        Get objects in a Maya set.
        
        Args:
            set_name: Name of the set
            
        Returns:
            List of object names
        """
        try:
            return self.set_manager.get_set_objects(set_name)
        except Exception as e:
            logger.error(f"Failed to get set objects: {e}")
            return []
    
    def add_objects_to_set(self, set_name: str, objects: List[str]) -> bool:
        """
        Add objects to a Maya set.
        
        Args:
            set_name: Name of the set
            objects: List of object names
            
        Returns:
            True if successful
        """
        try:
            self.set_manager.add_objects_to_set(set_name, objects)
            return True
        except Exception as e:
            logger.error(f"Failed to add objects to set: {e}")
            return False
    
    def remove_objects_from_set(self, set_name: str, objects: List[str]) -> bool:
        """
        Remove objects from a Maya set.
        
        Args:
            set_name: Name of the set
            objects: List of object names
            
        Returns:
            True if successful
        """
        try:
            self.set_manager.remove_objects_from_set(set_name, objects)
            return True
        except Exception as e:
            logger.error(f"Failed to remove objects from set: {e}")
            return False
    
    def clear_set(self, set_name: str) -> bool:
        """
        Clear all objects from a Maya set.
        
        Args:
            set_name: Name of the set
            
        Returns:
            True if successful
        """
        try:
            self.set_manager.clear_set(set_name)
            return True
        except Exception as e:
            logger.error(f"Failed to clear set: {e}")
            return False
    
    def duplicate_export_group(self, index: int) -> Optional[int]:
        """
        Duplicate an export group.
        
        Args:
            index: Index of the group to duplicate
            
        Returns:
            Index of the new group, or None if failed
        """
        if 0 <= index < len(self.data["export_groups"]):
            original = self.data["export_groups"][index]
            original_set = original.get("set_name")
            
            if not original_set or not self.maya_scene.object_exists(original_set):
                return None
            
            try:
                new_name = original["name"] + "_copy"
                new_set_name = self.set_manager.duplicate_set(original_set, new_name)
                
                self.sync_from_scene()
                
                # Find new group index
                for i, group in enumerate(self.data["export_groups"]):
                    if group["set_name"] == new_set_name:
                        return i
                
                return len(self.data["export_groups"]) - 1
            except Exception as e:
                logger.error(f"Failed to duplicate group: {e}")
                return None
        return None
    
    def move_group_up(self, index: int) -> bool:
        """
        Move a group up in the list.
        
        Args:
            index: Index of the group to move
            
        Returns:
            True if successful
        """
        if index <= 0 or index >= len(self.group_order):
            return False
        
        # Swap in order list
        self.group_order[index], self.group_order[index - 1] = \
            self.group_order[index - 1], self.group_order[index]
        
        # Resync to apply new order
        self.sync_from_scene()
        logger.info(f"Moved group up to index {index - 1}")
        return True
    
    def move_group_down(self, index: int) -> bool:
        """
        Move a group down in the list.
        
        Args:
            index: Index of the group to move
            
        Returns:
            True if successful
        """
        if index < 0 or index >= len(self.group_order) - 1:
            return False
        
        # Swap in order list
        self.group_order[index], self.group_order[index + 1] = \
            self.group_order[index + 1], self.group_order[index]
        
        # Resync to apply new order
        self.sync_from_scene()
        logger.info(f"Moved group down to index {index + 1}")
        return True
    
    def update_fbx_settings(self, settings: dict) -> None:
        """
        Update FBX export settings.
        
        Args:
            settings: Settings dictionary to update
        """
        self.data["fbx_settings"].update(settings)
    
    def get_fbx_settings(self) -> FBXSettingsDict:
        """
        Get FBX export settings.
        
        Returns:
            FBX settings dictionary
        """
        return self.data["fbx_settings"]
    
    def set_expanded_groups(self, expanded_set_names: List[str]) -> None:
        """
        Set which groups are expanded.
        
        Args:
            expanded_set_names: List of set_names that are expanded
        """
        self.data["expanded_groups"] = expanded_set_names
    
    def get_expanded_groups(self) -> List[str]:
        """
        Get which groups are expanded.
        
        Returns:
            List of set_names that are expanded
        """
        return self.data.get("expanded_groups", [])

