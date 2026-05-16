"""
src/audio/audio_emotion.py  —  EMOTISENSE AI v2
================================================
MFCC-based audio stress analyser.

Replaces the old RMS+ZCR rule-of-thumb with a proper
feature-engineering pipeline:

  Feature set (per chunk)
  -----------------------
  • 13 MFCCs + delta-MFCCs + delta-delta-MFCCs  (39 values)
  • Spectral centroid, rolloff, bandwidth, contrast
  • Pitch estimate (via autocorrelation)
  • RMS energy envelope variance
  • Speaking-rate proxy (syllable-energy peaks / second)

  Three-component stress score
  ----------------------------
  1. Vocal energy component     — log-normalised RMS vs calibrated baseline
  2. Spectral tension component — high-frequency energy ratio
  3. Prosodic irregularity      — pitch variance + MFCC-delta magnitude

  Post-processing
  ---------------
  • First 5 speech frames → calibration baseline (per-session)
  • Rolling 10-frame history with contextual amplification:
      sustained moderate stress → score boosted
      single spike             → score dampened
  • Silence / noise frames     → 0.0 returned, history not updated

Returns
-------
  float  (0.0 – 1.0)  stress score

  or via analyze_stress_detailed() →
  {
      "stress"       : float,
      "is_speech"    : bool,
      "quality"      : float,
      "components"   : {"energy": float, "spectral": float, "prosodic": float},
      "calibrated"   : bool,
      "frames_seen"  : int,
  }
"""

import warnings
import logging

import numpy as np

warnings.filterwarnings("ignore")
logging.getLogger("numba").setLevel(logging.ERROR)

# ── Constants ──────────────────────────────────────────────────────────────────
SAMPLE_RATE      = 16_000

# MFCC
N_MFCC          = 13
HOP_LENGTH      = 512
N_FFT           = 1024

# Stress component weights  (must sum to 1.0)
W_ENERGY        = 0.35
W_SPECTRAL      = 0.40
W_PROSODIC      = 0.25

# Calibration
CALIB_FRAMES    = 5       # speech frames to collect before scoring
CALIB_FALLBACK  = 0.06    # assumed baseline RMS if calibration not done

# Rolling history
HISTORY_SIZE    = 10
SUSTAIN_BOOST   = 1.18    # multiply score when stress sustained > 6 frames
SPIKE_DAMP      = 0.82    # multiply score when single-frame spike detected

# Spectral tension — frequencies above this are "high tension"
HF_BOUNDARY_HZ  = 3_000


# ── Librosa import (lazy, with graceful fallback) ──────────────────────────────

def _import_librosa():
    try:
        import librosa
        return librosa
    except ImportError:
        return None


# ── Feature extraction helpers ─────────────────────────────────────────────────

def _safe_mean(arr) -> float:
    try:
        v = float(np.mean(arr))
        return v if np.isfinite(v) else 0.0
    except Exception:
        return 0.0


def _safe_std(arr) -> float:
    try:
        v = float(np.std(arr))
        return v if np.isfinite(v) else 0.0
    except Exception:
        return 0.0


