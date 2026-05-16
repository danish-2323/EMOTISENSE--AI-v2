"""
src/fusion/fusion_engine.py  —  EMOTISENSE AI v2
=================================================
Dynamic multimodal fusion engine.

Replaces fixed 60/40 face/audio weights with:
  - Signal-quality-aware dynamic weight rebalancing
  - Quality-gated inputs (bad signal → reduced contribution)
  - Proper metric derivation for engagement, confidence, confusion
  - Independent EWA temporal smoothing on all fused outputs
  - 8-state dominant-state machine with confirmation hysteresis

Input
-----
  face_result  : dict   from FaceEmotionDetector.detect_emotions()
                 must contain "probs" (6-emotion dict) and optionally
                 "confidence" (float) and "model" (str)

  audio_result : dict   from AudioEmotionAnalyzer.analyze_stress_detailed()
                 must contain "stress" (float) and optionally
                 "is_speech", "quality", "components"

  OR legacy inputs:
  face_probs   : dict   {"happy": 0.x, ...}   (6 emotions)
  audio_stress : float  (0–1)

Output  (fuse_emotions() return dict)
------
  {
    "stress":         float,   # 0–1
    "engagement":     float,   # 0–1
    "confidence":     float,   # 0–1
    "confusion":      float,   # 0–1
    "dominant_state": str,     # one of 8 states
    "weights":        {"face": float, "audio": float},
    "quality":        {"face": float, "audio": float},
    "smoothed":       bool,
  }
"""

import warnings
from collections import deque

import numpy as np

warnings.filterwarnings("ignore")

# ── Constants ──────────────────────────────────────────────────────────────────

# Base weights (before quality adjustment)
BASE_FACE_W     = 0.58
BASE_AUDIO_W    = 0.42

# Quality gate thresholds
MIN_FACE_CONF   = 0.38    # below → reduce face weight
MIN_AUDIO_QUAL  = 0.15    # below → zero audio contribution

# EWA smoothing
SMOOTH_SIZE     = 5
SMOOTH_DECAY    = 0.70    # weight of newest frame

# Dominant state confirmation
CONFIRM_FRAMES  = 3       # frames a state must persist to be confirmed
HYSTERESIS      = 0.08    # extra margin needed to exit current state

# Metric derivation tuning
ENGAGEMENT_STRESS_PENALTY = 0.45   # how much stress suppresses engagement
CONFUSION_SURPRISE_W      = 0.35
CONFUSION_FEAR_W          = 0.45
CONFUSION_DELTA_W         = 0.20


# ── EWA buffer helper ──────────────────────────────────────────────────────────

class _EWABuffer:
    """Exponential weighted average over a fixed-size deque."""

    def __init__(self, size: int = SMOOTH_SIZE, decay: float = SMOOTH_DECAY):
        self._buf   = deque(maxlen=size)
        self._decay = decay

    def push(self, value: float) -> float:
        self._buf.append(float(value))
        if len(self._buf) == 1:
            return self._buf[0]
        weights = [self._decay ** i for i in range(len(self._buf))]
        items   = list(reversed(self._buf))   # newest first
        total_w = sum(weights[:len(items)])
        smoothed = sum(w * v for w, v in zip(weights, items)) / total_w
        return round(float(smoothed), 4)

    def reset(self):
        self._buf.clear()

    @property
    def mean(self) -> float:
        return float(np.mean(self._buf)) if self._buf else 0.0

    @property
    def ready(self) -> bool:
        return len(self._buf) >= 2


# ── Dominant state machine ─────────────────────────────────────────────────────

STATES = ["calm", "engaged", "stressed", "anxious",
          "confused", "positive", "fatigued", "neutral"]

