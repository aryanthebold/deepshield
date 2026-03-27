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

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — Cinematic dark theme, animated hero, bilingual polish
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Rajdhani:wght@400;500;600;700&display=swap');

/* ── CSS Variables ── */
:root {
    --bg-base:      #080c10;
    --bg-card:      #0d1420;
    --bg-elevated:  #111927;
    --border:       #1c2a3a;
    --border-glow:  #00e5601a;
    --accent:       #00e560;
    --accent-dim:   #00b84a;
    --accent-glow:  rgba(0,229,96,0.15);
    --danger:       #ff4757;
    --danger-dim:   #cc2233;
    --danger-glow:  rgba(255,71,87,0.15);
    --text-primary: #e8f0fe;
    --text-secondary: #8ba3c4;
    --text-muted:   #4a6080;
    --mono:         'JetBrains Mono', monospace;
    --hindi:        'Noto Sans Devanagari', sans-serif;
    --display:      'Rajdhani', 'Space Grotesk', sans-serif;
    --body:         'Space Grotesk', 'Noto Sans Devanagari', sans-serif;
}

/* ── Base reset ── */
html, body, [class*="css"] {
    font-family: var(--body);
    background-color: var(--bg-base) !important;
    color: var(--text-primary);
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 4rem;
    max-width: 820px;
}

/* ═══════════════════════════════════════════
   ANIMATIONS
═══════════════════════════════════════════ */
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(22px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes scanline {
    0%   { transform: translateY(-100%); opacity: 0.07; }
    100% { transform: translateY(800%);  opacity: 0.03; }
}
@keyframes pulse-ring {
    0%   { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0,229,96,0.25); }
    70%  { transform: scale(1);    box-shadow: 0 0 0 10px rgba(0,229,96,0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0,229,96,0); }
}
@keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes borderGlow {
    0%, 100% { border-color: #1c2a3a; }
    50%       { border-color: rgba(0,229,96,0.4); }
}
@keyframes countUp {
    from { opacity: 0; transform: scale(0.8); }
    to   { opacity: 1; transform: scale(1); }
}
@keyframes slideBarFake {
    from { width: 0%; }
    to   { width: var(--bar-w); }
}

/* ═══════════════════════════════════════════
   HERO SECTION
═══════════════════════════════════════════ */
.ds-hero-outer {
    position: relative;
    overflow: hidden;
    background: linear-gradient(145deg, #060a10 0%, #0a1420 40%, #060e0a 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0;
    margin-bottom: 1.6rem;
    animation: fadeIn 0.6s ease both;
}
.ds-hero-inner {
    position: relative;
    z-index: 2;
    padding: 2.4rem 2.4rem 2rem 2.4rem;
}

/* Scanline overlay */
.ds-hero-outer::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    animation: scanline 4s linear infinite;
    z-index: 1;
    opacity: 0.5;
}

/* Grid background */
.ds-hero-outer::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(0,229,96,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,229,96,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    z-index: 0;
}

/* Glow orbs */
.ds-hero-orb1 {
    position: absolute;
    top: -80px; right: -60px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(0,229,96,0.08) 0%, transparent 65%);
    z-index: 0;
}
.ds-hero-orb2 {
    position: absolute;
    bottom: -60px; left: 20%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(0,150,255,0.05) 0%, transparent 65%);
    z-index: 0;
}

.ds-hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(0,229,96,0.08);
    border: 1px solid rgba(0,229,96,0.25);
    border-radius: 30px;
    padding: 0.25rem 0.9rem;
    font-size: 0.72rem;
    font-family: var(--mono);
    color: var(--accent);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.1rem;
    animation: fadeSlideUp 0.5s 0.1s both;
}
.ds-hero-badge-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse-ring 2s ease infinite;
}

.ds-hero-title {
    font-family: var(--display);
    font-size: 3.2rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
    line-height: 1.05;
    margin: 0 0 0.15rem 0;
    animation: fadeSlideUp 0.5s 0.15s both;
}
.ds-hero-title .accent { color: var(--accent); }

