"""
Main Window
Slim coordinator that composes widgets and connects signals.
"""

import os
import subprocess
from typing import Optional

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from maya import OpenMayaUI as omui

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken6 import wrapInstance

from ..container import get_container
from ..maya_facade import MayaSceneInterface
from ..data_manager import DataManager
from ..exporters.export_service import ExportService
from .widgets.tree_view import ExportTreeWidget
from .widgets.toolbar import ExportToolbar
from .widgets.export_settings_panel import ExportSettingsPanel
from .widgets.fbx_settings_panel import FBXSettingsPanel
from .state_manager import SelectionStateManager, IsolationStateManager
from .dialogs import (
    NewGroupDialog, RenameGroupDialog, ConfirmDeleteDialog,
    ExportResultsDialog, ConfirmExportDialog, InfoDialog
)
from ..context_managers import PausedTimerContext
from ..constants import (
    REFRESH_INTERVAL_MS, BUTTON_HEIGHT_STANDARD, BUTTON_HEIGHT_EXPORT,
    SPACING_SMALL, MARGIN_SMALL, SPACING_MEDIUM,
    MIN_WINDOW_WIDTH, PREFERRED_WINDOW_WIDTH
)
from ..logger import get_logger

logger = get_logger(__name__)


def get_maya_main_window():
    """Get Maya's main window as a Qt object."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class BatchExporterWindow(QtWidgets.QWidget):
    """
    Main window for the batch exporter.
    Composes widgets and coordinates their interactions.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the main window.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Get dependencies from container
        container = get_container()
        self.data_manager = container.get_data_manager()
        self.export_service = container.get_export_service()
        self.maya_scene = container.get_maya_scene()
        
        # Create state managers
        self.selection_manager = SelectionStateManager(self.data_manager, self.maya_scene)
        self.isolation_manager = IsolationStateManager(self.data_manager, self.maya_scene)
        
        # Create UI
        self._create_ui()
        self._create_connections()
        
        # Setup refresh timer
        self._setup_refresh_timer()
        
        # Auto-load config if it exists for this scene
        self._auto_load_config()
        
        # Initial refresh
        self.tree_widget.refresh(preserve_selection=False)
        self._refresh_settings()
        self.toolbar.update_summary()
    
    def _create_ui(self) -> None:
        """Create the UI layout."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(MARGIN_SMALL, MARGIN_SMALL, MARGIN_SMALL, MARGIN_SMALL)
        main_layout.setSpacing(SPACING_SMALL)
        
        # Toolbar
        self.toolbar = ExportToolbar(self.data_manager)
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self._create_separator())
        
        # Tree panel
        tree_group = QtWidgets.QGroupBox("Level Hierarchy")
        tree_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        tree_layout = QtWidgets.QVBoxLayout(tree_group)
        tree_layout.setContentsMargins(6, 8, 6, 6)
        tree_layout.setSpacing(SPACING_SMALL)
        
        self.tree_widget = ExportTreeWidget(self.data_manager)
        tree_layout.addWidget(self.tree_widget)
        
        # Tree action buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(SPACING_SMALL)
        
        self.add_group_btn = QtWidgets.QPushButton(" + ")
        self.remove_btn = QtWidgets.QPushButton(" - ")
        self.move_up_btn = QtWidgets.QPushButton("↑")
        self.move_down_btn = QtWidgets.QPushButton("↓")
        self.add_selected_btn = QtWidgets.QPushButton("+ Add to Selected")
        self.remove_selected_btn = QtWidgets.QPushButton("- Remove from Selected")
        
        self.add_group_btn.setMinimumHeight(BUTTON_HEIGHT_STANDARD)
        self.remove_btn.setMinimumHeight(BUTTON_HEIGHT_STANDARD)
        self.move_up_btn.setMinimumHeight(BUTTON_HEIGHT_STANDARD)
        self.move_down_btn.setMinimumHeight(BUTTON_HEIGHT_STANDARD)
        self.add_selected_btn.setMinimumHeight(BUTTON_HEIGHT_STANDARD)
        self.remove_selected_btn.setMinimumHeight(BUTTON_HEIGHT_STANDARD)
        
        self.move_up_btn.setFixedWidth(30)
        self.move_down_btn.setFixedWidth(30)
        
        self.add_group_btn.setToolTip("Create a new export group")
        self.remove_btn.setToolTip("Remove selected groups or objects")
        self.move_up_btn.setToolTip("Move selected group up in the list")
        self.move_down_btn.setToolTip("Move selected group down in the list")
        self.add_selected_btn.setToolTip("Add selected scene objects to selected group(s)")
        self.remove_selected_btn.setToolTip("Remove selected scene objects from selected group(s)")
        
        buttons_layout.addWidget(self.add_group_btn)
        buttons_layout.addWidget(self.remove_btn)
        buttons_layout.addWidget(self.move_up_btn)
        buttons_layout.addWidget(self.move_down_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.add_selected_btn)
        buttons_layout.addWidget(self.remove_selected_btn)
        
        tree_layout.addLayout(buttons_layout)
        main_layout.addWidget(tree_group)
        
        # Export settings
        self.export_settings_panel = ExportSettingsPanel()
        main_layout.addWidget(self.export_settings_panel)
        
        # FBX settings
        self.fbx_settings_panel = FBXSettingsPanel()
        main_layout.addWidget(self.fbx_settings_panel)
        
        # Export panel
        main_layout.addWidget(self._create_separator())
        main_layout.addWidget(self._create_export_panel())
    
    def _create_separator(self) -> QtWidgets.QFrame:
        """Create a visual separator line."""
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setStyleSheet("QFrame { color: #555555; }")
        return line
    
    def _create_export_panel(self) -> QtWidgets.QWidget:
        """Create the export buttons panel."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, SPACING_SMALL, 0, 0)
        layout.setSpacing(SPACING_MEDIUM)
        
        self.save_btn = QtWidgets.QPushButton("Save Preset")
        self.load_btn = QtWidgets.QPushButton("Load Preset")
        self.export_selected_btn = QtWidgets.QPushButton("Export Selected")
        self.export_all_btn = QtWidgets.QPushButton("Export All")
        
        self.save_btn.setMinimumWidth(90)
        self.load_btn.setMinimumWidth(90)
        self.save_btn.setMinimumHeight(BUTTON_HEIGHT_EXPORT)
        self.load_btn.setMinimumHeight(BUTTON_HEIGHT_EXPORT)
        self.export_selected_btn.setMinimumHeight(BUTTON_HEIGHT_EXPORT)
        self.export_all_btn.setMinimumHeight(BUTTON_HEIGHT_EXPORT)
        
        self.save_btn.setToolTip("Save current configuration to a preset file")
        self.load_btn.setToolTip("Load configuration from a preset file")
        self.export_selected_btn.setToolTip("Export the currently selected group")
        self.export_all_btn.setToolTip("Export all groups in the list")
        
        self.export_selected_btn.setStyleSheet(
            "QPushButton { background-color: #4a90e2; color: white; font-weight: bold; } "
            "QPushButton:hover { background-color: #357abd; }"
        )
        self.export_all_btn.setStyleSheet(
            "QPushButton { background-color: #5cb85c; color: white; font-weight: bold; } "
            "QPushButton:hover { background-color: #4a9b4a; }"
        )
        
        layout.addWidget(self.save_btn)
        layout.addWidget(self.load_btn)
        layout.addStretch()
        layout.addWidget(self.export_selected_btn)
        layout.addWidget(self.export_all_btn)
        
        return widget
    
    def _create_connections(self) -> None:
        """Connect signals to slots."""
        # Tree widget
        self.tree_widget.selection_changed.connect(self._on_tree_selection_changed)
        self.tree_widget.context_menu_requested.connect(self._on_context_menu_requested)
        
        # Toolbar
        self.toolbar.select_in_scene_clicked.connect(self._select_objects_in_scene)
        self.toolbar.isolate_clicked.connect(self._toggle_isolate)
        self.toolbar.refresh_clicked.connect(self._manual_refresh)
        self.toolbar.update_clicked.connect(self._update_from_git)
        
        # Tree buttons
        self.add_group_btn.clicked.connect(self._add_group)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.move_up_btn.clicked.connect(self._on_move_up_clicked)
        self.move_down_btn.clicked.connect(self._on_move_down_clicked)
        self.add_selected_btn.clicked.connect(self._add_selected_objects)
        self.remove_selected_btn.clicked.connect(self._remove_selected_objects)
        
        # Export settings
        self.export_settings_panel.directory_changed.connect(self._on_directory_changed)
        self.export_settings_panel.prefix_changed.connect(self._on_prefix_changed)
        
        # FBX settings
        self.fbx_settings_panel.triangulate_changed.connect(self._on_fbx_setting_changed)
        self.fbx_settings_panel.up_axis_changed.connect(self._on_fbx_setting_changed)
        self.fbx_settings_panel.unit_changed.connect(self._on_fbx_setting_changed)
        
        # Export buttons
        self.save_btn.clicked.connect(self._save_config)
        self.load_btn.clicked.connect(self._load_config)
        self.export_selected_btn.clicked.connect(self._export_selected_group)
        self.export_all_btn.clicked.connect(self._export_all_groups)
    
    def _setup_refresh_timer(self) -> None:
        """Setup automatic tree refresh timer."""
        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.timeout.connect(self._on_timer_refresh)
        self.refresh_timer.start(REFRESH_INTERVAL_MS)
    
    def _auto_load_config(self) -> None:
        """Auto-load config file if it exists for the current scene (silent for new scenes)."""
        try:
            config_path = self.data_manager.get_json_path()
            
            # Only load if file exists (silent if not)
            if os.path.exists(config_path):
                logger.info(f"Auto-loading config: {config_path}")
                success, message = self.data_manager.load_from_file(config_path)
                if success:
                    logger.info(f"Auto-loaded config successfully")
                else:
                    # Failed to load - just log, don't show error to user
                    logger.debug(f"Could not auto-load config: {message}")
            # No logging if file doesn't exist - normal for new scenes
        except Exception as e:
            # Silently handle any errors - don't interrupt startup
            logger.debug(f"Auto-load skipped: {e}")
    
    def _on_timer_refresh(self) -> None:
        """Handle timer-based refresh."""
        self.tree_widget.refresh(preserve_selection=True)
        self.toolbar.update_summary()
    
    def _manual_refresh(self) -> None:
        """Handle manual refresh button click."""
        self.tree_widget.refresh(preserve_selection=True)
        self.toolbar.update_summary()
    
    def _update_from_git(self) -> None:
        """Handle update button click to pull from git."""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.toolbar.update_btn.setEnabled(False)
        self.toolbar.update_btn.setText("Updating...")
        
        class GitPullThread(QtCore.QThread):
            finished_signal = QtCore.Signal(bool, str)
            
            def __init__(self, directory):
                super().__init__()
                self.directory = directory
            
            def run(self):
                try:
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=self.directory,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        self.finished_signal.emit(True, result.stdout)
                    else:
                        self.finished_signal.emit(False, f"Git pull failed:\n\n{result.stderr}")
                except subprocess.TimeoutExpired:
                    self.finished_signal.emit(False, "Git pull timed out after 30 seconds.")
                except FileNotFoundError:
                    self.finished_signal.emit(False, "Git command not found. Make sure git is installed.")
                except Exception as e:
                    self.finished_signal.emit(False, f"An error occurred:\n\n{str(e)}")
        
        self.git_thread = GitPullThread(script_dir)
        self.git_thread.finished_signal.connect(self._on_git_pull_complete)
        self.git_thread.start()
    
    def _on_git_pull_complete(self, success: bool, message: str) -> None:
        """Handle git pull completion."""
        self.toolbar.update_btn.setEnabled(True)
        self.toolbar.update_btn.setText("Update")
        
        if success:
            InfoDialog.show_info(
                "Update Complete", 
                f"Git pull successful:\n\n{message}\n\nRestarting window to load new code...", 
                self
            )
            QtCore.QTimer.singleShot(500, self._restart_window)
        else:
            InfoDialog.show_error("Update Failed", message, self)
    
    def _restart_window(self) -> None:
        """Restart the window to load updated code."""
        import importlib
        import sys
        
        modules_to_reload = [
            mod for mod in sys.modules.keys() 
            if mod.startswith('batch_exporter')
        ]
        
        for mod_name in modules_to_reload:
            if mod_name in sys.modules:
                try:
                    importlib.reload(sys.modules[mod_name])
                except Exception as e:
                    logger.warning(f"Could not reload module {mod_name}: {e}")
        
        from ..ui.main_window import show_batch_exporter
        show_batch_exporter()
    
    def _on_tree_selection_changed(self) -> None:
        """Handle tree selection change."""
        group_index = self.tree_widget.get_selected_group_index()
        self.selection_manager.set_current_group(group_index)
    
    def _on_context_menu_requested(self, item, position) -> None:
        """Handle context menu request."""
        with PausedTimerContext(self.refresh_timer):
            if not item:
                self._show_empty_context_menu(position)
            else:
                item_data = item.data(0, QtCore.Qt.UserRole)
                if item_data and item_data.get("type") == "group":
                    self._show_group_context_menu(item_data["data"], position)
                elif item_data and item_data.get("type") == "object":
                    self._show_object_context_menu(position)
    
    def _show_empty_context_menu(self, position) -> None:
        """Show context menu for empty area."""
        menu = QtWidgets.QMenu(self)
        add_action = menu.addAction("Add Group")
        
        action = menu.exec_(self.tree_widget.tree_widget.viewport().mapToGlobal(position))
        if action == add_action:
            self._add_group()
    
    def _show_group_context_menu(self, group_data, position) -> None:
        """Show context menu for group items."""
        menu = QtWidgets.QMenu(self)
        
        # Find the group's current index
        set_name = group_data["set_name"]
        groups = self.data_manager.get_all_export_groups()
        current_index = None
        for i, group in enumerate(groups):
            if group.get("set_name") == set_name:
                current_index = i
                break
        
        # Movement actions
        move_up_action = menu.addAction("Move Up")
        move_down_action = menu.addAction("Move Down")
        
        # Disable if can't move
        if current_index is None or current_index == 0:
            move_up_action.setEnabled(False)
        if current_index is None or current_index >= len(groups) - 1:
            move_down_action.setEnabled(False)
        
        menu.addSeparator()
        rename_action = menu.addAction("Rename Group")
        duplicate_action = menu.addAction("Duplicate Group")
        menu.addSeparator()
        delete_action = menu.addAction("Delete Group")
        
        action = menu.exec_(self.tree_widget.tree_widget.viewport().mapToGlobal(position))
        
        if action == move_up_action and current_index is not None:
            self._move_group_up(current_index)
        elif action == move_down_action and current_index is not None:
            self._move_group_down(current_index)
        elif action == rename_action:
            self._rename_group(group_data)
        elif action == duplicate_action:
            self._duplicate_group(group_data)
        elif action == delete_action:
            self._delete_group(group_data)
    
    def _show_object_context_menu(self, position) -> None:
        """Show context menu for object items."""
        selected_items = self.tree_widget.tree_widget.selectedItems()
        
        menu = QtWidgets.QMenu(self)
        
        if len(selected_items) == 1:
            remove_action = menu.addAction("Remove from Group")
        else:
            remove_action = menu.addAction(f"Remove {len(selected_items)} Objects from Group")
        
        action = menu.exec_(self.tree_widget.tree_widget.viewport().mapToGlobal(position))
        
        if action == remove_action:
            self._remove_selected()
    
    def _add_group(self) -> None:
        """Add a new export group."""
        with PausedTimerContext(self.refresh_timer):
            name = NewGroupDialog.get_group_name(self)
            if name:
                new_index = self.data_manager.add_export_group(name)
                if new_index is not None:
                    self.tree_widget.refresh(preserve_selection=False)
                    self.toolbar.update_summary()
                else:
                    InfoDialog.show_error("Error", "Failed to create group")
    
    def _rename_group(self, group_data) -> None:
        """Rename a group."""
        current_name = group_data["name"]
        set_name = group_data["set_name"]
        
        new_name = RenameGroupDialog.get_new_name(current_name, self)
        if new_name:
            groups = self.data_manager.get_all_export_groups()
            for i, group in enumerate(groups):
                if group.get("set_name") == set_name:
                    if self.data_manager.update_export_group(i, name=new_name):
                        self.tree_widget.refresh(preserve_selection=True)
                    else:
                        InfoDialog.show_error("Error", "Failed to rename group")
                    break
    
    def _duplicate_group(self, group_data) -> None:
        """Duplicate a group."""
        set_name = group_data["set_name"]
        
        groups = self.data_manager.get_all_export_groups()
        for i, group in enumerate(groups):
            if group.get("set_name") == set_name:
                new_index = self.data_manager.duplicate_export_group(i)
                if new_index is not None:
                    self.tree_widget.refresh(preserve_selection=False)
                    self.toolbar.update_summary()
                else:
                    InfoDialog.show_error("Error", "Failed to duplicate group")
                break
    
    def _delete_group(self, group_data) -> None:
        """Delete a group."""
        if ConfirmDeleteDialog.confirm(f"Delete group '{group_data['name']}'?", self):
            set_name = group_data["set_name"]
            groups = self.data_manager.get_all_export_groups()
            for i, group in enumerate(groups):
                if group.get("set_name") == set_name:
                    if self.data_manager.remove_export_group(i):
                        self.tree_widget.refresh(preserve_selection=True)
                        self.toolbar.update_summary()
                    else:
                        InfoDialog.show_error("Error", "Failed to delete group")
                    break
    
    def _move_group_up(self, index: int) -> None:
        """Move a group up in the list."""
        if self.data_manager.move_group_up(index):
            self.tree_widget.refresh(preserve_selection=True)
        else:
            logger.warning(f"Cannot move group at index {index} up")
    
    def _move_group_down(self, index: int) -> None:
        """Move a group down in the list."""
        if self.data_manager.move_group_down(index):
            self.tree_widget.refresh(preserve_selection=True)
        else:
            logger.warning(f"Cannot move group at index {index} down")
    
    def _on_move_up_clicked(self) -> None:
        """Handle move up button click."""
        group_index = self.selection_manager.get_current_group_index()
        if group_index is not None:
            self._move_group_up(group_index)
    
    def _on_move_down_clicked(self) -> None:
        """Handle move down button click."""
        group_index = self.selection_manager.get_current_group_index()
        if group_index is not None:
            self._move_group_down(group_index)
    
    def _remove_selected(self) -> None:
        """Remove selected groups or objects."""
        with PausedTimerContext(self.refresh_timer):
            info = self.tree_widget.get_selected_items_info()
            groups_to_remove = info["groups"]
            objects_to_remove = info["objects_by_group"]
            
            if groups_to_remove:
                if ConfirmDeleteDialog.confirm(f"Delete {len(groups_to_remove)} group(s)?", self):
                    for group_data in groups_to_remove:
                        set_name = group_data["set_name"]
                        groups = self.data_manager.get_all_export_groups()
                        for i, group in enumerate(groups):
                            if group.get("set_name") == set_name:
                                self.data_manager.remove_export_group(i)
                                break
            
            for set_name, objects in objects_to_remove.items():
                self.data_manager.remove_objects_from_set(set_name, objects)
            
            self.tree_widget.refresh(preserve_selection=True)
            self.toolbar.update_summary()
    
    def _add_selected_objects(self) -> None:
        """Add selected scene objects to all selected groups in tree."""
        # Get selected groups from tree
        info = self.tree_widget.get_selected_items_info()
        selected_groups = info["groups"]
        
        if not selected_groups:
            InfoDialog.show_warning("No Groups Selected", "Please select one or more groups in the tree.", self)
            return
        
        # Get objects selected in Maya scene
        selected = self.maya_scene.get_selection(long=True)
        if not selected:
            InfoDialog.show_warning("No Objects Selected", "Please select objects in the Maya scene to add.", self)
            return
        
        # Add objects to each selected group
        success_count = 0
        for group in selected_groups:
            set_name = group.get("set_name")
            if set_name:
                if self.data_manager.add_objects_to_set(set_name, selected):
                    success_count += 1
        
        if success_count > 0:
            logger.info(f"Added {len(selected)} objects to {success_count} groups")
            self.tree_widget.refresh(preserve_selection=True)
            self.toolbar.update_summary()
            if success_count > 1:
                InfoDialog.show_info("Success", f"Added {len(selected)} object(s) to {success_count} groups", self)
        else:
            InfoDialog.show_error("Error", "Failed to add objects to groups", self)
    
    def _remove_selected_objects(self) -> None:
        """Remove selected scene objects from all selected groups in tree."""
        # Get selected groups from tree
        info = self.tree_widget.get_selected_items_info()
        selected_groups = info["groups"]
        
        if not selected_groups:
            InfoDialog.show_warning("No Groups Selected", "Please select one or more groups in the tree.", self)
            return
        
        # Get objects selected in Maya scene
        selected = self.maya_scene.get_selection(long=True)
        if not selected:
            InfoDialog.show_warning("No Objects Selected", "Please select objects in the Maya scene to remove.", self)
            return
        
        # Remove objects from each selected group
        success_count = 0
        for group in selected_groups:
            set_name = group.get("set_name")
            if set_name:
                if self.data_manager.remove_objects_from_set(set_name, selected):
                    success_count += 1
        
        if success_count > 0:
            logger.info(f"Removed {len(selected)} objects from {success_count} groups")
            self.tree_widget.refresh(preserve_selection=True)
            self.toolbar.update_summary()
            if success_count > 1:
                InfoDialog.show_info("Success", f"Removed {len(selected)} object(s) from {success_count} groups", self)
        else:
            InfoDialog.show_error("Error", "Failed to remove objects from groups", self)
    
    def _select_objects_in_scene(self) -> None:
        """Select objects from tree in Maya scene."""
        info = self.tree_widget.get_selected_items_info()
        objects_to_select = []
        
        # Add objects from selected groups
        for group in info["groups"]:
            set_name = group.get("set_name")
            if set_name:
                objects_to_select.extend(self.data_manager.get_set_objects(set_name))
        
        # Add individually selected objects
        for objects in info["objects_by_group"].values():
            objects_to_select.extend(objects)
        
        if objects_to_select:
            self.selection_manager.select_objects_in_scene(objects_to_select)
    
    def _toggle_isolate(self) -> None:
        """Toggle isolation."""
        # If currently isolated, always allow unisolation regardless of selection
        if self.isolation_manager.get_isolation_state():
            self.isolation_manager.unisolate()
            self.toolbar.set_isolated_state(False)
            return
        
        # If not isolated, we need a group selected to isolate
        group_index = self.selection_manager.get_current_group_index()
        if group_index is None:
            logger.warning("No group selected for isolation")
            return
        
        # Isolate the selected group
        success = self.isolation_manager.isolate_group(group_index)
        self.toolbar.set_isolated_state(success)
    
    def _on_directory_changed(self, directory: str) -> None:
        """Handle directory change."""
        settings = self.data_manager.get_fbx_settings()
        settings["export_directory"] = directory
        self.data_manager.update_fbx_settings(settings)
    
    def _on_prefix_changed(self, prefix: str) -> None:
        """Handle prefix change."""
        settings = self.data_manager.get_fbx_settings()
        settings["file_prefix"] = prefix
        self.data_manager.update_fbx_settings(settings)
    
    def _on_fbx_setting_changed(self) -> None:
        """Handle FBX setting change."""
        settings = self.data_manager.get_fbx_settings()
        settings["triangulate"] = self.fbx_settings_panel.get_triangulate()
        settings["up_axis"] = self.fbx_settings_panel.get_up_axis()
        settings["convert_unit"] = self.fbx_settings_panel.get_unit()
        self.data_manager.update_fbx_settings(settings)
    
    def _refresh_settings(self) -> None:
        """Refresh settings panels from data manager."""
        settings = self.data_manager.get_fbx_settings()
        
        self.export_settings_panel.set_directory(settings.get("export_directory", ""))
        self.export_settings_panel.set_prefix(settings.get("file_prefix", ""))
        
        self.fbx_settings_panel.set_triangulate(settings.get("triangulate", False))
        self.fbx_settings_panel.set_up_axis(settings.get("up_axis", "Y"))
        self.fbx_settings_panel.set_unit(settings.get("convert_unit", "cm"))
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Configuration",
            self.data_manager.get_json_path(),
            "JSON Files (*.json)"
        )
        
        if file_path:
            success, message = self.data_manager.save_to_file(file_path)
            if success:
                InfoDialog.show_info("Success", f"Preset saved successfully:\n{message}", self)
            else:
                InfoDialog.show_error("Error", f"Failed to save configuration:\n{message}", self)
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Configuration",
            self.data_manager.get_json_path(),
            "JSON Files (*.json)"
        )
        
        if file_path:
            success, message = self.data_manager.load_from_file(file_path)
            if success:
                self.tree_widget.refresh(preserve_selection=False)
                self._refresh_settings()
                self.toolbar.update_summary()
                InfoDialog.show_info("Success", f"Preset loaded successfully:\n{message}", self)
            else:
                InfoDialog.show_error("Error", f"Failed to load configuration:\n{message}", self)
    
    def _export_selected_group(self) -> None:
        """Export the currently selected group."""
        group_index = self.selection_manager.get_current_group_index()
        
        if group_index is None:
            InfoDialog.show_warning("No Group Selected", "Please select an export group first.", self)
            return
        
        group = self.data_manager.get_export_group(group_index)
        if not group:
            InfoDialog.show_error("Error", "Selected group not found", self)
            return
        
        settings = self.data_manager.get_fbx_settings()
        result = self.export_service.export_single_group(group, settings)
        
        ExportResultsDialog.show_single_result(result["success"], result["message"], self)
    
    def _export_all_groups(self) -> None:
        """Export all groups."""
        groups = self.data_manager.get_all_export_groups()
        
        if not groups:
            InfoDialog.show_warning("No Groups", "There are no export groups to export.", self)
            return
        
        if not ConfirmExportDialog.confirm_export_all(len(groups), self):
            return
        
        settings = self.data_manager.get_fbx_settings()
        results, success_count = self.export_service.export_all_groups(groups, settings)
        
        ExportResultsDialog.show_batch_results(results, success_count, len(groups), self)


def show_batch_exporter():
    """Show the Batch Exporter UI as a dockable workspace control."""
    global batch_exporter_window
    
    workspace_control_name = "batchExporterWorkspace"
    
    # Get Maya scene interface from container
    container = get_container()
    maya_scene = container.get_maya_scene()
    
    # Delete existing workspace control if it exists
    if maya_scene.workspace_control_exists(workspace_control_name):
        maya_scene.delete_ui(workspace_control_name)
    
    # Create new workspace control
    maya_scene.create_workspace_control(
        workspace_control_name,
        label="Batch Exporter",
        widthProperty="preferred",
        initialWidth=PREFERRED_WINDOW_WIDTH,
        minimumWidth=MIN_WINDOW_WIDTH,
        retain=False
    )
    
    # Get control widget
    control_ptr = maya_scene.find_control(workspace_control_name)
    if not control_ptr:
        raise RuntimeError("Failed to find workspace control")
    
    control_widget = wrapInstance(control_ptr, QtWidgets.QWidget)
    
    # Create and add main window
    batch_exporter_window = BatchExporterWindow(parent=control_widget)
    control_widget.layout().addWidget(batch_exporter_window)
    
    return batch_exporter_window

