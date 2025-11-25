# src/core/calibration_state.py
from core.roi import ROIManager
import cv2

class CalibrationState:
    def __init__(self):
        # Hardware
        self.cap_obj = None
        self.camera_index = None
        self.is_streaming = False
        
        # Image Data
        self.current_frame = None   # Live Frame (4 streaming)
        self.captured_image = None  # Captured Frame
        
        # Logic
        self.roi_manager = ROIManager()

    def release_camera(self):
        """Gracefully releases camera from OpenCV."""
        if self.cap_obj and self.cap_obj.isOpened():
            self.cap_obj.release()
        self.cap_obj = None
        self.is_streaming = False

#Import this singleton
global_calibration_state = CalibrationState()
