"""
Dependency Injection Container
Simple DI container for managing dependencies.
"""

from .maya_facade import MayaSceneAdapter, MayaSceneInterface
from .set_manager import SetManager
from .persistence import JsonConfigRepository, ConfigPathResolver, ConfigRepository
from .data_manager import DataManager
from .exporters.fbx_exporter import FBXExporter
from .exporters.export_service import ExportService
from .events import EventBus
from .logger import get_logger

logger = get_logger(__name__)


class Container:
    """Dependency injection container."""
    
    def __init__(self):
        """Initialize the container."""
        self._instances = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize all dependencies."""
        if self._initialized:
            logger.warning("Container already initialized")
            return
        
        logger.info("Initializing dependency container")
        
        # Create Maya facade
        maya_scene = MayaSceneAdapter()
        self._instances['maya_scene'] = maya_scene
        
        # Create managers
        set_manager = SetManager(maya_scene)
        self._instances['set_manager'] = set_manager
        
        config_repository = JsonConfigRepository()
        self._instances['config_repository'] = config_repository
        
        path_resolver = ConfigPathResolver(maya_scene)
        self._instances['path_resolver'] = path_resolver
        
        # Create data manager
        data_manager = DataManager(
            maya_scene=maya_scene,
            set_manager=set_manager,
            config_repository=config_repository,
            path_resolver=path_resolver
        )
        self._instances['data_manager'] = data_manager
        
        # Create exporters
        fbx_exporter = FBXExporter(maya_scene)
        self._instances['fbx_exporter'] = fbx_exporter
        
        export_service = ExportService(fbx_exporter)
        self._instances['export_service'] = export_service
        
        # Create event bus
        event_bus = EventBus()
        self._instances['event_bus'] = event_bus
        
        self._initialized = True
        logger.info("Dependency container initialized")
    
    def get_maya_scene(self) -> MayaSceneInterface:
        """Get Maya scene interface."""
        self._ensure_initialized()
        return self._instances['maya_scene']
    
    def get_set_manager(self) -> SetManager:
        """Get set manager."""
        self._ensure_initialized()
        return self._instances['set_manager']
    
    def get_config_repository(self) -> ConfigRepository:
        """Get config repository."""
        self._ensure_initialized()
        return self._instances['config_repository']
    
    def get_path_resolver(self) -> ConfigPathResolver:
        """Get path resolver."""
        self._ensure_initialized()
        return self._instances['path_resolver']
    
    def get_data_manager(self) -> DataManager:
        """Get data manager."""
        self._ensure_initialized()
        return self._instances['data_manager']
    
    def get_fbx_exporter(self) -> FBXExporter:
        """Get FBX exporter."""
        self._ensure_initialized()
        return self._instances['fbx_exporter']
    
    def get_export_service(self) -> ExportService:
        """Get export service."""
        self._ensure_initialized()
        return self._instances['export_service']
    
    def get_event_bus(self) -> EventBus:
        """Get event bus."""
        self._ensure_initialized()
        return self._instances['event_bus']
    
    def _ensure_initialized(self) -> None:
        """Ensure container is initialized."""
        if not self._initialized:
            self.initialize()
    
    def reset(self) -> None:
        """Reset the container (useful for testing)."""
        logger.info("Resetting dependency container")
        self._instances.clear()
        self._initialized = False


# Global container instance
_container: Container = None


def get_container() -> Container:
    """
    Get the global container instance.
    
    Returns:
        Container instance
    """
    global _container
    if _container is None:
        _container = Container()
        _container.initialize()
    return _container


def reset_container() -> None:
    """Reset the global container."""
    global _container
    if _container is not None:
        _container.reset()
    _container = None

