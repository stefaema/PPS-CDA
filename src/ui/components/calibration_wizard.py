# src/ui/components/calibration_wizard.py
from typing import List
from nicegui import ui
from core.calibration_context import CalibrationContext
from ui.pages.calibration_steps.step_base import CalibrationStep
from ui.layout_controller import layout_controller
from core.locale_manager import T
from core.log_manager import logger

class CalibrationWizardOrchestrator:
    """
    Manages the navigation flow of the Calibration Wizard.
    Controls the LayoutController and instantiates steps.
    """
    def __init__(self, container: ui.element, context: CalibrationContext, steps: List[CalibrationStep]):
        self.container = container
        self.context = context
        self.steps = steps
        self.current_idx = 0

    def start(self):
        """Begins the wizard at step 0."""
        self.context.reset()
        self.current_idx = 0
        self._load_current_step()

    def _load_current_step(self):
        if not (0 <= self.current_idx < len(self.steps)):
            logger.error(f"Invalid step index: {self.current_idx}")
            return

        step = self.steps[self.current_idx]
        
        tools: List[dict] = step.get_tools()

        if self.current_idx > 0:
            back_tool = {
                'icon': 'arrow_back',
                'callback': self._handle_back,
                'tooltip': T("back_to_previous_step"),
                'color': 'white'
            }
            tools.insert(0, back_tool)
        

        # 1. Update Layout (Navbar)
        layout_controller.set_title(step.title)
        layout_controller.set_tools(tools)

        # 2. Lifecycle: Enter
        step.on_enter()

        # 3. Render UI
        self.container.clear()
        with self.container:
            step.render(
                container=self.container,
                on_next=self._handle_next,
                on_back=self._handle_back
            )

    def _handle_next(self, *args):
        """Advances to the next step."""
        current_step = self.steps[self.current_idx]
        current_step.on_leave()

        if self.current_idx < len(self.steps) - 1:
            self.current_idx += 1
            self._load_current_step()
        else:
            self._finish()

    def _handle_back(self):
        """Returns to the previous step or exits."""
        current_step = self.steps[self.current_idx]
        current_step.on_leave()

        if self.current_idx > 0:
            self.current_idx -= 1
            self._load_current_step()
        else:
            ui.navigate.to('/')

    def _finish(self):
        """Finalizes the wizard."""
        ui.notify("Calibration Saved Successfully", type='positive')
        # Logic to save profile to disk/db would go here
        ui.navigate.to('/')
