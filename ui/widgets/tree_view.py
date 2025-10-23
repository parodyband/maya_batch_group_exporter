"""
Export Tree Widget
Tree view for displaying export groups and their objects.
"""

from typing import List, Set, Dict, Optional, Tuple
from ...types import ExportGroupDict

try:
    from PySide2 import QtCore, QtWidgets, QtGui
except ImportError:
    from PySide6 import QtCore, QtWidgets, QtGui

from ...data_manager import DataManager
from ...constants import TREE_ITEM_PADDING
from ...logger import get_logger

logger = get_logger(__name__)


class ExportTreeWidget(QtWidgets.QWidget):
    """
    Widget for displaying export groups and objects in a tree view.
    Handles search/filter, selection, and visual presentation.
    """
    
    # Signals
    group_selected = QtCore.Signal(int)  # group_index
    object_selected = QtCore.Signal(int, str)  # group_index, object_name
    selection_changed = QtCore.Signal()
    context_menu_requested = QtCore.Signal(object, QtCore.QPoint)  # item, position
    
    def __init__(self, data_manager: DataManager, parent=None):
        """
        Initialize the tree widget.
        
        Args:
            data_manager: Data manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.data_manager = data_manager
        self.expanded_groups_state: Optional[Set[str]] = None
        
        self._create_ui()
        self._create_connections()
    
    def _create_ui(self) -> None:
        """Create the UI layout."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Search bar
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search groups and objects...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumHeight(24)
        layout.addWidget(self.search_edit)
        
        # Tree widget
        tree_frame = QtWidgets.QFrame()
        tree_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        tree_frame.setFrameShadow(QtWidgets.QFrame.Sunken)
        tree_frame.setStyleSheet("QFrame { background-color: palette(base); }")
        tree_layout = QtWidgets.QVBoxLayout(tree_frame)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                border: none;
                selection-background-color: #4a90e2;
            }}
            QTreeWidget::item {{
                padding: {TREE_ITEM_PADDING}px;
            }}
            QTreeWidget::item:selected {{
                background-color: #4a90e2;
                color: white;
            }}
        """)
        tree_layout.addWidget(self.tree_widget)
        layout.addWidget(tree_frame)
    
    def _create_connections(self) -> None:
        """Connect signals."""
        self.search_edit.textChanged.connect(self._filter_tree_items)
        self.tree_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree_widget.customContextMenuRequested.connect(
            lambda pos: self.context_menu_requested.emit(
                self.tree_widget.itemAt(pos), pos
            )
        )
    
    def refresh(self, preserve_selection: bool = True) -> None:
        """
        Refresh the tree view.
        
        Args:
            preserve_selection: Whether to preserve current selection
        """
        # Capture state
        selected_groups: Set[str] = set()
        selected_objects: Set[Tuple[str, str]] = set()
        expanded_groups: Set[str] = set()
        
        if preserve_selection and self.tree_widget.topLevelItemCount() > 0:
            # Save expanded state
            for i in range(self.tree_widget.topLevelItemCount()):
                item = self.tree_widget.topLevelItem(i)
                if item:
                    item_data = item.data(0, QtCore.Qt.UserRole)
                    if item_data and item_data.get("type") == "group":
                        set_name = item_data["data"].get("set_name")
                        if set_name and item.isExpanded():
                            expanded_groups.add(set_name)
            
            self.expanded_groups_state = expanded_groups
            
            # Save selection
            for item in self.tree_widget.selectedItems():
                item_data = item.data(0, QtCore.Qt.UserRole)
                if item_data and item_data.get("type") == "group":
                    set_name = item_data["data"].get("set_name")
                    if set_name:
                        selected_groups.add(set_name)
                elif item_data and item_data.get("type") == "object":
                    parent_set = item_data["group"].get("set_name")
                    obj_name = item_data["name"]
                    if parent_set and obj_name:
                        selected_objects.add((parent_set, obj_name))
        
        # Block signals and clear
        self.tree_widget.blockSignals(True)
        self.tree_widget.clear()
        
        # Get groups
        groups = self.data_manager.get_all_export_groups()
        
        items_to_select = []
        
        # Build tree
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
                    obj_item.setData(0, QtCore.Qt.UserRole, {
                        "type": "object",
                        "name": obj,
                        "group": group
                    })
                    obj_item.setForeground(0, QtGui.QColor(180, 180, 180))
                    group_item.addChild(obj_item)
                    
                    # Check if should be selected
                    if (set_name, obj) in selected_objects:
                        items_to_select.append(obj_item)
            
            self.tree_widget.addTopLevelItem(group_item)
            
            # Restore expanded state
            if self.expanded_groups_state is not None:
                group_item.setExpanded(set_name in self.expanded_groups_state)
            else:
                group_item.setExpanded(True)
            
            # Check if group should be selected
            if set_name in selected_groups:
                items_to_select.append(group_item)
        
        # Unblock signals
        self.tree_widget.blockSignals(False)
        
        # Restore selection
        if items_to_select:
            # Temporarily disconnect
            try:
                self.tree_widget.itemSelectionChanged.disconnect(self._on_selection_changed)
            except (TypeError, RuntimeError) as e:
                # Signal wasn't connected, which is fine
                logger.debug(f"Could not disconnect signal: {e}")
            
            # Set current and select all
            self.tree_widget.setCurrentItem(items_to_select[0])
            for item in items_to_select:
                item.setSelected(True)
                parent = item.parent()
                if parent:
                    parent.setExpanded(True)
                    parent_data = parent.data(0, QtCore.Qt.UserRole)
                    if parent_data and parent_data.get("type") == "group":
                        parent_set_name = parent_data["data"].get("set_name")
                        if parent_set_name and self.expanded_groups_state is not None:
                            self.expanded_groups_state.add(parent_set_name)
            
            # Reconnect
            try:
                self.tree_widget.itemSelectionChanged.connect(self._on_selection_changed)
            except (TypeError, RuntimeError) as e:
                # Connection failed, which is an error
                logger.error(f"Could not reconnect signal: {e}")
        
        # Re-apply search filter
        if self.search_edit.text():
            self._filter_tree_items(self.search_edit.text())
    
    def _filter_tree_items(self, search_text: str) -> None:
        """
        Filter tree items based on search text.
        
        Args:
            search_text: Text to search for
        """
        search_text = search_text.lower()
        
        for i in range(self.tree_widget.topLevelItemCount()):
            group_item = self.tree_widget.topLevelItem(i)
            if not group_item:
                continue
            
            # Check if group name matches
            group_match = search_text in group_item.text(0).lower()
            
            # Check if any child matches
            child_match = False
            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                if child_item:
                    child_text_match = search_text in child_item.text(0).lower()
                    child_item.setHidden(not search_text == "" and not child_text_match)
                    if child_text_match:
                        child_match = True
            
            # Show group if it matches or if any child matches
            group_item.setHidden(not search_text == "" and not group_match and not child_match)
            
            # Expand groups with matching children
            if child_match and search_text != "":
                group_item.setExpanded(True)
    
    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        self.selection_changed.emit()
        
        # Emit specific signals
        selected = self.tree_widget.selectedItems()
        if selected:
            item = selected[0]
            item_data = item.data(0, QtCore.Qt.UserRole)
            
            if item_data and item_data.get("type") == "group":
                # Find group index
                groups = self.data_manager.get_all_export_groups()
                for i, group in enumerate(groups):
                    if group.get("set_name") == item_data["data"].get("set_name"):
                        self.group_selected.emit(i)
                        break
            elif item_data and item_data.get("type") == "object":
                # Find group index
                groups = self.data_manager.get_all_export_groups()
                parent_set = item_data["group"].get("set_name")
                for i, group in enumerate(groups):
                    if group.get("set_name") == parent_set:
                        self.object_selected.emit(i, item_data["name"])
                        break
    
    def get_selected_group_index(self) -> Optional[int]:
        """
        Get the index of the selected group.
        
        Returns:
            Group index, or None if no group selected
        """
        selected = self.tree_widget.selectedItems()
        if not selected:
            return None
        
        item = selected[0]
        item_data = item.data(0, QtCore.Qt.UserRole)
        
        # If object selected, get parent group
        if item_data and item_data.get("type") == "object":
            item = item.parent()
            if item:
                item_data = item.data(0, QtCore.Qt.UserRole)
        
        if item_data and item_data.get("type") == "group":
            groups = self.data_manager.get_all_export_groups()
            for i, group in enumerate(groups):
                if group.get("set_name") == item_data["data"].get("set_name"):
                    return i
        
        return None
    
    def get_selected_items_info(self) -> Dict[str, any]:
        """
        Get information about selected items.
        
        Returns:
            Dictionary with selection info
        """
        selected = self.tree_widget.selectedItems()
        
        groups = []
        objects_by_group = {}
        
        for item in selected:
            item_data = item.data(0, QtCore.Qt.UserRole)
            
            if item_data and item_data.get("type") == "group":
                groups.append(item_data["data"])
            elif item_data and item_data.get("type") == "object":
                group = item_data["group"]
                set_name = group.get("set_name")
                obj_name = item_data["name"]
                
                if set_name not in objects_by_group:
                    objects_by_group[set_name] = []
                objects_by_group[set_name].append(obj_name)
        
        return {
            "groups": groups,
            "objects_by_group": objects_by_group
        }
    
    def clear_search(self) -> None:
        """Clear the search field."""
        self.search_edit.clear()

