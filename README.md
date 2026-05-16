# EMOTISENSE AI 🧠

**Advanced AI-Powered Study Session Analyzer with Multimodal Emotion Recognition**

A real-time intelligent study monitoring system that combines facial emotion detection, audio stress analysis, and screen activity tracking to provide comprehensive insights into your study sessions.

---

## 🚀 Quick Start

Run the application in **2 commands**:

```bash
# Install dependencies
pip install -r requirements.txt

# Start backend
uvicorn backend.server:app --reload --port 8000

# Start frontend (in new terminal)
cd frontend
npm install
npm run dev
```

The application will open at `http://localhost:5173`

---

## 📁 Project Structure

```
EMOTISENSE-AI/
├── backend/
│   ├── server.py                  # FastAPI backend with WebSocket
│   ├── screen_analyser.py         # Screen activity analysis (OCR-free)
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main application with routing
│   │   ├── components/
│   │   │   ├── StudyPlanner.jsx       # Pre-session planning form
│   │   │   ├── FocusDashboard.jsx     # Real-time focus monitoring
│   │   │   ├── PomodoroTimer.jsx      # Pomodoro timer with breaks
│   │   │   ├── ScreenShare.jsx        # Screen sharing & app tracking
│   │   │   ├── StudyCoach.jsx         # AI coach with GPT integration
│   │   │   ├── StudyReport.jsx        # Post-session analysis
│   │   │   ├── ActivityLog.jsx        # Detailed activity timeline
│   │   │   ├── Screenshots.jsx        # Distraction screenshot gallery
│   │   │   ├── SessionHistory.jsx     # Past sessions with trends
│   │   │   └── Sidebar.jsx            # Navigation sidebar
│   │   └── styles/
│   │       └── globals.css            # Complete styling system
│   └── package.json               # Node dependencies
├── src/
│   ├── config.py                  # Configuration settings
│   ├── utils.py                   # Utility functions
│   ├── webcam/
│   │   ├── camera.py              # Camera capture
│   │   └── face_emotion.py        # Face emotion detection (FER)
│   ├── audio/
│   │   ├── mic_capture.py         # Microphone capture
│   │   └── audio_emotion.py       # Audio stress analysis
│   ├── fusion/
│   │   └── fusion_engine.py       # Multimodal fusion
│   ├── logger/
│   │   ├── session_logger.py      # Session logging
│   │   └── report_generator.py    # PDF report generation
│   └── fallback/
│       └── rule_based.py          # Simulation/fallback mode
└── outputs/
    ├── session_logs/              # Session CSV files
    ├── reports/                   # Generated PDF reports
    └── screenshots/               # Captured screenshots
```

---

## 🎯 Core Features

### 1. **Study Session Planner**
- Pre-session planning form with subject, duration, and goals
- Study mode selection (Deep Focus, Active Learning, Review)
- Break preference configuration (Pomodoro 25/5, 45/15, 60/10, Custom)
- Goal setting for focused study sessions

### 2. **Real-Time Focus Monitoring**
- **Dual Focus System**: Combines facial engagement (40%) + screen activity (60%)
- **Attention State Detection**: Deep Focus, Light Focus, Distracted, Fatigued, Stressed, On Break
- **Live Metrics Dashboard**:
  - Face Focus (facial engagement percentage)
  - Screen Focus (on-task app usage)
  - Stress Level (combined face + audio analysis)
  - Confidence Level
- **Session Progress Tracking**: Active time vs distracted time
- **Real-Time Alerts**: Immediate notifications for distractions

### 3. **Intelligent Screen Monitoring**
- **Entire Screen Sharing Enforcement**: Validates full screen share (no window/tab sharing)
- **Study App Declaration**: User declares which app they'll study in
- **Visual App Detection**: OCR-free detection using image analysis
  - Color pattern recognition
  - Brightness analysis
  - Visual heuristics for common apps
- **App Change Tracking**: Logs every app switch with timestamps
- **Focus Scoring**: 0-100 score based on whether user is in declared app

### 4. **Pomodoro Timer Integration**
- Work/break phase management
- Persistent timer across page navigation
- Automatic break reminders
- Customizable work and break durations

### 5. **AI Study Coach**
- **Real-Time Nudges**: GPT-powered motivational messages during distractions
- **Post-Session Analysis**: Comprehensive AI-generated feedback
- **Personalized Recommendations**: Tailored tips based on session performance
- **Graceful Fallback**: Works without API key using rule-based responses

