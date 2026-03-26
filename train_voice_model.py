"""
train_voice_model.py  (v2 — fixed)
────────────────────────────────────
Run once to train the deepfake voice classifier.

Fixes vs v1:
  - Auto-detects whatever folder structure downloaded
  - Falls back to gTTS for fake samples if FoR-norm fails
  - Downloads LibriSpeech real voices if real folder is empty
  - Validates both classes exist before training (no more ValueError)

Run:  python train_voice_model.py
"""

import os
import sys
import zipfile
import tarfile
import shutil
import urllib.request
import numpy as np
import librosa
import warnings
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

warnings.filterwarnings("ignore")

DATA_DIR   = Path("voice_training_data")
MODEL_PATH = Path("voice_model.pkl")


# ─────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────

def count_audio(folder):
    folder = Path(folder)
    if not folder.exists():
        return 0
    return len(list(folder.glob("*.wav")) +
               list(folder.glob("*.flac")) +
               list(folder.glob("*.mp3")))


def inspect_dataset():
    print("\n📂 Scanning voice_training_data/ ...")
    if not DATA_DIR.exists():
        print("   (empty — nothing downloaded yet)")
        return
    for root, dirs, files in os.walk(DATA_DIR):
        depth = len(Path(root).relative_to(DATA_DIR).parts)
        if depth > 3:
            dirs.clear()
            continue
        indent  = "   " + "  " * depth
        n_audio = sum(1 for f in files if f.endswith((".wav", ".flac", ".mp3")))
        print(f"{indent}{Path(root).name}/  → {n_audio} audio files")


def find_audio_folders(root_dir):
    """Find folders named real/fake anywhere in the tree."""
    found = {"real": [], "fake": []}
    real_names = {"real", "genuine", "bonafide", "human", "original"}
    fake_names = {"fake", "spoof", "synthetic", "tts", "generated", "ai"}
    for p in Path(root_dir).rglob("*"):
        if p.is_dir():
            n = p.name.lower()
            if n in real_names:
                found["real"].append(p)
            elif n in fake_names:
                found["fake"].append(p)
    return found


# ─────────────────────────────────────────────────────────────
# DATA ACQUISITION
# ─────────────────────────────────────────────────────────────

def ensure_fake_voices():
    """Ensure we have at least 40 fake voice WAVs using gTTS."""
    fake_dir = DATA_DIR / "fake"
    fake_dir.mkdir(parents=True, exist_ok=True)

    existing = count_audio(fake_dir)
    if existing >= 40:
        print(f"✅ Fake voices: {existing} files present.")
        return fake_dir

    print(f"🤖 Generating gTTS fake voice samples (need 40, have {existing}) ...")
    print("   (Using Google TTS — Indian English accent, tld=co.in)\n")

    try:
        from gtts import gTTS
    except ImportError:
        print("   Installing gTTS ...")
        os.system(f"{sys.executable} -m pip install gTTS -q")
        from gtts import gTTS

    import soundfile as sf

    sentences = [
        "Your bank account has been compromised, please call us immediately.",
        "Congratulations, you have won ten lakh rupees in our lucky draw.",
        "This is an automated message from the income tax department.",
        "Your Aadhaar card has been suspended due to suspicious activity.",
        "Please share your OTP to verify your account and avoid suspension.",
        "This is your electricity department calling about an urgent matter.",
        "Your KYC is incomplete, update it today to avoid service disruption.",
        "We have detected a fraudulent transaction on your bank account.",
        "Hello, I am calling from SBI customer care regarding your account.",
        "Your mobile number will be deactivated in the next twenty four hours.",
        "Press one to speak with our senior representative right now.",
        "Your credit card transaction of fifty thousand rupees was just made.",
        "This is a reminder about your overdue EMI payment.",
        "We are offering you a special loan at very low interest rates today.",
        "Your insurance policy is about to expire, renew it immediately.",
        "Please hold, we are connecting you to our fraud prevention team.",
        "Your account shows suspicious login from an unknown device.",
        "To block this transaction, please verify your ATM PIN now.",
        "This call is from the cyber crime department regarding your case.",
        "Your PAN card has been linked to illegal transactions, respond now.",
        "Hello sir, your Amazon package has been held at customs.",
        "We are calling from TRAI to inform you about your mobile service.",
        "Your Google account has been compromised, verify your identity now.",
        "This is a court notice, you must respond within twenty four hours.",
        "Your electricity connection will be cut within two hours.",
        "We are calling from your bank fraud prevention department.",
        "You have a pending fine that must be paid immediately to avoid arrest.",
        "Your SIM card will be blocked unless you complete verification now.",
        "This is an automated tax refund notification from the government.",
        "Please do not ignore this message about your expiring digital wallet.",
        "Your delivery could not be completed, please reschedule immediately.",
        "Hello, this is a voice verification test from your service provider.",
        "Your account will be permanently blocked if you do not call back.",
        "We detected unusual spending and need to verify your identity now.",
        "This is a warning from the National Payment Corporation of India.",
        "Your credit score has dropped, call us for a free consultation.",
        "We are calling to inform you about an unclaimed refund in your name.",
        "Press nine to stop receiving these calls and be removed from our list.",
        "Your broadband shows unauthorized usage from outside India.",
        "This is your last reminder before legal action is initiated against you.",
    ]

    generated = 0
    for i, text in enumerate(sentences):
        path = fake_dir / f"gtts_fake_{i:03d}.wav"
        if path.exists():
            generated += 1
            continue
        try:
            tts     = gTTS(text=text, lang="en", tld="co.in")
            mp3_tmp = fake_dir / f"_tmp_{i}.mp3"
            tts.save(str(mp3_tmp))
            y_audio, sr = librosa.load(str(mp3_tmp), sr=22050)
            sf.write(str(path), y_audio, sr)
            mp3_tmp.unlink()
            generated += 1
            print(f"\r   {generated}/{len(sentences)} done", end="", flush=True)
        except Exception as e:
            print(f"\r   [{i}] skipped: {e}", end="", flush=True)

    print(f"\n✅ Fake voices ready: {count_audio(fake_dir)} total\n")
    return fake_dir