def _extract_features(audio: np.ndarray, librosa) -> dict | None:
    """
    Extract the full feature set from a mono float32 audio array.
    Returns None if extraction fails.
    """
    try:
        sr = SAMPLE_RATE

        # ── MFCCs ─────────────────────────────────────────────────────────────
        mfcc        = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=N_MFCC,
                                            n_fft=N_FFT, hop_length=HOP_LENGTH)
        mfcc_delta  = librosa.feature.delta(mfcc)
        mfcc_delta2 = librosa.feature.delta(mfcc, order=2)

        mfcc_mean        = np.mean(mfcc,        axis=1)   # (13,)
        mfcc_std         = np.std(mfcc,         axis=1)
        delta_mean       = np.mean(mfcc_delta,  axis=1)
        delta_std        = np.std(mfcc_delta,   axis=1)
        delta2_mean      = np.mean(mfcc_delta2, axis=1)

        # ── Spectral features ─────────────────────────────────────────────────
        stft    = np.abs(librosa.stft(audio, n_fft=N_FFT, hop_length=HOP_LENGTH))
        freqs   = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)

        centroid  = librosa.feature.spectral_centroid( S=stft, sr=sr, n_fft=N_FFT)
        rolloff   = librosa.feature.spectral_rolloff(  S=stft, sr=sr)
        bandwidth = librosa.feature.spectral_bandwidth(S=stft, sr=sr, n_fft=N_FFT)

        try:
            contrast = librosa.feature.spectral_contrast(S=stft, sr=sr)
            contrast_mean = float(np.mean(contrast))
        except Exception:
            contrast_mean = 0.0

        # High-frequency energy ratio (above HF_BOUNDARY_HZ)
        hf_mask   = freqs >= HF_BOUNDARY_HZ
        total_e   = np.sum(stft ** 2) + 1e-10
        hf_energy = np.sum(stft[hf_mask, :] ** 2)
        hf_ratio  = float(hf_energy / total_e)

        # ── RMS energy ────────────────────────────────────────────────────────
        rms_frames = librosa.feature.rms(y=audio, hop_length=HOP_LENGTH)[0]
        rms_mean   = _safe_mean(rms_frames)
        rms_var    = _safe_std(rms_frames)

        # ── Pitch via autocorrelation ─────────────────────────────────────────
        try:
            f0, voiced_flag, _ = librosa.pyin(
                audio, sr=sr,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
                frame_length=N_FFT,
            )
            voiced_f0  = f0[voiced_flag] if voiced_flag is not None else np.array([])
            pitch_mean = float(np.nanmean(voiced_f0)) if len(voiced_f0) > 0 else 0.0
            pitch_var  = float(np.nanstd(voiced_f0))  if len(voiced_f0) > 0 else 0.0
            voiced_ratio = float(np.mean(voiced_flag)) if voiced_flag is not None else 0.0
        except Exception:
            pitch_mean   = 0.0
            pitch_var    = 0.0
            voiced_ratio = 0.0

        # ── Speaking-rate proxy ───────────────────────────────────────────────
        # Count local energy peaks above 60th percentile as rough syllable count
        rms_arr   = rms_frames.astype(float)
        threshold = np.percentile(rms_arr, 60)
        above     = (rms_arr > threshold).astype(int)
        crossings = int(np.sum(np.diff(above) == 1))   # rising edges
        duration  = len(audio) / sr
        speak_rate = crossings / (duration + 1e-6)

        return {
            # MFCC stats
            "mfcc_mean":      mfcc_mean,
            "mfcc_std":       mfcc_std,
            "delta_mean":     delta_mean,
            "delta_std":      delta_std,
            "delta2_mean":    delta2_mean,
            # Spectral
            "centroid_mean":  _safe_mean(centroid),
            "rolloff_mean":   _safe_mean(rolloff),
            "bandwidth_mean": _safe_mean(bandwidth),
            "contrast_mean":  contrast_mean,
            "hf_ratio":       hf_ratio,
            # Energy
            "rms_mean":       rms_mean,
            "rms_var":        rms_var,
            # Prosodic
            "pitch_mean":     pitch_mean,
            "pitch_var":      pitch_var,
            "voiced_ratio":   voiced_ratio,
            "speak_rate":     speak_rate,
        }

    except Exception as e:
        print(f"[AudioEmotion] Feature extraction error: {e}")
        return None


# ── Three-component stress scorer ──────────────────────────────────────────────

def _score_energy_component(features: dict, baseline_rms: float) -> float:
    """
    Vocal energy component.
    Log-normalised RMS relative to the calibrated baseline.
    Stressed speech is louder and more variable in energy.
    """
    rms      = features["rms_mean"]
    rms_var  = features["rms_var"]

    if baseline_rms < 1e-8:
        baseline_rms = CALIB_FALLBACK

    # How much louder than baseline? (log scale — avoids extreme values)
    ratio     = rms / (baseline_rms + 1e-8)
    log_ratio = np.log1p(max(0.0, ratio - 1.0))   # 0 when ratio=1, grows slowly
    energy_s  = np.clip(log_ratio / 1.5, 0.0, 1.0)

    # Energy variance boost — stressed speech has more energy fluctuation
    var_norm  = np.clip(rms_var / (baseline_rms * 0.5 + 1e-8), 0.0, 1.0)
    score     = 0.65 * float(energy_s) + 0.35 * float(var_norm)

    return float(np.clip(score, 0.0, 1.0))


