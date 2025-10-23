"""
Data Manager for Batch Exporter
Handles Maya sets and JSON persistence for export settings.
"""

import json
import os
import maya.cmds as cmds


class DataManager:
    SET_PREFIX = "batchExport_"
    
    def __init__(self):
        self.data = {
            "export_groups": [],
            "fbx_settings": self._get_default_fbx_settings()
        }
    
    def _get_default_fbx_settings(self):
        return {
            "up_axis": "Y",
            "triangulate": False,
            "convert_unit": "cm",
            "export_directory": "",
            "file_prefix": "",
        }
    
    def _create_set_name(self, group_name):
        """Create a unique Maya set name from group name."""
        base_name = self.SET_PREFIX + group_name.replace(" ", "_")
        return base_name
    
    def _get_unique_set_name(self, desired_name):
        """Get a unique set name that doesn't exist in the scene."""
        set_name = self._create_set_name(desired_name)
        
        if not cmds.objExists(set_name):
            return set_name
        
        counter = 1
        while cmds.objExists(f"{set_name}_{counter}"):
            counter += 1
        
        return f"{set_name}_{counter}"
    
    def get_json_path(self):
        """Get the JSON file path based on current Maya scene."""
        scene_path = cmds.file(query=True, sceneName=True)
        
        if scene_path:
            base_name = os.path.splitext(scene_path)[0]
            json_path = base_name + "_export_groups.json"
        else:
            json_path = os.path.join(
                os.path.expanduser("~"),
                "maya_export_groups_untitled.json"
            )
        
        return json_path
    
    def save_to_file(self, file_path=None):
        """Save export groups and settings to JSON file."""
        if file_path is None:
            file_path = self.get_json_path()
        
        self._sync_data_from_scene()
        
        try:
            with open(file_path, 'w') as f:
                json.dump(self.data, f, indent=4)
            return True, file_path
        except Exception as e:
            return False, str(e)
    
    def _sync_data_from_scene(self):
        """Sync data structure from Maya sets in the scene."""
        try:
            self.data["export_groups"] = []
            
            all_sets = cmds.ls(type="objectSet") or []
            export_sets = [s for s in all_sets if s.startswith(self.SET_PREFIX)]
            
            for set_name in export_sets:
                if cmds.objExists(set_name):
                    display_name = set_name[len(self.SET_PREFIX):]
                    
                    group = {
                        "name": display_name,
                        "set_name": set_name
                    }
                    self.data["export_groups"].append(group)
        except Exception as e:
            print(f"Error syncing data from scene: {e}")
    
    def load_from_file(self, file_path=None):
        """Load export groups and settings from JSON file."""
        if file_path is None:
            file_path = self.get_json_path()
        
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        try:
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)
                
                if "fbx_settings" not in loaded_data:
                    loaded_data["fbx_settings"] = self._get_default_fbx_settings()
                
                self.data["fbx_settings"] = loaded_data["fbx_settings"]
                
                self._create_sets_from_data(loaded_data.get("export_groups", []))
                self._sync_data_from_scene()
                
            return True, file_path
        except Exception as e:
            return False, str(e)
    
    def _create_sets_from_data(self, groups_data):
        """Create or update Maya sets from loaded JSON data."""
        for group_data in groups_data:
            set_name = group_data.get("set_name")
            display_name = group_data.get("name", "untitled")
            
            if not set_name:
                set_name = self._get_unique_set_name(display_name)
            
            if not cmds.objExists(set_name):
                cmds.sets(name=set_name, empty=True)
    
    def add_export_group(self, name):
        """Add a new export group as a Maya set."""
        set_name = self._get_unique_set_name(name)
        
        cmds.sets(name=set_name, empty=True)
        
        self._sync_data_from_scene()
        
        for i, group in enumerate(self.data["export_groups"]):
            if group["set_name"] == set_name:
                return i
        
        return len(self.data["export_groups"]) - 1
    
    def remove_export_group(self, index):
        """Remove an export group by index."""
        if 0 <= index < len(self.data["export_groups"]):
            group = self.data["export_groups"][index]
            set_name = group.get("set_name")
            
            if set_name and cmds.objExists(set_name):
                cmds.delete(set_name)
            
            self._sync_data_from_scene()
            return True
        return False
    
    def update_export_group(self, index, name=None):
        """Update an export group."""
        if 0 <= index < len(self.data["export_groups"]):
            group = self.data["export_groups"][index]
            set_name = group.get("set_name")
            
            if not set_name or not cmds.objExists(set_name):
                return False
            
            if name is not None:
                new_set_name = self._get_unique_set_name(name)
                if new_set_name != set_name:
                    cmds.rename(set_name, new_set_name)
                    set_name = new_set_name
            
            self._sync_data_from_scene()
            return True
        return False
    
    def get_export_group(self, index):
        """Get an export group by index."""
        self._sync_data_from_scene()
        if 0 <= index < len(self.data["export_groups"]):
            return self.data["export_groups"][index]
        return None
    
    def get_all_export_groups(self):
        """Get all export groups."""
        self._sync_data_from_scene()
        return self.data["export_groups"]
    
    def get_set_objects(self, set_name):
        """Get objects in a Maya set."""
        if cmds.objExists(set_name):
            members = cmds.sets(set_name, query=True) or []
            clean_members = []
            for member in members:
                if '.vtx[' in member:
                    clean_members.append(member.split('.vtx[')[0])
                else:
                    clean_members.append(member)
            return clean_members
        return []
    
    def add_objects_to_set(self, set_name, objects):
        """Add objects to a Maya set."""
        if cmds.objExists(set_name) and objects:
            try:
                cmds.sets(objects, addElement=set_name)
                return True
            except:
                return False
        return False
    
    def remove_objects_from_set(self, set_name, objects):
        """Remove objects from a Maya set."""
        if cmds.objExists(set_name) and objects:
            try:
                cmds.sets(objects, remove=set_name)
                return True
            except:
                return False
        return False
    
    def clear_set(self, set_name):
        """Clear all objects from a Maya set."""
        if cmds.objExists(set_name):
            members = cmds.sets(set_name, query=True) or []
            if members:
                cmds.sets(members, remove=set_name)
            return True
        return False
    
    def duplicate_export_group(self, index):
        """Duplicate an export group."""
        if 0 <= index < len(self.data["export_groups"]):
            original = self.data["export_groups"][index]
            original_set = original.get("set_name")
            
            if not original_set or not cmds.objExists(original_set):
                return None
            
            new_name = original["name"] + "_copy"
            new_set_name = self._get_unique_set_name(new_name)
            
            original_objects = self.get_set_objects(original_set)
            
            cmds.sets(original_objects, name=new_set_name)
            
            self._sync_data_from_scene()
            
            for i, group in enumerate(self.data["export_groups"]):
                if group["set_name"] == new_set_name:
                    return i
            
            return len(self.data["export_groups"]) - 1
        return None
    
    def update_fbx_settings(self, settings):
        """Update FBX export settings."""
        self.data["fbx_settings"].update(settings)
    
    def get_fbx_settings(self):
        """Get FBX export settings."""
        return self.data["fbx_settings"]

