"""
src/audio/mic_capture.py  —  EMOTISENSE AI v2
==============================================
Microphone capture with:
  - Voice Activity Detection (VAD)
  - Signal quality scoring
  - Automatic gain normalisation
  - Structured chunk output with metadata

Returned chunk dict
-------------------
{
    "audio"     : np.ndarray  (float32, mono, SAMPLE_RATE),
    "is_speech" : bool        (VAD result),
    "quality"   : float       (0–1, signal quality),
    "rms"       : float       (normalised RMS energy),
    "duration"  : float       (seconds captured),
}

If the microphone is unavailable, capture_audio_chunk() returns
_empty_chunk() so downstream code never receives None.
"""

import time
import warnings
import threading
from typing import Optional

import numpy as np

warnings.filterwarnings("ignore")

# ── Constants ──────────────────────────────────────────────────────────────────
SAMPLE_RATE      = 16_000        # Hz  — standard for speech models
CHUNK_DURATION   = 2.0           # seconds per analysis window
CHUNK_SAMPLES    = int(SAMPLE_RATE * CHUNK_DURATION)

# VAD thresholds
VAD_RMS_FLOOR    = 0.002         # below this → silence
VAD_ZCR_CEILING  = 0.45          # above this with low RMS → noise (not speech)
VAD_RMS_SPEECH   = 0.010         # above this → likely speech

# Gain normalisation
TARGET_RMS       = 0.08          # target RMS after normalisation
MAX_GAIN         = 20.0          # safety cap so we don't amplify pure noise
MIN_GAIN         = 0.2


def _empty_chunk(reason: str = "unavailable") -> dict:
    return {
        "audio":     np.zeros(CHUNK_SAMPLES, dtype=np.float32),
        "is_speech": False,
        "quality":   0.0,
        "rms":       0.0,
        "duration":  CHUNK_DURATION,
        "reason":    reason,
    }


# ── VAD helper ─────────────────────────────────────────────────────────────────

def _voice_activity(audio: np.ndarray) -> tuple[bool, float]:
    """
    Lightweight energy + ZCR voice activity detector.

    Returns
    -------
    is_speech : bool
    quality   : float  (0–1 confidence that audio is usable speech)
    """
    if audio is None or len(audio) == 0:
        return False, 0.0

    rms = float(np.sqrt(np.mean(audio ** 2)))

    # Zero crossing rate
    signs  = np.sign(audio)
    signs[signs == 0] = 1
    zcr    = float(np.mean(np.abs(np.diff(signs)) / 2))

    # ── Decision logic ────────────────────────────────────────────────────────
    if rms < VAD_RMS_FLOOR:
        # Pure silence
        return False, 0.0

    if rms < VAD_RMS_SPEECH and zcr > VAD_ZCR_CEILING:
        # Low amplitude + high ZCR → background noise / fan / AC hum
        quality = max(0.0, 0.3 - zcr * 0.5)
        return False, quality

    # Signal present — compute a quality score
    # Higher RMS (up to target) + moderate ZCR (speech range 0.05–0.35) = higher quality
    rms_score = min(1.0, rms / TARGET_RMS)
    zcr_score = 1.0 - abs(zcr - 0.20) / 0.30   # peaks at ZCR≈0.20
    zcr_score = max(0.0, min(1.0, zcr_score))
    quality   = round(0.6 * rms_score + 0.4 * zcr_score, 3)

    is_speech = rms >= VAD_RMS_SPEECH
    return is_speech, quality


# ── Gain normalisation ─────────────────────────────────────────────────────────

def _normalize_gain(audio: np.ndarray) -> np.ndarray:
    """
    Scale audio so its RMS sits near TARGET_RMS.
    Clips gain between MIN_GAIN and MAX_GAIN for safety.
    """
    rms = float(np.sqrt(np.mean(audio ** 2)))
    if rms < 1e-8:
        return audio   # silence — don't amplify
    gain = np.clip(TARGET_RMS / rms, MIN_GAIN, MAX_GAIN)
    normalised = audio * gain
    # Hard clip to [-1, 1] to prevent overflow artefacts
    return np.clip(normalised, -1.0, 1.0).astype(np.float32)


# ── MicrophoneCapture ──────────────────────────────────────────────────────────

class MicrophoneCapture:
    """
    Blocking audio capture with VAD and gain normalisation.

    Usage
    -----
        mic   = MicrophoneCapture()
        chunk = mic.capture_audio_chunk()   # blocks for CHUNK_DURATION seconds
        if chunk["is_speech"]:
            # pass chunk["audio"] to AudioEmotionAnalyzer
    """

    def __init__(self):
        self.is_available  = False
        self.sample_rate   = SAMPLE_RATE
        self.chunk_samples = CHUNK_SAMPLES
        self._lock         = threading.Lock()
        self._last_chunk   = _empty_chunk("init")
        self._init()

    # ── Init ──────────────────────────────────────────────────────────────────

    def _init(self):
        try:
            import sounddevice as sd
            # Quick test — query devices to confirm sounddevice works
            devices = sd.query_devices()
            default = sd.query_devices(kind="input")
            print(f"[Mic] Input device: {default.get('name', 'unknown')}")
            self._sd        = sd
            self.is_available = True
            print("[Mic] MicrophoneCapture ready ✓")
        except Exception as e:
            print(f"[Mic] sounddevice unavailable: {e}")
            self.is_available = False
            self._sd = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def capture_audio_chunk(self) -> dict:
        """
        Record CHUNK_DURATION seconds of audio.
        Always returns a chunk dict — never raises, never returns None.
        """
        if not self.is_available or self._sd is None:
            return _empty_chunk("mic_unavailable")

        try:
            raw = self._sd.rec(
                self.chunk_samples,
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocking=True,
            )
            audio = raw.flatten()

            # ── Gain normalise first ──────────────────────────────────────────
            normed = _normalize_gain(audio)

            # ── VAD ───────────────────────────────────────────────────────────
            is_speech, quality = _voice_activity(normed)

            rms = float(np.sqrt(np.mean(normed ** 2)))

            chunk = {
                "audio":     normed,
                "is_speech": is_speech,
                "quality":   quality,
                "rms":       round(rms, 5),
                "duration":  CHUNK_DURATION,
                "reason":    "ok",
            }

            with self._lock:
                self._last_chunk = chunk

            return chunk

        except Exception as e:
            print(f"[Mic] Capture error: {e}")
            return _empty_chunk(f"error:{e}")

    def get_last_chunk(self) -> dict:
        """Return the most recently captured chunk without blocking."""
        with self._lock:
            return self._last_chunk

    def get_device_info(self) -> dict:
        """Return info about the active input device."""
        if not self.is_available or self._sd is None:
            return {"available": False}
        try:
            d = self._sd.query_devices(kind="input")
            return {
                "available":   True,
                "name":        d.get("name", "unknown"),
                "sample_rate": int(d.get("default_samplerate", SAMPLE_RATE)),
                "channels":    int(d.get("max_input_channels", 1)),
            }
        except Exception:
            return {"available": self.is_available}