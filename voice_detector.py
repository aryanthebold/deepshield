"""
voice_detector.py
─────────────────
Deepfake voice detector for DeepShield.

Detection strategy (two-tier):
  1. ML model (Random Forest + GBM ensemble) trained on FoR-norm dataset
     → Used when voice_model.pkl exists (after running train_voice_model.py)
     → Expected accuracy: 85-95% on real + AI voices
  2. Rule-based fallback (7 weighted signals)
     → Used when model not yet trained
     → Expected accuracy: ~65-70%

Blending:  final_score = 0.75 * ml_score + 0.25 * rule_score
"""

import librosa
import numpy as np
import warnings
import pickle
from pathlib import Path

warnings.filterwarnings("ignore")

MODEL_PATH = Path("voice_model.pkl")
THRESHOLD  = 0.50   # above this → SYNTHETIC


# ─────────────────────────────────────────────────────────────
# FEATURE EXTRACTION  (must match train_voice_model.py exactly)
# ─────────────────────────────────────────────────────────────

def extract_features(audio_path, duration=10):
    """Extract 51-dim feature vector. Returns (vec, y, sr)."""
    try:
        y, sr = librosa.load(str(audio_path), duration=duration, sr=22050)
        if len(y) < sr * 0.5:
            return None, None, None

        features = []

        # MFCCs — 26 features (mean + std of 13 coefficients)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        features.extend(np.mean(mfcc, axis=1).tolist())
        features.extend(np.std(mfcc, axis=1).tolist())

        # Spectral shape — 6 features
        features.append(float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))))
        features.append(float(np.std(librosa.feature.spectral_centroid(y=y, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_flatness(y=y))))
        features.append(float(np.std(librosa.feature.spectral_flatness(y=y))))

        # RMS energy — 2 features
        rms = librosa.feature.rms(y=y)[0]
        features.append(float(np.mean(rms)))
        features.append(float(np.std(rms)))

        # ZCR — 2 features
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        features.append(float(np.mean(zcr)))
        features.append(float(np.std(zcr)))

        # Chroma — 12 features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features.extend(np.mean(chroma, axis=1).tolist())

        # HF energy ratio — 1 feature
        fft   = np.abs(np.fft.rfft(y))
        freqs = np.fft.rfftfreq(len(y), 1 / sr)
        hf    = float(np.sum(fft[freqs > 8000]))
        tot   = float(np.sum(fft))
        features.append(hf / tot if tot > 0 else 0.0)

        # Pitch variance — 1 feature
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        strong = pitches[magnitudes > np.max(magnitudes) * 0.1]
        features.append(float(np.std(strong)) if len(strong) > 0 else 0.0)

        # Tempo — 1 feature (bug fix: np.squeeze handles array return)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        features.append(float(np.squeeze(tempo)))

        vec = np.array(features, dtype=np.float32)
        vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
        return vec, y, sr

    except Exception:
        return None, None, None


# ─────────────────────────────────────────────────────────────
# ML MODEL INFERENCE
# ─────────────────────────────────────────────────────────────

_model_cache = None

def load_model():
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            _model_cache = pickle.load(f)
        return _model_cache
    return None

def ml_predict(vec):
    """Returns (P(fake): float|None, method: str)."""
    bundle = load_model()
    if bundle is None:
        return None, "no_model"
    try:
        X       = bundle["scaler"].transform(vec.reshape(1, -1))
        rf_prob = bundle["rf"].predict_proba(X)[0][1]
        gb_prob = bundle["gb"].predict_proba(X)[0][1]
        return float(0.6 * rf_prob + 0.4 * gb_prob), "ml_ensemble"
    except Exception:
        return None, "model_error"


# ─────────────────────────────────────────────────────────────
# RULE-BASED CHECKS
# ─────────────────────────────────────────────────────────────

SIGNAL_WEIGHTS = {
    "breathing":      0.25,
    "pitch_variance": 0.20,
    "formant":        0.20,
    "spectral_flat":  0.15,
    "hf_energy":      0.10,
    "silence_ratio":  0.05,
    "zcr_regularity": 0.05,
}

def _check_breathing(y, sr):
    triggered = float(np.std(librosa.feature.rms(y=y, hop_length=512)[0])) < 0.005
    return triggered, (
        "Breathing pattern absent — TTS voices have no energy variation between words"
        if triggered else "Normal energy variation — breathing pattern present"
    )

def _check_pitch_variance(y, sr):
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    strong = pitches[magnitudes > np.max(magnitudes) * 0.1]
    if len(strong) == 0:
        return False, "Could not extract pitch data"
    triggered = float(np.std(strong)) < 15
    return triggered, (
        "Unnaturally consistent pitch — human voices vary in tone naturally"
        if triggered else "Natural pitch variation detected"
    )

def _check_formants(y, sr):
    try:
        pre       = np.append(y[0], y[1:] - 0.97 * y[:-1])
        frame_len = int(0.025 * sr)
        hop       = int(0.010 * sr)
        variances = [
            np.var(np.abs(np.fft.rfft(pre[i:i+frame_len] * np.hanning(frame_len))))
            for i in range(0, len(pre) - frame_len, hop)
        ]
        if not variances:
            return False, "Formant analysis skipped"
        triggered = float(np.mean(variances)) < 500
        return triggered, (
            "Flat formant structure — vocal tract resonance is unnaturally static"
            if triggered else "Dynamic formant transitions — consistent with natural speech"
        )
    except Exception:
        return False, "Formant analysis skipped"

def _check_spectral_flatness(y, sr):
    triggered = float(np.mean(librosa.feature.spectral_flatness(y=y)[0])) < 0.005
    return triggered, (
        "Unnaturally tonal spectrum — TTS lacks the noisy texture of real consonants"
        if triggered else "Normal spectral texture detected"
    )

def _check_hf_energy(y, sr):
    fft   = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1 / sr)
    hf    = float(np.sum(fft[freqs > 8000]))
    tot   = float(np.sum(fft))
    triggered = (hf / tot if tot > 0 else 0) < 0.01
    return triggered, (
        "Missing high-frequency components — AI lacks natural noise above 8kHz"
        if triggered else "High-frequency content present — consistent with real recording"
    )

