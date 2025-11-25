# src/ui/pages/home.py
from nicegui import ui
from ui.layout import main_layout
from core.locale_manager import T

def menu_button(title_key: str, icon: str, target: str, subtext_key: str = ""):
    """
    Creates a Dark Glass button that glows on hover.
    """
    with ui.button(on_click=lambda: ui.navigate.to(target)) \
            .classes('group w-full h-auto py-5 px-6 rounded-xl '
                     'bg-transparent hover:bg-white/5 ' 
                     'border border-white/10 hover:border-sky-500/50 '
                     'transition-all duration-300 ease-out '
                     'no-underline relative overflow-hidden'): 
        
        # Hover Sheen
        ui.element('div').classes(
            'absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent '
            '-translate-x-full group-hover:translate-x-full transition-transform duration-1000 pointer-events-none'
        )

        with ui.row().classes('w-full items-center gap-6'):
            # Icon
            with ui.element('div').classes(
                'flex items-center justify-center w-12 h-12 rounded-full '
                'bg-slate-800/50 border border-white/5 '
                'group-hover:border-sky-500/30 group-hover:bg-sky-500/10 '
                'group-hover:scale-110 transition-all duration-300'
            ):
                ui.icon(icon, size='sm').classes('text-gray-400 group-hover:text-sky-400 transition-colors')

            # Text
            with ui.column().classes('gap-1 items-start flex-grow'):
                ui.label(T(title_key)).classes(
                    'text-lg font-bold text-gray-300 group-hover:text-white tracking-wide transition-colors text-left leading-tight'
                )
                if subtext_key:
                    ui.label(T(subtext_key)).classes(
                        'text-[10px] uppercase tracking-widest text-gray-600 group-hover:text-sky-400/70 font-mono transition-colors'
                    )

            # Arrow
            ui.icon('chevron_right').classes(
                'text-gray-700 group-hover:text-sky-400 '
                'opacity-50 group-hover:opacity-100 group-hover:translate-x-1 '
                'transition-all duration-300'
            )

def content():
    """Contents of the Launchpad"""

    # 1. GLOBAL CONTAINER: Uses flex to manage the video and content layers
    with ui.column().classes('w-full h-full items-center justify-center bg-black relative overflow-hidden p-0 m-0'):

        # 2. BACKGROUND VIDEO (Layer 0)
        video = ui.video(
            src='/assets/animated_background_light.mp4', # This path now works due to main.py config
            autoplay=True,
            loop=True,
            muted=True,
            controls=False
        ).classes(
            'absolute inset-0 w-full h-full object-cover z-0'
        ).style(
            # CSS Filter for "Negative" effect: Invert colors, adjust hue/brightness/contrast
            'filter: invert(1) hue-rotate(230deg);'
        )

        # 3. MAIN CARD (Layer 10)
        with ui.card().classes(
            'w-[500px] max-w-[90vw] p-12 rounded-3xl '
            'bg-slate-900/60 backdrop-blur-2xl '
            'border border-white/10 '
            'shadow-[0_0_50px_rgba(0,0,0,0.5)] '
            'flex flex-col items-center gap-10 z-10'
        ):
            
            # --- Header ---
            with ui.column().classes('w-full items-center justify-center gap-6'):
                ui.image('assets/icon.png').classes('w-24 h-24 opacity-90 drop-shadow-2xl')
                
                with ui.column().classes('items-center gap-2 text-center'):
                    ui.label(T('app_title')).classes(
                        'text-3xl font-black text-white tracking-widest uppercase leading-tight'
                    )
                    ui.label(T('home_subtitle')).classes(
                        'text-xs text-sky-600/80 font-mono tracking-[0.4em] font-bold'
                    )

            # --- Menu ---
            with ui.column().classes('w-full gap-4'):
                menu_button('home_calibration_title', 'build', '/calibration', 'home_calibration_subtitle')
                menu_button('home_scan_title', 'movie_filter', '/dashboard', 'home_scan_subtitle')
                menu_button('home_settings_title', 'tune', '/settings', 'home_settings_subtitle')

        # Footer (Layer 10, same as card)
        FOOTER_TEXT_SIZE = '16px'   
        with ui.row().classes('absolute bottom-8 items-center gap-2 opacity-30 z-10'):
            ui.label('v1.0.0').classes(f'text-[{FOOTER_TEXT_SIZE}] font-mono text-white')
            ui.label('•').classes(f'text-[{FOOTER_TEXT_SIZE}] text-sky-500')
            ui.label(T("app_author")).classes(f'text-[{FOOTER_TEXT_SIZE}] font-mono text-white tracking-widest')
            ui.label('•').classes(f'text-[{FOOTER_TEXT_SIZE}] text-sky-500')
            ui.label('2025').classes(f'text-[{FOOTER_TEXT_SIZE}] font-mono text-white')

def create_page():
    main_layout(content, show_header=False)
