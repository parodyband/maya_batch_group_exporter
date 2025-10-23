"""
Export Service
Coordinates export operations with progress tracking and error handling.
"""

from typing import List, Dict, Any
from .base import Exporter
from ..types import ExportGroupDict, ExportResultDict
from ..logger import get_logger

logger = get_logger(__name__)


class ExportService:
    """Service for coordinating export operations."""
    
    def __init__(self, exporter: Exporter):
        """
        Initialize the export service.
        
        Args:
            exporter: Exporter instance to use
        """
        self.exporter = exporter
    
    def export_single_group(self, group: ExportGroupDict, settings: Dict[str, Any]) -> ExportResultDict:
        """
        Export a single group.
        
        Args:
            group: Export group data
            settings: Export settings
            
        Returns:
            Export result dictionary
        """
        group_name = group.get("name", "untitled")
        logger.info(f"Starting export of group: {group_name}")
        
        success, message = self.exporter.export_group(group, settings)
        
        result: ExportResultDict = {
            "group_name": group_name,
            "success": success,
            "message": message
        }
        
        return result
    
    def export_all_groups(self, groups: List[ExportGroupDict], settings: Dict[str, Any]) -> tuple[List[ExportResultDict], int]:
        """
        Export all groups.
        
        Args:
            groups: List of export groups
            settings: Export settings
            
        Returns:
            Tuple of (results list, success count)
        """
        results: List[ExportResultDict] = []
        success_count = 0
        
        logger.info(f"Starting batch export of {len(groups)} groups")
        
        for i, group in enumerate(groups):
            group_name = group.get("name", f"Group {i}")
            logger.info(f"Exporting group {i+1}/{len(groups)}: {group_name}")
            
            result = self.export_single_group(group, settings)
            results.append(result)
            
            if result["success"]:
                success_count += 1
        
        logger.info(f"Batch export complete: {success_count}/{len(groups)} successful")
        
        return results, success_count

