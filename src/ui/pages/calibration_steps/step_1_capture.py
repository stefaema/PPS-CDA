# src/ui/pages/calibration_steps/step_1_capture.py
import cv2
from nicegui import ui
from core.locale_manager import T
from core.hardware_manager import global_hardware_manager
from core.log_manager import logger
from utils.image_processing import cv2_to_base64
from utils.list_cameras import get_aval_video_sources, FALLBACK_SOURCES
from ui.pages.calibration_steps.step_base import CalibrationStep

class Step1Capture(CalibrationStep):
    
    @property
    def title(self) -> str:
        return f"{T('calibration_wizard')} - {T('step_1_capture')}"

    def __init__(self, context):
        super().__init__(context)
        self.preview_image = None
        self.timer = None
        self.capture_btn = None

    def on_enter(self):
        """Start hardware resources if possible."""
        pass # We wait for user selection

    def on_leave(self):
        """Ensure camera is off when leaving step."""
        if self.timer:
            self.timer.deactivate()
        global_hardware_manager.stop_video_stream()

    def render(self, container, on_next, on_back):
        
        # Helper: Preview Loop
        def update_preview():
            if not global_hardware_manager.is_streaming: return
            frame = global_hardware_manager.get_latest_frame()
            if frame is not None and self.preview_image:
                self.preview_image.set_source(cv2_to_base64(frame))

        # Helper: Selection
        def on_camera_selected(e):
            idx = e.value
            if idx is None: return
            if global_hardware_manager.start_video_stream(idx):
                ui.notify(T("camera_connected"), type='positive')
                if self.capture_btn:
                    self.capture_btn.enable()
                    self.capture_btn.classes(remove='opacity-50 cursor-not-allowed', add='hover:scale-105')
                
                # Start Timer
                refresh_rate = 1.0 / global_hardware_manager.get_target_fps()
                if not self.timer:
                    self.timer = ui.timer(refresh_rate, update_preview)
                else:
                    self.timer.activate()
            else:
                ui.notify(T("camera_conn_error"), type='negative')

        # Helper: Capture
        def on_capture():
            frame = global_hardware_manager.get_latest_frame()
            if frame is not None:
                # SAVE TO CONTEXT
                self.context.set_captured_frame(frame)
                ui.notify(T("image_captured"), type='positive')
                on_next()
            else:
                ui.notify(T("error_no_captured_image"), type='warning')

        # --- UI Build ---
        sources = get_aval_video_sources()
        options = {s.index: s.name for s in sources} if sources else FALLBACK_SOURCES

        with container:
            # Fullscreen Preview
            self.preview_image = ui.image('assets/color_bars.png').classes('w-full h-full object-contain')

            # Floating Controls
            with ui.row().classes('absolute bottom-10 left-1/2 -translate-x-1/2 z-20'):
                with ui.card().classes('flex-row items-center gap-6 px-8 py-4 rounded-full bg-slate-900/90 border border-slate-700 shadow-2xl'):
                    
                    ui.select(options=options, label=T("video_source"), on_change=on_camera_selected) \
                        .classes('w-52').props('outlined dense dark behavior="menu"')
                    
                    ui.separator().props('vertical').classes('bg-slate-600 h-10')
                    
                    self.capture_btn = ui.button(T("capture"), on_click=on_capture) \
                        .props('icon=camera_alt color=accent unelevated rounded') \
                        .classes('px-6 py-2 font-bold opacity-50 cursor-not-allowed transition-all')
                    self.capture_btn.disable()