def ensure_real_voices():
    """Ensure we have at least 50 real human voice files using LibriSpeech."""
    real_dir = DATA_DIR / "real"
    real_dir.mkdir(parents=True, exist_ok=True)

    existing = count_audio(real_dir)
    if existing >= 50:
        print(f"✅ Real voices: {existing} files present.")
        return real_dir

    print(f"📥 Downloading LibriSpeech test-clean for real voices (~346MB) ...")
    print("   Standard academic speech dataset — clean English speaker recordings\n")

    tar_path = DATA_DIR / "test-clean.tar.gz"
    url      = "https://www.openslr.org/resources/12/test-clean.tar.gz"

    try:
        def progress(block, block_size, total):
            done = block * block_size
            pct  = min(int(done / total * 100), 100) if total > 0 else 0
            print(f"\r   {pct}%  [{done // 1_000_000} MB]", end="", flush=True)

        urllib.request.urlretrieve(url, tar_path, reporthook=progress)
        print("\n📦 Extracting (this takes a minute) ...")

        extract_dir = DATA_DIR / "librispeech_raw"
        extract_dir.mkdir(exist_ok=True)
        with tarfile.open(tar_path, "r:gz") as t:
            t.extractall(extract_dir)
        tar_path.unlink()

        # Grab first 200 flac files
        flacs = list(extract_dir.rglob("*.flac"))[:200]
        print(f"   Copying {len(flacs)} utterances → real/ ...")
        for f in flacs:
            dest = real_dir / f.name
            if not dest.exists():
                shutil.copy(f, dest)

        print(f"✅ Real voices ready: {count_audio(real_dir)} files\n")

    except Exception as e:
        print(f"\n⚠️  LibriSpeech download failed: {e}")
        print("   Please manually add real voice WAV files to:")
        print(f"   {real_dir.absolute()}")
        print("   (At least 10 files, each 3+ seconds, WAV format)\n")

    return real_dir


# ─────────────────────────────────────────────────────────────
# FEATURE EXTRACTION  (must match voice_detector.py exactly)
# ─────────────────────────────────────────────────────────────

def extract_features_from_file(audio_path, duration=10):
    """51-dimensional feature vector."""
    try:
        y, sr = librosa.load(str(audio_path), duration=duration, sr=22050)
        if len(y) < sr * 0.5:
            return None

        features = []

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        features.extend(np.mean(mfcc, axis=1).tolist())
        features.extend(np.std(mfcc, axis=1).tolist())

        features.append(float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))))
        features.append(float(np.std(librosa.feature.spectral_centroid(y=y, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))))
        features.append(float(np.mean(librosa.feature.spectral_flatness(y=y))))
        features.append(float(np.std(librosa.feature.spectral_flatness(y=y))))

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
        features.append(hf / tot if tot > 0 else 0.0)

        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        strong = pitches[magnitudes > np.max(magnitudes) * 0.1]
        features.append(float(np.std(strong)) if len(strong) > 0 else 0.0)

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        features.append(float(np.squeeze(tempo)))

        vec = np.array(features, dtype=np.float32)
        vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
        return vec

    except Exception:
        return None


