# src/ui/layout.py
from nicegui import ui
from typing import Callable
from core.locale_manager import T
from ui.styles.layout import GLOBAL_LAYOUT_STYLE
from ui.layout_controller import layout_controller

def theme_setup() -> None:
    """Configures global theme colors and styles."""
    ui.dark_mode().enable()
    ui.colors(
        primary='#5898d4',    
        secondary='#262626', 
        accent='#f59e0b', 
        positive='#21ba45',
        negative='#c10015',
        info='#31ccec',
        warning='#f2c037'
    )
    ui.add_head_html(GLOBAL_LAYOUT_STYLE)

def main_layout(page_content_func: Callable[[], None], show_header: bool = True) -> None:
    """
    Global Layout Wrapper.
    """
    theme_setup()
    
    # --- ROOT CONTAINER ---
    with ui.element('div').classes('fixed inset-0 bg-[#0a0a0a] overflow-hidden'):

        # --- HEADER SECTION ---
        if show_header:
            with ui.row().classes(
                'fixed top-0 left-0 right-0 h-16 z-50 '
                'items-center justify-between px-6 '
                'bg-slate-900/90 backdrop-blur-md '
                'border-b border-white/10 shadow-sm'
            ):
                
                # --- LEFT CLUSTER ---
                with ui.row().classes('items-center gap-4'):
                    ui.button(on_click=lambda: ui.navigate.to('/')) \
                        .props('icon=home flat round dense') \
                        .classes('text-gray-400 hover:text-sky-400 transition-colors') \
                        .tooltip(T('back_to_menu'))
                    
                    ui.separator().props('vertical').classes('h-6 bg-white/10')
                    
                    title_label = ui.label(T('app_title')).classes(
                        'text-lg font-bold tracking-wider text-slate-100'
                    )

                # --- RIGHT CLUSTER ---
                tools_row = ui.row().classes('items-center gap-2')

                # Register UI
                layout_controller.register_ui(title_label, tools_row)

        # --- BODY SECTION ---
        top_anchor = 'top-16' if show_header else 'top-0'
        
        with ui.element('div').classes(f'absolute inset-x-0 bottom-0 {top_anchor} overflow-hidden'):
            try:
                page_content_func()
            except Exception as e:
                ui.label(f"Error rendering page content: {str(e)}").classes('text-red-500 font-bold m-4')
                print(f"Page Render Error: {e}")
