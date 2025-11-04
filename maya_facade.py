"""
Maya API Facade
Provides abstraction layer over Maya commands for testability and dependency injection.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Tuple
import maya.cmds as cmds
import maya.mel as mel


class MayaSceneInterface(ABC):
    """Abstract interface for Maya scene operations."""
    
    @abstractmethod
    def object_exists(self, name: str) -> bool:
        """Check if an object exists in the scene."""
        pass
    
    @abstractmethod
    def create_set(self, name: str, empty: bool = True) -> str:
        """Create a new object set."""
        pass
    
    @abstractmethod
    def delete_object(self, name: str) -> None:
        """Delete an object from the scene."""
        pass
    
    @abstractmethod
    def rename_object(self, old_name: str, new_name: str) -> str:
        """Rename an object."""
        pass
    
    @abstractmethod
    def list_objects(self, object_type: Optional[str] = None) -> List[str]:
        """List objects in the scene, optionally filtered by type."""
        pass
    
    @abstractmethod
    def get_set_members(self, set_name: str) -> List[str]:
        """Get members of an object set."""
        pass
    
    @abstractmethod
    def add_to_set(self, objects: List[str], set_name: str) -> None:
        """Add objects to a set."""
        pass
    
    @abstractmethod
    def remove_from_set(self, objects: List[str], set_name: str) -> None:
        """Remove objects from a set."""
        pass
    
    @abstractmethod
    def get_selection(self, long: bool = False) -> List[str]:
        """Get currently selected objects."""
        pass
    
    @abstractmethod
    def select(self, objects: Optional[List[str]] = None, replace: bool = True, clear: bool = False) -> None:
        """Select objects in the scene."""
        pass
    
    @abstractmethod
    def refresh_viewport(self) -> None:
        """Force Maya to refresh/update the viewport."""
        pass
    
    @abstractmethod
    def get_isolate_set(self, panel: str) -> Optional[str]:
        """Get the name of the isolation set for a panel."""
        pass
    
    @abstractmethod
    def add_to_isolate_set(self, panel: str, objects: List[str]) -> None:
        """Add the specified objects to the panel's isolation set."""
        pass

    @abstractmethod
    def clear_isolate_set(self, panel: str) -> None:
        """Clear all objects from the panel's isolation set."""
        pass

    @abstractmethod
    def get_scene_name(self) -> str:
        """Get the current scene file path."""
        pass
    
    @abstractmethod
    def load_plugin(self, plugin_name: str) -> None:
        """Load a Maya plugin."""
        pass
    
    @abstractmethod
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded."""
        pass
    
    @abstractmethod
    def eval_mel(self, command: str) -> Any:
        """Execute a MEL command."""
        pass
    
    @abstractmethod
    def get_active_panel(self) -> Optional[str]:
        """Get the currently active panel."""
        pass
    
    @abstractmethod
    def get_panel_type(self, panel: str) -> str:
        """Get the type of a panel."""
        pass
    
    @abstractmethod
    def isolate_select(self, panel: str, state: Optional[bool] = None, 
                      add_selected: bool = False, load_selected: bool = False,
                      add_dag_object: Optional[str] = None,
                      remove_dag_object: Optional[str] = None,
                      update: bool = False,
                      query: bool = False) -> Optional[bool]:
        """Control viewport isolation."""
        pass
    
    @abstractmethod
    def warning(self, message: str) -> None:
        """Display a warning message."""
        pass
    
    @abstractmethod
    def workspace_control_exists(self, name: str) -> bool:
        """Check if a workspace control exists."""
        pass
    
    @abstractmethod
    def delete_ui(self, name: str) -> None:
        """Delete a UI element."""
        pass
    
    @abstractmethod
    def create_workspace_control(self, name: str, **kwargs) -> None:
        """Create a workspace control."""
        pass
    
    @abstractmethod
    def find_control(self, name: str) -> Optional[int]:
        """Find a control by name."""
        pass
    
    @abstractmethod
    def get_world_position(self, obj: str) -> Optional[Tuple[float, float, float]]:
        """Get the world space position of an object."""
        pass
    
    @abstractmethod
    def get_world_rotation(self, obj: str) -> Optional[Tuple[float, float, float]]:
        """Get the world space rotation of an object."""
        pass
    
    @abstractmethod
    def get_world_scale(self, obj: str) -> Optional[Tuple[float, float, float]]:
        """Get the world space scale of an object."""
        pass
    
    @abstractmethod
    def is_curve(self, obj: str) -> bool:
        """Check if an object is a NURBS curve."""
        pass
    
    @abstractmethod
    def get_curve_cvs(self, curve: str) -> Optional[List[Tuple[float, float, float]]]:
        """Get all CV positions for a curve in world space."""
        pass
    
    @abstractmethod
    def get_curve_degree(self, curve: str) -> Optional[int]:
        """Get the degree of a curve."""
        pass


class MayaSceneAdapter(MayaSceneInterface):
    """Concrete implementation of Maya scene operations using maya.cmds."""
    
    def object_exists(self, name: str) -> bool:
        """Check if an object exists in the scene."""
        return cmds.objExists(name)
    
    def create_set(self, name: str, empty: bool = True) -> str:
        """Create a new object set."""
        return cmds.sets(name=name, empty=empty)
    
    def delete_object(self, name: str) -> None:
        """Delete an object from the scene."""
        cmds.delete(name)
    
    def rename_object(self, old_name: str, new_name: str) -> str:
        """Rename an object."""
        return cmds.rename(old_name, new_name)
    
    def list_objects(self, object_type: Optional[str] = None) -> List[str]:
        """List objects in the scene, optionally filtered by type."""
        result = cmds.ls(type=object_type) if object_type else cmds.ls()
        return result or []
    
    def get_set_members(self, set_name: str) -> List[str]:
        """Get members of an object set."""
        if not self.object_exists(set_name):
            return []
        result = cmds.sets(set_name, query=True)
        return result or []
    
    def add_to_set(self, objects: List[str], set_name: str) -> None:
        """Add objects to a set."""
        if objects and self.object_exists(set_name):
            cmds.sets(objects, addElement=set_name)
    
    def remove_from_set(self, objects: List[str], set_name: str) -> None:
        """Remove objects from a set."""
        if objects and self.object_exists(set_name):
            cmds.sets(objects, remove=set_name)
    
    def get_selection(self, long: bool = False) -> List[str]:
        """Get currently selected objects."""
        result = cmds.ls(selection=True, long=long)
        return result or []
    
    def get_dag_path(self, node: str) -> Optional[str]:
        """Get the long (full DAG) path for a node if it exists."""
        if not node:
            return None
        try:
            long_paths = cmds.ls(node, long=True)
            if long_paths:
                return long_paths[0]
        except Exception:
            pass
        return node
    
    def select(self, objects: Optional[List[str]] = None, replace: bool = True, clear: bool = False) -> None:
        """Select objects in the scene."""
        if clear:
            cmds.select(clear=True)
        elif objects:
            cmds.select(objects, replace=replace)
    
    def refresh_viewport(self) -> None:
        """Force Maya to refresh/update the viewport."""
        cmds.refresh()
    
    def get_isolate_set(self, panel: str) -> Optional[str]:
        """Get the name of the isolation set for a panel."""
        try:
            # Maya creates a set named like "modelPanel4ViewSelectedSet" for isolation
            isolate_set = cmds.isolateSelect(panel, query=True, viewObjects=True)
            return isolate_set
        except Exception:
            return None
    
    def add_to_isolate_set(self, panel: str, objects: List[str]) -> None:
        """Add specified objects to the panel's isolation set."""
        if not objects:
            return
        for obj in objects:
            if obj and cmds.objExists(obj):
                cmds.isolateSelect(panel, addDagObject=obj)

    def clear_isolate_set(self, panel: str) -> None:
        """Clear all objects from the panel's isolation set."""
        # Turn isolation ON briefly to ensure the set exists
        was_on = cmds.isolateSelect(panel, query=True, state=True)
        if not was_on:
            cmds.isolateSelect(panel, state=True)
        
        # Now get and clear the set
        isolate_set = self.get_isolate_set(panel)
        if isolate_set and cmds.objExists(isolate_set):
            members = cmds.sets(isolate_set, query=True) or []
            if members:
                cmds.sets(members, remove=isolate_set)
        
        # Turn it back off if it was off
        if not was_on:
            cmds.isolateSelect(panel, state=False)

    def get_scene_name(self) -> str:
        """Get the current scene file path."""
        return cmds.file(query=True, sceneName=True)
    
    def load_plugin(self, plugin_name: str) -> None:
        """Load a Maya plugin."""
        cmds.loadPlugin(plugin_name)
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded."""
        return cmds.pluginInfo(plugin_name, query=True, loaded=True)
    
    def eval_mel(self, command: str) -> Any:
        """Execute a MEL command."""
        return mel.eval(command)
    
    def get_active_panel(self) -> Optional[str]:
        """Get the currently active panel."""
        panel = cmds.getPanel(withFocus=True)
        if not panel or cmds.getPanel(typeOf=panel) != "modelPanel":
            panel = cmds.playblast(activeEditor=True)
            if not panel or "modelPanel" not in panel:
                return None
        return panel
    
    def get_panel_type(self, panel: str) -> str:
        """Get the type of a panel."""
        return cmds.getPanel(typeOf=panel)
    
    def isolate_select(self, panel: str, state: Optional[bool] = None, 
                      add_selected: bool = False, load_selected: bool = False,
                      add_dag_object: Optional[str] = None,
                      remove_dag_object: Optional[str] = None,
                      update: bool = False,
                      query: bool = False) -> Optional[bool]:
        """Control viewport isolation."""
        if query:
            return cmds.isolateSelect(panel, query=True, state=True)
        
        if state is not None:
            # Convert boolean to int for Maya (1/0 instead of True/False)
            cmds.isolateSelect(panel, state=int(state))
            
        if update:
            # Update replaces the isolation set with current selection (clears old objects)
            cmds.isolateSelect(panel, update=True)
        elif remove_dag_object:
            # Remove specific object from isolation set
            cmds.isolateSelect(panel, removeDagObject=remove_dag_object)
        elif add_dag_object:
            # Add specific object to isolation set
            cmds.isolateSelect(panel, addDagObject=add_dag_object)
        elif load_selected:
            cmds.isolateSelect(panel, loadSelected=True)
        elif add_selected:
            cmds.isolateSelect(panel, addSelected=True)
            
        return None
    
    def warning(self, message: str) -> None:
        """Display a warning message."""
        cmds.warning(message)
    
    def workspace_control_exists(self, name: str) -> bool:
        """Check if a workspace control exists."""
        return cmds.workspaceControl(name, exists=True)
    
    def delete_ui(self, name: str) -> None:
        """Delete a UI element."""
        cmds.deleteUI(name)
    
    def create_workspace_control(self, name: str, **kwargs) -> None:
        """Create a workspace control."""
        cmds.workspaceControl(name, **kwargs)
    
    def find_control(self, name: str) -> Optional[int]:
        """Find a control by name."""
        from maya import OpenMayaUI as omui
        control_ptr = omui.MQtUtil.findControl(name)
        return int(control_ptr) if control_ptr else None
    
    def get_world_position(self, obj: str) -> Optional[Tuple[float, float, float]]:
        """Get the world space position of an object."""
        try:
            if not cmds.objExists(obj):
                return None
            pos = cmds.xform(obj, query=True, worldSpace=True, translation=True)
            return (pos[0], pos[1], pos[2])
        except Exception:
            return None
    
    def get_world_rotation(self, obj: str) -> Optional[Tuple[float, float, float]]:
        """Get the world space rotation of an object."""
        try:
            if not cmds.objExists(obj):
                return None
            rot = cmds.xform(obj, query=True, worldSpace=True, rotation=True)
            return (rot[0], rot[1], rot[2])
        except Exception:
            return None
    
    def get_world_scale(self, obj: str) -> Optional[Tuple[float, float, float]]:
        """Get the world space scale of an object."""
        try:
            if not cmds.objExists(obj):
                return None
            scale = cmds.xform(obj, query=True, worldSpace=True, scale=True)
            return (scale[0], scale[1], scale[2])
        except Exception:
            return None
    
    def is_curve(self, obj: str) -> bool:
        """Check if an object is a NURBS curve."""
        try:
            if not cmds.objExists(obj):
                return False
            # Check if it's a transform with a curve shape
            shapes = cmds.listRelatives(obj, shapes=True, type='nurbsCurve') or []
            if shapes:
                return True
            # Check if it's directly a curve shape
            return cmds.objectType(obj) == 'nurbsCurve'
        except Exception:
            return False
    
    def get_curve_cvs(self, curve: str) -> Optional[List[Tuple[float, float, float]]]:
        """Get all CV positions for a curve in world space."""
        try:
            if not cmds.objExists(curve):
                return None
            
            # Get the curve shape if it's a transform
            curve_shape = curve
            if cmds.objectType(curve) == 'transform':
                shapes = cmds.listRelatives(curve, shapes=True, type='nurbsCurve')
                if not shapes:
                    return None
                curve_shape = shapes[0]
            
            # Get number of CVs
            degree = cmds.getAttr(f"{curve_shape}.degree")
            spans = cmds.getAttr(f"{curve_shape}.spans")
            num_cvs = spans + degree
            
            # Get CV positions in world space
            cvs = []
            for i in range(num_cvs):
                pos = cmds.xform(f"{curve_shape}.cv[{i}]", query=True, worldSpace=True, translation=True)
                cvs.append((pos[0], pos[1], pos[2]))
            
            return cvs
        except Exception:
            return None
    
    def get_curve_degree(self, curve: str) -> Optional[int]:
        """Get the degree of a curve."""
        try:
            if not cmds.objExists(curve):
                return None
            
            # Get the curve shape if it's a transform
            curve_shape = curve
            if cmds.objectType(curve) == 'transform':
                shapes = cmds.listRelatives(curve, shapes=True, type='nurbsCurve')
                if not shapes:
                    return None
                curve_shape = shapes[0]
            
            return cmds.getAttr(f"{curve_shape}.degree")
        except Exception:
            return None

