"""
EMOTISENSE AI — FastAPI Backend
Replaces app.py (Streamlit). Exposes:
  WS  /ws/stream          → live emotion data every second
  POST /session/start      → start a session
  POST /session/stop       → stop session, return summary
  GET  /session/export/csv → download session CSV
  POST /session/export/pdf → generate + download PDF report
  GET  /health             → status check
"""

import asyncio
import json
import os
import time
import warnings
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

warnings.filterwarnings("ignore")

# ── Import your existing src modules ─────────────────────────────────────────
try:
    from src.webcam.camera import CameraCapture
    from src.webcam.face_emotion import FaceEmotionDetector
    from src.audio.mic_capture import MicrophoneCapture
    from src.audio.audio_emotion import AudioEmotionAnalyzer
    from src.fusion.fusion_engine import FusionEngine
    from src.logger.session_logger import SessionLogger
    from src.logger.report_generator import ReportGenerator
    from src.fallback.rule_based import FallbackEmotionGenerator
    from src.config import STRESS_THRESHOLD, ALERT_DURATION
    from src.utils import save_session_data
    MODULES_OK = True
except ImportError as e:
    print(f"[WARN] Could not import src modules: {e}")
    print("[WARN] Running in simulation-only mode.")
    MODULES_OK = False

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="EMOTISENSE AI", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # React dev server (localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singleton component holders ───────────────────────────────────────────────
class AppState:
    def __init__(self):
        self.camera          = None
        self.face_detector   = None
        self.mic_capture     = None
        self.audio_analyzer  = None
        self.fusion_engine   = None
        self.session_logger  = None
        self.report_gen      = None
        self.fallback        = None
        self.session_active  = False
        self.simulation_mode = False
        # Smoothing buffers
        self.face_buffer: list[dict] = []   # last N emotion dicts
        self.stress_buffer: list[float] = []
        self.SMOOTH_N = 5                   # frames to average
        # Study session
        self.current_plan: dict = {}
        self.screen_focus: int  = 65        # last screen focus score
        self.study_state_history: list[str] = []

state = AppState()


def init_components():
    """Lazy-init all ML components once."""
    if not MODULES_OK:
        state.simulation_mode = True
        state.fallback = _FallbackStub()
        return
    if state.face_detector is None:
        state.camera         = CameraCapture()
        state.face_detector  = FaceEmotionDetector()
        state.mic_capture    = MicrophoneCapture()
        state.audio_analyzer = AudioEmotionAnalyzer()
        state.fusion_engine  = FusionEngine()
        state.report_gen     = ReportGenerator()
        state.fallback       = FallbackEmotionGenerator()


# ── Fallback stub when src/ is unavailable ────────────────────────────────────
class _FallbackStub:
    def generate_face_emotions(self):
        import random, math
        t = time.time()
        h = max(0, 0.35 + 0.25 * math.sin(t * 0.3))
        n = max(0, 0.25 + 0.1  * math.cos(t * 0.5))
        s = max(0, 0.12 + 0.1  * math.sin(t * 0.7))
        total = h + n + s + 0.05 + 0.05 + 0.18
        return {
            "happy":    round(h / total, 3),
            "neutral":  round(n / total, 3),
            "sad":      round(s / total, 3),
            "angry":    round(0.05 / total, 3),
            "fear":     round(0.05 / total, 3),
            "surprise": round(0.18 / total, 3),
        }
    def generate_audio_stress(self):
        import math
        t = time.time()
        return round(max(0, min(1, 0.3 + 0.2 * math.sin(t * 0.4))), 3)


# ── Smoothing helpers ─────────────────────────────────────────────────────────
def smooth_emotions(emotions: dict) -> dict:
    """Average last N face emotion dicts to reduce flickering."""
    state.face_buffer.append(emotions)
    if len(state.face_buffer) > state.SMOOTH_N:
        state.face_buffer.pop(0)
    keys = list(emotions.keys())
    smoothed = {}
    for k in keys:
        smoothed[k] = round(
            sum(b.get(k, 0) for b in state.face_buffer) / len(state.face_buffer), 3
        )
    return smoothed


def smooth_stress(score: float) -> float:
    """Exponential moving average for stress."""
    state.stress_buffer.append(score)
    if len(state.stress_buffer) > state.SMOOTH_N:
        state.stress_buffer.pop(0)
    return round(sum(state.stress_buffer) / len(state.stress_buffer), 3)