class _StateMachine:
    """
    8-state machine with confirmation hysteresis.
    A state is only reported after CONFIRM_FRAMES consecutive frames
    predict it.  Exiting a state requires a signal stronger by HYSTERESIS.
    """

    def __init__(self):
        self._current:   str = "neutral"
        self._candidate: str = "neutral"
        self._streak:    int = 0

    def update(self, metrics: dict, face: dict, audio: dict) -> str:
        stress     = metrics["stress"]
        engagement = metrics["engagement"]
        confidence = metrics["confidence"]
        confusion  = metrics["confusion"]

        happy    = face.get("happy",    0.0)
        sad      = face.get("sad",      0.0)
        angry    = face.get("angry",    0.0)
        fear     = face.get("fear",     0.0)
        surprise = face.get("surprise", 0.0)
        neutral  = face.get("neutral",  0.0)
        is_speech = audio.get("is_speech", True)

        # ── Score each state ──────────────────────────────────────────────────
        scores = {}

        # Stressed: high stress, negative face, possibly loud speech
        scores["stressed"] = (
            0.50 * stress +
            0.30 * (sad * 0.4 + angry * 0.6) +
            0.20 * (1.0 - confidence)
        )

        # Anxious: high stress + high fear/confusion
        scores["anxious"] = (
            0.40 * stress +
            0.35 * fear +
            0.25 * confusion
        )

        # Confused: high confusion + low confidence + surprise
        scores["confused"] = (
            0.45 * confusion +
            0.30 * surprise +
            0.25 * (1.0 - confidence)
        )

        # Engaged: high engagement + low stress + moderate speech
        scores["engaged"] = (
            0.50 * engagement +
            0.30 * (1.0 - stress) +
            0.20 * (1.0 if is_speech else 0.3)
        )

        # Positive: happy face + low stress + good confidence
        scores["positive"] = (
            0.50 * happy +
            0.30 * confidence +
            0.20 * (1.0 - stress)
        )

        # Calm: low stress + neutral/happy face + good confidence
        scores["calm"] = (
            0.40 * (1.0 - stress) +
            0.35 * (neutral * 0.6 + happy * 0.4) +
            0.25 * confidence
        )

        # Fatigued: low engagement + low speech + neutral/sad face
        scores["fatigued"] = (
            0.40 * (1.0 - engagement) +
            0.30 * (sad * 0.5 + neutral * 0.5) +
            0.30 * (0.0 if is_speech else 1.0)
        )

        # Neutral: catch-all when nothing is dominant
        scores["neutral"] = (
            0.40 * neutral +
            0.30 * (1.0 - abs(stress - 0.3)) +
            0.30 * (1.0 - abs(engagement - 0.4))
        )

        predicted = max(scores, key=scores.get)

        # ── Hysteresis confirmation ───────────────────────────────────────────
        if predicted == self._candidate:
            self._streak += 1
        else:
            # Check hysteresis: new candidate must beat current by margin
            current_score = scores.get(self._current, 0.0)
            if scores[predicted] > current_score + HYSTERESIS:
                self._candidate = predicted
                self._streak    = 1
            else:
                self._streak = max(0, self._streak - 1)

        if self._streak >= CONFIRM_FRAMES:
            self._current   = self._candidate
            # Don't reset streak — state stays confirmed

        return self._current

    def reset(self):
        self._current   = "neutral"
        self._candidate = "neutral"
        self._streak    = 0


# ── Dynamic weight calculator ──────────────────────────────────────────────────

def _compute_weights(face_conf: float, audio_qual: float, audio_is_speech: bool) -> tuple[float, float]:
    """
    Rebalance face/audio weights based on signal quality.

    Rules
    -----
    - Low face confidence  → reduce face weight, boost audio
    - No speech / low audio quality → zero audio, give all to face
    - Both low             → fall back to base weights (best we can do)
    """
    # Start from base weights
    fw = BASE_FACE_W
    aw = BASE_AUDIO_W

    # Audio quality adjustment
    if not audio_is_speech or audio_qual < MIN_AUDIO_QUAL:
        # Audio unreliable — shift its weight to face
        shift = aw * 0.90   # give 90% of audio's weight to face
        fw   += shift
        aw   -= shift
    elif audio_qual < 0.40:
        # Moderate audio quality — partial shift
        factor = (audio_qual - MIN_AUDIO_QUAL) / (0.40 - MIN_AUDIO_QUAL)
        shift  = aw * (1.0 - factor) * 0.5
        fw    += shift
        aw    -= shift

    # Face confidence adjustment
    if face_conf < MIN_FACE_CONF:
        # Face unreliable — shift its weight to audio
        shift = fw * 0.80
        aw   += shift
        fw   -= shift
    elif face_conf < 0.55:
        factor = (face_conf - MIN_FACE_CONF) / (0.55 - MIN_FACE_CONF)
        shift  = fw * (1.0 - factor) * 0.35
        aw    += shift
        fw    -= shift

    # Normalise to sum=1
    total = fw + aw
    if total < 1e-6:
        return BASE_FACE_W, BASE_AUDIO_W

    fw = round(fw / total, 4)
    aw = round(aw / total, 4)
    return fw, aw


# ── Metric derivation ──────────────────────────────────────────────────────────

