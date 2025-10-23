"""
Logging Infrastructure
Centralized logging for the batch exporter with Maya integration.
"""

import logging
import sys
from typing import Optional


class MayaLogHandler(logging.Handler):
    """Custom log handler that integrates with Maya's script editor."""
    
    def __init__(self):
        super().__init__()
        self.maya_available = False
        try:
            import maya.cmds as cmds
            self.cmds = cmds
            self.maya_available = True
        except ImportError:
            pass
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to Maya's script editor."""
        try:
            msg = self.format(record)
            
            if not self.maya_available:
                print(msg)
                return
            
            if record.levelno >= logging.ERROR:
                self.cmds.error(msg)
            elif record.levelno >= logging.WARNING:
                self.cmds.warning(msg)
            else:
                # Info and debug go to script editor as regular output
                print(msg)
        except Exception:
            self.handleError(record)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for the batch exporter.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Add Maya handler
        maya_handler = MayaLogHandler()
        maya_handler.setLevel(logging.DEBUG)
        
        # Format: [LEVEL] module: message
        formatter = logging.Formatter(
            '[%(levelname)s] %(name)s: %(message)s'
        )
        maya_handler.setFormatter(formatter)
        
        logger.addHandler(maya_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


def set_log_level(level: int) -> None:
    """
    Set the global log level for all batch exporter loggers.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    root_logger = logging.getLogger('maya_batch_group_exporter')
    root_logger.setLevel(level)
    
    for handler in root_logger.handlers:
        handler.setLevel(level)

