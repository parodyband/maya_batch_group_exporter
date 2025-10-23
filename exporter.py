"""
Exporter Module
Handles FBX export operations and settings management.
"""

import os
import maya.cmds as cmds
import maya.mel as mel


class FBXExporter:
    def __init__(self):
        self._load_fbx_plugin()
    
    def _load_fbx_plugin(self):
        """Ensure FBX plugin is loaded."""
        if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            try:
                cmds.loadPlugin("fbxmaya")
            except:
                cmds.warning("Could not load FBX plugin")
    
    def apply_fbx_settings(self, settings):
        """Apply FBX export settings using MEL commands."""
        try:
            mel.eval('FBXResetExport')
            
            if "up_axis" in settings:
                mel.eval(f'FBXExportUpAxis {settings["up_axis"]}')
            
            if "triangulate" in settings:
                value = "true" if settings["triangulate"] else "false"
                mel.eval(f'FBXExportTriangulate -v {value}')
            
            if "convert_unit" in settings:
                unit = settings["convert_unit"]
                mel.eval(f'FBXExportConvertUnitString "{unit}"')
            
            return True
        except Exception as e:
            cmds.warning(f"Error applying FBX settings: {str(e)}")
            return False
    
    def export_group(self, group, fbx_settings):
        """Export a single group with the given FBX settings."""
        name = group.get("name", "untitled")
        set_name = group.get("set_name")
        
        export_directory = fbx_settings.get("export_directory", "")
        file_prefix = fbx_settings.get("file_prefix", "")
        
        if not export_directory:
            cmds.warning(f"Export directory not set")
            return False, f"Export directory not set"
        
        if not set_name or not cmds.objExists(set_name):
            cmds.warning(f"Export set does not exist: {name}")
            return False, f"Export set does not exist for {name}"
        
        set_members = cmds.sets(set_name, query=True) or []
        
        if not set_members:
            cmds.warning(f"No objects in group: {name}")
            return False, f"No objects in group {name}"
        
        filename = f"{file_prefix}{name}.fbx"
        export_path = os.path.join(export_directory, filename)
        
        if not os.path.exists(export_directory):
            try:
                os.makedirs(export_directory)
            except Exception as e:
                msg = f"Could not create directory: {export_directory}"
                cmds.warning(msg)
                return False, msg
        
        previous_selection = cmds.ls(selection=True)
        
        try:
            self.apply_fbx_settings(fbx_settings)
            
            cmds.select(set_members, replace=True)
            
            mel.eval(f'FBXExport -f "{export_path}" -s')
            
            if previous_selection:
                cmds.select(previous_selection, replace=True)
            else:
                cmds.select(clear=True)
            
            return True, f"Exported {name} to {export_path}"
        
        except Exception as e:
            if previous_selection:
                cmds.select(previous_selection, replace=True)
            else:
                cmds.select(clear=True)
            
            msg = f"Error exporting group '{name}': {str(e)}"
            cmds.warning(msg)
            return False, msg
    
    def export_all_groups(self, groups, fbx_settings):
        """Export all groups."""
        results = []
        success_count = 0
        
        for i, group in enumerate(groups):
            success, message = self.export_group(group, fbx_settings)
            results.append((group.get("name", f"Group {i}"), success, message))
            
            if success:
                success_count += 1
        
        return results, success_count

