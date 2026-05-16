"""
src/webcam/face_emotion.py  —  EMOTISENSE AI v2
================================================
Three-model ensemble face emotion detector.

Pipeline per frame
------------------
1. MediaPipe  →  face-presence guard (skip if no face detected)
2. FER        →  fast primary detection (every frame)
3. DeepFace   →  accurate secondary   (every 3rd frame, skipped if >800 ms)
4. Ensemble   →  weighted merge of available results
5. Confidence →  discard frame if top-emotion prob < MIN_CONFIDENCE
6. EWA buffer →  exponential weighted average over last BUFFER_SIZE results

Emotion keys (always 6):
    happy, sad, angry, fear, surprise, neutral
"""

import time
import warnings
import logging
from collections import deque

import cv2
import numpy as np

warnings.filterwarnings("ignore")
logging.getLogger("tensorflow").setLevel(logging.ERROR)
logging.getLogger("absl").setLevel(logging.ERROR)

# ── Constants ──────────────────────────────────────────────────────────────────
EMOTIONS        = ["happy", "sad", "angry", "fear", "surprise", "neutral"]
BUFFER_SIZE     = 7          # EWA window
EWA_DECAY       = 0.75       # weight of the newest frame vs older ones
MIN_CONFIDENCE  = 0.38       # discard detections below this top-emotion prob
DEEPFACE_EVERY  = 3          # run DeepFace every N frames
DEEPFACE_TIMEOUT= 0.85       # seconds — skip DeepFace if last call was slower

# Ensemble weights  (must sum to 1.0 when all models available)
W_FER       = 0.40
W_DEEPFACE  = 0.45
W_MEDIAPIPE = 0.15           # landmark heuristic (low weight — rough signal)

# DeepFace emotion key mapping → our 6-key schema
_DF_MAP = {
    "happy":    "happy",
    "sad":      "sad",
    "angry":    "angry",
    "fear":     "fear",
    "disgust":  "angry",     # fold disgust into angry
    "surprise": "surprise",
    "neutral":  "neutral",
}

