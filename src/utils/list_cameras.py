#src/utils/list_cameras.py
import sys
from cv2 import CAP_DSHOW, CAP_V4L2, CAP_ANY
from dataclasses import dataclass
from core.locale_manager import T
from cv2_enumerate_cameras import enumerate_cameras

# Use DSHOW for windows
# On Linux, the default V4L2 backend is used.

# Static Fallback Options, in case no cameras are detected (WEIRD CASE)
FALLBACK_SOURCES = {
    0: f'{T("video_device")} 1',
    1: f'{T("video_device")} 2',
    2: f'{T("video_device")} 3',
}

@dataclass
class VideoSource:
    """
    Represents a video source (camera) on the system. 
    
    Attributes:
        name (str): The display name of the camera.
        index (int): The index identifier for the camera.
    """
    name: str
    index: int

def _is_windows_platform():
    return sys.platform.startswith('win')

def _is_linux_platform():
    return sys.platform.startswith('linux')

def _get_api_preference():
    """ Returns the preferred OpenCV API flag based on the current platform. This prevents repeated sources and ensures compatibility."""
    if _is_windows_platform():
        return CAP_DSHOW
    elif _is_linux_platform():
        return CAP_V4L2
    else:
        return CAP_ANY

def get_aval_video_sources() -> list[VideoSource]:
    """
    Retrieves a list of available video sources (cameras, capture devices) on the system.
    """
    backend_flag = _get_api_preference()
    cams = enumerate_cameras(apiPreference=backend_flag)
    camera_info_list = [VideoSource(name=cam.name, index=cam.index) for cam in cams]
    return camera_info_list

if __name__ == "__main__":
    cameras = get_aval_video_sources()
    for camera in cameras:
        print(f"Camera Index: {camera.index}, Name: {camera.name}")
