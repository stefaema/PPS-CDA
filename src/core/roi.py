#src/core/roi.py
import uuid
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from core.log_manager import logger
import cv2
import numpy as np
from typing import Dict, Tuple, Any
from datetime import datetime
from core.geometry import LaneDefinition, AnchorDefinition

MIN_RAW_ROI_SIZE = 5  # Minimum size in pixels for RawROIs to be considered valid

class BaseROI:
    """
    Abstract definition of a Region of Interest. 
    Enforces geometry, identification, and the processing contract.
    """
    def __init__(self, x: int, y: int, width: int, height: int, roi_type: str):
        self.id: str = str(uuid.uuid4())
        self.roi_type = roi_type
        
        # Geometry (integers)
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)

    @property
    def end_x(self) -> int: 
        return self.x + self.width

    @property
    def end_y(self) -> int: 
        return self.y + self.height

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains_point(self, px: int, py: int) -> bool:
        """Hit-test for mouse interaction."""
        return (self.x <= px < self.end_x) and (self.y <= py < self.end_y)

    def crop(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Safely extracts the ROI content from a frame.
        Includes bounds checking to prevent segfaults/errors.
        """
        if frame is None:
            return None
            
        h, w = frame.shape[:2]
        
        # Clamping coordinates to image boundaries
        x1 = max(0, min(self.x, w))
        y1 = max(0, min(self.y, h))
        x2 = max(0, min(self.end_x, w))
        y2 = max(0, min(self.end_y, h))
        
        # Return None if invalid area
        if x2 <= x1 or y2 <= y1:
            return None
            
        return frame[y1:y2, x1:x2]

    def to_dict(self) -> Dict[str, Any]:
        """Serialization for UI or JSON storage."""
        return {
            'id': self.id,
            'type': self.roi_type,
            'x': self.x,
            'y': self.y,
            'w': self.width,
            'h': self.height
        }

    def __str__(self) -> str:
        return f"[{self.roi_type.upper()}] ID:{self.id[:4]}.. @({self.x},{self.y}) {self.width}x{self.height}"

class RawROI(BaseROI):
    """
    Represents a dirty, un-normalized ROI drawn by the user.
    Used exclusively during the Calibration Draft phase.
    """
    def __init__(self, x: int, y: int, w: int, h: int):
        super().__init__(x, y, w, h, roi_type='raw')

    @classmethod
    def from_points(cls, x1: int, y1: int, x2: int, y2: int) -> 'RawROI':
        """Factory to create from two mouse clicks."""
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        return cls(x, y, w, h)

class AlignedROI(BaseROI):
    """
    Represents a confirmed, x-aligned perforation.
    """
    def __init__(self, x: int, y: int, w: int, h: int):
        super().__init__(x, y, w, h, roi_type='aligned')

@dataclass
class CalibrationProfile:
    """
    The Golden Record. This object is serialized to JSON to save a session.
    It contains the Metadata, the Physics (Signals), and the Geometry (Lanes/Anchors).
    """
    # --- System Identity ---
    id: str = ""
    name: str = "" 
    timestamp: str = ""
    description: str = ""  

    # --- The Physics (Reference Signals) ---
    # 1D arrays of float values (0.0 - 255.0) representing the ideal perforation grayscale color density
    left_lane_signal: np.ndarray = field(default_factory=lambda: np.array([]))
    right_lane_signal: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # --- Geometry Definitions ---
    # Optional because 8mm might only have one side
    left_lane: Optional[LaneDefinition] = None
    right_lane: Optional[LaneDefinition] = None

    # --- Perforation Anchors ---
    # The expected Y-positions of holes relative to the signal
    left_anchors: Optional[List[AnchorDefinition]] = field(default_factory=list)
    right_anchors: Optional[List[AnchorDefinition]] = field(default_factory=list)

    @classmethod
    def create_new(cls) -> 'CalibrationProfile':
        """Factory method to generate a blank profile with unique ID."""
        return cls(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat()
        )

    def to_dict(self):
        """Helper for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "description": self.description,
            "left_lane_signal": self.left_lane_signal.tolist(),
            "right_lane_signal": self.right_lane_signal.tolist(),
            "left_lane": self.left_lane.to_dict() if self.left_lane else None,
            "right_lane": self.right_lane.to_dict() if self.right_lane else None,
            "anchors": [a.to_dict() for a in self.anchors]
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CalibrationProfile':
        """Helper for JSON deserialization."""
        profile = CalibrationProfile(
            id=data["id"],
            name=data.get("name", ""),
            timestamp=data["timestamp"],
            description=data.get("description", ""),
            left_lane_signal=np.array(data.get("left_lane_signal", []), dtype=np.float32),
            right_lane_signal=np.array(data.get("right_lane_signal", []), dtype=np.float32),
            left_lane=LaneDefinition(**data["left_lane"]) if data.get("left_lane") else None,
            right_lane=LaneDefinition(**data["right_lane"]) if data.get("right_lane") else None,
            anchors=[AnchorDefinition(**a) for a in data.get("anchors", [])]
        )
        return profile


class VerticalStrip(BaseROI):
    """
    Represents a full vertical lane on one side of the film.
    Acts as:
    1. A Sensor: Scans the full height to produce a 1D density profile.
    2. A Container: Holds the AlignedROIs (holes) known to exist in this lane.
    """
    def __init__(self, aligned_rois: List[AlignedROI], image_height: int, side: str = 'LEFT', frame: np.ndarray = None):


        if not aligned_rois:
            raise ValueError("VerticalStrip requires AlignedROIs to work.")
        
        x: int = aligned_rois[0].x
        w: int = aligned_rois[0].width

        # Aligned ROIs imply same x and width across all holes.
        if any(r.x != x or r.width != w for r in aligned_rois):
            raise ValueError("All AlignedROIs must have the same x and width for VerticalStrip.")
    
        # Full height of the image, as it is a vertical strip
        y: int = 0
        h: int = image_height

        self.aligned_rois: List[AlignedROI] = aligned_rois
        self.side: str = side.upper()

        super().__init__(x, y, w, h, roi_type='vertical_strip')
        self._reference_signal: Optional[np.ndarray] = None

        if frame is not None:
            self.compute_and_store_reference(frame)
        else:
            raise ValueError("Frame must be provided to compute reference signal. By default, it is required at initialization.")
        
    def compute_and_store_reference(self, frame: np.ndarray) -> bool:
        """
        Stores the current look of the film as the 'Zero' time offset point.
        """
        signal = self._extract_signal(frame)
        if signal is None: return False
        
        self._reference_signal = signal
        return True


    def _extract_signal(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Internal logic: Crop -> Gray -> Blur -> Collapse."""
        crop = self.crop(frame)
        if crop is None: return None
        
        # Fast conversion
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        
        # Denoise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Collapse (Mean density)
        return np.mean(blurred, axis=1, dtype=np.float32)

    def measure_vertical_offset(self, frame: np.ndarray) -> Tuple[float, float]:
        """
        The Engine calls this 24 times a second.
        
        Returns:
            (offset_pixels, confidence_score)
            - offset_pixels: +10 means film moved 10px DOWN. -10 means UP.
            - confidence: 0.0 to 1.0 (How similar is the signal?)
        """
        if self._reference_signal is None:
            raise RuntimeError("VerticalStrip not calibrated! No reference signal.")

        # 1. Get current signal
        live_signal = self._extract_signal(frame)
        if live_signal is None: return (0.0, 0.0)

        # 2. Cross-Correlation
        # We slide the live_signal over the reference_signal to find the best match.
        # mode='valid' returns only the overlapping area
        # Usually we only search a window, but full correlation is fast on 1D arrays.
        
        # Optimization: Normalize signals to get -1 to 1 result (Correlation Coefficient)
        ref_norm = (self._reference_signal - np.mean(self._reference_signal))
        ref_std = np.std(self._reference_signal)
        
        live_norm = (live_signal - np.mean(live_signal))
        live_std = np.std(live_signal)

        if ref_std == 0 or live_std == 0: return (0.0, 0.0) # Flat signal error

        correlation = np.correlate(live_norm, ref_norm, mode='full')
        correlation = correlation / (ref_std * live_std * len(live_signal))
        
        # 3. Find Peak
        peak_idx = np.argmax(correlation)
        max_val = correlation[peak_idx] # This is the confidence score
        
        # 4. Calculate Shift
        # The center of the correlation array represents 0 shift.
        # implementation detail: requires careful indexing math based on array lengths
        shift = peak_idx - (len(live_signal) - 1)
        
        self._last_offset = float(shift)
        return (self._last_offset, float(max_val))
    
    def generate_dataclasses(self) -> Tuple[LaneDefinition, List[AnchorDefinition]]:
        """
        Converts this VerticalStrip and its AlignedROIs into a LaneDefinition and list of AnchorDefinitions
        suitable for inclusion in a CalibrationProfile.
        """
        lane_side = self.side
        
        lane_def = LaneDefinition(
            side=lane_side,
            x=self.x,
            width=self.width
        )

        anchors: List[AnchorDefinition] = []
        for roi in self.aligned_rois:
            anchor = AnchorDefinition(
                id=roi.id,
                lane_side=lane_side,
                y=roi.y,
                height=roi.height
            )
            anchors.append(anchor)
        
        return lane_def, anchors

class CalibrationManager:
    """
    Manages the overall calibration state, including captured images and ROI management.
    """
    def __init__(self, raw_captured_image: Optional[np.ndarray] = None):
        self.raw_captured_image: Optional[np.ndarray] = raw_captured_image
        self.raw_rois: List[RawROI] = []
        self.aligned_rois: List[AlignedROI] = []

    def clear_all_rois(self):
        self.raw_rois = []
        self.aligned_rois = []
    
    def add_raw_roi(self, x1: int, y1: int, x2: int, y2: int) -> Optional[RawROI]:
        roi = RawROI.from_points(x1, y1, x2, y2)
        if roi.width > MIN_RAW_ROI_SIZE and roi.height > MIN_RAW_ROI_SIZE:
            self.raw_rois.append(roi)
            return roi
        return None
    
    def get_all_raw_rois(self) -> List[RawROI]:
        return self.raw_rois
    
    def remove_raw_roi_from_point(self, x: int, y: int) -> Optional[str]:
        for roi in reversed(self.raw_rois):
            if roi.contains_point(x, y):
                self.raw_rois.remove(roi)
                return roi.id
        return None

    def split_rois_by_side(self) -> Tuple[List[BaseROI], List[BaseROI]]:
        """
        Splits RawROIs into left and right lists based on their position relative to the image center.
        ROIs that straddle the center line are discarded with a warning.
        """
        image_width = self.raw_captured_image.shape[1]
        if image_width is None:
            logger.error("Cannot split ROIs by side: Image width is unknown.")
            return [], []

        mid_x = image_width // 2
        left, right = [], []

        for roi in self.raw_rois:
            # Strict boundary check
            if roi.end_x <= mid_x:
                left.append(roi)
            elif roi.x >= mid_x:
                right.append(roi)
            else:
                # ROI straddles the center line
                logger.warning(f"ROI {roi.id} crosses the center line ({mid_x}). Discarding.")
                continue 

        # Sort Top->Bottom
        left.sort(key=lambda r: r.y)
        right.sort(key=lambda r: r.y)
        logger.info(f"Split ROIs - LEFT: {len(left)}, RIGHT: {len(right)}")
        return left, right

    def align_raw_rois(self, raw_list: List[BaseROI]) -> Tuple[List[AlignedROI], List[AlignedROI]]:
        """
        aligns a list of RawROIs for both sides into AlignedROIs.
        1. Find common X-axis intersection for all ROIs on each side.
        2. Create AlignedROIs with unified X and Width, preserving Y and Height.
        3. Return two lists: left_aligned_rois, right_aligned_rois

        Args:
            raw_list (List[BaseROI]): List of RawROIs to align.
        Returns:
            Tuple[List[AlignedROI], List[AlignedROI]]: Aligned ROIs for left and right sides.
        """
        def align_side(raw_list: List[BaseROI], side_name: str) -> List[AlignedROI]:
            """
            Normalizes a list of RawROIs for one side into AlignedROIs.
            """
            aligned_rois: List[AlignedROI] = []
            current_max_start = raw_list[0].x
            current_min_end = raw_list[0].end_x
            for r in raw_list:
                current_max_start = max(current_max_start, r.x)
                current_min_end = min(current_min_end, r.end_x)

            width = current_min_end - current_max_start
 
            if width <= 0:
                logger.error(f"Normalization Failed for {side_name}: No common X-axis intersection.")
            # 3. Generate AlignedROIs, keeping Y and Height
            for raw in raw_list:
                aligned_roi = AlignedROI(
                    x=current_max_start,
                    y=raw.y,
                    w=width,
                    h=raw.height
                )
                aligned_rois.append(aligned_roi)
            return aligned_rois

        left_side_rois, right_side_rois = self.split_rois_by_side()

        if len(raw_list) == 0 or not raw_list:
            logger.warning(f"No ROIs to normalize")
            
        left_aligned_rois = align_side(left_side_rois, "LEFT")
        right_aligned_rois = align_side(right_side_rois, "RIGHT")
        logger.info(f"Aligned ROIs - LEFT: {len(left_aligned_rois)}, RIGHT: {len(right_aligned_rois)}")
        return left_aligned_rois, right_aligned_rois

    def generate_vertical_strips(self, frame: np.ndarray) -> Tuple[Optional[VerticalStrip], Optional[VerticalStrip]]:
        """
        Creates VerticalStrips for left and right sides from the aligned ROIs.
        """
        image_height = frame.shape[0]
        left_strip = None
        right_strip = None

        left_aligned_rois, right_aligned_rois = self.align_raw_rois(self.raw_rois)

        if left_aligned_rois:
            left_strip = VerticalStrip(left_aligned_rois, image_height, side='LEFT', frame=frame)
            if not left_strip.compute_and_store_reference(frame):
                logger.error("Failed to compute reference signal for LEFT strip.")

        if right_aligned_rois:
            right_strip = VerticalStrip(right_aligned_rois, image_height, side='RIGHT', frame=frame)
            if not right_strip.compute_and_store_reference(frame):
                logger.error("Failed to compute reference signal for RIGHT strip.")
        logger.info(f"Generated VerticalStrips - LEFT: {'Yes' if left_strip else 'No'}, RIGHT: {'Yes' if right_strip else 'No'}")
        return left_strip, right_strip

    def generate_calibration_profile(self, frame: np.ndarray) -> Optional[CalibrationProfile]:
        """
        Generates a CalibrationProfile from the current raw ROIs and captured image.
        """
        left_strip, right_strip = self.generate_vertical_strips(frame)

        if not left_strip and not right_strip:
            logger.error("Cannot generate CalibrationProfile: No valid VerticalStrips.")
            return None

        profile = CalibrationProfile.create_new()

        if left_strip:
            lane_def, anchors = left_strip.generate_dataclasses()
            profile.left_lane = lane_def
            profile.left_lane_signal = left_strip._reference_signal
            profile.left_anchors = anchors
            logger.info("Assigned LEFT lane data to CalibrationProfile.")
        if right_strip:
            lane_def, anchors = right_strip.generate_dataclasses()
            profile.right_lane = lane_def
            profile.right_lane_signal = right_strip._reference_signal
            profile.right_anchors = anchors
            logger.info("Assigned RIGHT lane data to CalibrationProfile.")

        logger.info("CalibrationProfile generation complete.")
        return profile
