# src/main.py
from nicegui import ui, app # <-- Import 'app' explicitly
from ui.pages import home, dashboard, calibration
from core.locale_manager import T
from core.log_manager import logger
import os

# --- STATIC FILE SETUP ---
# We define the local directory path based on the structure provided: 
# Video is in src/assets/, and main.py is in src/.
# Therefore, the local directory we want to serve is 'src/assets'.
local_assets_path = 'assets' 
URL_PREFIX = '/assets'

# Check if directory exists before mounting (ROBUSTNESS)
if os.path.isdir(local_assets_path):
    app.add_static_files(URL_PREFIX, local_assets_path)
    logger.info(f"Static files mounted: URL Prefix '{URL_PREFIX}' mapped to local path '{local_assets_path}'")
else:
    logger.error(f"STATIC FILE MOUNT FAILED: Asset directory not found at '{local_assets_path}'. Video will not load.")
# -------------------------


@ui.page('/')
def page_home():
    logger.debug("Navigated to Home page")
    home.create_page()

@ui.page('/dashboard')
def page_dashboard():
    logger.debug("Navigated to Scan page")
    dashboard.create_page()

@ui.page('/calibration')
def page_calibration():
    logger.debug("Navigated to Calibration page")
    calibration.create_page()

@ui.page('/settings')
def page_settings():
    logger.debug("Navigated to Settings page")
    #Placeholder
    from ui.layout import main_layout
    def content():
        ui.label(T('settings_title')).classes('text-2xl')
        ui.button(T('back_to_menu'), on_click=lambda: ui.navigate.to('/')).props('icon=home')
    main_layout(content)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title=T('app_title'),        
        dark=True,
        reload=False,
        favicon= "🎞️"    
        # Removed static_files from here as it's now handled via app.add_static_files()
    )
