"""
Event System
Observer pattern implementation for decoupled UI updates.
"""

from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class Event:
    """Base class for all events."""
    pass


@dataclass
class GroupAddedEvent(Event):
    """Fired when a new group is added."""
    group_index: int
    group_name: str


@dataclass
class GroupRemovedEvent(Event):
    """Fired when a group is removed."""
    group_name: str


@dataclass
class GroupUpdatedEvent(Event):
    """Fired when a group is updated."""
    group_index: int
    group_name: str


@dataclass
class GroupDuplicatedEvent(Event):
    """Fired when a group is duplicated."""
    original_index: int
    new_index: int


@dataclass
class ObjectsAddedToGroupEvent(Event):
    """Fired when objects are added to a group."""
    group_index: int
    object_count: int


@dataclass
class ObjectsRemovedFromGroupEvent(Event):
    """Fired when objects are removed from a group."""
    group_index: int
    object_count: int


@dataclass
class ExportCompletedEvent(Event):
    """Fired when an export completes."""
    success: bool
    group_name: str
    message: str


@dataclass
class SettingsChangedEvent(Event):
    """Fired when export settings change."""
    setting_name: str
    new_value: Any


class EventBus:
    """
    Event bus for pub-sub messaging.
    Allows decoupled communication between components.
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[type, List[Callable]] = {}
    
    def subscribe(self, event_type: type, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is published
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.__name__}")
    
    def unsubscribe(self, event_type: type, callback: Callable[[Event], None]) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type.__name__}")
            except ValueError:
                pass
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        event_type = type(event)
        
        if event_type not in self._subscribers:
            return
        
        logger.debug(f"Publishing {event_type.__name__}")
        
        for callback in self._subscribers[event_type]:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}")
    
    def clear_all(self) -> None:
        """Clear all subscribers."""
        self._subscribers.clear()
        logger.debug("Cleared all event subscribers")

