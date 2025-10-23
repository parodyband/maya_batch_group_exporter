# Maya Batch Exporter

A tool for managing export groups and batch exporting them with configurable FBX settings.

## Usage

### Launch the Tool

In Maya's Script Editor (Python tab), run:

```python
from maya_batch_group_exporter import show_batch_exporter
show_batch_exporter()
```

**Shelf Button Script (for easy reloading during development):**

```python
import sys
for key in list(sys.modules.keys()):
    if key.startswith('maya_batch_group_exporter'):
        del sys.modules[key]

from maya_batch_group_exporter import show_batch_exporter
show_batch_exporter()
```

### Workflow

1. **Create Export Groups**
   - Click "Add" in the Export Groups panel
   - Name your export group (e.g., "Character_LOD0", "Weapon_Handle")
   - Each group is stored as a Maya object set in your scene

2. **Add Objects to Groups**
   - Select objects in your Maya scene
   - Select the export group in the UI
   - Click "Add Selected" to add objects to the group
   - Objects are tracked using Maya sets, so they stay linked even after renaming

3. **Set Export Path**
   - Select a group
   - Enter or browse for the FBX export path in the Group Settings panel
   - Each group can export to a different file

4. **Configure FBX Settings**
   - Set global FBX export settings in the bottom panel
   - These settings apply to all exports
   - Options: Triangulate (on/off), Up Axis (Y/Z), and Unit conversion (cm/m/mm/in/ft)

5. **Export**
   - "Export Selected Group" - Export only the currently selected group
   - "Export All Groups" - Batch export all groups to their respective files

6. **Save/Load Configuration**
   - "Save Config" - Save groups and settings to a JSON file
   - "Load Config" - Load previously saved configuration
   - Auto-loads config based on current Maya scene name

## Features

- **Streamlined UI**: Compact, single-column tree interface
- **Auto-Refresh**: Tree view automatically updates every 0.5 seconds
- **Maya Sets Integration**: Export groups stored as Maya sets that survive object renaming, reparenting, and duplicating
- **Rename-Safe**: Objects stay linked to groups even after renaming
- **No Auto-Duplicate**: Duplicated objects stay OUT of export groups (not automatically added)
- **Simple FBX Controls**: Only the essential settings (Triangulate, Up Axis, Unit conversion)
- **JSON Persistence**: Save and load configurations for different projects
- **Batch Export**: Export multiple groups at once with consistent settings
- **Scene Integration**: Export groups are saved with your Maya scene and visible in the Outliner

## Technical Details

### Maya Sets

Export groups are implemented using Maya object sets (prefixed with `batchExport_`):
- Sets maintain object references automatically
- Objects stay linked even after renaming or reparenting
- Sets are saved with your Maya scene file
- Export settings are stored as custom attributes on the sets

### File Storage

Configuration files are automatically saved/loaded based on your Maya scene name:
- Format: `[scene_name]_export_groups.json`
- Contains: set names, export paths, and FBX settings
- For untitled scenes, config is saved to your home directory

The JSON file stores export settings while the actual object membership is stored in the Maya scene itself.