# FER emotion key mapping
_FER_MAP = {
    "happy":   "happy",
    "sad":     "sad",
    "angry":   "angry",
    "fear":    "fear",
    "surprise":"surprise",
    "neutral": "neutral",
    "disgust": "angry",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _zero_emotions() -> dict:
    return {e: 0.0 for e in EMOTIONS}


def _normalize(d: dict) -> dict:
    """Normalize a dict of floats to sum=1, return 6-key schema."""
    out   = _zero_emotions()
    total = sum(d.values())
    if total <= 0:
        out["neutral"] = 1.0
        return out
    for k, v in d.items():
        key = _FER_MAP.get(k) or _DF_MAP.get(k)
        if key:
            out[key] = out.get(key, 0.0) + v / total
    # re-normalize in case of key collisions (disgust → angry)
    total2 = sum(out.values())
    if total2 > 0:
        out = {k: round(v / total2, 4) for k, v in out.items()}
    return out


def _ewa_merge(buffer: deque) -> dict:
    """
    Exponential weighted average over the buffer.
    Newest entry has highest weight.
    """
    if not buffer:
        r = _zero_emotions(); r["neutral"] = 1.0; return r

    weights = [EWA_DECAY ** i for i in range(len(buffer))]
    # buffer[-1] is newest → index 0 in reversed list gets highest weight
    items   = list(reversed(buffer))   # newest first
    total_w = sum(weights[:len(items)])

    out = _zero_emotions()
    for w, frame_result in zip(weights, items):
        for emotion in EMOTIONS:
            out[emotion] += w * frame_result.get(emotion, 0.0)

    return {k: round(v / total_w, 4) for k, v in out.items()}


def _blend(results: list[tuple[dict, float]]) -> dict:
    """
    Blend multiple (emotion_dict, weight) pairs into one normalized dict.
    """
    out     = _zero_emotions()
    total_w = sum(w for _, w in results)
    if total_w <= 0:
        out["neutral"] = 1.0
        return out
    for d, w in results:
        for e in EMOTIONS:
            out[e] += d.get(e, 0.0) * w / total_w
    return {k: round(v, 4) for k, v in out.items()}


# ── MediaPipe heuristic ────────────────────────────────────────────────────────

class _MediaPipeHelper:
    """
    Uses MediaPipe Face Mesh for two jobs:
      1. Face-presence guard  (is there a face in the frame?)
      2. Rough landmark-based emotion heuristic (low accuracy but fast)
    """
    def __init__(self):
        self.available = False
        self.mp_face   = None
        self.detector  = None
        self._init()

    def _init(self):
        try:
            import mediapipe as mp
            self.mp_face  = mp.solutions.face_mesh
            self.detector = self.mp_face.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.available = True
            print("[FaceEmotion] MediaPipe FaceMesh loaded ✓")
        except Exception as e:
            print(f"[FaceEmotion] MediaPipe unavailable: {e}")

    def detect(self, frame_rgb: np.ndarray) -> tuple[bool, dict | None]:
        """
        Returns (face_present, emotion_heuristic_or_None).
        emotion_heuristic is a rough normalized dict — only used with low weight.
        """
        if not self.available or self.detector is None:
            return True, None   # assume face present if MP unavailable

        try:
            result = self.detector.process(frame_rgb)
            if not result.multi_face_landmarks:
                return False, None

            lm  = result.multi_face_landmarks[0].landmark
            h, w = frame_rgb.shape[:2]

            # ── Very rough heuristics from landmark geometry ──────────────
            # Mouth openness  →  happiness proxy
            upper_lip = lm[13].y * h
            lower_lip = lm[14].y * h
            mouth_gap = abs(lower_lip - upper_lip)

            # Eyebrow raise  →  surprise proxy
            left_brow  = lm[70].y  * h
            left_eye   = lm[159].y * h
            brow_raise = max(0.0, (left_eye - left_brow) / (h * 0.05 + 1e-6))

            # Eye openness  →  wide = surprise/fear, narrow = neutral/sad
            eye_top    = lm[159].y * h
            eye_bot    = lm[145].y * h
            eye_open   = abs(eye_bot - eye_top) / (h * 0.03 + 1e-6)

            mouth_norm  = min(1.0, mouth_gap / (h * 0.04 + 1e-6))
            brow_norm   = min(1.0, brow_raise / 3.0)
            eye_norm    = min(1.0, eye_open   / 3.0)

            happy    = mouth_norm * 0.8
            surprise = brow_norm  * 0.6 + eye_norm * 0.4
            neutral  = max(0.0, 1.0 - happy * 0.6 - surprise * 0.4)
            sad      = max(0.0, (1.0 - mouth_norm) * 0.3)
            fear     = max(0.0, eye_norm * 0.3 - happy * 0.2)
            angry    = 0.05

            raw = {"happy": happy, "neutral": neutral, "sad": sad,
                   "fear": fear, "surprise": surprise, "angry": angry}
            return True, _normalize(raw)

        except Exception:
            return True, None    # don't crash — assume face present


# ── FER wrapper ────────────────────────────────────────────────────────────────

class _FERHelper:
    def __init__(self):
        self.available = False
        self.detector  = None
        self._init()

    def _init(self):
        try:
            from fer import FER
            self.detector  = FER(mtcnn=True)
            self.available = True
            print("[FaceEmotion] FER (MTCNN) loaded ✓")
        except Exception as e:
            print(f"[FaceEmotion] FER unavailable: {e}")
            try:
                from fer import FER
                self.detector  = FER(mtcnn=False)
                self.available = True
                print("[FaceEmotion] FER (Haar fallback) loaded ✓")
            except Exception as e2:
                print(f"[FaceEmotion] FER completely unavailable: {e2}")

    def detect(self, frame_bgr: np.ndarray) -> dict | None:
        if not self.available or self.detector is None:
            return None
        try:
            results = self.detector.detect_emotions(frame_bgr)
            if not results:
                return None
            # Use the largest detected face
            best = max(results, key=lambda r: r["box"][2] * r["box"][3])
            return _normalize(best["emotions"])
        except Exception as e:
            print(f"[FaceEmotion] FER detect error: {e}")
            return None


# ── DeepFace wrapper ───────────────────────────────────────────────────────────

class _DeepFaceHelper:
    def __init__(self):
        self.available   = False
        self.last_ms     = 0.0
        self._init()

    def _init(self):
        try:
            from deepface import DeepFace   # noqa — just test import
            self.available = True
            print("[FaceEmotion] DeepFace loaded ✓")
        except Exception as e:
            print(f"[FaceEmotion] DeepFace unavailable: {e}")

    def detect(self, frame_bgr: np.ndarray) -> dict | None:
        if not self.available:
            return None
        # Skip if last call was too slow
        if self.last_ms > DEEPFACE_TIMEOUT:
            return None
        try:
            from deepface import DeepFace
            t0  = time.perf_counter()
            res = DeepFace.analyze(
                frame_bgr,
                actions=["emotion"],
                detector_backend="opencv",   # fast backend
                enforce_detection=False,
                silent=True,
            )
            self.last_ms = time.perf_counter() - t0

            # res is list or dict depending on version
            item = res[0] if isinstance(res, list) else res
            raw  = item.get("emotion", {})
            # DeepFace returns percentages — convert to 0–1
            total = sum(raw.values()) or 1.0
            normed = {k: v / total for k, v in raw.items()}
            return _normalize(normed)

        except Exception as e:
            print(f"[FaceEmotion] DeepFace detect error: {e}")
            self.last_ms = DEEPFACE_TIMEOUT + 0.1   # back-off
            return None


# ── Main detector ──────────────────────────────────────────────────────────────

class FaceEmotionDetector:
    """
    Drop-in replacement for the old FaceEmotionDetector.
    Public API (identical to v1):
        .is_available       → bool
        .detect_emotions(frame_bgr) → {"probs": {...}, "box": [...]}
        .draw_emotion_box(frame_bgr, result) → annotated frame
    """

    def __init__(self):
        print("[FaceEmotion] Initialising ensemble detector…")
        self._mp  = _MediaPipeHelper()
        self._fer = _FERHelper()
        self._df  = _DeepFaceHelper()

        self.is_available = self._fer.available or self._df.available

        # State
        self._buffer:       deque       = deque(maxlen=BUFFER_SIZE)
        self._last_valid:   dict | None = None
        self._frame_count:  int         = 0
        self._last_box:     list        = [0, 0, 100, 100]

        print(
            f"[FaceEmotion] Ready — "
            f"FER={'✓' if self._fer.available else '✗'}  "
            f"DeepFace={'✓' if self._df.available else '✗'}  "
            f"MediaPipe={'✓' if self._mp.available else '✗'}"
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def detect_emotions(self, frame_bgr: np.ndarray) -> dict:
        """
        Returns:
            {
                "probs": {"happy": 0.xx, "sad": 0.xx, ...},   # 6 emotions, sum≈1
                "box":   [x, y, w, h],                         # face bounding box
                "model": "ensemble|fer|deepface|fallback",      # which model(s) fired
                "confidence": 0.xx                             # top-emotion prob
            }
        """
        self._frame_count += 1

        # ── 1. Face-presence guard ────────────────────────────────────────────
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        face_present, mp_emotions = self._mp.detect(frame_rgb)

        if not face_present:
            # No face → return neutral, do not pollute buffer
            result = _zero_emotions(); result["neutral"] = 1.0
            return {"probs": result, "box": self._last_box,
                    "model": "no_face", "confidence": 1.0}

        # ── 2. FER (every frame) ──────────────────────────────────────────────
        fer_result = self._fer.detect(frame_bgr)

        # ── 3. DeepFace (every DEEPFACE_EVERY frames) ────────────────────────
        df_result = None
        if self._frame_count % DEEPFACE_EVERY == 0:
            df_result = self._df.detect(frame_bgr)

        # ── 4. Ensemble blend ─────────────────────────────────────────────────
        sources = []
        if fer_result:
            sources.append((fer_result, W_FER))
        if df_result:
            sources.append((df_result, W_DEEPFACE))
        if mp_emotions:
            sources.append((mp_emotions, W_MEDIAPIPE))

        if not sources:
            # All models failed — reuse last valid or neutral
            if self._last_valid:
                return {**self._last_valid, "model": "cached"}
            fallback = _zero_emotions(); fallback["neutral"] = 1.0
            return {"probs": fallback, "box": self._last_box,
                    "model": "fallback", "confidence": 0.0}

        blended = _blend(sources)
        model_tag = "+".join(
            (["fer"] if fer_result else []) +
            (["deepface"] if df_result else []) +
            (["mp"] if mp_emotions else [])
        )

        # ── 5. Confidence gate ────────────────────────────────────────────────
        top_conf = max(blended.values())
        if top_conf < MIN_CONFIDENCE and self._last_valid:
            # Low-confidence frame — reuse last good result but add to buffer
            blended = self._last_valid["probs"]
            model_tag = "low_conf→cached"

        # ── 6. EWA buffer smoothing ───────────────────────────────────────────
        self._buffer.append(blended)
        smoothed = _ewa_merge(self._buffer)

        # Extract face box from FER if available
        if self._fer.available and self._fer.detector:
            try:
                raw = self._fer.detector.detect_emotions(frame_bgr)
                if raw:
                    self._last_box = raw[0]["box"]
            except Exception:
                pass

        result = {
            "probs":      smoothed,
            "box":        self._last_box,
            "model":      model_tag,
            "confidence": round(top_conf, 3),
        }
        self._last_valid = result
        return result

    # ── Frame annotation ───────────────────────────────────────────────────────

    def draw_emotion_box(self, frame_bgr: np.ndarray, result: dict) -> np.ndarray:
        """
        Draw a clean bounding box + top-emotion label on the frame.
        Returns annotated frame (does not modify in place).
        """
        out   = frame_bgr.copy()
        probs = result.get("probs", {})
        box   = result.get("box",   [0, 0, 100, 100])
        model = result.get("model", "")
        conf  = result.get("confidence", 0.0)

        if not probs:
            return out

        top_emotion = max(probs, key=probs.get)
        top_prob    = probs[top_emotion]

        x, y, w, h = [int(v) for v in box]

        # ── Emotion → colour ──────────────────────────────────────────────────
        COLOR_MAP = {
            "happy":    (34,  197, 94),   # green
            "neutral":  (148, 163, 184),  # slate
            "sad":      (59,  130, 246),  # blue
            "angry":    (220, 38,  38),   # red
            "fear":     (147, 51,  234),  # purple
            "surprise": (234, 179, 8),    # amber
        }
        color = COLOR_MAP.get(top_emotion, (200, 200, 200))

        # ── Box ───────────────────────────────────────────────────────────────
        cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)

        # ── Label background ──────────────────────────────────────────────────
        label     = f"{top_emotion}  {int(top_prob * 100)}%"
        font      = cv2.FONT_HERSHEY_SIMPLEX
        font_scale= 0.55
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        pad = 5
        lx1, ly1 = x, max(0, y - th - pad * 2 - baseline)
        lx2, ly2 = x + tw + pad * 2, y

        cv2.rectangle(out, (lx1, ly1), (lx2, ly2), color, -1)
        cv2.putText(
            out, label,
            (lx1 + pad, ly2 - baseline - 1),
            font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA
        )

        # ── Confidence bar (bottom of box) ────────────────────────────────────
        bar_y  = y + h + 4
        bar_w  = int(w * top_prob)
        cv2.rectangle(out, (x, bar_y), (x + w, bar_y + 4), (50, 50, 50), -1)
        cv2.rectangle(out, (x, bar_y), (x + bar_w, bar_y + 4), color, -1)

        # ── Model tag (small, bottom-right of box) ────────────────────────────
        if model:
            cv2.putText(
                out, model,
                (x, y + h + 22),
                cv2.FONT_HERSHEY_PLAIN, 0.8,
                (180, 180, 180), 1, cv2.LINE_AA
            )

        return out

    # ── Convenience ───────────────────────────────────────────────────────────

    def reset_buffer(self):
        """Call this when starting a new session to clear the EWA buffer."""
        self._buffer.clear()
        self._last_valid  = None
        self._frame_count = 0
        print("[FaceEmotion] Buffer reset.")

    def get_model_info(self) -> dict:
        return {
            "fer":       self._fer.available,
            "deepface":  self._df.available,
            "mediapipe": self._mp.available,
            "buffer_size": BUFFER_SIZE,
            "ewa_decay":   EWA_DECAY,
            "min_confidence": MIN_CONFIDENCE,
        }