# ── Session logger stub (when src missing) ────────────────────────────────────
class _SessionLoggerStub:
    def __init__(self):
        self.session_id = f"SIM_{int(time.time())}"
        self.records: list[dict] = []
        self.screenshots: list = []
        self.start_time = None

    def start_session(self):
        self.start_time = datetime.now()
        self.records.clear()

    def stop_session(self):
        import pandas as pd
        return pd.DataFrame(self.records)

    def log_data(self, face_emotions, audio_stress, fused):
        self.records.append({
            "timestamp":  datetime.now().isoformat(),
            "stress":     fused.get("stress", 0),
            "engagement": fused.get("engagement", 0),
            "confidence": fused.get("confidence", 0),
            "confusion":  fused.get("confusion", 0),
            "dominant_state": fused.get("dominant_state", "neutral"),
            **{f"face_{k}": v for k, v in face_emotions.items()},
            "audio_stress": audio_stress,
        })

    def get_session_dataframe(self):
        import pandas as pd
        return pd.DataFrame(self.records)

    def get_session_stats(self):
        df = self.get_session_dataframe()
        if df.empty:
            return {}
        dur = (datetime.now() - self.start_time).seconds if self.start_time else 0
        return {
            "session_id":     self.session_id,
            "duration":       f"{dur // 60}m {dur % 60}s",
            "total_records":  len(df),
            "avg_stress":     round(df["stress"].mean(), 3),
            "avg_engagement": round(df["engagement"].mean(), 3),
            "avg_confidence": round(df["confidence"].mean(), 3),
            "peak_stress":    round(df["stress"].max(), 3),
            "dominant_states": df["dominant_state"].value_counts().to_dict(),
        }


# ── Study-specific state machine ─────────────────────────────────────────────
def compute_study_state(fused: dict, screen_focus: int, on_break: bool = False) -> str:
    """
    Determines study state based on facial emotions AND screen activity.
    Screen focus is weighted heavily since it's objective.
    STRICT MODE: Both face AND screen must be good for focus states.
    """
    if on_break:
        return 'On Break'
    
    stress     = fused.get('stress',     0)
    engagement = fused.get('engagement', 0)
    confidence = fused.get('confidence', 0)
    
    # Combined focus: face (40%) + screen (60%)
    face_focus = engagement * 100
    combined_focus = face_focus * 0.4 + screen_focus * 0.6 if screen_focus else face_focus
    
    # STRICT: If no face detected or very low engagement, mark as distracted immediately
    if engagement < 0.15:
        return 'Distracted'
    
    # Idle state - no activity at all
    if engagement < 0.1 and stress < 0.1:
        return 'Idle'
    
    # High stress overrides everything
    if stress > 0.65:
        return 'Stressed'
    
    # STRICT: Screen shows distraction (most important signal)
    if screen_focus < 50:  # Raised from 35 to 50
        return 'Distracted'
    
    # STRICT: Face shows disengagement (raised threshold)
    if engagement < 0.35:  # Raised from 0.25 to 0.35
        return 'Distracted'
    
    # Low confidence = fatigue
    if confidence < 0.3:
        return 'Fatigued'
    
    # STRICT: Deep focus requires BOTH face AND screen to be excellent
    if engagement > 0.65 and stress < 0.35 and screen_focus >= 80:  # Raised from 0.55/0.4/70
        return 'Deep Focus'
    
    # STRICT: Light focus requires decent performance on both
    if engagement > 0.45 and screen_focus >= 60:  # Added screen requirement
        return 'Light Focus'
    
    return 'Distracted'