def _derive_engagement(face: dict, audio: dict, stress: float) -> float:
    """
    Engagement = positive face signal + active speech,
                 penalised by stress.
    """
    happy    = face.get("happy",    0.0)
    surprise = face.get("surprise", 0.0)
    neutral  = face.get("neutral",  0.0)
    is_speech = audio.get("is_speech", True)
    voiced    = audio.get("components", {}).get("prosodic", 0.0)

    # Positive face contribution
    face_eng  = happy * 0.60 + surprise * 0.25 + neutral * 0.15

    # Speech activity contribution
    speech_eng = 0.70 if is_speech else 0.20
    speech_eng += voiced * 0.30   # more prosodic variation = more active

    raw = 0.55 * face_eng + 0.45 * speech_eng

    # Stress penalty — hard to be engaged when stressed
    penalised = raw * (1.0 - ENGAGEMENT_STRESS_PENALTY * stress)

    return float(np.clip(penalised, 0.0, 1.0))


def _derive_confusion(face: dict, audio: dict) -> float:
    """
    Confusion = fear + surprise face + audio prosodic irregularity.
    """
    fear     = face.get("fear",     0.0)
    surprise = face.get("surprise", 0.0)
    delta_irreg = audio.get("components", {}).get("prosodic", 0.0)

    raw = (
        CONFUSION_FEAR_W     * fear     +
        CONFUSION_SURPRISE_W * surprise +
        CONFUSION_DELTA_W    * delta_irreg
    )
    return float(np.clip(raw, 0.0, 1.0))


def _derive_confidence(face: dict, stress: float, confusion: float) -> float:
    """
    Confidence = positive stable face signal,
                 reduced by stress and confusion.
    """
    happy   = face.get("happy",   0.0)
    neutral = face.get("neutral", 0.0)
    sad     = face.get("sad",     0.0)
    angry   = face.get("angry",   0.0)

    # Positive face base
    pos_face = happy * 0.65 + neutral * 0.35
    neg_face = sad   * 0.50 + angry   * 0.50

    raw = pos_face - neg_face * 0.40

    # Reduce by stress and confusion
    raw = raw * (1.0 - 0.40 * stress) * (1.0 - 0.35 * confusion)

    return float(np.clip(raw, 0.0, 1.0))


# ── FusionEngine ───────────────────────────────────────────────────────────────

