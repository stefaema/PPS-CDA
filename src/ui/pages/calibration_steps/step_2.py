# src/ui/pages/calibration_steps/step2.py
from nicegui import ui, events
from core.calibration_state import global_calibration_state
from utils.image_processing import cv2_to_base64

def render(container, on_back, update_header):
    """Renderiza la UI del Paso 2."""
    container.clear()
    update_header("ASISTENTE DE CALIBRACIÓN - PASO 2: DEFINIR REGIONES DE INTERÉS")
    
    # Asegurar cámara liberada
    global_calibration_state.release_camera()

    # Obtener imagen del singleton
    img = global_calibration_state.captured_image
    if img is None:
        ui.notify("Error: No hay imagen capturada.", type='negative')
        on_back() # Volver si no hay datos
        return

    img_src = cv2_to_base64(img)
    roi_manager = global_calibration_state.roi_manager
    interactive_view = None

    # Estado local de la máquina de estados del mouse
    editor_state = {
        'drawing': False,
        'start_x': 0, 'start_y': 0
    }

    def update_static_svg():
        """Genera SVG estático (ROIs confirmados + Fantasma invisible)."""
        # Rectángulo fantasma (controlado por JS)
        svg_content = '<rect id="ghost_rect" width="0" height="0" fill="rgba(255, 255, 255, 0.2)" stroke="white" stroke-width="2" vector-effect="non-scaling-stroke" stroke-dasharray="10,5" visibility="hidden" pointer-events="none" />'
        
        # ROIs confirmados (controlados por Python/Singleton)
        for roi in roi_manager.get_all():
            svg_content += f'<rect x="{roi.x}" y="{roi.y}" width="{roi.width}" height="{roi.height}" fill="rgba(33, 186, 69, 0.2)" stroke="#21ba45" stroke-width="2" />'

            # Botón Borrar
            btn_s = 30
            bx, by = roi.x + roi.width - btn_s, roi.y
            svg_content += f'''
                <rect x="{bx}" y="{by}" width="{btn_s}" height="{btn_s}" fill="rgba(33, 186, 69, 0.5)" stroke="white" stroke-width="1" />
                <line x1="{bx+10}" y1="{by+10}" x2="{bx+btn_s-10}" y2="{by+btn_s-10}" stroke="white" stroke-width="2" pointer-events="none" />
                <line x1="{bx+btn_s-10}" y1="{by+10}" x2="{bx+10}" y2="{by+btn_s-10}" stroke="white" stroke-width="2" pointer-events="none" />
            '''
        if interactive_view:
            interactive_view.content = svg_content

    def on_mouse(e: events.MouseEventArguments):
        if e.image_x is None or e.image_y is None: return
        
        # Solo escuchamos mousedown (Clicks)
        if e.type == 'mousedown':
            mx, my = int(e.image_x), int(e.image_y)

            if editor_state['drawing']:
                # Click 2: Terminar
                roi_manager.add_from_clicks(editor_state['start_x'], editor_state['start_y'], mx, my)
                editor_state['drawing'] = False
                ui.run_javascript('window.stopGhostDrawing()')
                ui.notify('Perforación agregada', type='positive', timeout=500)
                update_static_svg()
                
            else:
                # Click 1: Empezar o Borrar
                deleted_id = roi_manager.remove_at_point(mx, my)
                if deleted_id:
                    ui.notify('ROI Eliminado', type='warning', timeout=500)
                    update_static_svg()
                else:
                    editor_state['drawing'] = True
                    editor_state['start_x'] = mx
                    editor_state['start_y'] = my
                    ui.run_javascript(f'window.startGhostDrawing({mx}, {my})')

    def on_key(e: events.KeyEventArguments):
        if e.key == 'Escape' and e.action.keydown and editor_state['drawing']:
            editor_state['drawing'] = False
            ui.run_javascript('window.stopGhostDrawing()')
            ui.notify('Selección Cancelada', type='info', timeout=300)

    def on_finish_click():
        if roi_manager.count >= 1:
            ui.notify(f'Completado: {roi_manager.count} perforaciones.', type='positive')
            print("ROIs Finales:", [r.to_dict() for r in roi_manager.get_all()])
        else:
            ui.notify('Define al menos 1 perforación.', type='warning')

    # --- RENDERIZADO UI ---
    with container:
        ui.keyboard(on_key=on_key)

        # Contenedor con SCROLL para evitar desfasaje de coordenadas
        with ui.column().classes('w-full h-full overflow-auto p-0 relative bg-black block'):
            interactive_view = ui.interactive_image(
                img_src, 
                on_mouse=on_mouse, 
                events=['mousedown'], 
                cross=True
            ).classes('w-auto h-auto block').style('max-width: 100%; max-height: 100%;')
            
            update_static_svg()

        # Panel Flotante
        with ui.row().classes('absolute bottom-10 left-1/2 -translate-x-1/2 z-20'):
            control_panel = ui.card().classes('flex-row items-center gap-6 px-8 py-4 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700 shadow-2xl')
            with control_panel:
                ui.button('REINTENTAR', on_click=on_back).props('icon=undo color=grey flat')
                ui.separator().props('vertical').classes('bg-slate-600 h-10')
                ui.label('Click para empezar/terminar. Click en ROI para borrar.').classes('text-gray-400 text-sm italic')
                ui.separator().props('vertical').classes('bg-slate-600 h-10')
                ui.button('FINALIZAR', on_click=on_finish_click).props('icon=check color=positive unelevated rounded').classes('font-bold')
