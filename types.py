"""
Type Definitions
Custom types and type aliases for the batch exporter.
"""

from typing import TypedDict, List, Literal


class ExportGroupDict(TypedDict):
    """Type definition for export group data structure."""
    name: str
    set_name: str


class FBXSettingsDict(TypedDict):
    """Type definition for FBX export settings."""
    up_axis: Literal["Y", "Z"]
    triangulate: bool
    convert_unit: Literal["cm", "m", "mm", "in", "ft"]
    export_directory: str
    file_prefix: str


class ExportDataDict(TypedDict):
    """Type definition for complete export configuration."""
    export_groups: List[ExportGroupDict]
    fbx_settings: FBXSettingsDict


class ExportResultDict(TypedDict):
    """Type definition for export operation result."""
    group_name: str
    success: bool
    message: str