def _check_silence_ratio(y, sr):
    triggered = float(np.sum(np.abs(y) < 0.01)) / len(y) > 0.50
    return triggered, (
        "Unusually high silence ratio — may indicate spliced or synthesized audio"
        if triggered else "Normal silence distribution"
    )

def _check_zcr_regularity(y, sr):
    triggered = float(np.std(librosa.feature.zero_crossing_rate(y)[0])) < 0.02
    return triggered, (
        "Mechanical zero-crossing regularity — indicates possible AI synthesis"
        if triggered else "Natural zero-crossing variation detected"
    )

def run_rule_checks(y, sr):
    checks = {
        "breathing":      _check_breathing(y, sr),
        "pitch_variance": _check_pitch_variance(y, sr),
        "formant":        _check_formants(y, sr),
        "spectral_flat":  _check_spectral_flatness(y, sr),
        "hf_energy":      _check_hf_energy(y, sr),
        "silence_ratio":  _check_silence_ratio(y, sr),
        "zcr_regularity": _check_zcr_regularity(y, sr),
    }
    findings, triggered = [], {}
    for name, (fired, detail) in checks.items():
        triggered[name] = fired
        findings.append(("⚠️ " if fired else "✅ ") + detail)
    return findings, triggered

def rule_score(triggered):
    score = 0.10 + sum(SIGNAL_WEIGHTS[k] for k, v in triggered.items() if v)
    return min(score, 0.95)


# ─────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

def detect_voice(audio_path):
    try:
        vec, y, sr = extract_features(audio_path)

        if vec is None:
            return {"error": "Could not extract audio features — use WAV format for best results."}

        duration = librosa.get_duration(y=y, sr=sr)
        if duration < 0.5:
            return {"error": "Audio too short — please upload at least 1 second."}

        # ML inference
        ml_prob, method = ml_predict(vec)

        # Rule-based checks
        findings, triggered = run_rule_checks(y, sr)
        r_score   = rule_score(triggered)
        rule_hits = sum(triggered.values())

        # Blend
        if ml_prob is not None:
            final_score      = 0.75 * ml_prob + 0.25 * r_score
            detection_method = "ML model + rule checks"
        else:
            final_score      = r_score
            detection_method = "Rule-based only — run train_voice_model.py for better accuracy"

        label      = "SYNTHETIC" if final_score > THRESHOLD else "AUTHENTIC"
        confidence = int(final_score * 100) if label == "SYNTHETIC" else int((1 - final_score) * 100)

        return {
            "score":            final_score,
            "label":            label,
            "confidence":       confidence,
            "findings":         findings,
            "duration":         round(duration, 1),
            "rule_hits":        rule_hits,
            "total_checks":     len(triggered),
            "sample_rate":      sr,
            "signal_scores":    {n: {"triggered": v, "weight": SIGNAL_WEIGHTS[n]} for n, v in triggered.items()},
            "ml_score":         round(ml_prob, 3) if ml_prob is not None else None,
            "rule_score":       round(r_score, 3),
            "detection_method": detection_method,
            "model_trained":    ml_prob is not None,
        }

    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}
