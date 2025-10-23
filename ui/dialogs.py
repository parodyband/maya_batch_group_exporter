"""
UI Dialogs
Reusable dialog windows.
"""

from typing import Optional, List

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtWidgets

from ..types import ExportResultDict
from ..logger import get_logger

logger = get_logger(__name__)


def get_maya_main_window():
    """Get Maya's main window as a Qt object."""
    from maya import OpenMayaUI as omui
    try:
        from shiboken2 import wrapInstance
    except ImportError:
        from shiboken6 import wrapInstance
    
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class NewGroupDialog(QtWidgets.QInputDialog):
    """Dialog for creating a new export group."""
    
    @staticmethod
    def get_group_name(parent=None) -> Optional[str]:
        """
        Show dialog to get a new group name.
        
        Args:
            parent: Parent widget
            
        Returns:
            Group name, or None if cancelled
        """
        dialog = QtWidgets.QInputDialog(parent or get_maya_main_window())
        dialog.setWindowTitle("New Export Group")
        dialog.setLabelText("Enter group name:")
        dialog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        
        ok = dialog.exec_()
        name = dialog.textValue()
        
        if ok and name:
            return name
        return None


class RenameGroupDialog(QtWidgets.QInputDialog):
    """Dialog for renaming an export group."""
    
    @staticmethod
    def get_new_name(current_name: str, parent=None) -> Optional[str]:
        """
        Show dialog to rename a group.
        
        Args:
            current_name: Current group name
            parent: Parent widget
            
        Returns:
            New group name, or None if cancelled
        """
        dialog = QtWidgets.QInputDialog(parent or get_maya_main_window())
        dialog.setWindowTitle("Rename Group")
        dialog.setLabelText("Enter new name:")
        dialog.setTextValue(current_name)
        dialog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        
        ok = dialog.exec_()
        new_name = dialog.textValue()
        
        if ok and new_name and new_name != current_name:
            return new_name
        return None


class ConfirmDeleteDialog:
    """Dialog for confirming deletion."""
    
    @staticmethod
    def confirm(message: str, parent=None) -> bool:
        """
        Show confirmation dialog.
        
        Args:
            message: Message to display
            parent: Parent widget
            
        Returns:
            True if confirmed
        """
        reply = QtWidgets.QMessageBox.question(
            parent or get_maya_main_window(),
            "Confirm Delete",
            message,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        return reply == QtWidgets.QMessageBox.Yes


class ExportResultsDialog:
    """Dialog for showing export results."""
    
    @staticmethod
    def show_single_result(success: bool, message: str, parent=None) -> None:
        """
        Show single export result.
        
        Args:
            success: Whether export succeeded
            message: Result message
            parent: Parent widget
        """
        if success:
            QtWidgets.QMessageBox.information(
                parent or get_maya_main_window(),
                "Export Complete",
                message
            )
        else:
            QtWidgets.QMessageBox.critical(
                parent or get_maya_main_window(),
                "Export Failed",
                message
            )
    
    @staticmethod
    def show_batch_results(results: List[ExportResultDict], success_count: int, 
                          total_count: int, parent=None) -> None:
        """
        Show batch export results.
        
        Args:
            results: List of export results
            success_count: Number of successful exports
            total_count: Total number of exports
            parent: Parent widget
        """
        message = f"Exported {success_count} of {total_count} groups successfully.\n\n"
        
        for result in results:
            status = "SUCCESS" if result["success"] else "FAILED"
            message += f"{status}: {result['group_name']}\n{result['message']}\n\n"
        
        if success_count == total_count:
            QtWidgets.QMessageBox.information(
                parent or get_maya_main_window(),
                "Export Complete",
                message
            )
        else:
            QtWidgets.QMessageBox.warning(
                parent or get_maya_main_window(),
                "Export Completed with Errors",
                message
            )


class ConfirmExportDialog:
    """Dialog for confirming export."""
    
    @staticmethod
    def confirm_export_all(group_count: int, parent=None) -> bool:
        """
        Confirm exporting all groups.
        
        Args:
            group_count: Number of groups to export
            parent: Parent widget
            
        Returns:
            True if confirmed
        """
        reply = QtWidgets.QMessageBox.question(
            parent or get_maya_main_window(),
            "Confirm Export",
            f"Export all {group_count} groups?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        return reply == QtWidgets.QMessageBox.Yes


class InfoDialog:
    """Generic information dialog."""
    
    @staticmethod
    def show_info(title: str, message: str, parent=None) -> None:
        """
        Show information message.
        
        Args:
            title: Dialog title
            message: Message to display
            parent: Parent widget
        """
        QtWidgets.QMessageBox.information(
            parent or get_maya_main_window(),
            title,
            message
        )
    
    @staticmethod
    def show_warning(title: str, message: str, parent=None) -> None:
        """
        Show warning message.
        
        Args:
            title: Dialog title
            message: Message to display
            parent: Parent widget
        """
        QtWidgets.QMessageBox.warning(
            parent or get_maya_main_window(),
            title,
            message
        )
    
    @staticmethod
    def show_error(title: str, message: str, parent=None) -> None:
        """
        Show error message.
        
        Args:
            title: Dialog title
            message: Message to display
            parent: Parent widget
        """
        QtWidgets.QMessageBox.critical(
            parent or get_maya_main_window(),
            title,
            message
        )