### 6. **Comprehensive Activity Log**
- **Detailed Timeline** of entire study session:
  - Session start/end events
  - App change events (expected vs detected app)
  - Distraction events (with reason and metrics)
  - Screenshot capture events (with trigger)
- **Filterable View**: All, App Changes, Distractions, Screenshots
- **Rich Metadata**: Timestamps, focus scores, stress levels, detected apps

### 7. **Smart Screenshot Capture**
- **Automatic Triggers**:
  - Face disengaged (< 35%)
  - Wrong app detected (< 50% screen focus)
  - High stress (> 60%)
  - App changes to wrong app
- **Dual Capture**: Both screen AND face reaction simultaneously
- **Intelligent Cooldown**: 15-20 second intervals to prevent spam
- **Manual Capture**: 📸 button for marking important moments

### 8. **Post-Session Study Report**
- **Grade System**: A/B/C/D based on average focus
- **Comprehensive Statistics**:
  - Average focus, stress, confidence
  - Total distractions with detailed breakdown
  - Session duration and data points
- **Peak Moments Analysis**: Highest stress and peak focus timestamps
- **Detailed Distraction Log**:
  - Type: Both (Face + Screen), Face Disengagement, Wrong App/Website
  - Face and screen focus percentages
  - Screenshot availability indicator (✅)
- **High Stress Moments**: Timeline of stress spikes
- **AI Coach Analysis**: Personalized insights and recommendations
- **Export Options**: CSV and PDF report generation

### 9. **Screenshot Gallery**
- **Dual Image View**: Screen capture + face reaction side-by-side
- **Detailed Metadata**:
  - Trigger reason (what caused the screenshot)
  - Detected app at time of capture
  - Face focus, screen focus, stress percentages
  - Distraction type classification
- **Filterable Gallery**: Browse all captured moments
- **Full-Screen Detail View**: Examine screenshots closely

### 10. **Session History**
- **Past Sessions List**: All previous study sessions
- **Trend Visualization**: Focus and stress trends over time
- **Session Details**: Goals, AI analysis, and performance metrics
- **Persistent Storage**: LocalStorage-based session management

---

## 🧠 Technology Stack

### Backend
- **FastAPI**: High-performance async web framework
- **WebSockets**: Real-time bidirectional communication
- **OpenCV**: Computer vision and image processing
- **FER (Facial Emotion Recognition)**: Deep learning emotion detection
- **librosa**: Audio feature extraction and analysis
- **sounddevice**: Real-time audio capture
- **Pillow (PIL)**: Image processing for screen analysis
- **pandas**: Data manipulation and analysis
- **ReportLab**: PDF report generation

### Frontend
- **React 18**: Modern UI framework with hooks
- **Vite**: Lightning-fast build tool
- **Recharts**: Data visualization and charts
- **Lucide React**: Beautiful icon library
- **WebSocket API**: Real-time data streaming
- **MediaDevices API**: Camera and screen capture
- **LocalStorage API**: Client-side data persistence

### AI & ML
- **TensorFlow**: Deep learning backend for FER
- **OpenAI GPT-3.5**: AI coach and analysis
- **Custom Fusion Engine**: Multimodal emotion fusion algorithm
- **Visual Pattern Recognition**: OCR-free app detection

---

## 📊 Metrics & Algorithms

### Primary Metrics
- **Stress Level** (0-100%): Combines negative facial emotions (sad, angry, fear) + audio stress
- **Engagement** (0-100%): Positive emotions (happy, surprise) adjusted by stress
- **Confusion** (0-100%): Emotion variance + moderate stress indicator
- **Confidence** (0-100%): Inverse of stress and confusion

### Focus Scoring Algorithm
```
Combined Focus = (Face Engagement × 40%) + (Screen Focus × 60%)

Face Engagement: Based on positive emotions from facial detection
Screen Focus: Based on visual app detection and declared study app match

Thresholds:
- Deep Focus: Face > 65% AND Screen > 80% AND Stress < 35%
- Light Focus: Face > 45% AND Screen > 60%
- Distracted: Face < 35% OR Screen < 50%
```

### Attention State Machine
1. **Deep Focus**: High engagement, low stress, correct app
2. **Light Focus**: Moderate engagement, correct app
3. **Distracted**: Low engagement OR wrong app
4. **Fatigued**: Low confidence, declining engagement
5. **Stressed**: High stress overrides other states
6. **On Break**: Pomodoro break phase
7. **Idle**: No activity detected

---

## 🎮 Usage Guide

### Starting a Study Session

