import random
import numpy as np
import time
from datetime import datetime
from src.config import EMOTIONS

class FallbackEmotionGenerator:
    def __init__(self):
        self.last_face_emotions = {emotion: 1/len(EMOTIONS) for emotion in EMOTIONS}
        self.last_audio_stress = 0.5
        self.emotion_trend = 0.0
        self.stress_trend = 0.0
        self.time_factor = 0
        self.scenario_timer = 0
        self.current_scenario = "normal"
    
    def generate_face_emotions(self):
        """Generate realistic dynamic face emotions"""
        self.time_factor += 1
        
        # Create base emotion pattern with time-based variation
        emotions = {}
        
        # Use sine waves for natural emotion fluctuation
        time_mod = self.time_factor * 0.1
        
        if self.current_scenario == "happy":
            emotions['happy'] = max(0.01, 0.4 + 0.3 * np.sin(time_mod))
            emotions['neutral'] = max(0.01, 0.3 + 0.1 * np.cos(time_mod * 0.7))
            emotions['surprise'] = max(0.01, 0.1 + 0.1 * np.sin(time_mod * 1.3))
            emotions['sad'] = max(0.01, 0.05 + 0.05 * np.sin(time_mod * 0.5))
            emotions['angry'] = max(0.01, 0.05 + 0.05 * np.cos(time_mod * 0.3))
            emotions['fear'] = max(0.01, 0.03 + 0.02 * np.sin(time_mod * 2))
            emotions['disgust'] = max(0.01, 0.02 + 0.03 * np.cos(time_mod * 1.7))
        elif self.current_scenario == "stressed":
            emotions['angry'] = max(0.01, 0.3 + 0.2 * np.sin(time_mod * 1.2))
            emotions['fear'] = max(0.01, 0.2 + 0.15 * np.cos(time_mod * 0.8))
            emotions['sad'] = max(0.01, 0.15 + 0.1 * np.sin(time_mod * 0.6))
            emotions['neutral'] = max(0.01, 0.2 + 0.1 * np.cos(time_mod))
            emotions['happy'] = max(0.01, 0.05 + 0.05 * np.sin(time_mod * 0.3))
            emotions['surprise'] = max(0.01, 0.05 + 0.05 * np.cos(time_mod * 1.5))
            emotions['disgust'] = max(0.01, 0.05 + 0.05 * np.sin(time_mod * 2.1))
        else:  # normal
            emotions['neutral'] = max(0.01, 0.4 + 0.2 * np.sin(time_mod * 0.5))
            emotions['happy'] = max(0.01, 0.25 + 0.15 * np.cos(time_mod * 0.7))
            emotions['sad'] = max(0.01, 0.1 + 0.08 * np.sin(time_mod * 0.3))
            emotions['surprise'] = max(0.01, 0.08 + 0.07 * np.cos(time_mod * 1.1))
            emotions['angry'] = max(0.01, 0.07 + 0.06 * np.sin(time_mod * 0.9))
            emotions['fear'] = max(0.01, 0.05 + 0.04 * np.cos(time_mod * 1.3))
            emotions['disgust'] = max(0.01, 0.05 + 0.04 * np.sin(time_mod * 1.7))
        
        # Normalize to ensure they sum to 1
        total = sum(emotions.values())
        if total > 0:
            emotions = {k: v/total for k, v in emotions.items()}
        else:
            # Fallback to neutral if something went wrong
            emotions = {
                'neutral': 0.7, 'happy': 0.1, 'sad': 0.05, 
                'angry': 0.05, 'fear': 0.05, 'surprise': 0.03, 'disgust': 0.02
            }
        
        # Change scenario periodically
        self.scenario_timer += 1
        if self.scenario_timer > 20:  # Change every 20 updates
            scenarios = ["normal", "happy", "stressed"]
            self.current_scenario = random.choice(scenarios)
            self.scenario_timer = 0
            print(f"Scenario changed to: {self.current_scenario}")
        
        self.last_face_emotions = emotions
        return emotions
    
    def generate_audio_stress(self):
        """Generate realistic dynamic audio stress"""
        # Base stress with time variation
        time_mod = self.time_factor * 0.08
        
        if self.current_scenario == "stressed":
            base_stress = 0.7 + 0.2 * np.sin(time_mod * 1.5)
        elif self.current_scenario == "happy":
            base_stress = 0.2 + 0.15 * np.sin(time_mod * 0.8)
        else:  # normal
            base_stress = 0.4 + 0.2 * np.sin(time_mod)
        
        # Add some noise
        noise = random.uniform(-0.1, 0.1)
        stress = base_stress + noise
        
        # Keep in bounds
        stress = max(0.0, min(1.0, stress))
        
        self.last_audio_stress = stress
        return stress
    
    def simulate_scenario(self, scenario_type="normal"):
        """Simulate specific emotional scenarios"""
        if scenario_type == "stressed":
            self.emotion_trend = -0.8
            self.stress_trend = 0.8
        elif scenario_type == "happy":
            self.emotion_trend = 0.8
            self.stress_trend = -0.5
        elif scenario_type == "confused":
            # Mixed emotions, moderate stress
            self.emotion_trend = 0.0
            self.stress_trend = 0.3
        else:  # normal
            self.emotion_trend = random.uniform(-0.3, 0.3)
            self.stress_trend = random.uniform(-0.3, 0.3)
    
    def generate_realistic_session_data(self, duration_minutes=5):
        """Generate realistic session data for demo purposes"""
        data_points = []
        points_per_minute = 60  # 1 point per second
        total_points = duration_minutes * points_per_minute
        
        # Simulate different phases
        phases = [
            ("normal", 0.3),      # 30% normal
            ("stressed", 0.2),    # 20% stressed
            ("happy", 0.3),       # 30% happy
            ("confused", 0.2)     # 20% confused
        ]
        
        current_phase = 0
        phase_progress = 0
        
        for i in range(total_points):
            # Check if we should switch phases
            phase_duration = int(total_points * phases[current_phase][1])
            if phase_progress >= phase_duration:
                current_phase = (current_phase + 1) % len(phases)
                phase_progress = 0
                self.simulate_scenario(phases[current_phase][0])
            
            # Generate data point
            timestamp = datetime.now()
            face_emotions = self.generate_face_emotions()
            audio_stress = self.generate_audio_stress()
            
            data_points.append({
                'timestamp': timestamp,
                'face_emotions': face_emotions,
                'audio_stress': audio_stress
            })
            
            phase_progress += 1
        
        return data_points