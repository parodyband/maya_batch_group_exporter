"""
FBX Settings Panel
Panel for FBX-specific export settings.
"""

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ...constants import (
    AVAILABLE_UP_AXES, AVAILABLE_UNITS,
    SPACING_LARGE, SPACING_MEDIUM, MARGIN_LARGE
)
from ...logger import get_logger

logger = get_logger(__name__)


class FBXSettingsPanel(QtWidgets.QGroupBox):
    """
    Panel for FBX-specific settings.
    """
    
    # Signals
    triangulate_changed = QtCore.Signal(bool)
    up_axis_changed = QtCore.Signal(str)
    unit_changed = QtCore.Signal(str)
    
    def __init__(self, parent=None):
        """
        Initialize the FBX settings panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__("FBX Settings", parent)
        
        self.setCheckable(True)
        self.setChecked(True)
        self.setStyleSheet("QGroupBox { font-weight: bold; }")
        
        self._create_ui()
        self._create_connections()
    
    def _create_ui(self) -> None:
        """Create the UI layout."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(MARGIN_LARGE, 10, MARGIN_LARGE, MARGIN_LARGE)
        layout.setSpacing(SPACING_LARGE)
        
        # Triangulate checkbox
        self.triangulate_checkbox = QtWidgets.QCheckBox("Triangulate")
        self.triangulate_checkbox.setToolTip("Triangulate geometry on export")
        layout.addWidget(self.triangulate_checkbox)
        
        layout.addSpacing(SPACING_MEDIUM)
        
        # Up axis
        up_label = QtWidgets.QLabel("Up:")
        up_label.setToolTip("Up axis for exported FBX")
        layout.addWidget(up_label)
        
        self.up_axis_combo = QtWidgets.QComboBox()
        self.up_axis_combo.addItems(AVAILABLE_UP_AXES)
        self.up_axis_combo.setFixedWidth(50)
        self.up_axis_combo.setMinimumHeight(22)
        self.up_axis_combo.setToolTip("Up axis for exported FBX")
        layout.addWidget(self.up_axis_combo)
        
        layout.addSpacing(SPACING_MEDIUM)
        
        # Unit conversion
        unit_label = QtWidgets.QLabel("Unit:")
        unit_label.setToolTip("Unit conversion for export")
        layout.addWidget(unit_label)
        
        self.unit_combo = QtWidgets.QComboBox()
        self.unit_combo.addItems(AVAILABLE_UNITS)
        self.unit_combo.setFixedWidth(60)
        self.unit_combo.setMinimumHeight(22)
        self.unit_combo.setToolTip("Unit conversion for export")
        layout.addWidget(self.unit_combo)
        
        layout.addStretch()
    
    def _create_connections(self) -> None:
        """Connect signals."""
        self.triangulate_checkbox.stateChanged.connect(
            lambda: self.triangulate_changed.emit(self.triangulate_checkbox.isChecked())
        )
        self.up_axis_combo.currentTextChanged.connect(self.up_axis_changed.emit)
        self.unit_combo.currentTextChanged.connect(self.unit_changed.emit)
    
    def get_triangulate(self) -> bool:
        """Get triangulate setting."""
        return self.triangulate_checkbox.isChecked()
    
    def set_triangulate(self, value: bool) -> None:
        """
        Set triangulate setting.
        
        Args:
            value: Whether to triangulate
        """
        self.triangulate_checkbox.blockSignals(True)
        self.triangulate_checkbox.setChecked(value)
        self.triangulate_checkbox.blockSignals(False)
    
    def get_up_axis(self) -> str:
        """Get up axis setting."""
        return self.up_axis_combo.currentText()
    
    def set_up_axis(self, axis: str) -> None:
        """
        Set up axis setting.
        
        Args:
            axis: Up axis ("Y" or "Z")
        """
        self.up_axis_combo.blockSignals(True)
        index = self.up_axis_combo.findText(axis)
        if index >= 0:
            self.up_axis_combo.setCurrentIndex(index)
        self.up_axis_combo.blockSignals(False)
    
    def get_unit(self) -> str:
        """Get unit setting."""
        return self.unit_combo.currentText()
    
    def set_unit(self, unit: str) -> None:
        """
        Set unit setting.
        
        Args:
            unit: Unit conversion
        """
        self.unit_combo.blockSignals(True)
        index = self.unit_combo.findText(unit)
        if index >= 0:
            self.unit_combo.setCurrentIndex(index)
        self.unit_combo.blockSignals(False)

