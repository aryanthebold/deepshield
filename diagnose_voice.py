"""
diagnose_voice.py
─────────────────
Run this to see exactly what's happening with your audio file.

Usage:
    python diagnose_voice.py your_audio_file.wav

It will print:
  - Whether voice_model.pkl loads correctly
  - The raw ML score (before blending)
  - The raw rule score
  - Every signal that fired
  - The blended final score
  - Why it might be misclassifying
"""

import sys
import pickle
import numpy as np
import librosa
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

MODEL_PATH = Path("voice_model.pkl")


def load_model():
    if not MODEL_PATH.exists():
        print("❌ voice_model.pkl NOT FOUND in current directory")
        print(f"   Looking in: {Path('.').absolute()}")
        return None
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)
    print(f"✅ Model loaded — version {bundle.get('version', '?')}")
    print(f"   RF estimators: {bundle['rf'].n_estimators}")
    print(f"   GB estimators: {bundle['gb'].n_estimators}")
    print(f"   Feature dims:  {bundle['features']}")

    # Report what it was trained on
    rf = bundle["rf"]
    classes = rf.classes_
    print(f"   Classes seen during training: {classes}  (0=real, 1=fake)")
    n_real_leaves = int(np.sum(rf.feature_importances_ > 0))
    print(f"   Top feature importances (first 5): {rf.feature_importances_[:5].round(4)}")
    return bundle


def extract_features(audio_path):
    y, sr = librosa.load(str(audio_path), duration=10, sr=22050)
    print(f"\n🎵 Audio loaded:")
    print(f"   Duration: {librosa.get_duration(y=y, sr=sr):.1f}s")
    print(f"   Sample rate: {sr} Hz")
    print(f"   RMS energy mean: {float(np.mean(librosa.feature.rms(y=y))):.5f}")
    print(f"   RMS energy std:  {float(np.std(librosa.feature.rms(y=y))):.5f}")

    features = []

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features.extend(np.mean(mfcc, axis=1).tolist())
    features.extend(np.std(mfcc, axis=1).tolist())

    sc = librosa.feature.spectral_centroid(y=y, sr=sr)
    features.append(float(np.mean(sc)))
    features.append(float(np.std(sc)))
    features.append(float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))))
    features.append(float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))))
    flat = librosa.feature.spectral_flatness(y=y)
    features.append(float(np.mean(flat)))
    features.append(float(np.std(flat)))

    rms = librosa.feature.rms(y=y)[0]
    features.append(float(np.mean(rms)))
    features.append(float(np.std(rms)))

    zcr = librosa.feature.zero_crossing_rate(y)[0]
    features.append(float(np.mean(zcr)))
    features.append(float(np.std(zcr)))

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    features.extend(np.mean(chroma, axis=1).tolist())

    fft   = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1 / sr)
    hf    = float(np.sum(fft[freqs > 8000]))
    tot   = float(np.sum(fft))
    hf_ratio = hf / tot if tot > 0 else 0.0
    features.append(hf_ratio)
    print(f"   HF energy ratio (>8kHz): {hf_ratio:.5f}  (AI voices: < 0.01)")

    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    strong = pitches[magnitudes > np.max(magnitudes) * 0.1]
    pitch_std = float(np.std(strong)) if len(strong) > 0 else 0.0
    features.append(pitch_std)
    print(f"   Pitch std: {pitch_std:.2f}  (AI voices: < 15)")

    flat_mean = float(np.mean(flat))
    print(f"   Spectral flatness mean: {flat_mean:.6f}  (AI voices: < 0.005)")

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    features.append(float(np.squeeze(tempo)))

    vec = np.array(features, dtype=np.float32)
    vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
    return vec, y, sr


