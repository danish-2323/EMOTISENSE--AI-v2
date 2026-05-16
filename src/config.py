import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
SESSION_LOGS_DIR = os.path.join(OUTPUTS_DIR, "session_logs")
REPORTS_DIR = os.path.join(OUTPUTS_DIR, "reports")
SNAPSHOTS_DIR = os.path.join(OUTPUTS_DIR, "snapshots")

# Audio settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_DURATION = 2.0
AUDIO_CHANNELS = 1

# Video settings
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
FPS = 30

# Emotion settings
EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
STRESS_THRESHOLD = 0.7
ALERT_DURATION = 5

# Dashboard settings
TIMELINE_SECONDS = 60
UPDATE_INTERVAL = 1.0

# Fusion weights
FACE_WEIGHT = 0.6
AUDIO_WEIGHT = 0.4

# Screenshot settings
SCREENSHOT_STRESS_THRESHOLD = 0.85
SCREENSHOT_STRESS_DURATION = 3
SCREENSHOT_HAPPY_CONFIDENCE = 0.75
SCREENSHOT_DISTRACTION_THRESHOLD = 0.3
SCREENSHOT_DISTRACTION_DURATION = 5
SCREENSHOT_COOLDOWN = 10

# Analytics settings
SESSION_QUALITY_WEIGHTS = {
    'stress': 0.4,
    'engagement': 0.3,
    'stability': 0.3
}