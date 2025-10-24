"""
State Managers
Manage UI state like selection and viewport isolation.
"""

from typing import Optional, List
from ..maya_facade import MayaSceneInterface
from ..data_manager import DataManager
from ..logger import get_logger

logger = get_logger(__name__)


class SelectionStateManager:
    """Manages selection state for the tree view."""
    
    def __init__(self, data_manager: DataManager, maya_scene: MayaSceneInterface):
        """
        Initialize the selection state manager.
        
        Args:
            data_manager: Data manager instance
            maya_scene: Maya scene interface
        """
        self.data_manager = data_manager
        self.maya_scene = maya_scene
        self.current_group_set_name: Optional[str] = None
    
    def set_current_group(self, index: Optional[int]) -> None:
        """
        Set the current group by index.
        
        Args:
            index: Group index
        """
        if index is not None:
            group = self.data_manager.get_export_group(index)
            if group:
                self.current_group_set_name = group.get("set_name")
                logger.debug(f"Set current group to: {self.current_group_set_name}")
            else:
                self.current_group_set_name = None
        else:
            self.current_group_set_name = None
    
    def get_current_group_index(self) -> Optional[int]:
        """
        Get the current group index.
        
        Returns:
            Group index, or None
        """
        if not self.current_group_set_name:
            return None
        
        # Find current index by set_name
        groups = self.data_manager.get_all_export_groups()
        for i, group in enumerate(groups):
            if group.get("set_name") == self.current_group_set_name:
                return i
        
        return None
    
    def select_objects_in_scene(self, object_names: List[str]) -> None:
        """
        Select objects in Maya scene.
        
        Args:
            object_names: List of object names to select
        """
        if object_names:
            try:
                self.maya_scene.select(object_names, replace=True)
                logger.info(f"Selected {len(object_names)} objects in scene")
            except Exception as e:
                logger.error(f"Failed to select objects in scene: {e}")
    
    def add_selected_scene_objects_to_current_group(self) -> bool:
        """
        Add selected scene objects to the current group.
        
        Returns:
            True if successful
        """
        try:
            if not self.current_group_set_name:
                logger.warning("No current group selected")
                return False
            
            selected = self.maya_scene.get_selection(long=True)
            
            if not selected:
                logger.warning("No objects selected in scene")
                return False
            
            success = self.data_manager.add_objects_to_set(self.current_group_set_name, selected)
            if success:
                logger.info(f"Added {len(selected)} objects to group {self.current_group_set_name}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to add selected objects to group: {e}")
            return False


class IsolationStateManager:
    """Manages viewport isolation state."""
    
    def __init__(self, data_manager: DataManager, maya_scene: MayaSceneInterface):
        """
        Initialize the isolation state manager.
        
        Args:
            data_manager: Data manager instance
            maya_scene: Maya scene interface
        """
        self.data_manager = data_manager
        self.maya_scene = maya_scene
        self.is_isolated = False
        self.isolated_panel: Optional[str] = None
    
    def isolate_group(self, group_index: int) -> bool:
        """
        Isolate a group in the active viewport.
        
        Args:
            group_index: Index of the group to isolate
            
        Returns:
            True if successful
        """
        try:
            group = self.data_manager.get_export_group(group_index)
            if not group:
                logger.error(f"Group not found at index {group_index}")
                return False
            
            set_name = group.get("set_name")
            if not set_name:
                logger.error("Group has no set name")
                return False
            
            objects = self.data_manager.get_set_objects(set_name)
            if not objects:
                logger.warning(f"No objects in group '{group.get('name')}'")
                return False
            
            # Get active panel
            active_panel = self.maya_scene.get_active_panel()
            if not active_panel:
                logger.warning("No active model panel found")
                return False
            
            logger.info(f"Isolating {len(objects)} objects from group '{group.get('name')}'")
            
            # Turn OFF isolation
            self.maya_scene.isolate_select(active_panel, state=False)
            
            # Turn ON isolation first to create/activate the set
            self.maya_scene.isolate_select(active_panel, state=True)
            
            # Get the isolation set (now it exists)
            isolate_set = self.maya_scene.get_isolate_set(active_panel)
            
            if isolate_set:
                logger.info(f"Isolation set name: {isolate_set}")
                
                try:
                    # Get current members
                    old_members = self.maya_scene.get_set_members(isolate_set)
                    logger.info(f"OLD MEMBERS IN SET: {len(old_members)} - {old_members[:5] if len(old_members) > 5 else old_members}")
                    
                    # Remove all old members
                    if old_members:
                        self.maya_scene.remove_from_set(old_members, isolate_set)
                        logger.info(f"REMOVED {len(old_members)} old objects")
                    
                    # Add ONLY our objects
                    if objects:
                        self.maya_scene.add_to_set(objects, isolate_set)
                        logger.info(f"ADDED {len(objects)} objects")
                        
                        # Verify
                        final_members = self.maya_scene.get_set_members(isolate_set)
                        logger.info(f"FINAL SET MEMBERS: {len(final_members)}")
                except Exception as e:
                    logger.error(f"Error manipulating isolation set: {e}")
            else:
                logger.warning("Could not find isolation set!")
            
            # Select the objects for visual feedback
            self.maya_scene.select(objects, replace=True)
            
            self.is_isolated = True
            self.isolated_panel = active_panel
            
            logger.info(f"Successfully isolated group '{group.get('name')}' in {active_panel}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to isolate group: {e}")
            return False
    
    def unisolate(self) -> bool:
        """
        Un-isolate the viewport.
        
        Returns:
            True if successful
        """
        if not self.isolated_panel:
            logger.debug("No panel is isolated")
            return True
        
        try:
            # Simply turn off isolation for the panel
            self.maya_scene.isolate_select(self.isolated_panel, state=False)
            logger.info(f"Unisolated panel {self.isolated_panel}")
        except Exception as e:
            # Panel might not exist anymore, which is fine
            logger.warning(f"Could not unisolate panel {self.isolated_panel}: {e}")
        
        # Always reset state, even if command failed
        self.is_isolated = False
        self.isolated_panel = None
        return True
    
    def toggle_isolation(self, group_index: int) -> bool:
        """
        Toggle isolation on/off.
        
        Args:
            group_index: Index of the group to isolate (if turning on)
            
        Returns:
            True if now isolated, False if unisolated
        """
        # Simple toggle: if anything is isolated, turn it off. Otherwise, turn it on.
        if self.is_isolated:
            logger.debug("Turning OFF isolation")
            self.unisolate()
            return False
        else:
            logger.debug(f"Turning ON isolation for group index {group_index}")
            self.isolate_group(group_index)
            return self.is_isolated
    
    def get_isolation_state(self) -> bool:
        """
        Get current isolation state.
        
        Returns:
            True if isolated
        """
        return self.is_isolated

