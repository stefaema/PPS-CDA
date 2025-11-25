import os
import sys
import threading
import time
from typing import Optional

import cv2
import numpy as np

from core.log_manager import logger

DEFAULT_RESOLUTION = (1920, 1080)


class HardwareManager:
    """
    Manages hardware interactions for video capture, providing a threaded
    interface to retrieve frames from a camera device.
    """

    def __init__(self, use_threading: bool = True):
        """
        Initialize the HardwareManager.

        Args:
            use_threading (bool): Whether to use a separate thread for frame capture.
                                  Defaults to True for performance.
        """
        self._cap: Optional[cv2.VideoCapture] = None
        self._camera_index: Optional[int] = None

        self._use_threading = use_threading
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._frame_lock = threading.Lock()

        self._latest_frame: Optional[np.ndarray] = None
        self._target_fps: float = 30.0

    def _configure_capture(self, cap: cv2.VideoCapture, width: int, height: int) -> None:
        """
        Configures camera properties (FOURCC, resolution, FPS, exposure, etc.).
        This logic relies on configurations known to work for DSHOW/C922.

        Args:
            cap (cv2.VideoCapture): The video capture object.
            width (int): Desired frame width.
            height (int): Desired frame height.
        """
        # --- 1. Define Codec (MJPG is essential for high performance) ---
        vid_fmt = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')

        # --- 2. Set Codec and Resolution (Order is crucial) ---

        # Set FOURCC first to unlock high resolution/FPS modes
        cap.set(cv2.CAP_PROP_FOURCC, vid_fmt)

        # Set resolution second
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        cap.set(cv2.CAP_PROP_FOURCC, vid_fmt)

        cap.set(cv2.CAP_PROP_FPS, int(self._target_fps))

        actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = cap.get(cv2.CAP_PROP_FPS)

        logger.info(f"Configuring Camera: {actual_width}x{actual_height} @ {actual_fps:.2f} FPS")

    def start_video_stream(self, index: int, width: int = DEFAULT_RESOLUTION[0], height: int = DEFAULT_RESOLUTION[1]) -> bool:
        """
        Starts the video stream for the specified camera index.

        Args:
            index (int): The index of the camera device.
            width (int): Desired frame width.
            height (int): Desired frame height.

        Returns:
            bool: True if the stream started successfully, False otherwise.
        """
        self.stop_video_stream()

        logger.debug(f"HardwareManager: Opening Camera {index}...")

        # Select platform-specific backend
        if sys.platform.startswith('linux'):
            # V4L2 is the standard on Linux
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        else:
            # Disable MSMF hardware transforms to prevent issues on Windows
            os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
            # DSHOW is preferred for property control on Windows
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            logger.error(f"HardwareManager: Failed to open Camera {index}")
            return False

        # --- CONFIGURE CAMERA PROPERTIES ---
        self._configure_capture(cap, width, height)

        self._cap = cap
        self._camera_index = index

        # Warmup: Read a few frames to let white balance/exposure settle
        for _ in range(5):
            self._cap.read()

        logger.info(f"Camera #{index} Stream Ready.")

        if self._use_threading:
            self._stop_event.clear()
            self._capture_thread = threading.Thread(
                target=self._capture_worker,
                name=f"CamThread-{index}",
                daemon=True
            )
            self._capture_thread.start()
        return True

    def stop_video_stream(self) -> None:
        """
        Stops the video stream and releases the camera resources.
        """
        if self._capture_thread and self._capture_thread.is_alive():
            self._stop_event.set()
            self._capture_thread.join(timeout=2.0)

        if self._cap:
            self._cap.release()

        self._cap = None
        with self._frame_lock:
            self._latest_frame = None

    def _capture_worker(self) -> None:
        """
        Background loop to fetch frames.
        Runs as fast as hardware allows to clear the buffer.
        """
        # Time.sleep is not used here because cap.read() blocks naturally
        # until the next frame is ready, which is the best synchronization method.

        while not self._stop_event.is_set():
            if self._cap is None:
                break

            # cap.read() blocks until the frame is available
            ret, frame = self._cap.read()

            if ret:
                # Process Frame (BGR -> RGB)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                with self._frame_lock:
                    self._latest_frame = frame_rgb
            else:
                logger.warning("HardwareManager: Empty frame. Backing off 100ms.")
                time.sleep(0.1)  # Pause if the camera is having issues

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Retrieves the most recent frame captured by the worker thread.

        Returns:
            Optional[np.ndarray]: The latest RGB frame, or None if unavailable.
        """
        if self._use_threading:
            with self._frame_lock:
                if self._latest_frame is None:
                    return None
                # Return a copy to avoid modification outside the lock
                return self._latest_frame.copy()
        else:
            # Non-threaded alternative (reads directly from the camera)
            if self._cap is None:
                return None
            ret, frame = self._cap.read()
            if ret:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return None

    def get_target_fps(self) -> float:
        """
        Returns the target FPS configuration.

        Returns:
            float: The target frames per second.
        """
        return self._target_fps

    def is_streaming(self) -> bool:
        """
        Checks if the camera is currently streaming.

        Returns:
            bool: True if the camera object exists, False otherwise.
        """
        return self._cap is not None


global_hardware_manager = HardwareManager()
