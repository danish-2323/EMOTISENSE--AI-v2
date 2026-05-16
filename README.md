# EMOTISENSE AI 🧠

**Multimodal Emotion Recognition using Audio + Face**

A real-time emotion monitoring system that combines facial emotion detection and audio stress analysis to provide comprehensive emotional insights.

## 🚀 Quick Start

Run the application in **1 command**:

```bash
# Install dependencies and run
pip install -r requirements.txt && streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
EMOTISENSE-AI/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                      # This file
├── src/
│   ├── config.py                  # Configuration settings
│   ├── utils.py                   # Utility functions (includes analytics & screenshots)
│   ├── webcam/
│   │   ├── camera.py              # Camera capture
│   │   └── face_emotion.py        # Face emotion detection
│   ├── audio/
│   │   ├── mic_capture.py         # Microphone capture
│   │   └── audio_emotion.py       # Audio stress analysis
│   ├── fusion/
│   │   └── fusion_engine.py       # Multimodal fusion
│   ├── dashboard/
│   │   ├── ui_components.py       # UI components
│   │   └── plots.py               # Visualization charts
│   ├── logger/
│   │   ├── session_logger.py      # Session logging with screenshots
│   │   └── report_generator.py    # PDF report generation
│   └── fallback/
│       └── rule_based.py          # Simulation/fallback mode
├── data/
│   └── sample_sessions/
│       └── demo_session.csv       # Sample session data
└── outputs/
    ├── session_logs/              # Session CSV files
    ├── reports/                   # Generated PDF reports
    └── screenshots/               # Captured screenshots during sessions
```

## 🎯 Features

### Core Functionality
- **Real-time Face Emotion Detection** (6 emotions: happy, sad, angry, fear, surprise, neutral)
- **Audio Stress Analysis** from microphone input
- **Multimodal Fusion Engine** combining face and audio data
- **Live Dashboard** with real-time metrics and alerts
- **Session Logging** with CSV export
- **PDF Report Generation** with insights and recommendations
- **Smart Screenshot Capture** during critical moments (auto + manual)
- **Session Intelligence** with advanced analytics and feedback
- **Quality Scoring System** for comprehensive session evaluation

### Dashboard Tabs
1. **Live Dashboard**: Real-time monitoring with video feed, metrics cards, and charts
2. **Session Report**: Comprehensive analysis with statistics and export options
3. **Screenshots**: Gallery of captured critical moments during session
4. **Analytics**: Advanced session intelligence with peak detection and feedback
5. **About**: Project information and technology stack

### Fallback Features
- **Simulation Mode**: Works without camera/microphone
- **Hardware Failure Handling**: Automatic fallback to simulated data
- **Robust Error Handling**: Graceful degradation when components fail

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Computer Vision**: OpenCV, FER (Facial Emotion Recognition)
- **Audio Processing**: sounddevice, librosa
- **Data Analysis**: pandas, numpy
- **Visualization**: plotly, matplotlib
- **Reports**: reportlab
- **Screenshots**: pyautogui, Pillow
- **Backup Detection**: DeepFace (fallback for FER)

## 📊 Metrics Provided

### Primary Metrics
- **Stress Level** (0-1): Combined face negative emotions + audio stress
- **Engagement** (0-1): Positive emotions adjusted by stress level
- **Confusion** (0-1): Emotion variance + moderate stress indicator
- **Confidence** (0-1): Inverse of stress and confusion

### Emotional States
- Stressed, Engaged, Calm, Positive, Negative, Neutral

### Audio Features
- RMS Energy, Zero Crossing Rate, MFCC coefficients, Spectral Centroid

## 🎮 Usage Instructions

### Starting a Session
1. Launch the application: `streamlit run app.py`
2. Click **"Start Session"** in the sidebar
3. Allow camera and microphone permissions when prompted
4. Monitor real-time emotions in the Live Dashboard

### Simulation Mode
- Toggle **"Simulation Mode"** if camera/microphone unavailable
- Generates realistic emotion patterns for demonstration
- Perfect for testing and demos without hardware