.ds-hero-hindi {
    font-family: var(--hindi);
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--accent-dim);
    margin: 0 0 0.9rem 0;
    animation: fadeSlideUp 0.5s 0.2s both;
}

.ds-hero-tagline {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin: 0 0 1.4rem 0;
    line-height: 1.65;
    max-width: 560px;
    animation: fadeSlideUp 0.5s 0.25s both;
}

.ds-hero-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    animation: fadeSlideUp 0.5s 0.3s both;
}
.ds-stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.3rem 0.8rem;
    font-size: 0.78rem;
    font-family: var(--mono);
    color: var(--text-secondary);
    transition: all 0.25s;
}
.ds-stat-pill:hover {
    border-color: rgba(0,229,96,0.3);
    color: var(--accent);
    transform: translateY(-1px);
}
.ds-stat-pill .pill-num { color: var(--accent); font-weight: 600; }

/* ═══════════════════════════════════════════
   TABS
═══════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 3px;
    background: var(--bg-card);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid var(--border);
    animation: fadeIn 0.4s 0.3s both;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px;
    padding: 0.55rem 1.2rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-muted);
    background: transparent;
    border: none;
    transition: all 0.2s;
    font-family: var(--body);
    letter-spacing: 0.01em;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-secondary);
    background: var(--bg-elevated);
}
.stTabs [aria-selected="true"] {
    background: var(--bg-elevated) !important;
    color: var(--accent) !important;
    border: 1px solid rgba(0,229,96,0.2) !important;
    box-shadow: 0 0 12px rgba(0,229,96,0.08);
}

/* ═══════════════════════════════════════════
   SECTION HEADER
═══════════════════════════════════════════ */
.ds-section-header {
    margin: 0.8rem 0 1.4rem 0;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
    animation: fadeSlideUp 0.4s both;
}
.ds-section-title {
    font-family: var(--display);
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 0.2rem 0;
    letter-spacing: 0.01em;
}
.ds-section-hindi {
    font-family: var(--hindi);
    font-size: 1rem;
    color: var(--text-muted);
    margin: 0;
}

