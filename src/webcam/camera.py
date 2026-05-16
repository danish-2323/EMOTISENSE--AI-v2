import cv2
import numpy as np
from src.config import VIDEO_WIDTH, VIDEO_HEIGHT

class CameraCapture:
    def __init__(self):
        self.cap = None
        self.is_active = False
        
    def start(self):
        """Start camera capture"""
        try:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)
                # Test if we can actually read a frame
                ret, frame = self.cap.read()
                if ret:
                    self.is_active = True
                    print("Camera started successfully")
                    return True
                else:
                    print("Camera opened but cannot read frames")
                    self.cap.release()
            else:
                print("Cannot open camera")
        except Exception as e:
            print(f"Camera error: {e}")
        
        self.is_active = False
        return False
    
    def get_frame(self):
        """Get current frame from camera"""
        if not self.is_active or not self.cap:
            return None
            
        ret, frame = self.cap.read()
        if ret:
            return cv2.flip(frame, 1)  # Mirror image
        return None
    
    def stop(self):
        """Stop camera capture"""
        if self.cap:
            self.cap.release()
        self.is_active = False
    
    def __del__(self):
        self.stop()