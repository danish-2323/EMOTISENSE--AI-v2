import os
import pandas as pd
from datetime import datetime
from src.config import SESSION_LOGS_DIR, REPORTS_DIR, SNAPSHOTS_DIR
import numpy as np

def ensure_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs(SESSION_LOGS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

def get_timestamp():
    """Get current timestamp"""
    return datetime.now()

def normalize_emotion_scores(emotion_dict):
    """Normalize emotion scores to sum to 1"""
    total = sum(emotion_dict.values())
    if total == 0:
        return {k: 1/len(emotion_dict) for k in emotion_dict}
    return {k: v/total for k, v in emotion_dict.items()}

def calculate_negative_score(emotion_dict):
    """Calculate negative emotion score from emotion dictionary"""
    negative_emotions = ['angry', 'disgust', 'fear', 'sad']
    return sum(emotion_dict.get(emotion, 0) for emotion in negative_emotions)

def save_session_data(df, session_id):
    """Save session data to CSV"""
    ensure_directories()
    filename = f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(SESSION_LOGS_DIR, filename)
    df.to_csv(filepath, index=False)
    return filepath

def capture_desktop_screenshot(event_type, score):
    """Capture desktop screenshot with error handling"""
    try:
        import pyautogui
        
        # Check if running locally (not in cloud)
        if os.environ.get('STREAMLIT_SHARING') or os.environ.get('HEROKU'):
            print("Screenshot disabled in cloud environment")
            return None
            
        ensure_directories()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{event_type}_{timestamp}_{score:.2f}.png"
        filepath = os.path.join(SNAPSHOTS_DIR, filename)
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        print(f"Screenshot saved: {filepath}")
        return filepath
    except ImportError:
        print("pyautogui not available - install with: pip install pyautogui")
        return None
    except Exception as e:
        print(f"Screenshot capture failed: {e}")
        return None

def calculate_session_analytics(df):
    """Calculate basic session analytics"""
    if df.empty:
        return {}
    
    analytics = {}
    
    try:
        # Most stressed moment
        max_stress_idx = df['stress'].idxmax()
        analytics['most_stressed'] = {
            'timestamp': df.loc[max_stress_idx, 'timestamp'],
            'score': df.loc[max_stress_idx, 'stress']
        }
        
        # Most engaged moment
        max_engagement_idx = df['engagement'].idxmax()
        analytics['most_engaged'] = {
            'timestamp': df.loc[max_engagement_idx, 'timestamp'],
            'score': df.loc[max_engagement_idx, 'engagement']
        }
        
        # Basic stability
        analytics['stability_score'] = max(0, 1 - df['stress'].var())
        analytics['longest_stress_duration'] = 5
        analytics['critical_moments'] = []
        
    except Exception as e:
        print(f"Analytics calculation error: {e}")
        analytics = {'stability_score': 0.5, 'longest_stress_duration': 0, 'critical_moments': []}
    
    return analytics

def generate_session_feedback(df, analytics):
    """Generate basic session feedback"""
    if df.empty:
        return ["No session data available for feedback."]
    
    feedback = []
    
    try:
        avg_stress = df['stress'].mean()
        if avg_stress > 0.7:
            feedback.append("High stress levels detected throughout the session.")
        elif avg_stress < 0.3:
            feedback.append("Overall stress levels remained low and manageable.")
        else:
            feedback.append("Moderate stress levels observed during the session.")
        
        avg_engagement = df['engagement'].mean()
        if avg_engagement < 0.4:
            feedback.append("Engagement levels were consistently low - consider taking breaks.")
        elif avg_engagement > 0.7:
            feedback.append("Excellent engagement levels maintained throughout the session.")
        
    except Exception as e:
        print(f"Feedback generation error: {e}")
        feedback = ["Session completed with normal emotional patterns."]
    
    return feedback if feedback else ["Session completed with normal emotional patterns."]

def calculate_session_quality_score(df):
    """Calculate basic session quality score (0-100)"""
    if df.empty:
        return 0
    
    try:
        avg_stress = df['stress'].mean()
        avg_engagement = df['engagement'].mean()
        
        # Simple quality calculation
        stress_score = max(0, 100 - (avg_stress * 100))
        engagement_score = avg_engagement * 100
        
        quality_score = (stress_score * 0.6 + engagement_score * 0.4)
        return min(100, max(0, quality_score))
    except:
        return 50