# src/ui/pages/dashboard.py
from nicegui import ui
from ui.layout import main_layout

def content():
    """Contenido específico del Dashboard."""
    
    # Grid principal: 2 columnas (Video 70% | Controles 30%)
    with ui.grid(columns='3fr 1fr').classes('w-full h-[calc(100vh-80px)] gap-4'): # Ajuste de altura
        
        # --- COLUMNA IZQUIERDA: VIDEO ---
        with ui.card().classes('w-full h-full bg-black items-center justify-center p-0 border border-gray-700'):
            # El componente interactivo donde se pinta el video y los sensores SVG
            video = ui.interactive_image('https://placehold.co/800x600/black/white?text=Waiting+for+Film+Preview') \
                .classes('w-full h-full object-contain')
            
            with ui.row().classes('absolute top-2 left-2 bg-black/50 p-1 rounded'):
                ui.label('Film: 16mm').classes('text-xs text-gray-300')
                ui.label('FPS: 24').classes('text-xs text-gray-300 ml-4')

        # --- COLUMNA DERECHA: CONTROLES Y DATOS ---
        with ui.column().classes('h-full justify-between'):
            
            # 1. Panel Superior: Acciones Principales
            with ui.card().classes('w-full bg-slate-800 border-l-4 border-primary'):
                ui.label('CONTROL DE EJECUCIÓN').classes('text-sm font-bold text-gray-400 mb-2')
                
                ui.button('INICIAR ESCANEO', on_click=lambda: ui.notify('Iniciando...')) \
                    .props('icon=play_arrow size=lg color=positive') \
                    .classes('w-full h-16 text-xl font-bold shadow-md mb-2')
                
                with ui.row().classes('w-full gap-2'):
                    ui.button('PAUSA').props('icon=pause color=warning').classes('flex-grow')
                    ui.button('STOP').props('icon=stop color=negative').classes('flex-grow')

            # 2. Panel Medio: Métricas / Sensores
            with ui.card().classes('w-full bg-slate-800'):
                ui.label('ESTADO DE CENTRADO').classes('text-sm font-bold text-gray-400 mb-2')
                
                with ui.column().classes('w-full items-center'):
                    ui.label('Error de posición (px):').classes('text-xs text-gray-400')
                    # Barra de error de centrado (ej: -5 a +5 píxeles)
                    ui.linear_progress(value=0.5, show_value=False).props('color=purple').classes('w-full h-2')
                    ui.label('Centrado OK').classes('text-xl font-bold text-green-400')

            # 3. Panel Inferior: Logs y Navegación
            with ui.column().classes('w-full gap-2'):
                log_area = ui.log().classes('w-full h-32 bg-black text-green-400 font-mono text-xs p-2 rounded border border-gray-700')
                log_area.push(f"[{ui.date()}] System Ready.")
                log_area.push("Waiting for user command...")
                
                ui.separator().classes('bg-gray-600 my-2')
                
                # Botón para ir al modo calibración
                ui.button('AJUSTE DE CALIBRACIÓN', on_click=lambda: ui.navigate.to('/calibration')) \
                    .props('icon=tune outline') \
                    .classes('w-full text-gray-400 hover:text-white')

# Esta función es la que llamará el main.py para renderizar la página
def create_page():
    main_layout(content, show_header=True, title="DIGITALIZACIÓN")