def _score_spectral_component(features: dict) -> float:
    """
    Spectral tension component.
    Stressed speech has higher-frequency concentration and wider bandwidth.
    High spectral centroid + high HF ratio + high bandwidth = tension.
    """
    # Normalise centroid against typical speech range (500–4000 Hz)
    centroid_norm  = np.clip((features["centroid_mean"] - 500) / 3500, 0.0, 1.0)

    # HF energy ratio — stressed speech has more high-frequency energy
    hf_score       = np.clip(features["hf_ratio"] / 0.35, 0.0, 1.0)

    # Bandwidth — wider = more tension
    bw_norm        = np.clip(features["bandwidth_mean"] / 4000, 0.0, 1.0)

    # Spectral contrast — lower contrast = more uniform = stress
    contrast_inv   = np.clip(1.0 - features["contrast_mean"] / 40.0, 0.0, 1.0)

    score = (
        0.30 * float(centroid_norm) +
        0.35 * float(hf_score)      +
        0.20 * float(bw_norm)       +
        0.15 * float(contrast_inv)
    )
    return float(np.clip(score, 0.0, 1.0))


def _score_prosodic_component(features: dict) -> float:
    """
    Prosodic irregularity component.
    Stress disrupts natural speech rhythm and causes pitch instability.
    High pitch variance + high MFCC delta magnitude + abnormal speaking rate = stress.
    """
    # Pitch variance — stressed speech has more pitch irregularity
    # Normalise: 0 Hz var = calm, ~80 Hz var = quite stressed
    pitch_var_norm = np.clip(features["pitch_var"] / 80.0, 0.0, 1.0)

    # MFCC delta magnitude — large deltas = rapid spectral change = stress
    delta_mag = float(np.mean(np.abs(features["delta_mean"])))
    delta_norm = np.clip(delta_mag / 15.0, 0.0, 1.0)

    delta2_mag = float(np.mean(np.abs(features["delta2_mean"])))
    delta2_norm = np.clip(delta2_mag / 8.0, 0.0, 1.0)

    # Speaking rate — very fast or very slow can indicate stress
    # Comfortable range: 2–5 syllable-peaks/sec
    rate = features["speak_rate"]
    if rate < 2.0:
        rate_stress = np.clip((2.0 - rate) / 2.0, 0.0, 1.0)    # too slow
    elif rate > 5.0:
        rate_stress = np.clip((rate - 5.0) / 3.0, 0.0, 1.0)    # too fast
    else:
        rate_stress = 0.0    # comfortable range

    score = (
        0.35 * float(pitch_var_norm) +
        0.30 * float(delta_norm)     +
        0.20 * float(delta2_norm)    +
        0.15 * float(rate_stress)
    )
    return float(np.clip(score, 0.0, 1.0))


# ── Rolling history with contextual adjustment ─────────────────────────────────

def _contextual_adjust(raw_score: float, history: list) -> float:
    """
    Dampen single spikes. Amplify sustained stress.
    """
    if len(history) < 2:
        return raw_score

    recent    = history[-6:]         # last 6 readings
    avg_recent = np.mean(recent)

    # Single spike: current score much higher than recent average
    if raw_score > avg_recent + 0.25 and len(history) >= 3:
        return raw_score * SPIKE_DAMP

    # Sustained stress: most recent frames all above 0.45
    if len(recent) >= 6 and avg_recent > 0.45 and raw_score > 0.40:
        return min(1.0, raw_score * SUSTAIN_BOOST)

    return raw_score


# ── AudioEmotionAnalyzer ───────────────────────────────────────────────────────

