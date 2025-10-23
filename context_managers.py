"""
Context Managers
Reusable context managers for resource management.
"""

from typing import Optional, List
from .maya_facade import MayaSceneInterface
from .logger import get_logger

logger = get_logger(__name__)


class MayaSelectionContext:
    """Context manager for saving and restoring Maya selection."""
    
    def __init__(self, maya_scene: MayaSceneInterface):
        """
        Initialize the selection context.
        
        Args:
            maya_scene: Maya scene interface
        """
        self.maya_scene = maya_scene
        self.saved_selection: Optional[List[str]] = None
    
    def __enter__(self):
        """Save current selection."""
        self.saved_selection = self.maya_scene.get_selection()
        logger.debug(f"Saved selection: {len(self.saved_selection)} objects")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore saved selection."""
        try:
            if self.saved_selection:
                self.maya_scene.select(self.saved_selection, replace=True)
            else:
                self.maya_scene.select(clear=True)
            logger.debug("Restored selection")
        except Exception as e:
            logger.warning(f"Failed to restore selection: {e}")
        return False


class IsolationContext:
    """Context manager for viewport isolation."""
    
    def __init__(self, maya_scene: MayaSceneInterface, panel: str):
        """
        Initialize the isolation context.
        
        Args:
            maya_scene: Maya scene interface
            panel: Panel name to isolate
        """
        self.maya_scene = maya_scene
        self.panel = panel
        self.was_isolated = False
    
    def __enter__(self):
        """Save isolation state."""
        try:
            self.was_isolated = self.maya_scene.isolate_select(
                self.panel, query=True
            ) or False
            logger.debug(f"Saved isolation state for {self.panel}: {self.was_isolated}")
        except Exception as e:
            logger.warning(f"Could not query isolation state: {e}")
            self.was_isolated = False
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore isolation state."""
        try:
            if not self.was_isolated:
                self.maya_scene.isolate_select(self.panel, state=False)
                logger.debug(f"Restored isolation state for {self.panel}")
        except Exception as e:
            logger.warning(f"Failed to restore isolation state: {e}")
        return False


class PausedTimerContext:
    """Context manager for pausing and resuming a QTimer."""
    
    def __init__(self, timer):
        """
        Initialize the timer context.
        
        Args:
            timer: QTimer instance to pause
        """
        self.timer = timer
        self.was_active = False
    
    def __enter__(self):
        """Pause the timer."""
        self.was_active = self.timer.isActive()
        if self.was_active:
            self.timer.stop()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Resume the timer if it was active."""
        if self.was_active:
            self.timer.start()
        return False

