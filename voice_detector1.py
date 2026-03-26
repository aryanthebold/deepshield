from pyexpat import features

import librosa
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

def extract_features(audio_path):
    try:
        y, sr = librosa.load(audio_path, duration=30, sr=22050)

        if len(y) < sr * 0.5:
            return None, None, None

        features = []

        # MFCC — captures vocal tract characteristics
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        features.extend(np.mean(mfcc, axis=1))
        features.extend(np.std(mfcc, axis=1))

        # Chroma — pitch class profiles
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features.extend(np.mean(chroma, axis=1))

        # Spectral features
        features.append(float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))))

        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)
        features.append(float(np.mean(zcr)))
        features.append(float(np.std(zcr)))

        # RMS energy
        rms = librosa.feature.rms(y=y)
        features.append(float(np.mean(rms)))
        features.append(float(np.std(rms)))

        # Tempo
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        features.append(float(np.squeeze(tempo)))
        return np.array(features), y, sr

    except Exception as e:
        return None, None, None

def rule_based_voice_checks(y, sr):
    findings = []
    try:
        # Check 1: Breathing pattern (RMS variance)
        rms = librosa.feature.rms(y=y)[0]
        if np.std(rms) < 0.005:
            findings.append("Breathing pattern absent — natural voices have energy variation between words")

        # Check 2: Pitch consistency
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_vals = pitches[magnitudes > np.max(magnitudes) * 0.1]
        if len(pitch_vals) > 0 and np.std(pitch_vals) < 10:
            findings.append("Unnaturally consistent pitch — human voices naturally vary in tone")

        # Check 3: Silence ratio
        silent = np.sum(np.abs(y) < 0.01)
        if silent / len(y) > 0.45:
            findings.append("Unusually high silence ratio — may indicate spliced or synthesized audio")

        # Check 4: High frequency content
        fft = np.abs(np.fft.fft(y))
        freqs = np.fft.fftfreq(len(fft), 1 / sr)
        hf_energy = np.sum(fft[freqs > 8000])
        total_energy = np.sum(fft)
        if total_energy > 0 and (hf_energy / total_energy) < 0.01:
            findings.append("Missing high-frequency components — AI voices often lack natural noise above 8kHz")

        # Check 5: ZCR variance
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        if np.std(zcr) < 0.02:
            findings.append("Mechanical zero-crossing regularity — indicates possible AI synthesis")

    except Exception:
        pass

    return findings if findings else ["No specific voice anomalies detected"]


def detect_voice(audio_path):
    try:
        features, y, sr = extract_features(audio_path)

        if features is None:
            return {"error": "Could not extract audio features — check file format"}

        duration = librosa.get_duration(y=y, sr=sr)
        if duration < 0.5:
            return {"error": "Audio too short — please upload at least 1 second"}

        findings = rule_based_voice_checks(y, sr)
        rule_hits = len([f for f in findings if "No specific" not in f])

        # Score: 0 rules=0.20, 1=0.38, 2=0.56, 3=0.74, 4+=0.88
        score = min(0.20 + rule_hits * 0.18, 0.92)
        label = "SYNTHETIC" if score > 0.45 else "AUTHENTIC"
        confidence = int(score * 100) if label == "SYNTHETIC" else int((1 - score) * 100)

        return {
            "score": score,
            "label": label,
            "confidence": confidence,
            "findings": findings,
            "duration": round(duration, 1),
            "rule_hits": rule_hits,
            "sample_rate": sr
        }

    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}