class AudioEmotionAnalyzer:
    """
    Drop-in replacement for the old AudioEmotionAnalyzer.

    Public API (identical to v1 + extras):
        .is_ready                      → bool
        .analyze_stress(chunk) → float (0–1)
        .analyze_stress_detailed(chunk) → dict
        .reset_session()               → resets calibration + history
        .get_calibration_info()        → dict
    """

    def __init__(self):
        self._librosa       = _import_librosa()
        self.is_ready       = self._librosa is not None
        # Calibration
        self._calib_rms:    list[float] = []
        self._baseline_rms: float       = CALIB_FALLBACK
        self._calibrated:   bool        = False
        # Rolling history
        self._history:      list[float] = []
        self._frames_seen:  int         = 0

        if self.is_ready:
            print("[AudioEmotion] Analyser ready ✓  (librosa loaded)")
        else:
            print("[AudioEmotion] librosa not found — stress will return 0.0")

    # ── Public API ─────────────────────────────────────────────────────────────

    def analyze_stress(self, chunk: dict | np.ndarray | None) -> float:
        """
        Main entry point.  Accepts either:
          - a chunk dict from MicrophoneCapture (preferred)
          - a raw np.ndarray (legacy compatibility)

        Returns a float 0.0–1.0.
        """
        result = self.analyze_stress_detailed(chunk)
        return result["stress"]

    def analyze_stress_detailed(self, chunk: dict | np.ndarray | None) -> dict:
        """
        Full analysis result dict.
        """
        # ── Normalise input ───────────────────────────────────────────────────
        if chunk is None:
            return self._null_result("null_input")

        if isinstance(chunk, np.ndarray):
            # Legacy: raw array passed directly
            audio      = chunk.flatten().astype(np.float32)
            is_speech  = True
            quality    = 0.7
        elif isinstance(chunk, dict):
            audio     = chunk.get("audio", np.zeros(1, dtype=np.float32))
            is_speech = chunk.get("is_speech", False)
            quality   = chunk.get("quality",   0.0)
        else:
            return self._null_result("unknown_input_type")

        # ── Skip silence / noise ──────────────────────────────────────────────
        if not is_speech or quality < 0.15:
            return self._null_result("no_speech", is_speech=False, quality=quality)

        if not self.is_ready:
            return self._null_result("librosa_unavailable")

        # ── Extract features ──────────────────────────────────────────────────
        features = _extract_features(audio, self._librosa)
        if features is None:
            return self._null_result("feature_extraction_failed")

        self._frames_seen += 1

        # ── Calibration phase ─────────────────────────────────────────────────
        if not self._calibrated:
            self._calib_rms.append(features["rms_mean"])
            if len(self._calib_rms) >= CALIB_FRAMES:
                self._baseline_rms = float(np.median(self._calib_rms))
                self._calibrated   = True
                print(f"[AudioEmotion] Calibrated. Baseline RMS = {self._baseline_rms:.5f}")
            # During calibration return a neutral-ish score
            raw_score  = float(np.clip(features["rms_mean"] / CALIB_FALLBACK * 0.3, 0.0, 0.5))
            components = {"energy": raw_score, "spectral": 0.0, "prosodic": 0.0}
            return self._build_result(raw_score, components, is_speech, quality, calibrated=False)

        # ── Three-component scoring ───────────────────────────────────────────
        c_energy   = _score_energy_component(features, self._baseline_rms)
        c_spectral = _score_spectral_component(features)
        c_prosodic = _score_prosodic_component(features)

        raw_score = (
            W_ENERGY   * c_energy   +
            W_SPECTRAL * c_spectral +
            W_PROSODIC * c_prosodic
        )
        raw_score = float(np.clip(raw_score, 0.0, 1.0))

        # ── Contextual adjustment ─────────────────────────────────────────────
        adjusted = _contextual_adjust(raw_score, self._history)

        # ── Update history ────────────────────────────────────────────────────
        self._history.append(adjusted)
        if len(self._history) > HISTORY_SIZE:
            self._history.pop(0)

        components = {
            "energy":   round(c_energy,   3),
            "spectral": round(c_spectral, 3),
            "prosodic": round(c_prosodic, 3),
        }
        return self._build_result(adjusted, components, is_speech, quality, calibrated=True)

    # ── Session management ─────────────────────────────────────────────────────

    def reset_session(self):
        """Call at the start of each new session to reset baseline + history."""
        self._calib_rms    = []
        self._baseline_rms = CALIB_FALLBACK
        self._calibrated   = False
        self._history      = []
        self._frames_seen  = 0
        print("[AudioEmotion] Session reset — calibration cleared.")

    def get_calibration_info(self) -> dict:
        return {
            "calibrated":    self._calibrated,
            "baseline_rms":  round(self._baseline_rms, 6),
            "calib_frames":  len(self._calib_rms),
            "frames_needed": CALIB_FRAMES,
            "frames_seen":   self._frames_seen,
            "history_len":   len(self._history),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _null_result(self, reason: str, is_speech: bool = False, quality: float = 0.0) -> dict:
        return {
            "stress":      0.0,
            "is_speech":   is_speech,
            "quality":     quality,
            "components":  {"energy": 0.0, "spectral": 0.0, "prosodic": 0.0},
            "calibrated":  self._calibrated,
            "frames_seen": self._frames_seen,
            "reason":      reason,
        }

    def _build_result(
        self, stress: float, components: dict,
        is_speech: bool, quality: float, calibrated: bool
    ) -> dict:
        return {
            "stress":      round(float(stress), 4),
            "is_speech":   is_speech,
            "quality":     round(quality, 3),
            "components":  components,
            "calibrated":  calibrated,
            "frames_seen": self._frames_seen,
            "reason":      "ok",
        }