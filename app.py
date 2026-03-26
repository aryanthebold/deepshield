import streamlit as st
from PIL import Image
import tempfile
import os
from image_detector import detect_image

# Page config
st.set_page_config(
    page_title="DeepShield",
    page_icon="🛡️",
    layout="centered"
)

# Header
st.title("🛡️ DeepShield")
st.markdown("**AI-powered deepfake detection — built for India**")
st.info("47% of Indian adults have encountered an AI voice or image scam. DeepShield fights back.")

st.divider()

# Tabs for each module
tab1, tab2, tab3, tab4 = st.tabs(["🖼️ Image", "🎬 Video", "🎙️ Voice", "💬 WhatsApp"])

with tab1:
    st.header("Image Deepfake Detector")
    st.write("Upload any image to check if it's AI-generated or manipulated.")

    uploaded_file = st.file_uploader(
        "Choose an image...",
        type=["jpg", "jpeg", "png", "webp"],
        key="image_upload"
    )

    if uploaded_file is not None:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        # Show the uploaded image
        col1, col2 = st.columns(2)
        with col1:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

        with col2:
            with st.spinner("Analyzing image..."):
                result = detect_image(tmp_path)

            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                score = result["score"]
                label = result["label"]
                confidence = result["confidence"]

                # Verdict
                if label == "SYNTHETIC":
                    st.error(f"DEEPFAKE DETECTED")
                    st.metric("Synthetic probability", f"{int(score*100)}%")
                else:
                    st.success(f"LOOKS AUTHENTIC")
                    st.metric("Authenticity score", f"{confidence}%")

                # Confidence bar
                st.progress(score if label == "SYNTHETIC" else 1 - score)

                # Explainability
                st.subheader("Why did we flag this?")
                for finding in result["findings"]:
                    if "No specific" in finding:
                        st.write(f"✅ {finding}")
                    else:
                        st.write(f"⚠️ {finding}")

        # Cleanup
        os.unlink(tmp_path)

with tab2:
    st.header("Video Deepfake Detector")
    st.write("Upload a video to analyze it frame by frame for deepfake artifacts.")

    uploaded_video = st.file_uploader(
        "Choose a video...",
        type=["mp4", "avi", "mov", "mkv"],
        key="video_upload"
    )

    if uploaded_video is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded_video.getvalue())
            tmp_path = tmp.name

        st.video(uploaded_video)

        with st.spinner("Analyzing video frames... this may take 30-60 seconds"):
            from video_detector import detect_video
            result = detect_video(tmp_path)

        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            score = result["score"]
            label = result["label"]

            if label == "SYNTHETIC":
                st.error("DEEPFAKE DETECTED")
                st.metric("Synthetic probability", f"{int(score*100)}%")
            else:
                st.success("LOOKS AUTHENTIC")
                st.metric("Authenticity score", f"{result['confidence']}%")

            # Frame analysis breakdown
            col1, col2, col3 = st.columns(3)
            col1.metric("Frames analyzed", result["total_frames_analyzed"])
            col2.metric("Suspicious frames", result["suspicious_frames"])
            col3.metric("Video duration", f"{result['duration']}s")

            # Frame-by-frame score chart
            if result["frame_scores"]:
                st.subheader("Frame-by-frame analysis")
                import pandas as pd
                chart_data = pd.DataFrame({
                    "Frame": range(1, len(result["frame_scores"]) + 1),
                    "Synthetic score": result["frame_scores"]
                })
                st.line_chart(chart_data.set_index("Frame"))
                st.caption("Spikes indicate potentially manipulated frames")

            # Explainability
            st.subheader("Why did we flag this?")
            for finding in result["findings"]:
                st.write(f"⚠️ {finding}")

        os.unlink(tmp_path)

