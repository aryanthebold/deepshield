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

with tab3:
    st.header("Voice Deepfake Detector")
    st.write("Upload an audio clip to detect AI-cloned or synthetic voices.")

    st.info("Supports MP3, WAV, M4A — minimum 3 seconds of audio")

    uploaded_audio = st.file_uploader(
    "Choose an audio file...",
    type=["wav", "mp3", "m4a", "ogg", "flac"],
    key="audio_upload"
)

    if uploaded_audio is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(uploaded_audio.getvalue())
            tmp_path = tmp.name

        st.audio(uploaded_audio)

        with st.spinner("Analyzing voice patterns..."):
            from voice_detector import detect_voice
            result = detect_voice(tmp_path)

        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            score = result["score"]
            label = result["label"]

            if label == "SYNTHETIC":
                st.error("AI VOICE DETECTED")
                st.metric("Synthetic probability", f"{int(score*100)}%")
            else:
                st.success("VOICE APPEARS AUTHENTIC")
                st.metric("Authenticity score", f"{result['confidence']}%")

            st.progress(score)

            col1, col2 = st.columns(2)
            col1.metric("Audio duration", f"{result['duration']}s")
            col2.metric("Anomalies found", result["rule_hits"])

            st.subheader("Why did we flag this?")
            for finding in result["findings"]:
                if "No specific" in finding:
                    st.write(f"✅ {finding}")
                else:
                    st.write(f"⚠️ {finding}")

            st.subheader("What to do if you received this call?")
            st.warning("""
            1. Do NOT share OTP, Aadhaar, or bank details
            2. Hang up and call back on the official number
            3. Report to cybercrime.gov.in or call 1930
            4. Alert your family members
            """)

        os.unlink(tmp_path)

with tab4:
    st.header("WhatsApp Forward Checker")
    st.write("Coming on Day 5 — send suspicious media to our WhatsApp bot")
    st.info("Forward any suspicious image or voice note to our WhatsApp number for instant analysis.")