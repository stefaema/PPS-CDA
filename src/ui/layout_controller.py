# src/ui/layout_controller.py
import logging
from typing import Optional, List, Callable, TypedDict, Any
from nicegui import ui

# Configure module-level logger
logger = logging.getLogger(__name__)

class ToolButton(TypedDict):
    """
    Type definition for a tool button in the navbar.
    """
    icon: str
    callback: Callable[[], Any]
    tooltip: Optional[str]
    color: Optional[str]  # e.g., 'white', 'warning', 'negative'

class LayoutController:
    """
    Singleton Controller for managing the Global Layout State.
    Acts as a bridge between business logic (Orchestrators) and the View (Layout).
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LayoutController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self._title_label: Optional[ui.label] = None
        self._tools_container: Optional[ui.row] = None
        self._default_title: str = "Audiovisual Lab"
        self._initialized = True

    def register_ui(self, title_label: ui.label, tools_container: ui.row) -> None:
        """
        Binds the actual UI elements to the controller. 
        Must be called once per page load by the main_layout.
        """
        if not isinstance(title_label, ui.label):
            logger.error(f"Invalid type for title_label: {type(title_label)}")
            return
        
        self._title_label = title_label
        self._tools_container = tools_container
        
        # Reset to default state on registration to prevent stale data from previous pages
        self.reset()
        logger.debug("Layout Controller registered new UI elements.")

    def set_title(self, text: str) -> None:
        """
        Updates the global header title. safe to call even if UI is not ready.
        """
        if self._title_label is None:
            logger.warning("Attempted to set title before UI registration.")
            return

        try:
            self._title_label.set_text(text)
        except Exception as e:
            logger.error(f"Failed to set title: {e}")

    def set_tools(self, tools: List[ToolButton]) -> None:
        """
        Dynamically populates the right-side tools area.
        
        Args:
            tools: A list of dictionaries matching the ToolButton TypedDict.
        """
        if self._tools_container is None:
            logger.warning("Attempted to set tools before UI registration.")
            return

        try:
            self._tools_container.clear()
            with self._tools_container:
                for tool in tools:
                    self._render_tool_button(tool)
        except Exception as e:
            logger.error(f"Failed to render tools: {e}")

    def _render_tool_button(self, tool: ToolButton):
        """Helper to render a single button with error checking."""
        icon = tool.get('icon', 'help')
        cb = tool.get('callback', lambda: None)
        tooltip = tool.get('tooltip')
        color = tool.get('color', 'white')

        btn = ui.button(on_click=cb) \
            .props(f'icon={icon} flat round dense color={color}')
        
        if tooltip:
            btn.tooltip(tooltip)

    def reset(self) -> None:
        """Resets the layout to its default state."""
        self.set_title(self._default_title)
        if self._tools_container:
            self._tools_container.clear()

# Global Singleton Instance
layout_controller = LayoutController()
