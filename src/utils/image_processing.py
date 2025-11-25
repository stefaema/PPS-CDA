# src/utils/image_processing.py
import cv2
import base64
import numpy as np

def cv2_to_base64(image, quality: int = 80, use_grayscale: bool = False) -> str:
    """Converts a BGR numpy array to a string base64 JPG"""
    if image is None: return None
    if use_grayscale:
        frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    is_success, buffer = cv2.imencode(".jpg", frame, encode_param)
    if not is_success: return None
    b64_img = base64.b64encode(buffer).decode()
    return f'data:image/jpeg;base64,{b64_img}'