### Generating Reports
1. Stop the active session
2. Navigate to **"Session Report"** tab
3. View statistics and charts
4. Export as CSV or generate PDF report

## 🔧 Configuration

Key settings in `src/config.py`:

```python
# Audio settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_DURATION = 2.0

# Video settings  
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480

# Thresholds
STRESS_THRESHOLD = 0.7
ALERT_DURATION = 5  # seconds

# Fusion weights
FACE_WEIGHT = 0.6
AUDIO_WEIGHT = 0.4
```

## 🚨 Alerts & Monitoring

- **High Stress Alert**: Triggered when stress > 0.7 for 5+ seconds
- **Real-time Timeline**: Shows last 60 seconds of emotion data
- **Stress Gauge**: Visual stress level indicator with color coding
- **Emotion Breakdown**: Detailed face emotion percentages
- **Critical Moment Detection**: Automatic identification of peak stress/confusion
- **Manual Screenshot Capture**: Mark important moments with 📸 button

## 📈 Output Files

### Session Logs
- Location: `outputs/session_logs/`
- Format: `session_{id}_{timestamp}.csv`
- Contains: Timestamp, emotions, stress scores, fused metrics

### PDF Reports
- Location: `outputs/reports/`
- Format: `emotion_report_{id}_{timestamp}.pdf`
- Contains: Session stats, charts, recommendations, peak analysis

### Screenshots
- Location: `outputs/screenshots/`
- Format: `screenshot_{session_id}_{timestamp}.png`
- Types: Auto-captured (critical moments) and manual captures

## 🔄 Fallback Mechanisms

1. **Camera Failure**: Uses simulated face emotions with realistic patterns
2. **Microphone Failure**: Generates stress scores based on last known values + noise
3. **Library Errors**: Graceful degradation with default values
4. **Complete Simulation**: Toggle for full demo mode without hardware

## 🎯 Hackathon Ready

- **Single Command Setup**: `pip install -r requirements.txt && streamlit run app.py`
- **Demo Mode**: Simulation toggle for presentations without hardware
- **Stable Performance**: Robust error handling and fallback systems
- **Professional UI**: Clean Streamlit interface with real-time updates
- **Export Capabilities**: CSV and PDF reports for judges/stakeholders
- **Smart Analytics**: Session intelligence with quality scoring and feedback
- **Visual Evidence**: Screenshot capture for critical moments documentation

## 🐛 Troubleshooting

### Common Issues

**Camera not working:**
- Enable "Simulation Mode" in sidebar
- Check camera permissions in browser
- Ensure no other applications are using the camera

**Microphone not detected:**
- Application automatically falls back to simulated audio
- Check microphone permissions
- Verify microphone is not muted

**Installation errors:**
```bash
# If librosa installation fails
pip install librosa --no-deps
pip install numba

# If sounddevice fails  
pip install sounddevice --upgrade
```

## 📝 License

This project is open source and available under the MIT License.

---

## 👨💻 Author

**Danish** — B.Tech Artificial Intelligence and Data Science 

Hackathon Project: **SRM IST × NOOBTRON — NOOB HACKFEST**

## 👥 Team Members — PRIMELOGIX

- **Danish M** — AI/ML Developer & Integration  
  Implemented the core emotion pipeline (face + audio processing), multimodal fusion logic, and integrated key modules into the working application.

- **Chidarth M** — UI/UX & Dashboard Support  
  Supported dashboard layout planning, user flow design, and UI feature suggestions for live monitoring.

- **Deephan T** — Research & Feature Design  
  Worked on problem research, identifying real-world use cases, and defining feature requirements for a practical solution.

- **Jothik Rithin Bio J** — Testing & Validation  
  Contributed to testing the application workflow, identifying edge cases, and improving demo stability.

- **Deepak T A** — Documentation & Presentation  
  Assisted with README preparation, pitch content structuring, and hackathon submission formatting.

---

**Built for hackathons, designed for impact.** 🚀
