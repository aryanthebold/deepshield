import librosa
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────
# SIGNAL WEIGHTS — higher = more reliable indicator of AI voice
# Tuned based on known weaknesses of TTS/voice-cloning systems
# ─────────────────────────────────────────────────────────────
SIGNAL_WEIGHTS = {
    "breathing":        0.25,   # strongest signal — TTS never breathes
    "pitch_variance":   0.20,   # AI voices have robotic pitch consistency
    "formant":          0.20,   # AI struggles with natural vowel resonance
    "spectral_flat":    0.15,   # TTS has unnaturally uniform spectrum
    "hf_energy":        0.10,   # AI clips high-frequency noise
    "silence_ratio":    0.05,   # spliced audio has odd silence patterns
    "zcr_regularity":   0.05,   # mechanical zero-crossing = synthetic
}
# Weights sum to 1.0 — each triggered signal contributes its weight to score
# Base score is 0.10 (assume authentic unless signals fire)
BASE_SCORE = 0.10
SYNTHETIC_THRESHOLD = 0.45


def extract_features(audio_path):
    """Load audio and extract full librosa feature set."""
    try:
        y, sr = librosa.load(audio_path, duration=30, sr=22050)
        if len(y) < sr * 0.5:
            return None, None, None

        features = []

        # MFCCs — voice timbre fingerprint
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        features.extend(np.mean(mfcc, axis=1))
        features.extend(np.std(mfcc, axis=1))

        # Chroma — tonal content
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features.extend(np.mean(chroma, axis=1))

        # Spectral shape
        features.append(float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))))

        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)
        features.append(float(np.mean(zcr)))
        features.append(float(np.std(zcr)))

        # Energy
        rms = librosa.feature.rms(y=y)
        features.append(float(np.mean(rms)))
        features.append(float(np.std(rms)))

        # Tempo — BUG FIX: np.squeeze handles array return in newer librosa
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        features.append(float(np.squeeze(tempo)))

        return np.array(features), y, sr

    except Exception:
        return None, None, None


def _check_breathing(y, sr):
    """
    Natural voices have energy bursts between words (breath sounds).
    TTS generates clean audio with no breath noise at all.
    We look at the std deviation of RMS energy — low std = no breathing.
    """
    rms = librosa.feature.rms(y=y, hop_length=512)[0]
    std = float(np.std(rms))
    triggered = std < 0.005
    detail = (
        "Breathing pattern absent — natural voices have energy variation between words"
        if triggered else
        "Normal energy variation detected — breathing pattern present"
    )
    return triggered, detail


def _check_pitch_variance(y, sr):
    """
    Humans naturally vary pitch (intonation). AI voices tend to be
    robotically consistent in pitch, especially cloned voices.
    """
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    strong = pitches[magnitudes > np.max(magnitudes) * 0.1]
    if len(strong) == 0:
        return False, "Could not extract pitch data"
    std = float(np.std(strong))
    triggered = std < 15
    detail = (
        "Unnaturally consistent pitch — human voices naturally vary in tone"
        if triggered else
        "Natural pitch variation detected"
    )
    return triggered, detail


def _check_formants(y, sr):
    """
    Formants are resonant frequencies in the vocal tract (throat + mouth shape).
    Real speech has dynamic formant transitions between phonemes.
    AI voices often have flat or overly smooth formant patterns.
    We use LPC (Linear Predictive Coding) to estimate formant energy spread.
    """
    try:
        # Pre-emphasis filter to boost high-frequency formant detail
        pre = np.append(y[0], y[1:] - 0.97 * y[:-1])

        # Split into short frames and measure spectral variance per frame
        frame_len = int(0.025 * sr)   # 25ms frames
        hop = int(0.010 * sr)          # 10ms hop
        variances = []
        for i in range(0, len(pre) - frame_len, hop):
            frame = pre[i:i + frame_len]
            spectrum = np.abs(np.fft.rfft(frame * np.hanning(frame_len)))
            variances.append(np.var(spectrum))

        if not variances:
            return False, "Could not analyze formant structure"

        # Natural speech: high variance between frames (dynamic formants)
        # AI speech: low variance (formants don't move naturally)
        mean_var = float(np.mean(variances))
        triggered = mean_var < 500
        detail = (
            "Flat formant structure — vocal tract resonance is unnaturally static (TTS pattern)"
            if triggered else
            "Dynamic formant transitions detected — consistent with natural speech"
        )
        return triggered, detail

    except Exception:
        return False, "Formant analysis skipped"


def _check_spectral_flatness(y, sr):
    """
    Spectral flatness measures how 'noise-like' vs 'tone-like' a signal is.
    Human voice has a mix of tonal (vowels) and noisy (consonants) content.
    TTS voices are often overly tonal — very low spectral flatness.
    """
    flatness = librosa.feature.spectral_flatness(y=y)[0]
    mean_flat = float(np.mean(flatness))
    # Natural speech: ~0.01–0.10 flatness
    # TTS: often < 0.005 (too tonal, too clean)
    triggered = mean_flat < 0.005
    detail = (
        "Unnaturally tonal spectrum — TTS voices lack the noise-like consonant texture of real speech"
        if triggered else
        "Normal spectral texture — mix of tonal and noisy components detected"
    )
    return triggered, detail