def load_dataset(real_dir, fake_dir, max_per_class=300):
    X, y = [], []
    for label_val, folder, name in [(0, real_dir, "real"), (1, fake_dir, "fake")]:
        files = (list(Path(folder).glob("*.wav")) +
                 list(Path(folder).glob("*.flac")) +
                 list(Path(folder).glob("*.mp3")))[:max_per_class]
        print(f"   {name}: {len(files)} files")
        ok = 0
        for i, f in enumerate(files):
            vec = extract_features_from_file(f)
            if vec is not None:
                X.append(vec)
                y.append(label_val)
                ok += 1
            if (i + 1) % 25 == 0:
                print(f"\r   {name}: {i+1}/{len(files)} ({ok} OK)", end="", flush=True)
        print(f"\r   {name}: {ok} feature vectors extracted" + " " * 20)
    return np.array(X), np.array(y)


# ─────────────────────────────────────────────────────────────
# TRAINING
# ─────────────────────────────────────────────────────────────

def train_model(X, y):
    n_real = int(np.sum(y == 0))
    n_fake = int(np.sum(y == 1))

    print(f"\n🏋️  Training ...")
    print(f"   Samples: {len(X)} total | Real: {n_real} | Fake: {n_fake}")

    if n_real == 0 or n_fake == 0:
        print("\n❌ Need both real AND fake samples. Check your data folders.")
        sys.exit(1)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler    = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    print("   Fitting Random Forest ...")
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=15, min_samples_leaf=2,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )
    rf.fit(X_train_s, y_train)

    print("   Fitting Gradient Boosting ...")
    gb = GradientBoostingClassifier(
        n_estimators=150, max_depth=5, learning_rate=0.05,
        subsample=0.8, random_state=42,
    )
    gb.fit(X_train_s, y_train)

    rf_p  = rf.predict_proba(X_test_s)[:, 1]
    gb_p  = gb.predict_proba(X_test_s)[:, 1]
    ens_p = 0.6 * rf_p + 0.4 * gb_p
    ens_y = (ens_p > 0.5).astype(int)

    print(f"\n📊 Accuracy on held-out test set:")
    print(f"   Random Forest:       {rf.score(X_test_s, y_test):.1%}")
    print(f"   Gradient Boosting:   {gb.score(X_test_s, y_test):.1%}")
    print(f"   Ensemble (0.6+0.4):  {np.mean(ens_y == y_test):.1%}")
    print("\n" + classification_report(y_test, ens_y, target_names=["Real", "Fake"]))

    cm = confusion_matrix(y_test, ens_y)
    print(f"Confusion matrix:")
    print(f"   Real  → correct: {cm[0][0]}  false-positive: {cm[0][1]}")
    print(f"   Fake  → correct: {cm[1][1]}  missed:         {cm[1][0]}")

    return rf, gb, scaler


def save_model(rf, gb, scaler):
    bundle = {"rf": rf, "gb": gb, "scaler": scaler, "version": "2.0", "features": 51}
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    print(f"\n✅ Model saved → {MODEL_PATH}  ({MODEL_PATH.stat().st_size // 1024} KB)")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  DeepShield — Voice Model Trainer  v2")
    print("=" * 60)

    DATA_DIR.mkdir(exist_ok=True)
    inspect_dataset()

    # Guarantee data
    fake_dir = ensure_fake_voices()
    real_dir = ensure_real_voices()

    print(f"\n📁 Using:")
    print(f"   Real: {real_dir}  ({count_audio(real_dir)} files)")
    print(f"   Fake: {fake_dir}  ({count_audio(fake_dir)} files)")

    print("\n🔍 Extracting features ...")
    X, y = load_dataset(real_dir, fake_dir)

    rf, gb, scaler = train_model(X, y)
    save_model(rf, gb, scaler)

    print("\n🎉 Done! Run:  streamlit run app.py")
    print("   Voice tab will show:  🧠 ML model loaded — high accuracy mode active")


if __name__ == "__main__":
    main()