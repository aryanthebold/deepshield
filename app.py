import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import tempfile
import os

# Import your detectors
from image_detector import detect_image
# (Make sure to import your other detectors here if they aren't imported inside the tabs)

# 1. Page config MUST be the very first Streamlit command
st.set_page_config(
    page_title="DeepShield | AI Deepfake Detection",
    page_icon="🛡️",
    layout="wide", # Set to wide for the HTML homepage
    initial_sidebar_state="collapsed"
)

# 2. ROUTING LOGIC: Check the URL for '?page=dashboard'
if st.query_params.get("page") == "dashboard":
    
    # --- DASHBOARD VIEW (MODERNIZED) ---
    
    # Inject Custom Dashboard CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Apply custom font */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Gradient Title */
    .dashboard-title {
        background: linear-gradient(135deg, #00e560 0%, #007bb5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3.5rem;
        margin-bottom: -10px;
        padding-top: 15px;
    }
    
    /* Subtitle */
    .dashboard-subtitle {
        color: #a0aec0;
        font-size: 1.25rem;
        font-weight: 400;
        margin-bottom: 25px;
    }
    
    /* Glassmorphism Info Card */
    .info-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(14px);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        margin-bottom: 20px;
        border-left: 5px solid #00e560;
    }
    .info-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 40px rgba(0, 229, 96, 0.15);
        border-color: rgba(0, 229, 96, 0.3);
    }
    
    /* Styled Tabs */
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #a0aec0 !important;
        padding: 18px 25px !important;
        transition: all 0.3s ease-in-out !important;
        letter-spacing: 0.5px;
    }
    button[data-baseweb="tab"]:hover {
        background-color: rgba(0, 229, 96, 0.08) !important;
        color: #ffffff !important;
        border-radius: 12px 12px 0 0 !important;
    }
    button[aria-selected="true"] {
        color: #00e560 !important;
        border-bottom: 3px solid #00e560 !important;
        background-color: transparent !important;
    }
    
    /* File Uploader Hover Glow */
    [data-testid="stFileUploader"] {
        border-radius: 16px;
        border: 1px dashed rgba(255, 255, 255, 0.15);
        padding: 15px;
        transition: all 0.3s ease;
        background-color: rgba(0, 0, 0, 0.15);
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #00e560;
        background-color: rgba(0, 229, 96, 0.04);
        box-shadow: 0 0 15px rgba(0, 229, 96, 0.1);
    }
    
    /* Tab Headers */
    .tab-header {
        font-weight: 700;
        color: #f8fafc;
        margin-top: 15px;
        margin-bottom: 10px;
        font-size: 2rem;
    }
    
    </style>
    """, unsafe_allow_html=True)
    
    # Back button positioned nicely
    col_back, _ = st.columns([1, 6])
    with col_back:
        if st.button("⬅️ Back to Home", use_container_width=True):
            st.query_params.clear()
            st.rerun()
            
    st.markdown('<h1 class="dashboard-title">🛡️ DeepShield Workspace</h1>', unsafe_allow_html=True)
    st.markdown('<p class="dashboard-subtitle">Advanced AI forensics and analysis suite.</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <h4 style="margin:0px 0px 8px 0px; color:#00e560; font-weight:600;">⚡ Network Intelligence</h4>
        <p style="margin:0px; color:#e2e8f0; font-size:1.05rem; line-height:1.6;">
            47% of Indian adults have encountered an AI voice or image scam. 
            Upload media below to run it through our state-of-the-art forensic models and detect synthetic artifacts locally.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("") # Helper spacer

    # Tabs for each module
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🖼️ Image Forensics", "🎬 Video Analysis", "🎙️ Sonic Scan", "💬 WhatsApp Integration", "🤖 Telegram Bot"])

    with tab1:
        st.markdown("<div class='tab-header'>🖼️ Image Deepfake Detector</div>", unsafe_allow_html=True)
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
                st.image(uploaded_file, caption="Uploaded Image", width="stretch")

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
                    findings = result.get("findings", [])
                    
                    # Check if the text implies no anomalies, but the AI still flagged it
                    is_clean_findings = not findings or any("No specific" in f or "No anomalies" in f for f in findings)

                    if label == "SYNTHETIC" and is_clean_findings:
                        st.warning("⚠️ High synthetic probability detected by the core AI model, even though local forensic rules missed it.")
                    elif is_clean_findings:
                        st.success("✅ No anomalies detected.")
                    else:
                        for finding in findings:
                            if "No specific" in finding or "No anomalies" in finding:
                                st.success(f"✅ {finding}")
                            else:
                                st.warning(f"⚠️ {finding}")
            # Cleanup
            os.unlink(tmp_path)

    with tab2:
        st.markdown("<div class='tab-header'>🎬 Video Deepfake Detector</div>", unsafe_allow_html=True)
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

    # ── TAB 3 — VOICE ──────────────────
    with tab3:
        st.markdown("<div class='tab-header'>🎙️ Voice Deepfake Detector</div>", unsafe_allow_html=True)
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
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

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
        # --- Cinematic Header & Bilingual Subtitle ---
        st.markdown("<div class='tab-header'>💬 WhatsApp Bot Integration</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-family: \"Noto Sans Devanagari\", sans-serif; color: #a0a0a0; font-size: 1.1rem; margin-top: -15px;'>व्हाट्सएप बॉट एकीकरण</p>", 
            unsafe_allow_html=True
        )
        
        st.write("DeepShield works where 500 million Indians already are. No app downloads required — just forward suspicious media directly on WhatsApp for real-time analysis.")
        st.divider()

        col1, col2 = st.columns([1.2, 1])

        with col1:
            st.subheader("How to Use (Live Demo)")
            st.markdown("""
            **Step 1: Connect to the Sandbox**
            Save our Twilio Sandbox number to your phone contacts as *DeepShield*.
            
            **Step 2: Activate the Session**
            Send your Twilio join code (e.g., `join <your-sandbox-word>`) to the number to connect your phone to the local ngrok tunnel.
            
            **Step 3: Forward & Scan**
            Forward any suspicious image, video, or voice note directly to the chat. DeepShield will process the media and reply within 30 seconds with a plain-language verdict.
            """)
            
            # YESIST12 Pitch Framing
            st.info("💡 **Impact:** This approach bypasses the barrier of enterprise tools, bringing AI forensics directly to rural populations and elderly users who are highly vulnerable to UPI and voice cloning scams.")

        with col2:
            # --- Custom CSS for the Glowing Number Box ---
            st.markdown("""
            <style>
            .glow-box {
                background-color: #080c10;
                border: 2px solid #00e560;
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                box-shadow: 0 0 15px rgba(0, 229, 96, 0.2);
                animation: pulse-border 2.5s infinite alternate;
            }
            @keyframes pulse-border {
                from { box-shadow: 0 0 10px rgba(0, 229, 96, 0.1); border-color: rgba(0, 229, 96, 0.5); }
                to { box-shadow: 0 0 25px rgba(0, 229, 96, 0.6); border-color: #00e560; }
            }
            .wa-number {
                font-family: 'JetBrains Mono', monospace;
                font-size: 26px;
                color: #00e560;
                font-weight: bold;
                letter-spacing: 2px;
                margin: 10px 0;
            }
            .wa-status {
                display: inline-block;
                background-color: rgba(0, 229, 96, 0.1);
                color: #00e560;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 15px;
            }
            </style>
            
            <div class="glow-box">
                <div class="wa-status">🟢 ONLINE (NGROK TUNNEL)</div>
                <h3 style="color: white; margin-bottom: 0px;">DeepShield Bot</h3>
                <p style="color: #a0a0a0; font-size: 14px;">Twilio Sandbox Number</p>
                <p class="wa-number">+1 (415) 523-8886</p>
                <p style="color: #a0a0a0; font-size: 14px; margin-top: 15px;">Send your <b>join</b> code to activate</p>
            </div>
            """, unsafe_allow_html=True)

    with tab5:
        # --- Telegram Header & Bilingual Subtitle ---
        st.markdown("<div class='tab-header'>🤖 Telegram Bot Integration</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-family: \"Noto Sans Devanagari\", sans-serif; color: #a0a0a0; font-size: 1.1rem; margin-top: -15px;'>टेलीग्राम बॉट एकीकरण</p>", 
            unsafe_allow_html=True
        )
        
        st.write("DeepShield is also available seamlessly on Telegram. Forward any voice note, video, or image to our Telegram Bot to get an instant deepfake analysis report on the go.")
        st.divider()

        col1, col2 = st.columns([1.2, 1])

        with col1:
            st.subheader("How to Use (Live Demo)")
            st.markdown("""
            **Step 1: Find the Bot**
            Search for **@DeepShield_Bot** (or your configured bot username) on Telegram.
            
            **Step 2: Start the Chat**
            Tap **START** or send `/start` to activate the bot.
            
            **Step 3: Forward & Scan**
            Send or forward any suspicious image, video, or audio file directly to the chat. Our bot will process the media using the DeepShield engine and reply with a verdict instantly.
            """)
            
            st.info("💡 **Impact:** Telegram's fast and lightweight interface paired with our bot makes DeepShield accessible to anyone, anywhere—bridging the gap to easy, reliable AI forensics.")

        with col2:
            st.markdown("""
            <style>
            .telegram-glow-box {
                background-color: #0c1424;
                border: 2px solid #0088cc;
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                box-shadow: 0 0 15px rgba(0, 136, 204, 0.2);
                animation: tg-pulse-border 2.5s infinite alternate;
            }
            @keyframes tg-pulse-border {
                from { box-shadow: 0 0 10px rgba(0, 136, 204, 0.1); border-color: rgba(0, 136, 204, 0.5); }
                to { box-shadow: 0 0 25px rgba(0, 136, 204, 0.6); border-color: #0088cc; }
            }
            .tg-username {
                font-family: 'JetBrains Mono', monospace;
                font-size: 26px;
                color: #0088cc;
                font-weight: bold;
                letter-spacing: 1px;
                margin: 10px 0;
            }
            .tg-status {
                display: inline-block;
                background-color: rgba(0, 136, 204, 0.1);
                color: #0088cc;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 15px;
            }
            .tg-button {
                display: inline-block;
                background-color: #0088cc;
                color: white !important;
                text-decoration: none;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
                margin-top: 15px;
                transition: all 0.3s ease;
            }
            .tg-button:hover {
                background-color: #0077b3;
                box-shadow: 0 4px 10px rgba(0, 136, 204, 0.4);
                color: white !important;
            }
            </style>
            
            <div class="telegram-glow-box">
                <div class="tg-status">🔵 BOT ONLINE</div>
                <h3 style="color: white; margin-bottom: 0px;">DeepShield Telegram</h3>
                <p style="color: #a0a0a0; font-size: 14px;">Official Bot</p>
                <p class="tg-username">@DeepShield_Bot</p>
                <a href="https://t.me/deepshield_bot" target="_blank" class="tg-button">Open in Telegram</a>
            </div>
            """, unsafe_allow_html=True)

# 3. ROUTING LOGIC: Handle custom HTML pages
else:
    import html
    
    # Hide Streamlit chrome
    st.markdown("""
        <style>
            header { display: none !important; }
            .block-container { padding: 0rem !important; max-width: 100% !important; }
            [data-testid="collapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # Check which page the user wants (e.g. /?page=problem)
    page = st.query_params.get("page", "home")
    
    # Map the query param to the specific HTML file
    pages_map = {
        "problem": "problem.html",
        "solution": "solution.html",
        "how": "how.html",
        "compare": "compare.html"
    }
    
    # Default is the main landing page
    html_file = pages_map.get(page, "1.html")
    
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        safe_html = html.escape(html_content).replace('\n', '&#10;').replace('\r', '&#13;')

        # Render the iframe
        st.markdown(f"""
            <!-- Page: {page} -->
            <iframe
                key="{page}"
                srcdoc="{safe_html}"
                style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; border: none; z-index: 99999;"
                sandbox="allow-scripts allow-top-navigation allow-same-origin allow-popups"
            ></iframe>
        """, unsafe_allow_html=True)

    except FileNotFoundError:
        st.error(f"Could not find '{html_file}'. Please ensure it is in the same folder as app.py.")