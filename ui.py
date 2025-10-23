"""
UI Module for Batch Exporter
Main window and interface for managing export groups.
"""

import os
import maya.cmds as cmds
from maya import OpenMayaUI as omui

try:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance

from .data_manager import DataManager
from .exporter import FBXExporter


def get_maya_main_window():
    """Get Maya's main window as a Qt object."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class BatchExporterUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BatchExporterUI, self).__init__(parent)
        
        self.data_manager = DataManager()
        self.exporter = FBXExporter()
        self.current_group_index = None
        
        self._create_ui()
        self._create_connections()
        self._refresh_tree(preserve_selection=False)
        self._refresh_fbx_settings()
        self._setup_refresh_timer()
    
    def _setup_refresh_timer(self):
        """Set up timer for automatic tree refresh."""
        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.timeout.connect(self._on_timer_refresh)
        self.refresh_timer.start(500)
    
    def _on_timer_refresh(self):
        """Handle timer-based refresh."""
        self._refresh_tree(preserve_selection=True)
    
    def _with_paused_timer(self, func):
        """Execute a function with timer paused."""
        self.refresh_timer.stop()
        try:
            return func()
        finally:
            self.refresh_timer.start(500)
    
    def _create_ui(self):
        """Create the UI layout."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        main_layout.addWidget(self._create_tree_panel())
        main_layout.addWidget(self._create_group_actions_panel())
        main_layout.addWidget(self._create_fbx_settings_panel())
        main_layout.addWidget(self._create_export_panel())
    
    def _create_tree_panel(self):
        """Create tree view for groups and objects."""
        group_box = QtWidgets.QGroupBox()
        layout = QtWidgets.QVBoxLayout(group_box)
        layout.setContentsMargins(3, 6, 3, 3)
        layout.setSpacing(2)
        
        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        layout.addWidget(self.tree_widget)
        
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(4)
        
        self.add_group_btn = QtWidgets.QPushButton("+ Group")
        self.remove_btn = QtWidgets.QPushButton("Remove")
        self.add_selected_btn = QtWidgets.QPushButton("Add Selected")
        self.select_objects_btn = QtWidgets.QPushButton("Select in Scene")
        self.refresh_btn = QtWidgets.QPushButton("↻")
        
        button_height = 24
        self.add_group_btn.setMinimumHeight(button_height)
        self.remove_btn.setMinimumHeight(button_height)
        self.add_selected_btn.setMinimumHeight(button_height)
        self.select_objects_btn.setMinimumHeight(button_height)
        self.refresh_btn.setMinimumHeight(button_height)
        self.refresh_btn.setFixedWidth(32)
        self.refresh_btn.setToolTip("Refresh tree view")
        
        buttons_layout.addWidget(self.add_group_btn)
        buttons_layout.addWidget(self.remove_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.add_selected_btn)
        buttons_layout.addWidget(self.select_objects_btn)
        buttons_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(buttons_layout)
        
        return group_box
    
    def _create_group_actions_panel(self):
        """Create panel for export settings."""
        group_box = QtWidgets.QGroupBox("Export Settings")
        layout = QtWidgets.QVBoxLayout(group_box)
        layout.setContentsMargins(6, 8, 6, 6)
        layout.setSpacing(4)
        
        dir_layout = QtWidgets.QHBoxLayout()
        dir_layout.setSpacing(6)
        
        dir_label = QtWidgets.QLabel("Directory:")
        dir_label.setFixedWidth(60)
        dir_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        dir_layout.addWidget(dir_label)
        
        self.export_dir_edit = QtWidgets.QLineEdit()
        self.export_dir_edit.setPlaceholderText("Export directory...")
        dir_layout.addWidget(self.export_dir_edit)
        
        self.browse_dir_btn = QtWidgets.QPushButton("...")
        self.browse_dir_btn.setFixedWidth(32)
        self.browse_dir_btn.setMinimumHeight(22)
        dir_layout.addWidget(self.browse_dir_btn)
        layout.addLayout(dir_layout)
        
        prefix_layout = QtWidgets.QHBoxLayout()
        prefix_layout.setSpacing(6)
        
        prefix_label = QtWidgets.QLabel("Prefix:")
        prefix_label.setFixedWidth(60)
        prefix_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        prefix_layout.addWidget(prefix_label)
        
        self.prefix_edit = QtWidgets.QLineEdit()
        self.prefix_edit.setPlaceholderText("Optional prefix...")
        prefix_layout.addWidget(self.prefix_edit)
        
        prefix_layout.addSpacing(32)
        
        layout.addLayout(prefix_layout)
        
        return group_box
    
    def _create_fbx_settings_panel(self):
        """Create the FBX settings panel."""
        group_box = QtWidgets.QGroupBox("FBX Settings")
        layout = QtWidgets.QHBoxLayout(group_box)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)
        
        self.fbx_settings_widgets = {}
        
        self.triangulate_checkbox = QtWidgets.QCheckBox("Triangulate")
        self.fbx_settings_widgets["triangulate"] = self.triangulate_checkbox
        layout.addWidget(self.triangulate_checkbox)
        
        layout.addSpacing(8)
        
        layout.addWidget(QtWidgets.QLabel("Up:"))
        self.up_axis_combo = QtWidgets.QComboBox()
        self.up_axis_combo.addItems(["Y", "Z"])
        self.up_axis_combo.setFixedWidth(50)
        self.up_axis_combo.setMinimumHeight(22)
        self.fbx_settings_widgets["up_axis"] = self.up_axis_combo
        layout.addWidget(self.up_axis_combo)
        
        layout.addSpacing(8)
        
        layout.addWidget(QtWidgets.QLabel("Unit:"))
        self.unit_combo = QtWidgets.QComboBox()
        self.unit_combo.addItems(["cm", "m", "mm", "in", "ft"])
        self.unit_combo.setFixedWidth(60)
        self.unit_combo.setMinimumHeight(22)
        self.fbx_settings_widgets["convert_unit"] = self.unit_combo
        layout.addWidget(self.unit_combo)
        
        layout.addStretch()
        
        return group_box
    
    def _create_export_panel(self):
        """Create the export buttons panel."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)
        
        self.save_btn = QtWidgets.QPushButton("Save")
        self.load_btn = QtWidgets.QPushButton("Load")
        self.export_selected_btn = QtWidgets.QPushButton("Export Selected")
        self.export_all_btn = QtWidgets.QPushButton("Export All")
        
        button_height = 28
        self.save_btn.setFixedWidth(60)
        self.load_btn.setFixedWidth(60)
        self.save_btn.setMinimumHeight(button_height)
        self.load_btn.setMinimumHeight(button_height)
        self.export_selected_btn.setMinimumHeight(button_height)
        self.export_all_btn.setMinimumHeight(button_height)
        
        self.export_selected_btn.setStyleSheet("background-color: #4a90e2; color: white; font-weight: bold;")
        self.export_all_btn.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold;")
        
        layout.addWidget(self.save_btn)
        layout.addWidget(self.load_btn)
        layout.addStretch()
        layout.addWidget(self.export_selected_btn)
        layout.addWidget(self.export_all_btn)
        
        return widget
    
    def _create_connections(self):
        """Connect UI signals to slots."""
        self.tree_widget.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)
        
        self.add_group_btn.clicked.connect(self._add_group)
        self.remove_btn.clicked.connect(self._remove_selected)
        self.refresh_btn.clicked.connect(self._manual_refresh)
        self.add_selected_btn.clicked.connect(self._add_selected_objects)
        self.select_objects_btn.clicked.connect(self._select_objects_in_scene)
        
        self.browse_dir_btn.clicked.connect(self._browse_export_directory)
        self.export_dir_edit.textChanged.connect(self._on_export_dir_changed)
        self.prefix_edit.textChanged.connect(self._on_prefix_changed)
        
        self.save_btn.clicked.connect(self._save_config)
        self.load_btn.clicked.connect(self._load_config)
        self.export_selected_btn.clicked.connect(self._export_selected_group)
        self.export_all_btn.clicked.connect(self._export_all_groups)
        
        self.triangulate_checkbox.stateChanged.connect(self._on_fbx_setting_changed)
        self.up_axis_combo.currentTextChanged.connect(self._on_fbx_setting_changed)
        self.unit_combo.currentTextChanged.connect(self._on_fbx_setting_changed)
    
    def _refresh_tree(self, preserve_selection=True):
        """Refresh the tree widget."""
        try:
            selected_items_data = []
            if preserve_selection:
                for item in self.tree_widget.selectedItems():
                    item_data = item.data(0, QtCore.Qt.UserRole)
                    if item_data["type"] == "group":
                        selected_items_data.append(("group", item_data["data"].get("set_name")))
                    elif item_data["type"] == "object":
                        parent_set = item_data["group"].get("set_name")
                        obj_name = item_data["name"]
                        selected_items_data.append(("object", parent_set, obj_name))
            
            self.tree_widget.blockSignals(True)
            self.tree_widget.clear()
            
            groups = self.data_manager.get_all_export_groups()
        except Exception as e:
            print(f"Error refreshing tree: {e}")
            return
        
        items_to_select = []
        
        for group in groups:
            group_item = QtWidgets.QTreeWidgetItem([group["name"]])
            group_item.setData(0, QtCore.Qt.UserRole, {"type": "group", "data": group})
            
            font = group_item.font(0)
            font.setBold(True)
            group_item.setFont(0, font)
            group_item.setForeground(0, QtGui.QColor(100, 150, 255))
            
            set_name = group.get("set_name")
            if set_name:
                objects = self.data_manager.get_set_objects(set_name)
                for obj in objects:
                    obj_item = QtWidgets.QTreeWidgetItem([obj])
                    obj_item.setData(0, QtCore.Qt.UserRole, {"type": "object", "name": obj, "group": group})
                    obj_item.setForeground(0, QtGui.QColor(180, 180, 180))
                    group_item.addChild(obj_item)
                    
                    if preserve_selection:
                        for sel_type, *sel_data in selected_items_data:
                            if sel_type == "object" and sel_data[0] == set_name and sel_data[1] == obj:
                                items_to_select.append(obj_item)
            
            self.tree_widget.addTopLevelItem(group_item)
            group_item.setExpanded(True)
            
            if preserve_selection:
                for sel_type, *sel_data in selected_items_data:
                    if sel_type == "group" and sel_data[0] == set_name:
                        items_to_select.append(group_item)
        
        if items_to_select:
            for item in items_to_select:
                item.setSelected(True)
            self.tree_widget.setCurrentItem(items_to_select[0])
        
        try:
            self.tree_widget.blockSignals(False)
        except:
            pass
    
    def _get_selected_group_item(self):
        """Get the selected group item (or parent group of selected object)."""
        selected = self.tree_widget.selectedItems()
        if not selected:
            return None
        
        item = selected[0]
        item_data = item.data(0, QtCore.Qt.UserRole)
        
        if item_data["type"] == "group":
            return item
        elif item_data["type"] == "object":
            return item.parent()
        
        return None
    
    def _update_group_settings(self):
        """Update export settings display."""
        group_item = self._get_selected_group_item()
        
        if group_item:
            self.current_group_index = self._get_group_index_from_item(group_item)
        else:
            self.current_group_index = None
    
    def _get_group_index_from_item(self, group_item):
        """Get the data manager index for a group item."""
        group_data = group_item.data(0, QtCore.Qt.UserRole)["data"]
        groups = self.data_manager.get_all_export_groups()
        
        for i, group in enumerate(groups):
            if group.get("set_name") == group_data.get("set_name"):
                return i
        
        return None
    
    def _refresh_export_settings(self):
        """Refresh export settings from data manager."""
        settings = self.data_manager.get_fbx_settings()
        
        self.export_dir_edit.blockSignals(True)
        self.export_dir_edit.setText(settings.get("export_directory", ""))
        self.export_dir_edit.blockSignals(False)
        
        self.prefix_edit.blockSignals(True)
        self.prefix_edit.setText(settings.get("file_prefix", ""))
        self.prefix_edit.blockSignals(False)
    
    def _refresh_fbx_settings(self):
        """Refresh FBX settings from data manager."""
        settings = self.data_manager.get_fbx_settings()
        
        self.triangulate_checkbox.blockSignals(True)
        self.triangulate_checkbox.setChecked(settings.get("triangulate", False))
        self.triangulate_checkbox.blockSignals(False)
        
        self.up_axis_combo.blockSignals(True)
        up_axis = settings.get("up_axis", "Y")
        index = self.up_axis_combo.findText(up_axis)
        if index >= 0:
            self.up_axis_combo.setCurrentIndex(index)
        self.up_axis_combo.blockSignals(False)
        
        self.unit_combo.blockSignals(True)
        unit = settings.get("convert_unit", "cm")
        index = self.unit_combo.findText(unit)
        if index >= 0:
            self.unit_combo.setCurrentIndex(index)
        self.unit_combo.blockSignals(False)
        
        self._refresh_export_settings()
    
    def _on_tree_selection_changed(self):
        """Handle tree selection change."""
        self._update_group_settings()
    
    def _manual_refresh(self):
        """Manually refresh the tree view."""
        self._refresh_tree(preserve_selection=True)
    
    def _show_context_menu(self, position):
        """Show context menu on tree widget."""
        item = self.tree_widget.itemAt(position)
        if not item:
            return
        
        item_data = item.data(0, QtCore.Qt.UserRole)
        if not item_data or item_data.get("type") != "group":
            return
        
        group_data = item_data["data"].copy()
        
        def _show_menu():
            menu = QtWidgets.QMenu(self)
            
            rename_action = menu.addAction("Rename Group")
            duplicate_action = menu.addAction("Duplicate Group")
            menu.addSeparator()
            delete_action = menu.addAction("Delete Group")
            
            action = menu.exec_(self.tree_widget.viewport().mapToGlobal(position))
            
            if action == rename_action:
                self._rename_group_by_data(group_data)
            elif action == duplicate_action:
                self._duplicate_group_by_data(group_data)
            elif action == delete_action:
                self._delete_group_by_data(group_data)
        
        self._with_paused_timer(_show_menu)
    
    def _rename_group_by_data(self, group_data):
        """Rename a group via dialog using group data."""
        current_name = group_data["name"]
        set_name = group_data["set_name"]
        
        dialog = QtWidgets.QInputDialog(get_maya_main_window())
        dialog.setWindowTitle("Rename Group")
        dialog.setLabelText("Enter new name:")
        dialog.setTextValue(current_name)
        dialog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        
        ok = dialog.exec_()
        new_name = dialog.textValue()
        
        if ok and new_name and new_name != current_name:
            groups = self.data_manager.get_all_export_groups()
            for i, group in enumerate(groups):
                if group.get("set_name") == set_name:
                    self.data_manager.update_export_group(i, name=new_name)
                    self._refresh_tree(preserve_selection=True)
                    break
    
    def _duplicate_group_by_data(self, group_data):
        """Duplicate a group using group data."""
        set_name = group_data["set_name"]
        
        groups = self.data_manager.get_all_export_groups()
        for i, group in enumerate(groups):
            if group.get("set_name") == set_name:
                new_index = self.data_manager.duplicate_export_group(i)
                if new_index is not None:
                    self._refresh_tree(preserve_selection=False)
                break
    
    def _delete_group_by_data(self, group_data):
        """Delete a group using group data."""
        set_name = group_data["set_name"]
        
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Delete",
            f"Delete group '{group_data['name']}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            groups = self.data_manager.get_all_export_groups()
            for i, group in enumerate(groups):
                if group.get("set_name") == set_name:
                    self.data_manager.remove_export_group(i)
                    self._refresh_tree(preserve_selection=True)
                    break
    
    def _add_group(self):
        """Add a new export group."""
        def _create_group():
            dialog = QtWidgets.QInputDialog(self)
            dialog.setWindowTitle("New Export Group")
            dialog.setLabelText("Enter group name:")
            dialog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
            
            ok = dialog.exec_()
            name = dialog.textValue()
            
            if ok and name:
                new_index = self.data_manager.add_export_group(name)
                self._refresh_tree(preserve_selection=False)
                
                if new_index is not None:
                    groups = self.data_manager.get_all_export_groups()
                    if new_index < len(groups):
                        new_group = groups[new_index]
                        for i in range(self.tree_widget.topLevelItemCount()):
                            item = self.tree_widget.topLevelItem(i)
                            item_data = item.data(0, QtCore.Qt.UserRole)
                            if item_data["data"].get("set_name") == new_group.get("set_name"):
                                self.tree_widget.setCurrentItem(item)
                                break
        
        self._with_paused_timer(_create_group)
    
    def _remove_selected(self):
        """Remove selected groups or objects."""
        selected = self.tree_widget.selectedItems()
        if not selected:
            return
        
        def _do_remove():
            groups_to_remove = []
            objects_to_remove = {}
            
            for item in selected:
                item_data = item.data(0, QtCore.Qt.UserRole)
                
                if item_data["type"] == "group":
                    groups_to_remove.append(item_data["data"].copy())
                elif item_data["type"] == "object":
                    group = item_data["group"]
                    set_name = group.get("set_name")
                    obj_name = item_data["name"]
                    
                    if set_name not in objects_to_remove:
                        objects_to_remove[set_name] = []
                    objects_to_remove[set_name].append(obj_name)
            
            if groups_to_remove:
                reply = QtWidgets.QMessageBox.question(
                    self, "Confirm Delete",
                    f"Delete {len(groups_to_remove)} group(s)?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    for group_data in groups_to_remove:
                        set_name = group_data["set_name"]
                        groups = self.data_manager.get_all_export_groups()
                        for i, group in enumerate(groups):
                            if group.get("set_name") == set_name:
                                self.data_manager.remove_export_group(i)
                                break
            
            for set_name, objects in objects_to_remove.items():
                self.data_manager.remove_objects_from_set(set_name, objects)
            
            self._refresh_tree(preserve_selection=True)
        
        self._with_paused_timer(_do_remove)
    
    def _add_selected_objects(self):
        """Add selected objects from Maya scene to the current group."""
        group_item = self._get_selected_group_item()
        
        if not group_item:
            QtWidgets.QMessageBox.warning(
                self, "No Group Selected",
                "Please select an export group first."
            )
            return
        
        selected = cmds.ls(selection=True, long=True)
        
        if not selected:
            QtWidgets.QMessageBox.warning(
                self, "No Selection",
                "Please select objects in the Maya scene."
            )
            return
        
        group_data = group_item.data(0, QtCore.Qt.UserRole)["data"]
        set_name = group_data.get("set_name")
        
        if set_name:
            self.data_manager.add_objects_to_set(set_name, selected)
            self._refresh_tree(preserve_selection=True)
    
    def _select_objects_in_scene(self):
        """Select objects in Maya scene."""
        selected = self.tree_widget.selectedItems()
        if not selected:
            return
        
        objects_to_select = []
        
        for item in selected:
            item_data = item.data(0, QtCore.Qt.UserRole)
            
            if item_data["type"] == "group":
                group_data = item_data["data"]
                set_name = group_data.get("set_name")
                if set_name:
                    objects = self.data_manager.get_set_objects(set_name)
                    objects_to_select.extend(objects)
            
            elif item_data["type"] == "object":
                objects_to_select.append(item_data["name"])
        
        if objects_to_select:
            cmds.select(objects_to_select, replace=True)
        else:
            QtWidgets.QMessageBox.warning(
                self, "No Objects",
                "No objects to select."
            )
    
    def _browse_export_directory(self):
        """Browse for export directory."""
        current_dir = self.export_dir_edit.text() or ""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Export Directory", current_dir
        )
        
        if directory:
            self.export_dir_edit.setText(directory)
    
    def _on_export_dir_changed(self, text):
        """Handle export directory change."""
        settings = self.data_manager.get_fbx_settings()
        settings["export_directory"] = text
        self.data_manager.update_fbx_settings(settings)
    
    def _on_prefix_changed(self, text):
        """Handle prefix change."""
        settings = self.data_manager.get_fbx_settings()
        settings["file_prefix"] = text
        self.data_manager.update_fbx_settings(settings)
    
    def _on_fbx_setting_changed(self):
        """Handle FBX setting change."""
        settings = {
            "triangulate": self.triangulate_checkbox.isChecked(),
            "up_axis": self.up_axis_combo.currentText(),
            "convert_unit": self.unit_combo.currentText()
        }
        
        self.data_manager.update_fbx_settings(settings)
    
    def _save_config(self):
        """Save configuration to JSON file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Configuration", 
            self.data_manager.get_json_path(),
            "JSON Files (*.json)"
        )
        
        if file_path:
            success, message = self.data_manager.save_to_file(file_path)
            if success:
                QtWidgets.QMessageBox.information(
                    self, "Success",
                    f"Configuration saved to:\n{message}"
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    f"Failed to save configuration:\n{message}"
                )
    
    def _load_config(self):
        """Load configuration from JSON file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Configuration",
            self.data_manager.get_json_path(),
            "JSON Files (*.json)"
        )
        
        if file_path:
            success, message = self.data_manager.load_from_file(file_path)
            if success:
                self._refresh_tree(preserve_selection=False)
                self._refresh_fbx_settings()
                QtWidgets.QMessageBox.information(
                    self, "Success",
                    f"Configuration loaded from:\n{message}"
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Error",
                    f"Failed to load configuration:\n{message}"
                )
    
    
    def _export_selected_group(self):
        """Export the currently selected group."""
        if self.current_group_index is None:
            QtWidgets.QMessageBox.warning(
                self, "No Group Selected",
                "Please select an export group first."
            )
            return
        
        group = self.data_manager.get_export_group(self.current_group_index)
        fbx_settings = self.data_manager.get_fbx_settings()
        
        success, message = self.exporter.export_group(group, fbx_settings)
        
        if success:
            QtWidgets.QMessageBox.information(
                self, "Export Complete", message
            )
        else:
            QtWidgets.QMessageBox.critical(
                self, "Export Failed", message
            )
    
    def _export_all_groups(self):
        """Export all groups."""
        groups = self.data_manager.get_all_export_groups()
        
        if not groups:
            QtWidgets.QMessageBox.warning(
                self, "No Groups",
                "There are no export groups to export."
            )
            return
        
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Export",
            f"Export all {len(groups)} groups?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply != QtWidgets.QMessageBox.Yes:
            return
        
        fbx_settings = self.data_manager.get_fbx_settings()
        results, success_count = self.exporter.export_all_groups(groups, fbx_settings)
        
        message = f"Exported {success_count} of {len(groups)} groups successfully.\n\n"
        
        for name, success, msg in results:
            status = "SUCCESS" if success else "FAILED"
            message += f"{status}: {name}\n{msg}\n\n"
        
        if success_count == len(groups):
            QtWidgets.QMessageBox.information(
                self, "Export Complete", message
            )
        else:
            QtWidgets.QMessageBox.warning(
                self, "Export Completed with Errors", message
            )


def show_batch_exporter():
    """Show the Batch Exporter UI as a dockable workspace control."""
    global batch_exporter_window
    
    workspace_control_name = "batchExporterWorkspace"
    
    if cmds.workspaceControl(workspace_control_name, exists=True):
        cmds.deleteUI(workspace_control_name)
    
    cmds.workspaceControl(
        workspace_control_name,
        label="Batch Exporter",
        widthProperty="preferred",
        initialWidth=600,
        minimumWidth=400,
        retain=False
    )
    
    control_ptr = omui.MQtUtil.findControl(workspace_control_name)
    control_widget = wrapInstance(int(control_ptr), QtWidgets.QWidget)
    
    batch_exporter_window = BatchExporterUI(parent=control_widget)
    control_widget.layout().addWidget(batch_exporter_window)
    
    return batch_exporter_window

