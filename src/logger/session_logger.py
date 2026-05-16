import pandas as pd
from datetime import datetime
import uuid

class SessionLogger:
    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.session_data = []
        self.start_time = None
        self.is_active = False
        self.screenshots = []
        self.screenshot_cooldowns = {}
    
    def start_session(self):
        """Start a new logging session"""
        self.session_id = str(uuid.uuid4())[:8]
        self.session_data = []
        self.start_time = datetime.now()
        self.is_active = True
        self.screenshots = []
        self.screenshot_cooldowns = {}
        print(f"Session {self.session_id} started at {self.start_time}")
    
    def log_data(self, face_emotions, audio_stress_score, fused_metrics):
        """Log data point to session"""
        if not self.is_active:
            return
        
        timestamp = datetime.now()
        
        # Create data point
        data_point = {
            'timestamp': timestamp,
            'session_id': self.session_id,
            'audio_stress_score': audio_stress_score,
            **face_emotions,  # Unpack face emotions
            **fused_metrics   # Unpack fused metrics
        }
        
        self.session_data.append(data_point)
    
    def manual_screenshot(self, fused_metrics):
        """Manually capture screenshot"""
        try:
            from src.utils import capture_desktop_screenshot
            
            current_time = datetime.now()
            filepath = capture_desktop_screenshot('MANUAL', fused_metrics.get('stress', 0))
            if filepath:
                self.screenshots.append({
                    'type': 'MANUAL',
                    'timestamp': current_time,
                    'score': fused_metrics.get('stress', 0),
                    'filepath': filepath
                })
                return True
            return False
        except Exception as e:
            print(f"Manual screenshot error: {e}")
            return False
    
    def get_session_dataframe(self):
        """Get current session data as DataFrame"""
        if not self.session_data:
            return pd.DataFrame()
        
        return pd.DataFrame(self.session_data)
    
    def stop_session(self):
        """Stop current session"""
        if self.is_active:
            self.is_active = False
            end_time = datetime.now()
            duration = end_time - self.start_time if self.start_time else None
            print(f"Session {self.session_id} stopped. Duration: {duration}")
            return self.get_session_dataframe()
        return pd.DataFrame()
    
    def get_session_stats(self):
        """Get session statistics"""
        df = self.get_session_dataframe()
        if df.empty:
            return {}
        
        stats = {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'duration': datetime.now() - self.start_time if self.start_time else None,
            'total_records': len(df),
            'avg_stress': df['stress'].mean() if 'stress' in df.columns else 0,
            'max_stress': df['stress'].max() if 'stress' in df.columns else 0,
            'avg_engagement': df['engagement'].mean() if 'engagement' in df.columns else 0,
            'avg_confidence': df['confidence'].mean() if 'confidence' in df.columns else 0,
            'dominant_states': df['dominant_state'].value_counts().to_dict() if 'dominant_state' in df.columns else {},
            'screenshots': self.screenshots,
            'feedback': ["Session completed with normal emotional patterns."],
            'quality_score': 75
        }
        
        return stats