/* ═══════════════════════════════════════════
   VERDICT CARDS
═══════════════════════════════════════════ */
.verdict-card {
    border-radius: 16px;
    padding: 1.6rem 1.7rem;
    margin: 1.2rem 0 0.3rem 0;
    display: flex;
    align-items: flex-start;
    gap: 1.2rem;
    border: 1px solid;
    animation: fadeSlideUp 0.45s both;
    position: relative;
    overflow: hidden;
}
.verdict-card::before {
    content: '';
    position: absolute;
    inset: 0;
    opacity: 0.04;
    background-image:
        linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px);
    background-size: 24px 24px;
    pointer-events: none;
}
.verdict-fake {
    background: linear-gradient(135deg, #150609 0%, #0e0a0b 100%);
    border-color: rgba(255,71,87,0.35);
    box-shadow: 0 0 30px rgba(255,71,87,0.07), inset 0 1px 0 rgba(255,71,87,0.1);
}
.verdict-real {
    background: linear-gradient(135deg, #050f09 0%, #070d0a 100%);
    border-color: rgba(0,229,96,0.3);
    box-shadow: 0 0 30px rgba(0,229,96,0.06), inset 0 1px 0 rgba(0,229,96,0.1);
}
.verdict-icon {
    font-size: 2.4rem;
    line-height: 1;
    flex-shrink: 0;
    margin-top: 0.1rem;
    filter: drop-shadow(0 0 8px currentColor);
}
.verdict-en {
    font-family: var(--display);
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 0.25rem 0;
    letter-spacing: 0.03em;
}
.verdict-hi {
    font-family: var(--hindi);
    font-size: 1.05rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
}
.verdict-fake .verdict-hi { color: #ff7b8a; }
.verdict-real .verdict-hi { color: var(--accent); }
.verdict-score {
    font-family: var(--mono);
    font-size: 0.8rem;
    color: var(--text-muted);
    letter-spacing: 0.03em;
}

/* ═══════════════════════════════════════════
   SCORE BARS
═══════════════════════════════════════════ */
.ds-score-wrap {
    margin: 0.5rem 0 1.4rem 0;
    animation: fadeIn 0.4s 0.1s both;
}
.ds-score-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.73rem;
    color: var(--text-muted);
    margin-bottom: 0.45rem;
    font-family: var(--mono);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.ds-score-label .score-val {
    color: var(--text-secondary);
    font-weight: 600;
}
.ds-score-bar-bg {
    background: #131c28;
    border-radius: 99px;
    height: 10px;
    overflow: hidden;
    border: 1px solid var(--border);
}
.ds-score-bar-fill-fake {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #991b2b, #ff4757, #ff6b7a);
    box-shadow: 0 0 12px rgba(255,71,87,0.4);
    transition: width 1s cubic-bezier(0.16,1,0.3,1);
}
.ds-score-bar-fill-real {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #00803a, var(--accent), #5eff9f);
    box-shadow: 0 0 12px rgba(0,229,96,0.35);
    transition: width 1s cubic-bezier(0.16,1,0.3,1);
}

/* ═══════════════════════════════════════════
   FINDING ITEMS
═══════════════════════════════════════════ */
.finding-item {
    display: flex;
    align-items: flex-start;
    gap: 0.65rem;
    padding: 0.6rem 0.9rem;
    border-radius: 10px;
    margin-bottom: 0.45rem;
    font-size: 0.87rem;
    color: var(--text-secondary);
    background: var(--bg-card);
    border: 1px solid var(--border);
    line-height: 1.45;
    transition: all 0.2s;
    animation: fadeSlideUp 0.35s both;
}
.finding-item:hover {
    border-color: rgba(0,229,96,0.2);
    background: var(--bg-elevated);
    transform: translateX(3px);
}

/* ═══════════════════════════════════════════
   SAFETY WARNING
═══════════════════════════════════════════ */
.ds-safety {
    background: linear-gradient(135deg, #130d00, #0f0a00);
    border: 1px solid rgba(251,191,36,0.3);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-top: 1.2rem;
    animation: fadeSlideUp 0.4s both;
    box-shadow: 0 0 20px rgba(251,191,36,0.05);
}
.ds-safety-title {
    font-family: var(--display);
    font-size: 1.05rem;
    font-weight: 700;
    color: #fbbf24;
    margin: 0 0 0.9rem 0;
    letter-spacing: 0.02em;
}
.ds-safety-item {
    font-size: 0.87rem;
    color: #c9a24a;
    margin-bottom: 0.5rem;
    display: flex;
    gap: 0.6rem;
    line-height: 1.5;
    padding: 0.35rem 0.5rem;
    border-radius: 6px;
    transition: background 0.2s;
}
.ds-safety-item:hover { background: rgba(251,191,36,0.05); }

/* ═══════════════════════════════════════════
   INFO CHIPS
═══════════════════════════════════════════ */
.ds-chip {
    display: inline-flex;
    align-items: center;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 0.2rem 0.65rem;
    font-size: 0.77rem;
    color: var(--text-muted);
    font-family: var(--mono);
    margin-right: 0.4rem;
    margin-bottom: 0.45rem;
    letter-spacing: 0.03em;
    transition: all 0.2s;
}
.ds-chip:hover {
    border-color: rgba(0,229,96,0.25);
    color: var(--accent);
}

/* ═══════════════════════════════════════════
   METRIC BOXES
═══════════════════════════════════════════ */
.ds-metric-row {
    display: flex;
    gap: 0.8rem;
    flex-wrap: wrap;
    margin: 1rem 0 1.3rem 0;
}
.ds-metric-box {
    flex: 1;
    min-width: 100px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1rem 0.85rem 1rem;
    text-align: center;
    transition: all 0.25s;
    animation: countUp 0.4s both;
}
.ds-metric-box:hover {
    border-color: rgba(0,229,96,0.25);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
.ds-metric-val {
    font-family: var(--mono);
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-primary);
    display: block;
    letter-spacing: -0.02em;
}
.ds-metric-label {
    font-family: var(--hindi);
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-top: 0.2rem;
    display: block;
    line-height: 1.4;
}

/* ═══════════════════════════════════════════
   WHATSAPP CARD
═══════════════════════════════════════════ */
.wa-card {
    background: linear-gradient(145deg, #060f09, #080d0b);
    border: 1px solid rgba(0,229,96,0.15);
    border-radius: 18px;
    padding: 2rem;
    text-align: center;
    margin-top: 1.2rem;
    animation: fadeSlideUp 0.45s both;
    position: relative;
    overflow: hidden;
}
.wa-card::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(0,229,96,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.wa-card-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-family: var(--mono);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 0.5rem 0;
}
.wa-number {
    font-family: var(--mono);
    font-size: 1.45rem;
    font-weight: 600;
    color: var(--accent);
    background: rgba(0,229,96,0.06);
    border: 1px solid rgba(0,229,96,0.2);
    border-radius: 10px;
    padding: 0.65rem 1.4rem;
    display: inline-block;
    margin: 0.7rem 0 0.5rem 0;
    letter-spacing: 0.05em;
    animation: borderGlow 3s ease infinite;
}
.wa-subtitle {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin: 0 0 1.2rem 0;
}
.wa-step {
    font-size: 0.88rem;
    color: var(--text-secondary);
    margin: 0.5rem 0;
    text-align: left;
    padding: 0.5rem 0.7rem;
    border-radius: 8px;
    transition: background 0.2s;
}
.wa-step:hover { background: rgba(0,229,96,0.04); }

/* ═══════════════════════════════════════════
   DIVIDER
═══════════════════════════════════════════ */
.ds-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.4rem 0;
}

/* ═══════════════════════════════════════════
   UPLOAD ZONE ENHANCEMENT
═══════════════════════════════════════════ */
[data-testid="stFileUploader"] {
    border-radius: 14px !important;
    transition: all 0.3s;
}
[data-testid="stFileUploader"] > div {
    border: 2px dashed var(--border) !important;
    border-radius: 14px !important;
    background: var(--bg-card) !important;
    transition: all 0.3s !important;
}
[data-testid="stFileUploader"] > div:hover {
    border-color: rgba(0,229,96,0.35) !important;
    background: rgba(0,229,96,0.03) !important;
}

/* ═══════════════════════════════════════════
   SPINNER OVERRIDE
═══════════════════════════════════════════ */
.stSpinner > div {
    border-color: var(--accent) var(--border) var(--border) !important;
}

/* ═══════════════════════════════════════════
   DATAFRAME
═══════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border) !important;
}

/* ═══════════════════════════════════════════
   EXPANDER
═══════════════════════════════════════════ */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(0,229,96,0.2) !important;
}

/* ═══════════════════════════════════════════
   MOBILE
═══════════════════════════════════════════ */
@media (max-width: 600px) {
    .ds-hero-title  { font-size: 2.2rem; }
    .ds-hero-inner  { padding: 1.6rem 1.4rem 1.4rem 1.4rem; }
    .ds-metric-row  { gap: 0.5rem; }
    .ds-metric-box  { min-width: 80px; padding: 0.7rem 0.7rem; }
    .ds-metric-val  { font-size: 1.2rem; }
    .verdict-card   { flex-direction: column; gap: 0.7rem; }
    .ds-hero-stats  { gap: 0.4rem; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def verdict_card(label, score, confidence):
    """Render animated bilingual verdict card."""
    if label == "SYNTHETIC":
        pct = int(score * 100)
        html = f"""
        <div class="verdict-card verdict-fake">
            <div class="verdict-icon">⚠️</div>
            <div class="verdict-text-block">
                <p class="verdict-en">DEEPFAKE DETECTED</p>
                <p class="verdict-hi">⚠️ नकली — AI द्वारा निर्मित सामग्री</p>
                <span class="verdict-score">synthetic_probability: {pct}% &nbsp;|&nbsp; confidence: HIGH</span>
            </div>
        </div>
        <div class="ds-score-wrap">
            <div class="ds-score-label">
                <span>Synthetic Score / नकलीपन स्कोर</span>
                <span class="score-val">{pct}%</span>
            </div>
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
                <p class="verdict-hi">✅ असली — यह वास्तविक प्रतीत होता है</p>
                <span class="verdict-score">authenticity_score: {pct}% &nbsp;|&nbsp; no_manipulation_detected</span>
            </div>
        </div>
        <div class="ds-score-wrap">
            <div class="ds-score-label">
                <span>Authenticity / प्रामाणिकता</span>
                <span class="score-val">{pct}%</span>
            </div>
            <div class="ds-score-bar-bg">
                <div class="ds-score-bar-fill-real" style="width:{pct}%"></div>
            </div>
        </div>
        """
    st.markdown(html, unsafe_allow_html=True)


def findings_list(findings, label):
    """Render findings as styled list items with bilingual logic."""
    for f in findings:
        is_warning = (label == "SYNTHETIC"
                      and "No specific" not in f
                      and "No anomalies" not in f
                      and "Authentic" not in f)
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
    cols_html = "".join([
        f'<div class="ds-metric-box"><span class="ds-metric-val">{v}</span>'
        f'<span class="ds-metric-label">{l}</span></div>'
        for v, l in metrics
    ])
    st.markdown(f'<div class="ds-metric-row">{cols_html}</div>', unsafe_allow_html=True)


def safety_block():
    st.markdown("""
    <div class="ds-safety">
        <p class="ds-safety-title">⚠️ सावधान रहें — Stay Safe</p>
        <div class="ds-safety-item"><span>🚫</span><span>OTP, Aadhaar, या बैंक विवरण साझा न करें — Do NOT share OTP, Aadhaar, or bank details</span></div>
        <div class="ds-safety-item"><span>📞</span><span>फोन काटें और आधिकारिक नंबर पर वापस कॉल करें — Hang up and call back on the official number</span></div>
        <div class="ds-safety-item"><span>🌐</span><span>साइबर अपराध की रिपोर्ट करें — Report at <strong style="color:#fbbf24">cybercrime.gov.in</strong> or call <strong style="color:#fbbf24">1930</strong></span></div>
        <div class="ds-safety-item"><span>👨‍👩‍👧</span><span>अपने परिवार को इस स्कैम के बारे में बताएं — Alert your family about this scam</span></div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HERO BANNER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="ds-hero-outer">
    <div class="ds-hero-orb1"></div>
    <div class="ds-hero-orb2"></div>
    <div class="ds-hero-inner">
        <div class="ds-hero-badge">
            <span class="ds-hero-badge-dot"></span>
            YESIST12 · Team Cardinals · SDG 16
        </div>
        <p class="ds-hero-title">🛡️ Deep<span class="accent">Shield</span></p>
        <p class="ds-hero-hindi">डीपफेक पहचान प्रणाली — भारत के लिए</p>
        <p class="ds-hero-tagline">
            AI-powered deepfake detection for images, videos &amp; voices.<br>
            Built for India's 500 million WhatsApp users — in Hindi &amp; English.
        </p>
        <div class="ds-hero-stats">
            <span class="ds-stat-pill"><span class="pill-num">47%</span> Indian adults targeted</span>
            <span class="ds-stat-pill"><span class="pill-num">₹50K+</span> avg. victim loss</span>
            <span class="ds-stat-pill"><span class="pill-num">96%</span> detection accuracy</span>
            <span class="ds-stat-pill"><span class="pill-num">3</span> modalities covered</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "🖼️  Image / छवि",
    "🎬  Video / वीडियो",
    "🎙️  Voice / आवाज़",
    "💬  WhatsApp"
])


# ════════════════════════════════════════════════════════
# TAB 1 — IMAGE
# ════════════════════════════════════════════════════════
with tab1:
    section_header("Image Deepfake Detector", "छवि डीपफेक पहचानकर्ता")
    st.markdown(
        '<span class="ds-chip">JPG</span><span class="ds-chip">PNG</span>'
        '<span class="ds-chip">WEBP</span><span class="ds-chip">max 200 MB</span>',
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
            st.image(uploaded_file, caption="Uploaded / अपलोड की गई छवि", use_container_width=True)

        with col2:
            with st.spinner("Analyzing / विश्लेषण हो रहा है..."):
                try:
                    from image_detector import detect_image
                    result = detect_image(tmp_path)
                except Exception as e:
                    result = {"error": str(e)}

            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                # ── FIX: normalise score & label reliably ──────────────────
                raw_score  = result.get("score", 0.5)
                # If score is already 0-1, keep; if returned as 0-100, divide
                score      = raw_score / 100 if raw_score > 1 else raw_score
                label      = result.get("label", "AUTHENTIC")
                # Confidence: prefer explicit field, fall back correctly
                if label == "SYNTHETIC":
                    confidence = result.get("confidence", int(score * 100))
                else:
                    confidence = result.get("confidence", int((1 - score) * 100))

                verdict_card(label, score, confidence)

                st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)
                st.markdown("**Why? / क्यों?**")
                findings = result.get("findings", [])
                if not findings:
                    findings = ["No anomalies detected. / कोई विसंगति नहीं मिली।"]
                findings_list(findings, label)

                if label == "SYNTHETIC":
                    safety_block()

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
    st.caption("Analyzes 10 evenly-spaced frames • 30–60 seconds / 10 फ्रेम का विश्लेषण — 30-60 सेकंड")

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
            try:
                from video_detector import detect_video
                result = detect_video(tmp_path)
            except Exception as e:
                result = {"error": str(e)}

        if "error" in result:
            st.error(f"❌ Error: {result['error']}")
        else:
            # ── FIX: normalise video score ─────────────────────────────────
            raw_score  = result.get("score", 0.5)
            score      = raw_score / 100 if raw_score > 1 else raw_score
            label      = result.get("label", "AUTHENTIC")
            if label == "SYNTHETIC":
                confidence = result.get("confidence", int(score * 100))
            else:
                confidence = result.get("confidence", int((1 - score) * 100))

            verdict_card(label, score, confidence)

            metric_row([
                (result.get("total_frames_analyzed", "—"), "Frames / फ्रेम"),
                (result.get("suspicious_frames", "—"),     "Suspicious / संदिग्ध"),
                (f"{result.get('duration', '—')}s",        "Duration / अवधि"),
            ])

            frame_scores = result.get("frame_scores", [])
            if frame_scores:
                st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)
                st.markdown("**Frame-by-frame analysis / फ्रेम-दर-फ्रेम विश्लेषण**")
                import pandas as pd
                chart_data = pd.DataFrame({
                    "Frame": range(1, len(frame_scores) + 1),
                    "Synthetic score": frame_scores
                })
                st.line_chart(chart_data.set_index("Frame"), color="#00e560")
                st.caption("Spikes = manipulated frames / स्पाइक = हेरफेर किए गए फ्रेम")

            findings = result.get("findings", [])
            if findings:
                st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)
                findings_list(findings, label)

            if label == "SYNTHETIC":
                safety_block()

        os.unlink(tmp_path)


# ════════════════════════════════════════════════════════
# TAB 3 — VOICE
# ════════════════════════════════════════════════════════
with tab3:
    section_header("Voice Deepfake Detector", "आवाज़ डीपफेक पहचानकर्ता")

    # Model status banner
    if Path("voice_model.pkl").exists():
        st.markdown(
            '<div class="finding-item"><span>🧠</span>'
            '<span>ML model loaded — उच्च सटीकता मोड सक्रिय (high accuracy mode active)</span></div>',
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ ML model not found. Run `python train_voice_model.py` for best accuracy. / "
                   "सर्वोत्तम परिणाम के लिए ML मॉडल ट्रेन करें।")

    st.markdown(
        '<span class="ds-chip">WAV</span><span class="ds-chip">MP3</span>'
        '<span class="ds-chip">OGG</span><span class="ds-chip">FLAC</span>'
        '<span class="ds-chip">M4A</span>',
        unsafe_allow_html=True
    )
    st.caption("💡 WAV files give best results. MP3/M4A need ffmpeg. / WAV फ़ाइलें सबसे सटीक हैं।")

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
            try:
                # ── FIX: handle pkg_resources issue gracefully ─────────────
                import importlib
                try:
                    import pkg_resources  # noqa
                except ImportError:
                    import subprocess, sys
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "setuptools", "-q"],
                        check=False
                    )
                from voice_detector import detect_voice
                result = detect_voice(tmp_path)
            except Exception as e:
                result = {"error": str(e)}

        if "error" in result:
            st.error(f"❌ {result['error']}")
            st.info("💡 Tip: Run `pip install setuptools` in your venv if you see pkg_resources errors.")
        else:
            # ── FIX: normalise voice score ─────────────────────────────────
            raw_score  = result.get("score", 0.5)
            score      = raw_score / 100 if raw_score > 1 else raw_score
            label      = result.get("label", "AUTHENTIC")
            # Confidence fix: for AUTHENTIC, confidence should reflect how authentic
            if label == "SYNTHETIC":
                confidence = result.get("confidence", int(score * 100))
            else:
                # authenticity confidence = 1 - synthetic score
                confidence = result.get("confidence", int((1 - score) * 100))

            verdict_card(label, score, confidence)

            metric_row([
                (f"{int(score*100)}%" if label == "SYNTHETIC" else f"{confidence}%",
                 "Score / स्कोर"),
                (f"{result.get('duration', '—')}s",     "Duration / अवधि"),
                (f"{result.get('rule_hits', 0)}/{result.get('total_checks', 5)}",
                 "Anomalies / विसंगतियाँ"),
                (f"{result.get('sample_rate', '—')} Hz", "Sample rate"),
            ])

            # ML breakdown (only when model is trained)
            if result.get("model_trained", False):
                st.markdown('<hr class="ds-divider">', unsafe_allow_html=True)
                st.markdown("**Score breakdown / स्कोर विवरण**")
                metric_row([
                    (f"{int(result.get('ml_score', 0)*100)}%",   "ML model"),
                    (f"{int(result.get('rule_score', 0)*100)}%", "Rule-based / नियम"),
                    (f"{int(score*100)}%",                        "Final / अंतिम"),
                ])
                method = result.get("detection_method", "hybrid")
                st.caption(f"Method: {method} • 75% ML + 25% rule-based")

            # Signal analysis table
            signal_scores = result.get("signal_scores", {})
            if signal_scores:
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
                        "Signal": LABELS.get(k, k),
                        "Result": "⚠️ Suspicious / संदिग्ध" if v.get("triggered") else "✅ Normal / सामान्य",
                        "Weight": f"{int(v.get('weight', 0)*100)}%",
                    }
                    for k, v in signal_scores.items()
                ]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            findings = result.get("findings", [])
            if findings:
                with st.expander("📋 Detailed findings / विस्तृत निष्कर्ष"):
                    for f in findings:
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
        <p class="wa-card-label">Send suspicious media to / संदिग्ध मीडिया भेजें</p>
        <div class="wa-number">+1 (415) 523-8886</div>
        <p class="wa-subtitle">WhatsApp Sandbox — Powered by Twilio</p>
        <hr style="border:none;border-top:1px solid #1a2e1a;margin:1rem 0 1.2rem 0;">
        <div class="wa-step">1️⃣ &nbsp;Join sandbox — send <strong style="color:#00e560">join [your-word]</strong> to the number above</div>
        <div class="wa-step">2️⃣ &nbsp;Forward any suspicious image or voice note / संदिग्ध छवि या आवाज़ नोट भेजें</div>
        <div class="wa-step">3️⃣ &nbsp;Get instant analysis in Hindi &amp; English / हिंदी और अंग्रेज़ी में तुरंत विश्लेषण पाएं</div>
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
