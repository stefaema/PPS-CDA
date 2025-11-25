# src/ui/pages/calibration_steps/step_3_profile.py
import numpy as np
from nicegui import ui
from core.locale_manager import T
from utils.image_processing import cv2_to_base64
from ui.pages.calibration_steps.step_base import CalibrationStep

PLOT_WIDTH = 150

class Step3Profile(CalibrationStep):
    
    @property
    def title(self) -> str:
        return f"{T('calibration_wizard')} - {T('step_3_generate_profile')}"

    @staticmethod
    def _generate_signal_polyline(signal: np.ndarray, height: int, x_offset: int, max_width: int, mirror: bool = False) -> str:
        """Utility for drawing signal graphs."""
        if signal is None or len(signal) == 0: return ""
        s_min, s_max = np.min(signal), np.max(signal)
        
        # Avoid division by zero
        if s_max - s_min == 0:
            norm_signal = np.zeros_like(signal)
        else:
            norm_signal = (signal - s_min) / (s_max - s_min)
        
        points = []
        step = 2
        # Use existing signal length or image height, whichever is smaller to prevent index errors
        limit = min(len(norm_signal), height)
        
        for y in range(0, limit, step):
            val = norm_signal[y]
            w = val * max_width
            x = (x_offset - w) if mirror else (x_offset + w)
            points.append(f"{x:.1f},{y}")
        return " ".join(points)

    def render(self, container, on_next, on_back):
        profile = self.context.calibration_profile
        image = self.context.captured_frame

        if not profile or image is None:
            ui.notify(T("error_no_calibration_data"), type='negative')
            on_back()
            return

        # --- Data Prep ---
        img_h, img_w = image.shape[:2]
        img_src = cv2_to_base64(image, use_grayscale=True)
        
        l_lane = profile.left_lane
        r_lane = profile.right_lane
        
        # --- SVG Overlay Generation ---
        svg_elements = []

        # Styles matching original code
        l_strip_style = 'fill="rgba(0, 255, 255, 0.2)"' 
        r_strip_style = 'fill="rgba(255, 235, 59, 0.2)"'
        
        l_center_style = 'stroke="cyan" stroke-width="1.5"'
        r_center_style = 'stroke="yellow" stroke-width="1.5"'
        l_bound_style = 'stroke="cyan" stroke-width="1" stroke-dasharray="4,2" opacity="0.7"'
        r_bound_style = 'stroke="yellow" stroke-width="1" stroke-dasharray="4,2" opacity="0.7"'

        # 1. Vertical Strips (Lanes)
        if l_lane:
            svg_elements.append(f'<rect x="{l_lane.x}" y="0" width="{l_lane.width}" height="{img_h}" {l_strip_style} />')
        if r_lane:
            svg_elements.append(f'<rect x="{r_lane.x}" y="0" width="{r_lane.width}" height="{img_h}" {r_strip_style} />')

        # 2. Anchor Lines (Restored)
        if l_lane and profile.left_anchors:
            target_x = l_lane.x + l_lane.width
            for anchor in profile.left_anchors:
                y_start = anchor.y
                y_mid = anchor.y + (anchor.height / 2)
                y_end = anchor.y + anchor.height
                
                # Top Bound
                svg_elements.append(f'<line x1="0" y1="{y_start}" x2="{target_x}" y2="{y_start}" {l_bound_style} vector-effect="non-scaling-stroke" />')
                # Center Line
                svg_elements.append(f'<line x1="0" y1="{y_mid}" x2="{target_x}" y2="{y_mid}" {l_center_style} vector-effect="non-scaling-stroke" />')
                # Bottom Bound
                svg_elements.append(f'<line x1="0" y1="{y_end}" x2="{target_x}" y2="{y_end}" {l_bound_style} vector-effect="non-scaling-stroke" />')

        if r_lane and profile.right_anchors:
            target_x = r_lane.x
            for anchor in profile.right_anchors:
                y_start = anchor.y
                y_mid = anchor.y + (anchor.height / 2)
                y_end = anchor.y + anchor.height
                
                # Top Bound
                svg_elements.append(f'<line x1="{img_w}" y1="{y_start}" x2="{target_x}" y2="{y_start}" {r_bound_style} vector-effect="non-scaling-stroke" />')
                # Center Line
                svg_elements.append(f'<line x1="{img_w}" y1="{y_mid}" x2="{target_x}" y2="{y_mid}" {r_center_style} vector-effect="non-scaling-stroke" />')
                # Bottom Bound
                svg_elements.append(f'<line x1="{img_w}" y1="{y_end}" x2="{target_x}" y2="{y_end}" {r_bound_style} vector-effect="non-scaling-stroke" />')

        # 3. Signal Plots
        if l_lane:
            pts = self._generate_signal_polyline(profile.left_lane_signal, img_h, x_offset=0, max_width=PLOT_WIDTH, mirror=False)
            svg_elements.append(f'<polyline points="{pts}" fill="none" stroke="rgba(0, 255, 255, 0.5)" stroke-width="1" vector-effect="non-scaling-stroke"/>')

        if r_lane:
            pts = self._generate_signal_polyline(profile.right_lane_signal, img_h, x_offset=img_w, max_width=PLOT_WIDTH, mirror=True)
            svg_elements.append(f'<polyline points="{pts}" fill="none" stroke="rgba(255, 235, 59, 0.5)" stroke-width="1" vector-effect="non-scaling-stroke"/>')

        svg_content = "".join(svg_elements)

        # --- UI Rendering ---
        with container:
                    with ui.element('div').classes('w-full h-full bg-black overflow-y-auto relative'):
                        
                        with ui.element('div').classes('relative w-full'):
                            
                            ui.image(img_src).classes('w-full h-auto block').props('no-spinner')
                            
                            ui.html(f'''
                                <svg viewBox="0 0 {img_w} {img_h}" preserveAspectRatio="none" style="position: absolute; top: 0; left: 0; width:100%; height:100%; pointer-events: none;">
                                    {svg_content}
                                </svg>
                            ''', sanitize= False)

                    with ui.card().classes('absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 bg-slate-900/95 p-6 border border-slate-600 shadow-2xl z-50'):
                        
                        ui.label(T('profile_summary')).classes('text-xl font-bold text-primary mb-2')
                        ui.separator().classes('bg-slate-600 mb-4')

                        ui.input(label=T('profile_name'), placeholder=T("profile_name_placeholder")) \
                            .bind_value(profile, 'name') \
                            .props('outlined dense dark autofocus').classes('w-full mb-2')
                        
                        ui.textarea(label=T('profile_description'), placeholder=T('profile_description_placeholder')) \
                            .bind_value(profile, 'description') \
                            .props('outlined dense dark rows=2').classes('w-full mb-4')

                        with ui.grid(columns=2).classes('w-full gap-2 text-sm text-gray-300 mb-4'):
                            ui.label(T('profile_id') + ':')
                            ui.label(str(profile.id)[:8] + '...').classes('font-mono text-xs')
                            
                            ui.label(T('lanes_detected') + ':')
                            lane_text = []
                            if l_lane: lane_text.append('LEFT')
                            if r_lane: lane_text.append('RIGHT')
                            ui.label(', '.join(lane_text) if lane_text else 'NONE').classes('font-bold text-accent')

                            ui.label(T('total_anchors') + ':')
                            count = len(profile.left_anchors or []) + len(profile.right_anchors or [])
                            ui.label(str(count)).classes('font-bold')

                        ui.separator().classes('bg-slate-600 mb-4')
                        
                        with ui.row().classes('w-full justify-between'):
                            ui.button(T("back_to_rois"), on_click=on_back).props('icon=arrow_back color=grey flat')
                            
                            def on_finish_click():
                                if not profile.name:
                                    ui.notify(T("error_profile_name_required"), type='warning')
                                    return
                                ui.notify(T("calibration_complete"), type='positive')
                                on_next(profile)

                            ui.button(T("finish_calibration"), on_click=on_finish_click) \
                                .props('icon=save color=positive unelevated') \
                                .classes('font-bold')