class FusionEngine:
    """
    Drop-in replacement for the old FusionEngine.

    Public API (identical to v1 + extras):
        .fuse_emotions(face_result, audio_result) → dict
        .reset_session()
        .get_history_stats() → dict
    """

    def __init__(self):
        # Per-metric EWA buffers
        self._buf_stress     = _EWABuffer()
        self._buf_engagement = _EWABuffer()
        self._buf_confidence = _EWABuffer()
        self._buf_confusion  = _EWABuffer()

        # State machine
        self._state_machine  = _StateMachine()

        # History for stats
        self._history: deque = deque(maxlen=60)

        print("[Fusion] FusionEngine v2 ready ✓")

    # ── Public API ─────────────────────────────────────────────────────────────

    def fuse_emotions(
        self,
        face_result:  dict | None,
        audio_result: dict | float | None,
    ) -> dict:
        """
        Main fusion call.

        Accepts
        -------
        face_result  : output of FaceEmotionDetector.detect_emotions()
                       OR a plain 6-emotion dict (legacy)
        audio_result : output of AudioEmotionAnalyzer.analyze_stress_detailed()
                       OR a plain float (legacy)
        """

        # ── Normalise face input ──────────────────────────────────────────────
        if face_result is None:
            face_probs = {"neutral": 1.0, "happy": 0.0, "sad": 0.0,
                          "angry": 0.0, "fear": 0.0, "surprise": 0.0}
            face_conf  = 0.0
        elif isinstance(face_result, dict) and "probs" in face_result:
            face_probs = face_result["probs"]
            face_conf  = float(face_result.get("confidence", 0.5))
        elif isinstance(face_result, dict):
            # Legacy: plain emotion dict
            face_probs = face_result
            face_conf  = float(max(face_result.values())) if face_result else 0.5
        else:
            face_probs = {"neutral": 1.0, "happy": 0.0, "sad": 0.0,
                          "angry": 0.0, "fear": 0.0, "surprise": 0.0}
            face_conf  = 0.0

        # ── Normalise audio input ─────────────────────────────────────────────
        if audio_result is None:
            audio_stress  = 0.0
            audio_qual    = 0.0
            audio_is_speech = False
            audio_components = {"energy": 0.0, "spectral": 0.0, "prosodic": 0.0}
        elif isinstance(audio_result, (float, int)):
            # Legacy: plain float stress score
            audio_stress     = float(np.clip(audio_result, 0.0, 1.0))
            audio_qual       = 0.7     # assume reasonable quality
            audio_is_speech  = audio_stress > 0.05
            audio_components = {"energy": audio_stress, "spectral": 0.0, "prosodic": 0.0}
        elif isinstance(audio_result, dict):
            audio_stress     = float(np.clip(audio_result.get("stress",    0.0), 0.0, 1.0))
            audio_qual       = float(audio_result.get("quality",   0.5))
            audio_is_speech  = bool(audio_result.get("is_speech",  True))
            audio_components = audio_result.get("components",
                                {"energy": 0.0, "spectral": 0.0, "prosodic": 0.0})
        else:
            audio_stress     = 0.0
            audio_qual       = 0.0
            audio_is_speech  = False
            audio_components = {"energy": 0.0, "spectral": 0.0, "prosodic": 0.0}

        # Enrich audio dict for downstream helpers
        audio_enriched = {
            "stress":      audio_stress,
            "quality":     audio_qual,
            "is_speech":   audio_is_speech,
            "components":  audio_components,
        }

        # ── Dynamic weights ───────────────────────────────────────────────────
        face_w, audio_w = _compute_weights(face_conf, audio_qual, audio_is_speech)

        # ── Quality-gated stress fusion ───────────────────────────────────────
        # Face negative emotion proxy
        neg_face = (
            face_probs.get("sad",   0.0) * 0.55 +
            face_probs.get("angry", 0.0) * 0.70 +
            face_probs.get("fear",  0.0) * 0.60
        )
        neg_face = float(np.clip(neg_face, 0.0, 1.0))

        # Audio stress contribution (zeroed if no speech)
        audio_contrib = audio_stress if audio_is_speech else 0.0

        raw_stress = face_w * neg_face + audio_w * audio_contrib

        # ── Derive other metrics ──────────────────────────────────────────────
        raw_engagement = _derive_engagement(face_probs, audio_enriched, raw_stress)
        raw_confusion  = _derive_confusion(face_probs, audio_enriched)
        raw_confidence = _derive_confidence(face_probs, raw_stress, raw_confusion)

        # ── EWA smoothing ─────────────────────────────────────────────────────
        stress     = self._buf_stress.push(raw_stress)
        engagement = self._buf_engagement.push(raw_engagement)
        confusion  = self._buf_confusion.push(raw_confusion)
        confidence = self._buf_confidence.push(raw_confidence)

        smoothed_metrics = {
            "stress":     stress,
            "engagement": engagement,
            "confidence": confidence,
            "confusion":  confusion,
        }

        # ── Dominant state ────────────────────────────────────────────────────
        dominant = self._state_machine.update(
            smoothed_metrics, face_probs, audio_enriched
        )

        # ── Build result ──────────────────────────────────────────────────────
        result = {
            **smoothed_metrics,
            "dominant_state": dominant,
            "weights":  {"face": face_w, "audio": audio_w},
            "quality":  {"face": round(face_conf, 3), "audio": round(audio_qual, 3)},
            "smoothed": self._buf_stress.ready,
        }

        self._history.append(result)
        return result

    # ── Session management ─────────────────────────────────────────────────────

    def reset_session(self):
        """Call at the start of each new session."""
        self._buf_stress.reset()
        self._buf_engagement.reset()
        self._buf_confidence.reset()
        self._buf_confusion.reset()
        self._state_machine.reset()
        self._history.clear()
        print("[Fusion] Session reset.")

    def get_history_stats(self) -> dict:
        """Summary statistics over all fused frames this session."""
        if not self._history:
            return {}

        stresses     = [h["stress"]     for h in self._history]
        engagements  = [h["engagement"] for h in self._history]
        confidences  = [h["confidence"] for h in self._history]
        confusions   = [h["confusion"]  for h in self._history]
        states       = [h["dominant_state"] for h in self._history]

        from collections import Counter
        state_counts = dict(Counter(states))

        return {
            "frames":           len(self._history),
            "avg_stress":       round(float(np.mean(stresses)),    3),
            "avg_engagement":   round(float(np.mean(engagements)), 3),
            "avg_confidence":   round(float(np.mean(confidences)), 3),
            "avg_confusion":    round(float(np.mean(confusions)),  3),
            "peak_stress":      round(float(np.max(stresses)),     3),
            "dominant_states":  state_counts,
            "most_common_state": max(state_counts, key=state_counts.get) if state_counts else "neutral",
        }