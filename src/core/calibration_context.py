# src/core/calibration_context.py
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from core.roi import CalibrationManager, CalibrationProfile

@dataclass
class CalibrationContext:
    """
    Holds the state for a single run of the Calibration Wizard.
    Passes data between steps without tight coupling.
    """
    # Step 1 Output
    captured_frame: Optional[np.ndarray] = None
    
    # Step 2 State/Output
    calibration_manager: Optional[CalibrationManager] = None
    
    # Step 3 Output
    calibration_profile: Optional[CalibrationProfile] = None

    def set_captured_frame(self, frame: np.ndarray):
        """
        Sets the frame and resets downstream data to ensure consistency.
        If user goes back and retakes photo, old ROIs are invalid.
        """
        self.captured_frame = frame
        self.calibration_manager = None
        self.calibration_profile = None

    def reset(self):
        """Clears all data."""
        self.captured_frame = None
        self.calibration_manager = None
        self.calibration_profile = None