1. **Plan Your Session**
   - Navigate to "Plan Session"
   - Enter subject (e.g., "Java Programming")
   - Select duration (25/45/60 minutes or custom)
   - Choose study mode and break preference
   - Set your goals
   - Click "Start Study Session"

2. **Declare Study App**
   - Enter the app/website you'll study in (e.g., "ChatGPT", "VSCode", "Google Docs")
   - Click "Continue to Screen Share"

3. **Share Your Screen**
   - Select "Entire Screen" (NOT window or tab)
   - Click "Share"
   - System validates full screen share

4. **Monitor Your Focus**
   - Watch real-time focus score (Face 40% + Screen 60%)
   - Receive alerts when distracted
   - Get AI coach nudges for motivation
   - Use Pomodoro timer for breaks

5. **Review Your Session**
   - Stop session when done
   - View comprehensive study report
   - Check activity log for detailed timeline
   - Browse screenshots of distraction moments
   - Export CSV or generate PDF report

### Simulation Mode
- Toggle "Simulation Mode" in sidebar
- Works without camera/microphone
- Generates realistic emotion patterns
- Perfect for testing and demos

---

## 🔧 Configuration

Key settings in `src/config.py`:

```python
# Audio settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_DURATION = 2.0

# Video settings  
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480

# Focus thresholds (STRICT MODE)
FACE_ENGAGEMENT_THRESHOLD = 0.35  # 35%
SCREEN_FOCUS_THRESHOLD = 0.50     # 50%
STRESS_ALERT_THRESHOLD = 0.60     # 60%

# Screenshot capture
SCREENSHOT_COOLDOWN = 20  # seconds
APP_CHANGE_COOLDOWN = 15  # seconds

# Fusion weights
FACE_WEIGHT = 0.4   # 40%
SCREEN_WEIGHT = 0.6 # 60%
```

---

## 🚨 Alerts & Monitoring

### Real-Time Alerts
- **High Stress Alert**: Triggered when stress > 60% for 5+ seconds
- **Face Disengagement**: When facial engagement < 35%
- **Wrong App Alert**: When not in declared study app (screen focus < 50%)
- **Combined Distraction**: Both face and screen show distraction

### Visual Indicators
- **Color-Coded Focus Score**:
  - Green (≥80%): Excellent focus
  - Blue (≥60%): Good focus
  - Orange (≥40%): Moderate focus
  - Red (<40%): Poor focus
- **Attention State Badge**: Shows current state with color coding
- **Real-Time Timeline**: Last 60 seconds of emotion data
- **Stress Gauge**: Visual stress level indicator

---

## 📈 Output Files

### Session Logs
- **Location**: `outputs/session_logs/`
- **Format**: `session_{id}_{timestamp}.csv`
- **Contains**: Timestamp, emotions, stress scores, fused metrics, study states

### PDF Reports
- **Location**: `outputs/reports/`
- **Format**: `emotion_report_{id}_{timestamp}.pdf`
- **Contains**: Session stats, charts, recommendations, peak analysis

### Screenshots
- **Location**: `outputs/screenshots/` (or browser localStorage)
- **Format**: Base64 encoded images
- **Types**: 
  - Auto-captured (distraction/stress moments)
  - Manual captures (user-triggered)
  - Dual images (screen + face)

### Activity Log
- **Storage**: Browser localStorage (`emotisense_activity_log`)
- **Format**: JSON array of activity events
- **Retention**: Last 200 activities

---

## 🔄 Fallback Mechanisms

1. **Camera Failure**: Uses simulated face emotions with realistic patterns
2. **Microphone Failure**: Generates stress scores based on last known values
3. **Screen Share Failure**: Automatic retry with instructions
4. **OCR Unavailable**: Visual pattern recognition without text extraction
5. **AI API Failure**: Rule-based fallback responses
6. **Complete Simulation**: Toggle for full demo mode without hardware

---

## 🎯 Key Innovations

### 1. **Dual Focus System**
- First study analyzer to combine facial engagement AND screen activity
- Screen weighted higher (60%) for objectivity
- Prevents gaming the system by just looking at camera

### 2. **Entire Screen Enforcement**
- Validates full screen share (not window/tab)
- Auto-retry on wrong selection
- Ensures comprehensive monitoring

### 3. **OCR-Free App Detection**
- Works without Tesseract installation
- Visual pattern recognition using colors and brightness
- Faster and more reliable than text-based OCR

### 4. **Comprehensive Activity Log**
- Every app change tracked with timestamps
- Distraction events with detailed reasons
- Screenshot triggers documented
- Complete audit trail of study session

