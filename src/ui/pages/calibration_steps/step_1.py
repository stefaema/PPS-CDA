# src/ui/pages/calibration_steps/step1.py
from nicegui import ui
from core.calibration_state import global_calibration_state
from utils.image_processing import cv2_to_base64
import cv2

# Configuración local del paso
FPS_PREVIEW = 15  
REFRESH_INTERVAL = 1.0 / FPS_PREVIEW

STATIC_DEVICE_OPTIONS = {
    0: 'Dispositivo de Video 1',
    1: 'Dispositivo de Video 2',
    2: 'Dispositivo de Video 3',
}

def start_camera(index):
    """Inicia cámara en 4K y actualiza el estado global."""
    global_calibration_state.release_camera()
    if index is None: return False

    cap = cv2.VideoCapture(index)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
    
    if cap.isOpened():
        ret, _ = cap.read()
        if ret:
            global_calibration_state.cap_obj = cap
            global_calibration_state.camera_index = index
            global_calibration_state.is_streaming = True
            return True
    return False

def render(container, on_next, update_header):
    """Renderiza la UI del Paso 1 en el contenedor dado."""
    container.clear()
    update_header("ASISTENTE DE CALIBRACIÓN - PASO 1: CAPTURA")
    
    # Limpiamos ROIs viejos si volvemos a este paso
    global_calibration_state.roi_manager.clear()

    # Referencias UI Locales
    ui_refs = {
        'preview_image': None,
        'capture_btn': None,
        'timer': None
    }

    def update_preview_loop():
        if not global_calibration_state.is_streaming: return
        
        cap = global_calibration_state.cap_obj
        if cap and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                global_calibration_state.current_frame = frame
                # Preview
                src = cv2_to_base64(frame)
                if src and ui_refs['preview_image']:
                    ui_refs['preview_image'].set_source(src)

    def on_camera_selected(e):
        idx = e.value
        if idx is None: return
        
        if start_camera(idx):
            ui.notify('Cámara conectada (4K).', type='positive', timeout=1000)
            ui_refs['capture_btn'].enable()
            ui_refs['capture_btn'].classes(remove='opacity-50 cursor-not-allowed', add='hover:scale-105')
            
            if not ui_refs['timer']:
                ui_refs['timer'] = ui.timer(REFRESH_INTERVAL, update_preview_loop)
            else:
                ui_refs['timer'].activate()
        else:
            ui.notify('Error al conectar cámara.', type='negative')

    def on_capture_click():
        if global_calibration_state.current_frame is not None:
            # GUARDAR EN SINGLETON
            global_calibration_state.captured_image = global_calibration_state.current_frame.copy()
            
            # Detener recursos
            if ui_refs['timer']: ui_refs['timer'].deactivate()
            global_calibration_state.release_camera()
            
            ui.notify('Imagen capturada.', type='positive', timeout=500)
            
            # NAVEGAR
            on_next()

    # --- RENDERIZADO UI ---
    with container:
        # Fondo
        ui_refs['preview_image'] = ui.image('assets/color_bars.png').classes('w-full h-full object-contain')

        # Controles
        with ui.row().classes('absolute bottom-10 left-1/2 -translate-x-1/2 z-20'):
            control_panel = ui.card().classes('flex-row items-center gap-6 px-8 py-4 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700 shadow-2xl')
            
            with control_panel:
                ui.select(options=STATIC_DEVICE_OPTIONS, label='Fuente', on_change=on_camera_selected) \
                    .classes('w-52').props('outlined dense dark behavior="menu"')
                
                ui.separator().props('vertical').classes('bg-slate-600 h-10')
                
                ui_refs['capture_btn'] = ui.button('CAPTURAR', on_click=on_capture_click) \
                    .props('icon=camera_alt color=accent unelevated rounded') \
                    .classes('px-6 py-2 font-bold opacity-50 cursor-not-allowed transition-all')
                ui_refs['capture_btn'].disable()
