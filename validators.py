"""
Input Validators
Validation logic for user inputs and data.
"""

import os
import re
from typing import List, Optional
from .exceptions import ValidationError
from .logger import get_logger

logger = get_logger(__name__)


class NameValidator:
    """Validates group and object names."""
    
    # Invalid characters for Maya object names
    INVALID_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
    
    @staticmethod
    def validate_group_name(name: str) -> str:
        """
        Validate a group name.
        
        Args:
            name: The group name to validate
            
        Returns:
            Sanitized group name
            
        Raises:
            ValidationError: If the name is invalid
        """
        if not name:
            raise ValidationError("Group name cannot be empty")
        
        if not isinstance(name, str):
            raise ValidationError(f"Group name must be a string, got {type(name)}")
        
        # Strip whitespace
        name = name.strip()
        
        if not name:
            raise ValidationError("Group name cannot be only whitespace")
        
        # Check length
        if len(name) > 255:
            raise ValidationError("Group name is too long (max 255 characters)")
        
        # Check for invalid characters (less strict for display names)
        if NameValidator.INVALID_CHARS_PATTERN.search(name):
            raise ValidationError(
                f"Group name contains invalid characters: {name}"
            )
        
        return name
    
    @staticmethod
    def sanitize_for_maya_name(name: str) -> str:
        """
        Sanitize a name to be safe for Maya object names.
        
        Args:
            name: The name to sanitize
            
        Returns:
            Sanitized name safe for Maya
        """
        # Replace spaces with underscores
        sanitized = name.replace(" ", "_")
        
        # Remove invalid characters
        sanitized = NameValidator.INVALID_CHARS_PATTERN.sub("_", sanitized)
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = "_" + sanitized
        
        # Remove consecutive underscores
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        
        return sanitized


class PathValidator:
    """Validates file paths and directories."""
    
    @staticmethod
    def validate_directory(path: str, must_exist: bool = False) -> str:
        """
        Validate a directory path.
        
        Args:
            path: The directory path to validate
            must_exist: If True, raises error if directory doesn't exist
            
        Returns:
            Validated directory path
            
        Raises:
            ValidationError: If the path is invalid
        """
        if not path:
            raise ValidationError("Directory path cannot be empty")
        
        if not isinstance(path, str):
            raise ValidationError(f"Directory path must be a string, got {type(path)}")
        
        # Normalize path
        path = os.path.normpath(path)
        
        # Check if it's an absolute path
        if not os.path.isabs(path):
            logger.warning(f"Directory path is not absolute: {path}")
        
        # Check existence if required
        if must_exist and not os.path.exists(path):
            raise ValidationError(f"Directory does not exist: {path}")
        
        # Check if it's a file (should be a directory)
        if os.path.exists(path) and os.path.isfile(path):
            raise ValidationError(f"Path is a file, not a directory: {path}")
        
        return path
    
    @staticmethod
    def validate_file_path(path: str, must_exist: bool = False, 
                          extensions: Optional[List[str]] = None) -> str:
        """
        Validate a file path.
        
        Args:
            path: The file path to validate
            must_exist: If True, raises error if file doesn't exist
            extensions: List of valid extensions (e.g., ['.json', '.txt'])
            
        Returns:
            Validated file path
            
        Raises:
            ValidationError: If the path is invalid
        """
        if not path:
            raise ValidationError("File path cannot be empty")
        
        if not isinstance(path, str):
            raise ValidationError(f"File path must be a string, got {type(path)}")
        
        # Normalize path
        path = os.path.normpath(path)
        
        # Check extension if specified
        if extensions:
            _, ext = os.path.splitext(path)
            if ext.lower() not in [e.lower() for e in extensions]:
                raise ValidationError(
                    f"Invalid file extension. Expected one of {extensions}, got '{ext}'"
                )
        
        # Check existence if required
        if must_exist and not os.path.exists(path):
            raise ValidationError(f"File does not exist: {path}")
        
        # Check if it's a directory (should be a file)
        if os.path.exists(path) and os.path.isdir(path):
            raise ValidationError(f"Path is a directory, not a file: {path}")
        
        return path
    
    @staticmethod
    def is_path_writable(path: str) -> bool:
        """
        Check if a path is writable.
        
        Args:
            path: Path to check (file or directory)
            
        Returns:
            True if writable, False otherwise
        """
        try:
            # If path exists, check if writable
            if os.path.exists(path):
                return os.access(path, os.W_OK)
            
            # If path doesn't exist, check if parent directory is writable
            parent = os.path.dirname(path)
            if not parent:
                parent = "."
            
            return os.access(parent, os.W_OK)
        except Exception as e:
            logger.warning(f"Error checking if path is writable: {e}")
            return False

