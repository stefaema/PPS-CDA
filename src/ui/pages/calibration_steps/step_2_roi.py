# src/ui/pages/calibration_steps/step_2_roi.py
from nicegui import ui, events
from core.locale_manager import T
from core.log_manager import logger
from core.roi import CalibrationManager
from utils.image_processing import cv2_to_base64
from utils.draw_utils import generate_rect_svg, get_color
from ui.pages.calibration_steps.step_base import CalibrationStep
from ui.layout_controller import ToolButton

class Step2ROI(CalibrationStep):
    
    @property
    def title(self) -> str:
        return f"{T('calibration_wizard')} - {T('step_2_define_rois')}"

    def __init__(self, context):
        super().__init__(context)
        self.interactive_view = None
        self.drawing_state = {'active': False, 'start_x': 0, 'start_y': 0}

    def on_enter(self):
        # Initialize Manager if needed
        if self.context.captured_frame is None:
            logger.error("Step 2 entered without captured frame")
            return

        if self.context.calibration_manager is None:
            logger.info("Initializing new CalibrationManager")
            self.context.calibration_manager = CalibrationManager(self.context.captured_frame)
        else:
            # If we already have one (navigated back), ensure it uses the current frame
            self.context.calibration_manager.raw_captured_image = self.context.captured_frame

    def get_tools(self):
        """Custom tools for the Navbar."""
        return [
            {
                'icon': 'delete_forever', 
                'callback': self._clear_all_rois, 
                'tooltip': T('clear_all_rois'),
                'color': 'negative'
            }
        ]

    def _clear_all_rois(self):
        if self.context.calibration_manager:
            self.context.calibration_manager.clear_all_rois()
            self._update_svg()
            ui.notify(T("all_rois_cleared"), type='warning', timeout=500)

    def _update_svg(self):
        """Refreshes the SVG overlay."""
        if not self.interactive_view or not self.context.calibration_manager: 
            return

        # Ghost Rect (Hidden by default)
        svg_content = f'<rect id="ghost_rect" width="0" height="0" fill="{get_color("#d6cb00",0.2)}" stroke="{get_color("#d6cb00",1.0)}" stroke-width="2" vector-effect="non-scaling-stroke" stroke-dasharray="10,5" visibility="hidden" pointer-events="none" />'
        
        # Existing ROIs
        rois = self.context.calibration_manager.get_all_raw_rois()
        for roi in rois:
            # Main Box
            svg_content += generate_rect_svg(roi.x, roi.y, roi.width, roi.height, fill=get_color("#21ba45", 0.2), stroke="#21ba45")
            
            # Delete Icon (Simplified geometry)
            bx, by = roi.x + roi.width - 25, roi.y
            svg_content += f'<rect x="{bx}" y="{by}" width="25" height="25" fill="red" opacity="0.0" />' # Hitbox
            svg_content += f'<text x="{bx+5}" y="{by+18}" fill="white" font-size="20" font-weight="bold" pointer-events="none">×</text>'

        self.interactive_view.content = svg_content

    def render(self, container, on_next, on_back):
        if self.context.captured_frame is None:
            ui.notify(T("error_no_captured_image"), type='negative')
            on_back()
            return

        img_src = cv2_to_base64(self.context.captured_frame, use_grayscale=True)

        def on_mouse(e: events.MouseEventArguments):
            if e.image_x is None or e.image_y is None: return
            
            # MOUSE DOWN
            if e.type == 'mousedown':
                mx, my = int(e.image_x), int(e.image_y)
                
                if self.drawing_state['active']:
                    # Finish Drawing
                    self.context.calibration_manager.add_raw_roi(self.drawing_state['start_x'], self.drawing_state['start_y'], mx, my)
                    self.drawing_state['active'] = False
                    ui.run_javascript('window.stopGhostDrawing()')
                    ui.notify(T("roi_added"), type='positive', timeout=500)
                    self._update_svg()
                else:
                    # Check for Deletion or Start Drawing
                    deleted_id = self.context.calibration_manager.remove_raw_roi_from_point(mx, my)
                    if deleted_id:
                        ui.notify(T("roi_deleted"), type='warning', timeout=500)
                        self._update_svg()
                    else:
                        # Start Drawing
                        self.drawing_state['active'] = True
                        self.drawing_state['start_x'] = mx
                        self.drawing_state['start_y'] = my
                        ui.run_javascript(f'window.startGhostDrawing({mx}, {my})')

        def on_finish_click():
            rois = self.context.calibration_manager.get_all_raw_rois()
            if len(rois) < 1:
                ui.notify(T("error_no_rois_defined"), type='warning')
                return
            
            # Generate Profile for Next Step
            try:
                frame = self.context.captured_frame
                self.context.calibration_profile = self.context.calibration_manager.generate_calibration_profile(frame)
                on_next()
            except Exception as e:
                logger.error(f"Profile Generation Failed: {e}")
                ui.notify("Failed to generate profile. Check logs.", type='negative')

        # --- UI Build ---
        with container:
            # Key Handler
            def handle_key(e: events.KeyEventArguments):
                if e.key == 'Escape' and self.drawing_state['active']:
                    self.drawing_state['active'] = False
                    ui.run_javascript('window.stopGhostDrawing()')
                    ui.notify(T("selection_cancelled"))

            ui.keyboard(on_key=handle_key)

            # Interactive Area
            with ui.column().classes('w-full h-full overflow-auto bg-black relative'):
                self.interactive_view = ui.interactive_image(
                    img_src, 
                    on_mouse=on_mouse, 
                    events=['mousedown'], 
                    cross=True
                ).classes('w-full h-auto')
                
                self._update_svg()

            # Overlay Task Tools
            with ui.row().classes('absolute bottom-10 left-1/2 -translate-x-1/2 z-20'):
                with ui.card().classes('flex-row items-center gap-6 px-8 py-4 rounded-full bg-slate-900/90 border border-slate-700 shadow-2xl'):

                    ui.button(
                        T("clear_all_rois"), 
                        on_click=self._clear_all_rois
                    ).props('icon=delete_forever color=negative unelevated rounded') \
                    .classes('px-6 py-2 font-bold text-lg font-bold')
                    
                    # Spacer
                    ui.separator().props('vertical').classes('h-6 bg-white/10')

                    # Finish Step Button
                    ui.button(T("finish_step"), on_click=on_finish_click) \
                        .props('icon=check color=positive unelevated rounded') \
                        .classes('px-6 py-2 font-bold text-lg font-bold')
                
                