### 5. **Dual Screenshot Capture**
- Captures BOTH screen and face simultaneously
- Shows what you were doing AND your reaction
- Provides complete context for distractions

### 6. **Intelligent Screenshot Triggers**
- Multiple trigger conditions (face, screen, stress, app change)
- Smart cooldown to prevent spam
- Captures critical moments automatically

### 7. **Persistent Session State**
- Timer persists across page navigation
- Screen share stream maintained
- Auto-redirect to focus monitor during active session

---

## 🐛 Troubleshooting

### Camera not working
- Enable "Simulation Mode" in sidebar
- Check camera permissions in browser
- Ensure no other applications are using the camera

### Microphone not detected
- Application automatically falls back to simulated audio
- Check microphone permissions
- Verify microphone is not muted

### Screen share issues
- Must select "Entire Screen" (not window/tab)
- Look for "Entire Screen" or "Screen" tab in picker
- System will auto-retry if wrong selection detected

### Backend connection failed
```bash
# Ensure backend is running
uvicorn backend.server:app --reload --port 8000

# Check if port 8000 is available
netstat -ano | findstr :8000
```

### Frontend not loading
```bash
# Ensure frontend is running
cd frontend
npm run dev

# Check if port 5173 is available
```

---

## 📝 Requirements

### Python Dependencies
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
opencv-python>=4.8.0
fer>=22.5.0
librosa>=0.10.0
sounddevice>=0.4.6
numpy>=1.24.0
pandas>=2.0.0
pillow>=10.0.0
reportlab>=4.0.0
python-multipart>=0.0.6
openai>=1.0.0
```

### Node Dependencies
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "recharts": "^2.10.0",
  "lucide-react": "^0.294.0"
}
```

---

## 🚀 Deployment

### Local Development
```bash
# Backend
uvicorn backend.server:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

### Production Build
```bash
# Frontend
cd frontend
npm run build
# Serve dist/ folder with nginx or similar

# Backend
uvicorn backend.server:app --host 0.0.0.0 --port 8000
```

---

## 🎓 Use Cases

- **Students**: Track focus during study sessions, identify distraction patterns
- **Remote Workers**: Monitor productivity and maintain focus
- **Researchers**: Analyze attention patterns and cognitive load
- **Educators**: Understand student engagement in online learning
- **Self-Improvement**: Build better study habits with data-driven insights

---

## 🔒 Privacy & Data

- **All processing happens locally** - no data sent to external servers (except optional AI coach)
- **Camera feed never stored** - only analyzed in real-time
- **Screenshots stored locally** - in browser localStorage
- **Session data exportable** - full control over your data
- **Optional AI features** - can be disabled completely

---

## 📊 Performance

- **Real-time processing**: 1 FPS emotion detection
- **Low latency**: <100ms WebSocket updates
- **Efficient**: Runs on standard laptop hardware
- **Scalable**: Handles 3+ hour study sessions
- **Responsive**: React-based UI with smooth animations

---

## 🎨 UI/UX Features

- **Modern Design**: Clean, professional interface with gradients and shadows
- **Dark Theme**: Easy on the eyes for long study sessions
- **Responsive Layout**: Works on different screen sizes
- **Smooth Animations**: Fade-ins, transitions, hover effects
- **Intuitive Navigation**: Clear sidebar with icons
- **Real-Time Updates**: Live data streaming without page refresh
- **Visual Feedback**: Color-coded metrics and alerts

---

## 🏆 Achievements

- ✅ **Multimodal Fusion**: Combines face, audio, and screen data
- ✅ **Real-Time Processing**: Sub-second latency
- ✅ **Comprehensive Logging**: Every event tracked
- ✅ **Smart Automation**: Automatic screenshot capture
- ✅ **AI Integration**: GPT-powered insights
- ✅ **Production Ready**: Robust error handling and fallbacks
- ✅ **User Friendly**: One-command setup and intuitive UI

---

## 📄 License

This project is open source and available under the MIT License.

---

## 👨‍💻 Author

**Danish M**  
B.Tech Artificial Intelligence and Data Science  
SRM Institute of Science and Technology

**Project**: EMOTISENSE AI - Advanced Study Session Analyzer  
**Built with**: React, FastAPI, TensorFlow, OpenAI GPT

---

## 🙏 Acknowledgments

- **FER Library**: Facial emotion recognition
- **OpenAI**: GPT-3.5 for AI coach
- **React Community**: Amazing ecosystem
- **FastAPI**: Modern Python web framework

---

**Built for students, designed for impact.** 🚀

*Transform your study sessions with AI-powered insights.*
