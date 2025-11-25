# src/ui/pages/calibration_steps/step_base.py
from abc import ABC, abstractmethod
from typing import List, Callable
from nicegui import ui
from core.calibration_context import CalibrationContext
from ui.layout_controller import ToolButton

class CalibrationStep(ABC):
    """
    Abstract Base Class for all Calibration Wizard Steps.
    Enforces a standard lifecycle and interface.
    """
    def __init__(self, context: CalibrationContext):
        self.context = context

    @property
    @abstractmethod
    def title(self) -> str:
        """The title to appear in the Navbar."""
        pass

    @abstractmethod
    def render(self, container: ui.element, on_next: Callable, on_back: Callable):
        """
        Draws the UI for this step.
        Args:
            container: The parent UI element to draw into.
            on_next: Callback to proceed to the next step.
            on_back: Callback to return to previous step.
        """
        pass

    def get_tools(self) -> List[ToolButton]:
        """
        Returns a list of tool buttons specific to this step.
        Override this in child classes if needed.
        """
        return []

    def on_enter(self):
        """Lifecycle hook: Called when the step becomes active."""
        pass

    def on_leave(self):
        """Lifecycle hook: Called when navigating away from the step."""
        pass