# ── Core emotion tick (called every ~1 second) ────────────────────────────────
def emotion_tick() -> dict:
    """
    Run one cycle of face + audio emotion detection.
    Returns a JSON-serialisable dict ready to send to the browser.
    """
    sim = state.simulation_mode or not MODULES_OK

    # ── Face emotions ─────────────────────────────────────────────────────────
    frame_b64 = None
    if sim:
        face_emotions = state.fallback.generate_face_emotions()
    else:
        frame = state.camera.get_frame() if state.camera.is_active else None
        if frame is not None and state.face_detector.is_available:
            result = state.face_detector.detect_emotions(frame)
            if isinstance(result, dict) and "probs" in result:
                face_emotions = result["probs"]
                frame = state.face_detector.draw_emotion_box(frame, result)
            else:
                face_emotions = state.fallback.generate_face_emotions()
            # Encode frame as JPEG base64 for browser
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            import base64
            frame_b64 = base64.b64encode(buf).decode("utf-8")
        else:
            face_emotions = state.fallback.generate_face_emotions()

    face_emotions = smooth_emotions(face_emotions)

    # ── Audio stress ──────────────────────────────────────────────────────────
    if sim:
        audio_stress = state.fallback.generate_audio_stress()
    else:
        audio_data   = state.mic_capture.capture_audio_chunk()
        audio_stress = state.audio_analyzer.analyze_stress(audio_data)

    audio_stress = smooth_stress(audio_stress)

    # ── Fusion ────────────────────────────────────────────────────────────────
    if sim or state.fusion_engine is None:
        # Simple inline fusion when src unavailable
        neg = face_emotions.get("sad", 0) + face_emotions.get("angry", 0) + face_emotions.get("fear", 0)
        pos = face_emotions.get("happy", 0) + face_emotions.get("surprise", 0)
        stress     = round(0.6 * (neg * 0.8 + audio_stress * 0.2) + 0.4 * audio_stress, 3)
        engagement = round(max(0, pos - stress * 0.3), 3)
        confusion  = round(min(1, face_emotions.get("fear", 0) + face_emotions.get("sad", 0) * 0.5), 3)
        confidence = round(max(0, 1 - stress - confusion * 0.5), 3)
        if stress > 0.65:   dominant = "stressed"
        elif engagement > 0.5: dominant = "engaged"
        elif pos > 0.4:    dominant = "positive"
        else:               dominant = "neutral"
        fused = {
            "stress": stress, "engagement": engagement,
            "confusion": confusion, "confidence": confidence,
            "dominant_state": dominant,
        }
    else:
        fused = state.fusion_engine.fuse_emotions(face_emotions, audio_stress)

    # ── Log ───────────────────────────────────────────────────────────────────
    if state.session_active and state.session_logger:
        state.session_logger.log_data(face_emotions, audio_stress, fused)

    # ── Alert flag ────────────────────────────────────────────────────────────
    df = state.session_logger.get_session_dataframe() if state.session_logger else None
    alert = False
    if df is not None and not df.empty and len(df) >= ALERT_DURATION:
        recent = df["stress"].tail(ALERT_DURATION)
        alert  = bool((recent > STRESS_THRESHOLD).all())

    study_state = compute_study_state(fused, state.screen_focus)
    state.study_state_history.append(study_state)

    return {
        "ts":           datetime.now().isoformat(),
        "face":         face_emotions,
        "audio_stress": audio_stress,
        "fused":        fused,
        "alert":        alert,
        "frame":        frame_b64,
        "simulation":   sim,
        "study_state":  study_state,
        "screen_focus": state.screen_focus,
    }


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status":       "ok",
        "session":      state.session_active,
        "simulation":   state.simulation_mode,
        "modules":      MODULES_OK,
    }


# ── Study endpoints ───────────────────────────────────────────────────────────

class StudyPlan(BaseModel):
    subject:      str  = ''
    duration:     str  = '45 min'
    durationMins: int  = 45
    mode:         str  = 'Deep Focus'
    breakPref:    str  = 'Pomodoro 25/5'
    goals:        str  = ''


@app.post("/study/plan")
def save_plan(plan: StudyPlan):
    state.current_plan = plan.dict()
    return {"ok": True}


@app.post("/study/screen")
async def analyse_screen(screenshot: UploadFile = File(...), study_app: str = ''):
    from backend.screen_analyser import analyse_screenshot
    data   = await screenshot.read()
    
    # Get the app user should be studying in
    if not study_app:
        study_app = state.current_plan.get('subject', '')
    
    result = analyse_screenshot(data, study_app)
    state.screen_focus = result['focus_score']
    
    # Add current stress level from emotion data
    if state.session_logger:
        df = state.session_logger.get_session_dataframe()
        if not df.empty:
            result['stress_level'] = int(df['stress'].iloc[-1] * 100) if 'stress' in df.columns else 0
        else:
            result['stress_level'] = 0
    else:
        result['stress_level'] = 0
    
    return result


@app.get("/study/coach/nudge")
def coach_nudge(subject: str = '', state_name: str = 'Distracted'):
    msg = _claude_nudge(subject, state_name)
    return {"message": msg}


class ReportRequest(BaseModel):
    plan:  dict = {}
    stats: dict = {}


@app.post("/study/coach/report")
def coach_report(req: ReportRequest):
    report = _claude_report(req.plan, req.stats)
    return {"report": report}


@app.get("/study/history")
def study_history():
    """Returns session list from outputs/session_logs/."""
    logs_dir = Path("outputs/session_logs")
    files    = sorted(logs_dir.glob("*.csv"), reverse=True) if logs_dir.exists() else []
    return {"sessions": [f.stem for f in files[:50]]}


@app.get("/study/history/{session_id}")
def study_history_detail(session_id: str):
    import pandas as pd
    path = Path(f"outputs/session_logs/{session_id}.csv")
    if not path.exists():
        return JSONResponse({"error": "Not found"}, status_code=404)
    df = pd.read_csv(path)
    return {"session_id": session_id, "records": df.to_dict(orient='records')}


# ── GPT helpers (graceful fallback if no API key) ────────────────────────────

