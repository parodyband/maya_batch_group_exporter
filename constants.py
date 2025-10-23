"""
Constants
All magic numbers and constant values used throughout the application.
"""

# Maya set naming
SET_PREFIX = "batchExport_"

# UI refresh timing (milliseconds)
REFRESH_INTERVAL_MS = 500

# UI dimensions
BUTTON_HEIGHT_STANDARD = 24
BUTTON_HEIGHT_ACTION = 26
BUTTON_HEIGHT_EXPORT = 30
LABEL_WIDTH_STANDARD = 60
BROWSE_BUTTON_WIDTH = 32
MIN_WINDOW_WIDTH = 400
PREFERRED_WINDOW_WIDTH = 600

# UI spacing
SPACING_SMALL = 4
SPACING_MEDIUM = 6
SPACING_LARGE = 8
SPACING_XLARGE = 12

# UI margins
MARGIN_SMALL = 4
MARGIN_MEDIUM = 6
MARGIN_LARGE = 8

# Tree widget settings
TREE_ITEM_PADDING = 2

# Default FBX settings
DEFAULT_UP_AXIS = "Y"
DEFAULT_TRIANGULATE = False
DEFAULT_CONVERT_UNIT = "cm"
DEFAULT_EXPORT_DIRECTORY = ""
DEFAULT_FILE_PREFIX = ""

# Available options
AVAILABLE_UP_AXES = ["Y", "Z"]
AVAILABLE_UNITS = ["cm", "m", "mm", "in", "ft"]

# File extensions
JSON_EXTENSION = ".json"
FBX_EXTENSION = ".fbx"
EXPORT_GROUPS_SUFFIX = "_export_groups"

# Fallback file name for untitled scenes
UNTITLED_SCENE_FILENAME = "maya_export_groups_untitled.json"

