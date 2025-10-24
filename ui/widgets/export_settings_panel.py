"""
Export Settings Panel
Panel for export directory and file prefix settings.
"""

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ...constants import (
    LABEL_WIDTH_STANDARD, BROWSE_BUTTON_WIDTH,
    SPACING_MEDIUM, MARGIN_LARGE
)
from ...logger import get_logger

logger = get_logger(__name__)


class ExportSettingsPanel(QtWidgets.QGroupBox):
    """
    Panel for configuring export directory and file prefix.
    """
    
    # Signals
    directory_changed = QtCore.Signal(str)
    prefix_changed = QtCore.Signal(str)
    
    def __init__(self, parent=None):
        """
        Initialize the export settings panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__("Export Settings", parent)
        
        self.setStyleSheet("QGroupBox { font-weight: bold; }")
        self._create_ui()
        self._create_connections()
    
    def _create_ui(self) -> None:
        """Create the UI layout."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(MARGIN_LARGE, 10, MARGIN_LARGE, MARGIN_LARGE)
        layout.setSpacing(SPACING_MEDIUM)
        
        # Directory row
        dir_layout = QtWidgets.QHBoxLayout()
        dir_layout.setSpacing(SPACING_MEDIUM)
        
        dir_label = QtWidgets.QLabel("Directory:")
        dir_label.setFixedWidth(LABEL_WIDTH_STANDARD)
        dir_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        dir_layout.addWidget(dir_label)
        
        self.export_dir_edit = QtWidgets.QLineEdit()
        self.export_dir_edit.setPlaceholderText("Export directory (absolute or relative)...")
        self.export_dir_edit.setToolTip("Export directory - use absolute path (C:/path) or relative to scene (../Models/)")
        dir_layout.addWidget(self.export_dir_edit)
        
        self.browse_dir_btn = QtWidgets.QPushButton("...")
        self.browse_dir_btn.setFixedWidth(BROWSE_BUTTON_WIDTH)
        self.browse_dir_btn.setMinimumHeight(22)
        self.browse_dir_btn.setToolTip("Browse for export directory")
        dir_layout.addWidget(self.browse_dir_btn)
        
        layout.addLayout(dir_layout)
        
        # Prefix row
        prefix_layout = QtWidgets.QHBoxLayout()
        prefix_layout.setSpacing(SPACING_MEDIUM)
        
        prefix_label = QtWidgets.QLabel("Prefix:")
        prefix_label.setFixedWidth(LABEL_WIDTH_STANDARD)
        prefix_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        prefix_layout.addWidget(prefix_label)
        
        self.prefix_edit = QtWidgets.QLineEdit()
        self.prefix_edit.setPlaceholderText("Optional prefix...")
        self.prefix_edit.setToolTip("Files will be saved as [Prefix][GroupName].fbx")
        prefix_layout.addWidget(self.prefix_edit)
        
        prefix_layout.addSpacing(BROWSE_BUTTON_WIDTH)
        
        layout.addLayout(prefix_layout)
    
    def _create_connections(self) -> None:
        """Connect signals."""
        self.export_dir_edit.textChanged.connect(self.directory_changed.emit)
        self.prefix_edit.textChanged.connect(self.prefix_changed.emit)
        self.browse_dir_btn.clicked.connect(self._browse_directory)
    
    def _browse_directory(self) -> None:
        """Browse for export directory."""
        current_dir = self.export_dir_edit.text() or ""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Export Directory", current_dir
        )
        
        if directory:
            self.export_dir_edit.setText(directory)
    
    def get_directory(self) -> str:
        """Get the current directory."""
        return self.export_dir_edit.text()
    
    def set_directory(self, directory: str) -> None:
        """
        Set the directory.
        
        Args:
            directory: Directory path
        """
        self.export_dir_edit.blockSignals(True)
        self.export_dir_edit.setText(directory)
        self.export_dir_edit.blockSignals(False)
    
    def get_prefix(self) -> str:
        """Get the current prefix."""
        return self.prefix_edit.text()
    
    def set_prefix(self, prefix: str) -> None:
        """
        Set the prefix.
        
        Args:
            prefix: File prefix
        """
        self.prefix_edit.blockSignals(True)
        self.prefix_edit.setText(prefix)
        self.prefix_edit.blockSignals(False)

