"""
Set Manager
Handles Maya object set operations.
"""

from typing import List, Optional
from .maya_facade import MayaSceneInterface
from .constants import SET_PREFIX
from .exceptions import SetNotFoundError, MayaOperationError
from .validators import NameValidator
from .logger import get_logger

logger = get_logger(__name__)


class SetManager:
    """Manages Maya object sets for export groups."""
    
    def __init__(self, maya_scene: MayaSceneInterface):
        """
        Initialize the SetManager.
        
        Args:
            maya_scene: Maya scene interface for operations
        """
        self.maya_scene = maya_scene
    
    def create_set_name(self, group_name: str) -> str:
        """
        Create a Maya set name from a group name.
        
        Args:
            group_name: Display name for the group
            
        Returns:
            Maya set name with prefix
        """
        sanitized = NameValidator.sanitize_for_maya_name(group_name)
        return SET_PREFIX + sanitized
    
    def get_unique_set_name(self, desired_name: str) -> str:
        """
        Get a unique set name that doesn't exist in the scene.
        
        Args:
            desired_name: Desired group name
            
        Returns:
            Unique set name
        """
        set_name = self.create_set_name(desired_name)
        
        if not self.maya_scene.object_exists(set_name):
            return set_name
        
        counter = 1
        while self.maya_scene.object_exists(f"{set_name}_{counter}"):
            counter += 1
        
        return f"{set_name}_{counter}"
    
    def create_set(self, group_name: str) -> str:
        """
        Create a new Maya object set.
        
        Args:
            group_name: Name for the export group
            
        Returns:
            The created set name
            
        Raises:
            MayaOperationError: If set creation fails
        """
        try:
            set_name = self.get_unique_set_name(group_name)
            self.maya_scene.create_set(set_name, empty=True)
            logger.info(f"Created set: {set_name}")
            return set_name
        except Exception as e:
            raise MayaOperationError(f"Failed to create set '{group_name}': {e}")
    
    def delete_set(self, set_name: str) -> None:
        """
        Delete a Maya object set.
        
        Args:
            set_name: Name of the set to delete
            
        Raises:
            SetNotFoundError: If set doesn't exist
            MayaOperationError: If deletion fails
        """
        if not self.maya_scene.object_exists(set_name):
            raise SetNotFoundError(f"Set does not exist: {set_name}")
        
        try:
            self.maya_scene.delete_object(set_name)
            logger.info(f"Deleted set: {set_name}")
        except Exception as e:
            raise MayaOperationError(f"Failed to delete set '{set_name}': {e}")
    
    def rename_set(self, old_name: str, new_display_name: str) -> str:
        """
        Rename a Maya object set.
        
        Args:
            old_name: Current set name
            new_display_name: New display name for the group
            
        Returns:
            The new set name
            
        Raises:
            SetNotFoundError: If set doesn't exist
            MayaOperationError: If rename fails
        """
        if not self.maya_scene.object_exists(old_name):
            raise SetNotFoundError(f"Set does not exist: {old_name}")
        
        try:
            new_set_name = self.get_unique_set_name(new_display_name)
            if new_set_name != old_name:
                actual_name = self.maya_scene.rename_object(old_name, new_set_name)
                logger.info(f"Renamed set from {old_name} to {actual_name}")
                return actual_name
            return old_name
        except Exception as e:
            raise MayaOperationError(f"Failed to rename set '{old_name}': {e}")
    
    def get_set_objects(self, set_name: str) -> List[str]:
        """
        Get objects in a Maya set.
        
        Args:
            set_name: Name of the set
            
        Returns:
            List of object names
            
        Raises:
            SetNotFoundError: If set doesn't exist
        """
        if not self.maya_scene.object_exists(set_name):
            raise SetNotFoundError(f"Set does not exist: {set_name}")
        
        try:
            members = self.maya_scene.get_set_members(set_name)
            
            # Clean up vertex selection syntax if present
            clean_members = []
            for member in members:
                if '.vtx[' in member:
                    clean_members.append(member.split('.vtx[')[0])
                else:
                    clean_members.append(member)
            
            return clean_members
        except Exception as e:
            raise MayaOperationError(f"Failed to get objects from set '{set_name}': {e}")
    
    def add_objects_to_set(self, set_name: str, objects: List[str]) -> None:
        """
        Add objects to a Maya set.
        
        Args:
            set_name: Name of the set
            objects: List of object names to add
            
        Raises:
            SetNotFoundError: If set doesn't exist
            MayaOperationError: If operation fails
        """
        if not self.maya_scene.object_exists(set_name):
            raise SetNotFoundError(f"Set does not exist: {set_name}")
        
        if not objects:
            return
        
        try:
            self.maya_scene.add_to_set(objects, set_name)
            logger.debug(f"Added {len(objects)} objects to set '{set_name}'")
        except Exception as e:
            raise MayaOperationError(f"Failed to add objects to set '{set_name}': {e}")
    
    def remove_objects_from_set(self, set_name: str, objects: List[str]) -> None:
        """
        Remove objects from a Maya set.
        
        Args:
            set_name: Name of the set
            objects: List of object names to remove
            
        Raises:
            SetNotFoundError: If set doesn't exist
            MayaOperationError: If operation fails
        """
        if not self.maya_scene.object_exists(set_name):
            raise SetNotFoundError(f"Set does not exist: {set_name}")
        
        if not objects:
            return
        
        try:
            self.maya_scene.remove_from_set(objects, set_name)
            logger.debug(f"Removed {len(objects)} objects from set '{set_name}'")
        except Exception as e:
            raise MayaOperationError(f"Failed to remove objects from set '{set_name}': {e}")
    
    def clear_set(self, set_name: str) -> None:
        """
        Clear all objects from a Maya set.
        
        Args:
            set_name: Name of the set
            
        Raises:
            SetNotFoundError: If set doesn't exist
            MayaOperationError: If operation fails
        """
        if not self.maya_scene.object_exists(set_name):
            raise SetNotFoundError(f"Set does not exist: {set_name}")
        
        try:
            members = self.maya_scene.get_set_members(set_name)
            if members:
                self.maya_scene.remove_from_set(members, set_name)
                logger.debug(f"Cleared {len(members)} objects from set '{set_name}'")
        except Exception as e:
            raise MayaOperationError(f"Failed to clear set '{set_name}': {e}")
    
    def list_export_sets(self) -> List[str]:
        """
        List all export sets in the scene.
        
        Returns:
            List of export set names
        """
        try:
            all_sets = self.maya_scene.list_objects(object_type="objectSet")
            export_sets = [s for s in all_sets if s.startswith(SET_PREFIX)]
            return export_sets
        except Exception as e:
            logger.error(f"Failed to list export sets: {e}")
            return []
    
    def duplicate_set(self, set_name: str, new_display_name: str) -> str:
        """
        Duplicate a Maya set with its contents.
        
        Args:
            set_name: Name of the set to duplicate
            new_display_name: Display name for the new set
            
        Returns:
            Name of the new set
            
        Raises:
            SetNotFoundError: If source set doesn't exist
            MayaOperationError: If duplication fails
        """
        if not self.maya_scene.object_exists(set_name):
            raise SetNotFoundError(f"Set does not exist: {set_name}")
        
        try:
            # Get objects from original set
            objects = self.get_set_objects(set_name)
            
            # Create new set
            new_set_name = self.get_unique_set_name(new_display_name)
            
            # Create set with objects
            if objects:
                # Maya's sets command can create and populate in one call
                self.maya_scene.create_set(new_set_name, empty=True)
                self.maya_scene.add_to_set(objects, new_set_name)
            else:
                self.maya_scene.create_set(new_set_name, empty=True)
            
            logger.info(f"Duplicated set '{set_name}' as '{new_set_name}'")
            return new_set_name
        except Exception as e:
            raise MayaOperationError(f"Failed to duplicate set '{set_name}': {e}")