def run_rules(y, sr):
    print("\n📏 Rule-based signals:")

    signals = {}

    # Breathing
    rms_std = float(np.std(librosa.feature.rms(y=y, hop_length=512)[0]))
    fired = rms_std < 0.005
    signals["breathing"] = fired
    print(f"   {'⚠️ ' if fired else '✅ '} Breathing (RMS std={rms_std:.5f}, threshold=0.005): {'FIRED' if fired else 'ok'}")

    # Pitch variance
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    strong = pitches[magnitudes > np.max(magnitudes) * 0.1]
    pitch_std = float(np.std(strong)) if len(strong) > 0 else 0
    fired = pitch_std < 15
    signals["pitch"] = fired
    print(f"   {'⚠️ ' if fired else '✅ '} Pitch variance (std={pitch_std:.2f}, threshold=15): {'FIRED' if fired else 'ok'}")

    # Spectral flatness
    flat_mean = float(np.mean(librosa.feature.spectral_flatness(y=y)[0]))
    fired = flat_mean < 0.005
    signals["spectral_flat"] = fired
    print(f"   {'⚠️ ' if fired else '✅ '} Spectral flatness (mean={flat_mean:.6f}, threshold=0.005): {'FIRED' if fired else 'ok'}")

    # HF energy
    fft   = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1 / sr)
    ratio = float(np.sum(fft[freqs > 8000])) / float(np.sum(fft))
    fired = ratio < 0.01
    signals["hf_energy"] = fired
    print(f"   {'⚠️ ' if fired else '✅ '} HF energy ratio ({ratio:.5f}, threshold=0.01): {'FIRED' if fired else 'ok'}")

    # Silence ratio
    sil = float(np.sum(np.abs(y) < 0.01)) / len(y)
    fired = sil > 0.50
    signals["silence"] = fired
    print(f"   {'⚠️ ' if fired else '✅ '} Silence ratio ({sil:.3f}, threshold=0.50): {'FIRED' if fired else 'ok'}")

    # ZCR
    zcr_std = float(np.std(librosa.feature.zero_crossing_rate(y)[0]))
    fired = zcr_std < 0.02
    signals["zcr"] = fired
    print(f"   {'⚠️ ' if fired else '✅ '} ZCR regularity (std={zcr_std:.5f}, threshold=0.02): {'FIRED' if fired else 'ok'}")

    hits = sum(signals.values())
    rule_s = min(0.10 + hits * 0.15, 0.95)
    print(f"\n   Signals fired: {hits}/6")
    print(f"   Rule score: {rule_s:.3f}")
    return rule_s


def main():
    if len(sys.argv) < 2:
        print("Usage: python diagnose_voice.py your_audio.wav")
        print("\nNo file given — using a test tone instead to check model loading.")
        audio_path = None
    else:
        audio_path = sys.argv[1]
        if not Path(audio_path).exists():
            print(f"❌ File not found: {audio_path}")
            sys.exit(1)

    print("=" * 60)
    print("  DeepShield Voice Diagnostics")
    print("=" * 60)

    # 1. Model check
    print("\n🔍 Checking model ...")
    bundle = load_model()

    if audio_path is None:
        print("\n(No audio file provided — model check complete)")
        return

    # 2. Feature extraction
    print("\n🔍 Extracting features ...")
    vec, y, sr = extract_features(audio_path)

    # 3. ML score
    if bundle:
        X = bundle["scaler"].transform(vec.reshape(1, -1))
        rf_prob = bundle["rf"].predict_proba(X)[0][1]
        gb_prob = bundle["gb"].predict_proba(X)[0][1]
        ml_score = 0.6 * rf_prob + 0.4 * gb_prob
        print(f"\n🤖 ML scores:")
        print(f"   Random Forest P(fake):       {rf_prob:.3f}")
        print(f"   Gradient Boosting P(fake):   {gb_prob:.3f}")
        print(f"   Ensemble ML score:           {ml_score:.3f}")
    else:
        ml_score = None
        print("\n⚠️  No model — skipping ML score")

    # 4. Rule score
    rule_s = run_rules(y, sr)

    # 5. Final blend
    print("\n📊 Final score calculation:")
    if ml_score is not None:
        final = 0.75 * ml_score + 0.25 * rule_s
        print(f"   0.75 × ML({ml_score:.3f}) + 0.25 × rules({rule_s:.3f}) = {final:.3f}")
    else:
        final = rule_s
        print(f"   Rules only: {final:.3f}")

    label = "SYNTHETIC" if final > 0.50 else "AUTHENTIC"
    print(f"\n{'🤖 RESULT: SYNTHETIC' if label == 'SYNTHETIC' else '✅ RESULT: AUTHENTIC'}")
    print(f"   Final score: {final:.3f}  (threshold: 0.50)")

    # 6. Diagnosis
    print("\n💡 Diagnosis:")
    if ml_score is not None and ml_score < 0.40:
        print("   ⚠️  ML model is scoring LOW on fake probability.")
        print("   This usually means the model trained mostly on clean TTS")
        print("   but your test file has PHONE/MIC distortion added on top,")
        print("   which makes it look different from training data.")
        print("   → Fix: retrain with phone-recorded AI voice samples too.")
    if rule_s < 0.40:
        print("   ⚠️  Rules aren't firing either.")
        print("   Phone recording adds noise/room echo that masks AI artifacts.")
        print("   Spectral flatness and HF energy thresholds may need loosening.")
    if ml_score is not None and ml_score > 0.60:
        print("   ✅ ML model IS detecting fake — check if app.py is loading")
        print("   the new voice_detector.py (restart Streamlit fully).")


if __name__ == "__main__":
    main()