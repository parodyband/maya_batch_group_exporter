"""
Export Toolbar
Toolbar with view controls and scene summary.
"""

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ...data_manager import DataManager
from ...constants import BUTTON_HEIGHT_ACTION, SPACING_MEDIUM
from ...logger import get_logger

logger = get_logger(__name__)


class ExportToolbar(QtWidgets.QWidget):
    """
    Toolbar widget for view controls and scene summary.
    """
    
    # Signals
    select_in_scene_clicked = QtCore.Signal()
    isolate_clicked = QtCore.Signal()
    refresh_clicked = QtCore.Signal()
    
    def __init__(self, data_manager: DataManager, parent=None):
        """
        Initialize the toolbar.
        
        Args:
            data_manager: Data manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.data_manager = data_manager
        self.is_isolated = False
        
        self._create_ui()
        self._create_connections()
    
    def _create_ui(self) -> None:
        """Create the UI layout."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 4)
        layout.setSpacing(SPACING_MEDIUM)
        
        # Action buttons
        self.select_objects_btn = QtWidgets.QPushButton("Select in Scene")
        self.isolate_btn = QtWidgets.QPushButton("Isolate")
        self.refresh_btn = QtWidgets.QPushButton("↻ Refresh")
        
        self.select_objects_btn.setMinimumHeight(BUTTON_HEIGHT_ACTION)
        self.isolate_btn.setMinimumHeight(BUTTON_HEIGHT_ACTION)
        self.refresh_btn.setMinimumHeight(BUTTON_HEIGHT_ACTION)
        
        self.select_objects_btn.setToolTip("Select objects from selected group/items in Maya scene")
        self.isolate_btn.setToolTip("Isolate selected group in viewport")
        self.refresh_btn.setToolTip("Refresh tree view")
        
        layout.addWidget(self.select_objects_btn)
        layout.addWidget(self.isolate_btn)
        layout.addStretch()
        
        # Scene summary
        self.summary_label = QtWidgets.QLabel("0 groups | 0 objects")
        self.summary_label.setStyleSheet("QLabel { color: #888888; font-size: 10px; }")
        layout.addWidget(self.summary_label)
        
        layout.addWidget(self.refresh_btn)
    
    def _create_connections(self) -> None:
        """Connect signals."""
        self.select_objects_btn.clicked.connect(self.select_in_scene_clicked.emit)
        self.isolate_btn.clicked.connect(self.isolate_clicked.emit)
        self.refresh_btn.clicked.connect(self.refresh_clicked.emit)
    
    def update_summary(self) -> None:
        """Update the scene summary label."""
        groups = self.data_manager.get_all_export_groups()
        total_objects = 0
        
        for group in groups:
            set_name = group.get("set_name")
            if set_name:
                objects = self.data_manager.get_set_objects(set_name)
                total_objects += len(objects)
        
        self.summary_label.setText(f"{len(groups)} groups | {total_objects} objects")
    
    def set_isolated_state(self, is_isolated: bool) -> None:
        """
        Update the isolate button appearance.
        
        Args:
            is_isolated: Whether currently isolated
        """
        self.is_isolated = is_isolated
        
        if is_isolated:
            self.isolate_btn.setText("Unisolate")
            self.isolate_btn.setStyleSheet(
                "QPushButton { background-color: #e67e22; color: white; font-weight: bold; }"
            )
        else:
            self.isolate_btn.setText("Isolate")
            self.isolate_btn.setStyleSheet("")

