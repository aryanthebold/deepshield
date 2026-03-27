import streamlit as st
from PIL import Image
import tempfile
import os
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DeepShield — डीपशील्ड",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Noto+Sans+Devanagari:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Syne', 'Noto Sans Devanagari', sans-serif;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 780px;
}

/* ── Hero banner ── */
.ds-hero {
    background: linear-gradient(135deg, #0d1117 0%, #0f1f0f 50%, #0d1117 100%);
    border: 1px solid #1a3a1a;
    border-radius: 16px;
    padding: 2rem 2rem 1.5rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.ds-hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(0,255,80,0.07) 0%, transparent 70%);
    pointer-events: none;
}
.ds-hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin: 0 0 0.2rem 0;
}
.ds-hero-hindi {
    font-family: 'Noto Sans Devanagari', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #00cc44;
    margin: 0 0 0.8rem 0;
}
.ds-hero-tagline {
    font-size: 0.9rem;
    color: #8b949e;
    margin: 0;
    line-height: 1.5;
}
.ds-hero-stat {
    display: inline-block;
    background: rgba(0,204,68,0.1);
    border: 1px solid rgba(0,204,68,0.25);
    border-radius: 6px;
    padding: 0.25rem 0.7rem;
    font-size: 0.8rem;
    color: #00cc44;
    margin-top: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #0d1117;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #21262d;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 0.5rem 1.1rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: #8b949e;
    background: transparent;
    border: none;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: #161b22 !important;
    color: #00cc44 !important;
    border: 1px solid #1a3a1a !important;
}

/* ── Section header ── */
.ds-section-header {
    margin: 0.5rem 0 1.2rem 0;
}
.ds-section-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #e6edf3;
    margin: 0 0 0.15rem 0;
}
.ds-section-hindi {
    font-family: 'Noto Sans Devanagari', sans-serif;
    font-size: 0.95rem;
    color: #8b949e;
    margin: 0;
}