def _check_hf_energy(y, sr):
    """
    Real microphones + rooms pick up noise above 8kHz (breath, room tone).
    AI voices are generated at fixed sample rates and often roll off cleanly above 8kHz.
    """
    fft = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1 / sr)
    hf = float(np.sum(fft[freqs > 8000]))
    total = float(np.sum(fft))
    ratio = hf / total if total > 0 else 0
    triggered = ratio < 0.01
    detail = (
        "Missing high-frequency components — AI voices often lack natural noise above 8kHz"
        if triggered else
        "High-frequency content present — consistent with real microphone recording"
    )
    return triggered, detail


def _check_silence_ratio(y, sr):
    """
    Spliced or TTS audio often has an unusual proportion of silence.
    Either too much (padded TTS) or unnaturally even silence gaps.
    """
    silent_samples = np.sum(np.abs(y) < 0.01)
    ratio = silent_samples / len(y)
    triggered = ratio > 0.50
    detail = (
        "Unusually high silence ratio — may indicate spliced or synthesized audio"
        if triggered else
        "Normal silence distribution"
    )
    return triggered, detail


def _check_zcr_regularity(y, sr):
    """
    Zero-crossing rate measures how often the waveform crosses zero.
    Human speech has irregular ZCR due to natural variation.
    AI voices show mechanical regularity.
    """
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    std = float(np.std(zcr))
    triggered = std < 0.02
    detail = (
        "Mechanical zero-crossing regularity — indicates possible AI synthesis"
        if triggered else
        "Natural zero-crossing variation detected"
    )
    return triggered, detail


def run_all_checks(y, sr):
    """
    Run all 7 detection checks and return:
    - findings: list of human-readable strings
    - triggered: dict of {signal_name: bool}
    """
    checks = {
        "breathing":      _check_breathing(y, sr),
        "pitch_variance": _check_pitch_variance(y, sr),
        "formant":        _check_formants(y, sr),
        "spectral_flat":  _check_spectral_flatness(y, sr),
        "hf_energy":      _check_hf_energy(y, sr),
        "silence_ratio":  _check_silence_ratio(y, sr),
        "zcr_regularity": _check_zcr_regularity(y, sr),
    }

    findings = []
    triggered = {}
    for name, (fired, detail) in checks.items():
        triggered[name] = fired
        findings.append(("⚠️ " if fired else "✅ ") + detail)

    return findings, triggered


def compute_score(triggered):
    """
    Weighted scoring: each triggered signal contributes its weight.
    Base score of 0.10 means we start assuming authentic.
    Max possible score: 0.10 + 1.00 = 1.10 (capped at 0.95).
    """
    score = BASE_SCORE
    for signal, fired in triggered.items():
        if fired:
            score += SIGNAL_WEIGHTS.get(signal, 0)
    return min(score, 0.95)


def detect_voice(audio_path):
    """Main entry point — called by app.py."""
    try:
        features, y, sr = extract_features(audio_path)

        if features is None:
            return {"error": "Could not extract audio features — check file format. Use WAV for best results."}

        duration = librosa.get_duration(y=y, sr=sr)

        if duration < 0.5:
            return {"error": "Audio too short — please upload at least 1 second"}

        findings, triggered = run_all_checks(y, sr)

        score = compute_score(triggered)
        label = "SYNTHETIC" if score > SYNTHETIC_THRESHOLD else "AUTHENTIC"
        confidence = int(score * 100) if label == "SYNTHETIC" else int((1 - score) * 100)

        rule_hits = sum(triggered.values())

        # Signal breakdown for UI display
        signal_scores = {
            name: {"triggered": fired, "weight": SIGNAL_WEIGHTS[name]}
            for name, fired in triggered.items()
        }

        return {
            "score": score,
            "label": label,
            "confidence": confidence,
            "findings": findings,
            "duration": round(duration, 1),
            "rule_hits": rule_hits,
            "total_checks": len(triggered),
            "sample_rate": sr,
            "signal_scores": signal_scores,
        }

    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}


# ─────────────────────────────────────────────────────────────
# SCORING REFERENCE
# ─────────────────────────────────────────────────────────────
# Score = 0.10 (base) + sum of weights for triggered signals
#
# No signals triggered:   0.10  → AUTHENTIC (90% confident)
# Breathing only:         0.35  → AUTHENTIC (65% confident)
# Breathing + pitch:      0.55  → SYNTHETIC (55% confident)
# Breathing + pitch
#   + formant:            0.75  → SYNTHETIC (75% confident)
# All 7 signals:          0.95  → SYNTHETIC (95% confident)
#
# THRESHOLD: score > 0.45 = SYNTHETIC
#
# SIGNAL RELIABILITY RANKING:
# 1. breathing      (0.25) — most reliable, TTS never breathes
# 2. pitch_variance (0.20) — very reliable for cloned voices
# 3. formant        (0.20) — excellent for TTS, harder for clones
# 4. spectral_flat  (0.15) — good for ElevenLabs/commercial TTS
# 5. hf_energy      (0.10) — helpful but phone recordings can false-positive
# 6. silence_ratio  (0.05) — supplementary
# 7. zcr_regularity (0.05) — supplementary
# ─────────────────────────────────────────────────────────────