def _claude_nudge(subject: str, study_state: str) -> str:
    """Uses OpenAI GPT for study nudges."""
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        return _fallback_nudge(study_state, subject)
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        prompt = (
            f"You are a concise study coach. The student is studying '{subject}' "
            f"and their current state is '{study_state}'. "
            "Give ONE short motivational nudge (max 2 sentences) to help them refocus."
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _fallback_nudge(study_state, subject)


def _claude_report(plan: dict, stats: dict) -> str:
    """Uses OpenAI GPT for post-session report."""
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        return _fallback_report(plan, stats)
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        prompt = (
            f"You are an expert study coach. Analyse this study session and give personalised feedback.\n"
            f"Subject: {plan.get('subject','Unknown')}\n"
            f"Mode: {plan.get('mode','—')}\n"
            f"Goals: {plan.get('goals','—')}\n"
            f"Duration: {plan.get('duration','—')}\n"
            f"Avg Focus: {round(stats.get('avg_engagement',0)*100)}%\n"
            f"Avg Stress: {round(stats.get('avg_stress',0)*100)}%\n"
            f"Distractions: {stats.get('distractions',0)}\n\n"
            "Write 3-4 sentences: what went well, what to improve, one specific tip for next session."
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _fallback_report(plan, stats)


def _fallback_nudge(study_state: str, subject: str) -> str:
    tips = {
        'Distracted': f"You seem distracted — close other tabs and return to {subject or 'your task'}.",
        'Stressed':   "Take 3 deep breaths, then continue. You've got this.",
        'Fatigued':   "You look tired — splash water on your face or do 10 jumping jacks.",
        'Idle':       "Ready to continue? Set a small goal for the next 10 minutes.",
    }
    return tips.get(study_state, "Stay focused — every minute counts!")


def _fallback_report(plan: dict, stats: dict) -> str:
    focus = round(stats.get('avg_engagement', 0) * 100)
    stress = round(stats.get('avg_stress', 0) * 100)
    subject = plan.get('subject', 'your subject')
    tip = "Try shorter Pomodoro sessions" if focus < 50 else "Keep up the great work"
    return (
        f"You studied {subject} with an average focus of {focus}% and stress of {stress}%. "
        f"{'Your focus was strong — well done!' if focus >= 65 else 'There were some focus dips during the session.'} "
        f"{tip} and review your distraction log to identify patterns."
    )


@app.post("/session/start")
def session_start(body: dict = {}):
    init_components()
    sim = body.get("simulation", False)
    state.simulation_mode = sim
    if body.get('plan'):
        state.current_plan = body['plan']
    state.screen_focus = 65
    state.study_state_history.clear()

    if MODULES_OK:
        state.session_logger = SessionLogger()
    else:
        state.session_logger = _SessionLoggerStub()

    state.session_logger.start_session()

    if not sim and MODULES_OK:
        ok = state.camera.start()
        if not ok:
            state.simulation_mode = True

    state.session_active = True
    state.face_buffer.clear()
    state.stress_buffer.clear()

    return {"ok": True, "session_id": state.session_logger.session_id, "simulation": state.simulation_mode}


@app.post("/session/stop")
def session_stop():
    state.session_active = False
    if MODULES_OK and state.camera:
        state.camera.stop()

    if not state.session_logger:
        return {"ok": False, "error": "No active session"}

    df    = state.session_logger.stop_session()
    stats = state.session_logger.get_session_stats()

    if not df.empty and MODULES_OK:
        try:
            save_session_data(df, state.session_logger.session_id)
        except Exception:
            pass

    return {"ok": True, "stats": stats}


@app.get("/session/export/csv")
def export_csv():
    if not state.session_logger:
        return JSONResponse({"error": "No session data"}, status_code=404)
    df = state.session_logger.get_session_dataframe()
    if df.empty:
        return JSONResponse({"error": "Empty session"}, status_code=404)
    path = Path(f"outputs/session_logs/session_{state.session_logger.session_id}.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return FileResponse(path, media_type="text/csv", filename=path.name)


@app.post("/session/export/pdf")
def export_pdf():
    if not state.session_logger or not MODULES_OK:
        return JSONResponse({"error": "PDF unavailable"}, status_code=404)
    try:
        stats = state.session_logger.get_session_stats()
        df    = state.session_logger.get_session_dataframe()
        path  = state.report_gen.generate_pdf_report(stats, df)
        return FileResponse(path, media_type="application/pdf", filename=Path(path).name)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/session/stats")
def session_stats():
    if not state.session_logger:
        return JSONResponse({"error": "No session"}, status_code=404)
    return state.session_logger.get_session_stats()


# ── WebSocket live stream ─────────────────────────────────────────────────────

@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Client connected")
    try:
        while True:
            if state.session_active:
                try:
                    data = emotion_tick()
                    await websocket.send_text(json.dumps(data))
                except Exception as e:
                    print(f"[WS] tick error: {e}")
                    traceback.print_exc()
            else:
                # Send a heartbeat so client knows server is alive
                await websocket.send_text(json.dumps({"status": "idle"}))

            await asyncio.sleep(1.0)          # 1 fps — plenty for emotion monitoring

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Unexpected error: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)