/* ── Verdict cards ── */
.verdict-card {
    border-radius: 14px;
    padding: 1.4rem 1.5rem;
    margin: 1rem 0;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    border: 1px solid;
}
.verdict-fake {
    background: linear-gradient(135deg, #1a0a0a, #110d0d);
    border-color: #7f1d1d;
}
.verdict-real {
    background: linear-gradient(135deg, #0a1a0e, #0d110d);
    border-color: #14532d;
}
.verdict-icon {
    font-size: 2rem;
    line-height: 1;
    flex-shrink: 0;
}
.verdict-text-block {}
.verdict-en {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e6edf3;
    margin: 0 0 0.2rem 0;
}
.verdict-hi {
    font-family: 'Noto Sans Devanagari', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 0.4rem 0;
}
.verdict-fake .verdict-hi { color: #f87171; }
.verdict-real .verdict-hi { color: #4ade80; }
.verdict-score {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #8b949e;
}

/* ── Score bar ── */
.ds-score-wrap {
    margin: 0.8rem 0 1.2rem 0;
}
.ds-score-label {
    font-size: 0.75rem;
    color: #8b949e;
    margin-bottom: 0.3rem;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.ds-score-bar-bg {
    background: #21262d;
    border-radius: 99px;
    height: 8px;
    overflow: hidden;
}
.ds-score-bar-fill-fake {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #dc2626, #f97316);
    transition: width 0.6s ease;
}
.ds-score-bar-fill-real {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #16a34a, #4ade80);
    transition: width 0.6s ease;
}

/* ── Findings ── */
.finding-item {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.5rem 0.8rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    font-size: 0.87rem;
    color: #c9d1d9;
    background: #161b22;
    border: 1px solid #21262d;
    line-height: 1.4;
}

/* ── Safety warning ── */
.ds-safety {
    background: linear-gradient(135deg, #1a1000, #110f00);
    border: 1px solid #713f12;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-top: 1rem;
}
.ds-safety-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #fbbf24;
    margin: 0 0 0.7rem 0;
}
.ds-safety-item {
    font-size: 0.85rem;
    color: #d1b75a;
    margin-bottom: 0.35rem;
    display: flex;
    gap: 0.5rem;
    line-height: 1.4;
}

/* ── Info chips ── */
.ds-chip {
    display: inline-block;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 0.2rem 0.6rem;
    font-size: 0.78rem;
    color: #8b949e;
    font-family: 'JetBrains Mono', monospace;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
}

/* ── Metric row ── */
.ds-metric-row {
    display: flex;
    gap: 0.8rem;
    flex-wrap: wrap;
    margin: 0.8rem 0;
}
.ds-metric-box {
    flex: 1;
    min-width: 100px;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    text-align: center;
}
.ds-metric-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4rem;
    font-weight: 600;
    color: #e6edf3;
    display: block;
}
.ds-metric-label {
    font-size: 0.72rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.2rem;
    display: block;
}

/* ── WhatsApp card ── */
.wa-card {
    background: linear-gradient(135deg, #0a1a0a, #0d150d);
    border: 1px solid #1a3a1a;
    border-radius: 14px;
    padding: 1.8rem;
    text-align: center;
    margin-top: 1rem;
}
.wa-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.3rem;
    font-weight: 600;
    color: #4ade80;
    background: #0d1f0d;
    border: 1px solid #14532d;
    border-radius: 8px;
    padding: 0.6rem 1.2rem;
    display: inline-block;
    margin: 0.8rem 0;
    letter-spacing: 0.05em;
}
.wa-step {
    font-size: 0.85rem;
    color: #8b949e;
    margin: 0.3rem 0;
    text-align: left;
}

/* ── Divider ── */
.ds-divider {
    border: none;
    border-top: 1px solid #21262d;
    margin: 1.2rem 0;
}

/* ── Mobile responsiveness ── */
@media (max-width: 600px) {
    .ds-hero-title { font-size: 1.8rem; }
    .ds-metric-row { gap: 0.5rem; }
    .ds-metric-box { min-width: 80px; padding: 0.6rem 0.7rem; }
    .ds-metric-val { font-size: 1.1rem; }
}
</style>
""", unsafe_allow_html=True)


# ── Helper functions ──────────────────────────────────────────────────────────

def verdict_card(label, score, confidence):
    """Render a bilingual verdict card."""
    if label == "SYNTHETIC":
        pct = int(score * 100)
        html = f"""
        <div class="verdict-card verdict-fake">
            <div class="verdict-icon">⚠️</div>
            <div class="verdict-text-block">
                <p class="verdict-en">DEEPFAKE DETECTED</p>
                <p class="verdict-hi">नकली — यह AI द्वारा बनाया गया है</p>
                <span class="verdict-score">Synthetic probability: {pct}%</span>
            </div>
        </div>
        <div class="ds-score-wrap">
            <div class="ds-score-label">Synthetic score / नकलीपन</div>
            <div class="ds-score-bar-bg">
                <div class="ds-score-bar-fill-fake" style="width:{pct}%"></div>
            </div>
        </div>
        """
    else:
        pct = int(confidence) if confidence else int((1 - score) * 100)
        html = f"""
        <div class="verdict-card verdict-real">
            <div class="verdict-icon">✅</div>
            <div class="verdict-text-block">
                <p class="verdict-en">LOOKS AUTHENTIC</p>
                <p class="verdict-hi">असली — यह वास्तविक प्रतीत होता है</p>
                <span class="verdict-score">Authenticity score: {pct}%</span>
            </div>
        </div>
        <div class="ds-score-wrap">
            <div class="ds-score-label">Authenticity / प्रामाणिकता</div>
            <div class="ds-score-bar-bg">
                <div class="ds-score-bar-fill-real" style="width:{pct}%"></div>
            </div>
        </div>
        """
    st.markdown(html, unsafe_allow_html=True)


def findings_list(findings, label):
    """Render findings as styled list items."""
    for f in findings:
        is_warning = label == "SYNTHETIC" and "No specific" not in f and "No anomalies" not in f
        icon = "⚠️" if is_warning else "✅"
        st.markdown(
            f'<div class="finding-item"><span>{icon}</span><span>{f}</span></div>',
            unsafe_allow_html=True
        )


def section_header(en, hi):
    st.markdown(f"""
    <div class="ds-section-header">
        <p class="ds-section-title">{en}</p>
        <p class="ds-section-hindi">{hi}</p>
    </div>
    """, unsafe_allow_html=True)


def metric_row(metrics: list):
    """metrics = list of (value, label) tuples"""
    cols_html = "".join([
        f'<div class="ds-metric-box"><span class="ds-metric-val">{v}</span><span class="ds-metric-label">{l}</span></div>'
        for v, l in metrics
    ])
    st.markdown(f'<div class="ds-metric-row">{cols_html}</div>', unsafe_allow_html=True)


def safety_block():
    st.markdown("""
    <div class="ds-safety">
        <p class="ds-safety-title">⚠️ सावधान रहें — Stay Safe</p>
        <div class="ds-safety-item"><span>🚫</span><span>OTP, Aadhaar, या बैंक विवरण साझा न करें — Do NOT share OTP, Aadhaar, or bank details</span></div>
        <div class="ds-safety-item"><span>📞</span><span>फोन काटें और आधिकारिक नंबर पर वापस कॉल करें — Hang up and call back on the official number</span></div>
        <div class="ds-safety-item"><span>🌐</span><span>Report at <strong>cybercrime.gov.in</strong> or call <strong>1930</strong></span></div>
        <div class="ds-safety-item"><span>👨‍👩‍👧</span><span>अपने परिवार को इस स्कैम के बारे में बताएं — Alert your family</span></div>
    </div>
    """, unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ds-hero">
    <p class="ds-hero-title">🛡️ DeepShield</p>
    <p class="ds-hero-hindi">डीपफेक पहचान — भारत के लिए</p>
    <p class="ds-hero-tagline">AI-powered deepfake detection for images, videos & voices.<br>Built for India, in Hindi & English.</p>
    <span class="ds-hero-stat">⚡ 47% of Indian adults have faced an AI scam</span>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🖼️ Image / छवि",
    "🎬 Video / वीडियो",
    "🎙️ Voice / आवाज़",
    "💬 WhatsApp"
])


# ════════════════════════════════════════════════════════
# TAB 1 — IMAGE
# ════════════════════════════════════════════════════════
with tab1:
    section_header("Image Deepfake Detector", "छवि डीपफेक पहचानकर्ता")
    st.markdown(
        '<span class="ds-chip">JPG</span><span class="ds-chip">PNG</span>'
        '<span class="ds-chip">WEBP</span><span class="ds-chip">max 200MB</span>',
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Upload image / छवि अपलोड करें",
        type=["jpg", "jpeg", "png", "webp"],
        key="image_upload",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        col1, col2 = st.columns([1, 1], gap="medium")

        with col1:
            st.image(uploaded_file, caption="Uploaded Image / अपलोड की गई छवि", use_container_width=True)

        with col2:
            with st.spinner("Analyzing / विश्लेषण हो रहा है..."):
                from image_detector import detect_image
                result = detect_image(tmp_path)

            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                score      = result["score"]
                label      = result["label"]
                confidence = result.get("confidence", int((1 - score) * 100))

                verdict_card(label, score, confidence)

                st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)
                st.markdown("**Why? / क्यों?**")
                findings_list(result.get("findings", []), label)

        os.unlink(tmp_path)


# ════════════════════════════════════════════════════════
# TAB 2 — VIDEO
# ════════════════════════════════════════════════════════
with tab2:
    section_header("Video Deepfake Detector", "वीडियो डीपफेक पहचानकर्ता")
    st.markdown(
        '<span class="ds-chip">MP4</span><span class="ds-chip">AVI</span>'
        '<span class="ds-chip">MOV</span><span class="ds-chip">MKV</span>',
        unsafe_allow_html=True
    )
    st.caption("Analyzes 10 evenly-spaced frames • 30–60 seconds / 10 फ्रेम का विश्लेषण करता है")

    uploaded_video = st.file_uploader(
        "Upload video / वीडियो अपलोड करें",
        type=["mp4", "avi", "mov", "mkv"],
        key="video_upload",
        label_visibility="collapsed"
    )

    if uploaded_video is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded_video.getvalue())
            tmp_path = tmp.name

        st.video(uploaded_video)

        with st.spinner("Analyzing frames / फ्रेम का विश्लेषण हो रहा है... (30–60s)"):
            from video_detector import detect_video
            result = detect_video(tmp_path)

        if "error" in result:
            st.error(f"❌ Error: {result['error']}")
        else:
            score = result["score"]
            label = result["label"]
            confidence = result.get("confidence", int((1 - score) * 100))

            verdict_card(label, score, confidence)

            metric_row([
                (result["total_frames_analyzed"], "Frames / फ्रेम"),
                (result["suspicious_frames"],     "Suspicious / संदिग्ध"),
                (f"{result['duration']}s",        "Duration / अवधि"),
            ])

            if result.get("frame_scores"):
                st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)
                st.markdown("**Frame-by-frame analysis / फ्रेम-दर-फ्रेम विश्लेषण**")
                import pandas as pd
                chart_data = pd.DataFrame({
                    "Frame": range(1, len(result["frame_scores"]) + 1),
                    "Synthetic score": result["frame_scores"]
                })
                st.line_chart(chart_data.set_index("Frame"), color="#00cc44")
                st.caption("Spikes = manipulated frames / स्पाइक = हेरफेर किए गए फ्रेम")

            if result.get("findings"):
                st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)
                findings_list(result["findings"], label)

            if label == "SYNTHETIC":
                safety_block()

        os.unlink(tmp_path)


# ════════════════════════════════════════════════════════
# TAB 3 — VOICE
# ════════════════════════════════════════════════════════
with tab3:
    section_header("Voice Deepfake Detector", "आवाज़ डीपफेक पहचानकर्ता")

    if Path("voice_model.pkl").exists():
        st.markdown(
            '<div class="finding-item"><span>🧠</span><span>ML model loaded — high accuracy mode / उच्च सटीकता मोड सक्रिय</span></div>',
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ ML model not trained. Run `python train_voice_model.py` for best accuracy.")

    st.markdown(
        '<span class="ds-chip">WAV</span><span class="ds-chip">MP3</span>'
        '<span class="ds-chip">OGG</span><span class="ds-chip">FLAC</span>',
        unsafe_allow_html=True
    )
    st.caption("💡 WAV files work best — MP3/M4A need ffmpeg / WAV फ़ाइलें सबसे अच्छी हैं")

    uploaded_audio = st.file_uploader(
        "Upload audio / ऑडियो अपलोड करें",
        type=["wav", "mp3", "m4a", "ogg", "flac"],
        key="audio_upload",
        label_visibility="collapsed"
    )

    if uploaded_audio is not None:
        suffix = "." + uploaded_audio.name.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_audio.getvalue())
            tmp_path = tmp.name

        st.audio(uploaded_audio)

        with st.spinner("Analyzing voice / आवाज़ का विश्लेषण हो रहा है..."):
            from voice_detector import detect_voice
            result = detect_voice(tmp_path)

        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            score      = result["score"]
            label      = result["label"]
            confidence = result.get("confidence", int((1 - score) * 100))

            verdict_card(label, score, confidence)

            metric_row([
                (f"{int(score*100)}%" if label == "SYNTHETIC" else f"{confidence}%",
                 "Score / स्कोर"),
                (f"{result['duration']}s",  "Duration / अवधि"),
                (f"{result['rule_hits']}/{result['total_checks']}",
                 "Anomalies / विसंगतियाँ"),
                (f"{result['sample_rate']}Hz", "Sample rate"),
            ])

            # Score breakdown (ML mode)
            if result.get("model_trained", False):
                st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)
                st.markdown("**Score breakdown / स्कोर विवरण**")
                metric_row([
                    (f"{int(result['ml_score']*100)}%",   "ML model"),
                    (f"{int(result['rule_score']*100)}%", "Rule-based / नियम"),
                    (f"{int(score*100)}%",                "Final / अंतिम"),
                ])
                st.caption(f"Method: {result['detection_method']} • 75% ML + 25% rules")

            # Signal table
            st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)
            st.markdown("**Signal analysis / संकेत विश्लेषण**")
            import pandas as pd
            LABELS = {
                "breathing":      "Breathing / सांस",
                "pitch_variance": "Pitch variation / पिच",
                "formant":        "Formant dynamics",
                "spectral_flat":  "Spectral texture",
                "hf_energy":      "High-freq energy (>8kHz)",
                "silence_ratio":  "Silence / मौन",
                "zcr_regularity": "ZCR regularity",
            }
            rows = [
                {
                    "Signal":  LABELS.get(k, k),
                    "Result":  "⚠️ Suspicious / संदिग्ध" if v["triggered"] else "✅ Normal / सामान्य",
                    "Weight":  f"{int(v['weight']*100)}%",
                }
                for k, v in result["signal_scores"].items()
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            with st.expander("📋 Detailed findings / विस्तृत निष्कर्ष"):
                for f in result["findings"]:
                    st.write(f)

            if label == "SYNTHETIC":
                safety_block()

        os.unlink(tmp_path)


# ════════════════════════════════════════════════════════
# TAB 4 — WHATSAPP
# ════════════════════════════════════════════════════════
with tab4:
    section_header("WhatsApp Forward Checker", "व्हाट्सएप फॉरवर्ड जांचकर्ता")

    st.markdown("""
    <div class="wa-card">
        <p style="color:#8b949e; font-size:0.85rem; margin:0 0 0.3rem 0;">Send any suspicious media to / संदिग्ध मीडिया भेजें:</p>
        <div class="wa-number">+1 (415) 523-8886</div>
        <p style="color:#8b949e; font-size:0.8rem; margin:0.5rem 0 1rem 0;">WhatsApp Sandbox — Twilio</p>
        <hr style="border:none;border-top:1px solid #1a3a1a;margin:1rem 0;">
        <div class="wa-step">1️⃣ &nbsp;Join sandbox — send <strong style="color:#4ade80">join [your-word]</strong> to the number above</div>
        <div class="wa-step">2️⃣ &nbsp;Forward any suspicious image or voice note / संदिग्ध छवि या आवाज़ नोट भेजें</div>
        <div class="wa-step">3️⃣ &nbsp;Receive instant analysis in Hindi & English / हिंदी और अंग्रेज़ी में तुरंत विश्लेषण</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)

    st.markdown("**Supported formats / समर्थित फ़ॉर्मेट**")
    st.markdown(
        '<span class="ds-chip">JPG / PNG</span>'
        '<span class="ds-chip">WebP</span>'
        '<span class="ds-chip">OGG voice note</span>'
        '<span class="ds-chip">WAV / MP3</span>',
        unsafe_allow_html=True
    )

    st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)
    st.markdown("**Bot status / बॉट स्थिति**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            '<div class="finding-item"><span>🟢</span><span>Flask webhook — localhost:5000</span></div>',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            '<div class="finding-item"><span>🔗</span><span>ngrok tunnel required — run <code>ngrok http 5000</code></span></div>',
            unsafe_allow_html=True
        )

    with st.expander("⚙️ Setup guide / सेटअप गाइड"):
        st.code("""# Terminal 1 — Start the bot
cd deepshield
venv\\Scripts\\activate
python whatsapp_bot.py

# Terminal 2 — Expose via ngrok
ngrok http 5000

# Then update Twilio webhook:
# console.twilio.com → Messaging → WhatsApp → Sandbox settings
# Paste ngrok URL + /webhook
""", language="bash")
