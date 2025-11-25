# src/ui/pages/calibration.py
from nicegui import ui
from ui.layout import main_layout
from core.calibration_context import CalibrationContext
from ui.components.calibration_wizard import CalibrationWizardOrchestrator
from ui.pages.calibration_steps.step_1_capture import Step1Capture
from ui.pages.calibration_steps.step_2_roi import Step2ROI
from ui.pages.calibration_steps.step_3_profile import Step3Profile
from ui.scripts.calibration import ALL_CALIBRATION_SCRIPTS
from ui.styles.calibration import ALL_CALIBRATION_STYLES

def content():
    # 1. Inject Dependencies (Scripts/Styles)
    for style in ALL_CALIBRATION_STYLES: ui.add_head_html(style)
    for script in ALL_CALIBRATION_SCRIPTS: ui.add_body_html(script)

    # 2. Setup Context and Container
    # The container fills the space provided by main_layout
    wizard_container = ui.element('div').classes('w-full h-full p-0 m-0')
    
    context = CalibrationContext()
    
    # 3. Define Steps
    steps = [
        Step1Capture(context),
        Step2ROI(context),
        Step3Profile(context)
    ]
    
    # 4. Start Orchestrator
    orchestrator = CalibrationWizardOrchestrator(wizard_container, context, steps)
    orchestrator.start()

def create_page():
    # show_header=True invokes the layout with Navbar + Controller logic
    main_layout(content, show_header=True)
