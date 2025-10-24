# Maya Batch Exporter

Batch export FBX files from Maya. Create export groups, configure settings, and export everything at once.

## Installation

Copy the `maya_batch_group_exporter` folder to your Maya scripts directory:
- Windows: `C:\Users\<username>\Documents\maya\scripts\`
- Mac: `~/Library/Preferences/Autodesk/maya/scripts/`
- Linux: `~/maya/scripts/`

## How to Use

Run this in Maya's Script Editor:

```python
from maya_batch_group_exporter import show_batch_exporter
show_batch_exporter()
```

Or if you're developing and want to reload:

```python
import sys
for key in list(sys.modules.keys()):
    if key.startswith('maya_batch_group_exporter'):
        del sys.modules[key]

from maya_batch_group_exporter import show_batch_exporter
show_batch_exporter()
```

## Basic Workflow

1. Click "+ Group" to create an export group
2. Select objects in your scene, select a group, click "+ Add Selected"
3. Set your export directory and FBX settings
4. Click "Export Selected" or "Export All"

Your settings are automatically saved with the Maya scene.

## Features

- Export groups are stored as Maya sets, so objects stay linked even if you rename them
- Save/load presets as JSON
- Configure FBX export settings (triangulate, up axis, etc.)
- Batch export multiple groups at once

## Project Structure

The code is organized to be testable and maintainable:

```
maya_batch_group_exporter/
├── __init__.py
├── container.py           # Dependency injection
├── maya_facade.py         # Wraps Maya API
├── set_manager.py         # Handles Maya sets
├── data_manager.py        # Manages export groups
├── persistence.py         # JSON save/load
├── validators.py          # Input validation
├── events.py              # Event system
├── exporters/
│   ├── base.py
│   ├── fbx_exporter.py
│   └── export_service.py
└── ui/
    ├── main_window.py
    └── widgets/
```

## Technical Notes

- Export groups use Maya sets with the prefix `batchExport_`
- Config files are named `[scene_name]_export_groups.json`
- The UI updates automatically when Maya's selection changes
- Works with Maya 2018+ (Python 2.7 or 3.x)

## Debugging

Turn on debug logging:

```python
from maya_batch_group_exporter.logger import set_log_level
import logging

set_log_level(logging.DEBUG)
```
