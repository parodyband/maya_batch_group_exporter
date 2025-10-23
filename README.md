# Maya Batch Exporter v2.0

A professional tool for managing export groups and batch exporting FBX files with configurable settings.

**Version 2.0** - Complete architectural refactoring following SOLID principles.

## Features

- **SOLID Architecture**: Clean separation of concerns with dependency injection
- **Testable Design**: Abstract interfaces enable mocking and unit testing
- **Streamlined UI**: Modular widget components with clear responsibilities
- **Auto-Refresh**: Event-driven updates instead of polling
- **Maya Sets Integration**: Export groups stored as Maya sets
- **Rename-Safe**: Objects stay linked to groups even after renaming
- **JSON Persistence**: Save and load configurations
- **Batch Export**: Export multiple groups with consistent settings

## Installation

1. Copy the entire `maya_batch_group_exporter` directory to your Maya scripts folder:
   - Windows: `C:\Users\<username>\Documents\maya\scripts\`
   - Mac: `~/Library/Preferences/Autodesk/maya/scripts/`
   - Linux: `~/maya/scripts/`

2. Restart Maya or reload scripts

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
   - Click "+ Group" button
   - Name your export group
   - Each group is stored as a Maya object set

2. **Add Objects to Groups**
   - Select objects in Maya scene
   - Select the export group in the UI
   - Click "+ Add Selected"

3. **Configure Export Settings**
   - Set export directory and optional file prefix
   - Configure FBX settings (triangulate, up axis, unit conversion)

4. **Export**
   - "Export Selected" - Export currently selected group
   - "Export All" - Batch export all groups

5. **Save/Load Configuration**
   - "Save Preset" - Save groups and settings to JSON
   - "Load Preset" - Load previously saved configuration

## Architecture

### Core Principles

The refactored architecture follows SOLID principles:

- **Single Responsibility**: Each class has one clear purpose
- **Open/Closed**: Extensible through abstractions
- **Liskov Substitution**: Interfaces can be mocked for testing
- **Interface Segregation**: Focused interfaces
- **Dependency Inversion**: Depends on abstractions, not concretions

### Project Structure

```
maya_batch_group_exporter/
├── __init__.py                 # Entry point
├── container.py                # Dependency injection container
├── constants.py                # Configuration constants
├── types.py                    # Type definitions
├── logger.py                   # Logging infrastructure
├── exceptions.py               # Custom exceptions
│
├── maya_facade.py              # Maya API abstraction
├── validators.py               # Input validation
├── context_managers.py         # Resource management
├── events.py                   # Event bus for pub-sub
│
├── set_manager.py              # Maya set operations
├── persistence.py              # JSON config persistence
├── data_manager.py             # Orchestrates data operations
│
├── exporters/
│   ├── __init__.py
│   ├── base.py                 # Abstract exporter interface
│   ├── fbx_exporter.py         # FBX implementation
│   └── export_service.py       # Export coordination
│
└── ui/
    ├── __init__.py
    ├── main_window.py          # Main UI coordinator
    ├── dialogs.py              # Reusable dialogs
    ├── state_manager.py        # UI state management
    └── widgets/
        ├── __init__.py
        ├── tree_view.py        # Export tree widget
        ├── toolbar.py          # Toolbar with controls
        ├── export_settings_panel.py
        └── fbx_settings_panel.py
```

### Key Components

#### Maya Facade (`maya_facade.py`)
- Abstracts Maya API behind testable interfaces
- Enables dependency injection and mocking
- `MayaSceneInterface` (ABC) / `MayaSceneAdapter` (implementation)

#### Data Layer
- **SetManager**: Maya set operations only
- **ConfigRepository**: JSON persistence abstraction
- **DataManager**: Orchestrates operations using composition

#### Export Layer
- **Exporter** (ABC): Abstract interface for testability
- **FBXExporter**: Concrete FBX implementation
- **ExportService**: Coordinates export operations with progress tracking

#### UI Layer
- **Modular Widgets**: Each widget has single responsibility
- **State Managers**: Separate selection and isolation state
- **Event-Driven**: Uses signals for decoupled communication
- **Main Window**: Slim coordinator (<400 lines)

#### Infrastructure
- **Container**: Dependency injection container
- **EventBus**: Pub-sub for decoupled components
- **Context Managers**: Resource management (selection, timers)
- **Validators**: Input validation with clear errors
- **Logger**: Integrated with Maya's script editor

## Extension Points

### Adding Custom Validation

```python
from validators import NameValidator

# Extend validation rules
class CustomNameValidator(NameValidator):
    @staticmethod
    def validate_group_name(name: str) -> str:
        name = super().validate_group_name(name)
        # Add custom validation
        if "invalid" in name.lower():
            raise ValidationError("Name cannot contain 'invalid'")
        return name
```

### Custom Export Post-Processing

```python
from exporters.export_service import ExportService

class CustomExportService(ExportService):
    def export_single_group(self, group, settings):
        result = super().export_single_group(group, settings)
        # Add post-processing
        if result["success"]:
            self._apply_custom_processing(result)
        return result
```

### Adding Event Listeners

```python
from container import get_container
from events import GroupAddedEvent

container = get_container()
event_bus = container.get_event_bus()

def on_group_added(event: GroupAddedEvent):
    print(f"Group added: {event.group_name}")

event_bus.subscribe(GroupAddedEvent, on_group_added)
```

## Testing

The architecture enables comprehensive testing:

```python
# Example: Testing SetManager with mock Maya
from set_manager import SetManager
from tests.mocks.mock_maya_scene import MockMayaScene

def test_create_set():
    mock_maya = MockMayaScene()
    manager = SetManager(mock_maya)
    
    set_name = manager.create_set("TestGroup")
    assert mock_maya.object_exists(set_name)
```

## Technical Details

### Maya Sets
- Export groups implemented as Maya object sets (prefix: `batchExport_`)
- Sets maintain object references automatically
- Objects stay linked even after renaming or reparenting
- Sets saved with Maya scene file

### File Storage
- Configuration auto-saved/loaded based on Maya scene name
- Format: `[scene_name]_export_groups.json`
- Contains set names, export paths, and FBX settings
- Object membership stored in Maya scene itself

### Performance
- Event-driven updates (no unnecessary polling)
- Differential tree updates (only modified items)
- Non-blocking exports (background thread support ready)

## Breaking Changes from v1.0

**v2.0 is NOT backwards compatible with v1.0 JSON configs.**

Old configurations will need to be recreated. This is a complete architectural rewrite following SOLID principles.

To migrate:
1. Note your old export groups and settings
2. Recreate groups in v2.0
3. Reconfigure settings
4. Save new preset

## Development

### Requirements
- Maya 2018+ (Python 2.7 or 3.x)
- PySide2 or PySide6

### Debugging

Enable debug logging:

```python
from maya_batch_group_exporter.logger import set_log_level
import logging

set_log_level(logging.DEBUG)
```

### Reset Container

For development/testing:

```python
from maya_batch_group_exporter import reset_container

# Reset and reinitialize
reset_container()
```

## License

MIT License - See LICENSE file for details

## Credits

**Version 2.0** - Complete SOLID refactoring
- Dependency injection architecture
- Modular widget system
- Comprehensive error handling
- Full type annotations
- Testable design

**Version 1.0** - Initial release
- Basic export group management
- FBX export functionality