# ── TAB 3 — VOICE  (replace existing tab3 block in app.py) ──────────────────
with tab3:
    st.header("Voice Deepfake Detector")
    st.write("Upload an audio clip to detect AI-cloned or synthetic voices.")

    # Show whether ML model is loaded
    from pathlib import Path
    if Path("voice_model.pkl").exists():
        st.success("🧠 ML model loaded — high accuracy mode active")
    else:
        st.warning("⚠️ ML model not trained yet. Run `python train_voice_model.py` for best accuracy. Currently using rule-based detection only.")

    st.info("📁 Use **WAV files** — MP3/M4A require ffmpeg (not installed)")

    uploaded_audio = st.file_uploader(
        "Choose an audio file...",
        type=["wav", "mp3", "m4a", "ogg", "flac"],
        key="audio_upload"
    )

    if uploaded_audio is not None:
        suffix = "." + uploaded_audio.name.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_audio.getvalue())
            tmp_path = tmp.name

        st.audio(uploaded_audio)

        with st.spinner("Analyzing voice patterns..."):
            from voice_detector import detect_voice
            result = detect_voice(tmp_path)

        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            score = result["score"]
            label = result["label"]

            # ── Verdict ──────────────────────────────────────────
            if label == "SYNTHETIC":
                st.error("🤖 AI VOICE DETECTED")
            else:
                st.success("✅ VOICE APPEARS AUTHENTIC")

            st.progress(score)

            # ── Metrics ───────────────────────────────────────────
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(
                "Synthetic score" if label == "SYNTHETIC" else "Authenticity",
                f"{int(score * 100)}%" if label == "SYNTHETIC" else f"{result['confidence']}%"
            )
            col2.metric("Duration",        f"{result['duration']}s")
            col3.metric("Anomalies found", f"{result['rule_hits']} / {result['total_checks']}")
            col4.metric("Sample rate",     f"{result['sample_rate']} Hz")

            # ── Score breakdown ───────────────────────────────────
            if result.get("model_trained", False):
                st.subheader("Score breakdown")
                bc1, bc2, bc3 = st.columns(3)
                bc1.metric("ML model score",  f"{int(result['ml_score'] * 100)}%",
                           help="Random Forest + Gradient Boosting ensemble")
                bc2.metric("Rule-based score", f"{int(result['rule_score'] * 100)}%",
                           help="7 weighted acoustic signal checks")
                bc3.metric("Final (blended)",  f"{int(score * 100)}%",
                           help="75% ML + 25% rules")
                st.caption(f"Detection method: {result['detection_method']}")

            # ── Signal table ──────────────────────────────────────
            st.subheader("Signal analysis")
            import pandas as pd
            LABELS = {
                "breathing":      "Breathing pattern",
                "pitch_variance": "Pitch variation",
                "formant":        "Formant dynamics",
                "spectral_flat":  "Spectral texture",
                "hf_energy":      "High-freq energy (>8kHz)",
                "silence_ratio":  "Silence pattern",
                "zcr_regularity": "ZCR regularity",
            }
            rows = [
                {
                    "Signal":       LABELS.get(k, k),
                    "Result":       "⚠️ Suspicious" if v["triggered"] else "✅ Normal",
                    "Weight":       f"{int(v['weight']*100)}%",
                }
                for k, v in result["signal_scores"].items()
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # ── Findings ──────────────────────────────────────────
            with st.expander("Detailed findings"):
                for f in result["findings"]:
                    st.write(f)

            # ── Safety block ──────────────────────────────────────
            if label == "SYNTHETIC":
                st.warning("""
**If you received this as a call or voice note:**
- 🚫 Do NOT share OTP, Aadhaar, or bank details
- 📞 Hang up and call back on the **official number**
- 🌐 Report at [cybercrime.gov.in](https://cybercrime.gov.in) or call **1930**
- 👨‍👩‍👧 Alert your family about this scam
                """)

        os.unlink(tmp_path)

with tab4:
    st.header("WhatsApp Forward Checker")
    st.write("Coming on Day 5 — send suspicious media to our WhatsApp bot")
    st.info("Forward any suspicious image or voice note to our WhatsApp number for instant analysis.")