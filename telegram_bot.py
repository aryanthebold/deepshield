"""
DeepShield — Telegram Bot (Merged HTML + Feature Rich Version)
==============================================================
Uses python-telegram-bot (v20+) with polling (no webhook/ngrok needed).
Receives images, voice messages, and documents. Runs detection, replies with verdict.
HTML parsing is used to prevent strict markdown crashing errors.
"""

import os
import asyncio
import tempfile
import traceback
import logging

# python-telegram-bot v20+
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode, ChatAction

# ── Load .env ─────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── DeepShield modules ────────────────────────────────────────────────────────
from image_detector import detect_image
from voice_detector import detect_voice
# If you have video integrated, import it here:
# from video_detector import detect_video 

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def cleanup(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def verdict_emoji(label: str) -> str:
    label = label.upper()
    if "SYNTHETIC" in label or "FAKE" in label or "DEEPFAKE" in label:
        return "🚨"
    if "AUTHENTIC" in label or "REAL" in label:
        return "✅"
    return "⚠️"

def format_image_reply(result: dict, filename: str) -> str:
    score      = result.get("deepfake_score", result.get("score", 0))
    label      = result.get("label", "UNKNOWN")
    confidence = result.get("confidence", abs(score - 0.5) * 200)
    method     = result.get("method", "rule-based")
    pct_fake   = round(score * 100)
    pct_real   = 100 - pct_fake
    emoji      = verdict_emoji(label)

    msg = (
        f"{emoji} <b>DeepShield Image Analysis</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 File: <code>{filename}</code>\n"
        f"🏷️ Verdict: <b>{label}</b>\n"
        f"📊 Synthetic probability: <b>{pct_fake}%</b>\n"
        f"✅ Authentic probability: <b>{pct_real}%</b>\n"
        f"🎯 Confidence: {round(confidence)}%\n"
        f"🔬 Method: {method}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )

    findings = result.get("findings", [])
    if findings:
        msg += "⚠️ <b>Suspicious signals detected:</b>\n"
        for f in findings[:4]:
            msg += f"  • {f}\n"
        msg += "\n"

    if "SYNTHETIC" in label.upper() or "FAKE" in label.upper():
        msg += (
            "❗ <b>This media shows signs of AI manipulation.</b>\n"
            "Do NOT share or act on this content.\n"
            "Report to: <a href='https://cybercrime.gov.in'>cybercrime.gov.in</a>"
        )
    else:
        msg += "This media appears to be authentic. Stay vigilant! 🛡️"

    return msg

def format_voice_reply(result: dict, filename: str) -> str:
    score      = result.get("score", 0)
    label      = result.get("label", "UNKNOWN")
    confidence = result.get("confidence", abs(score - 0.5) * 200)
    ml_score   = result.get("ml_score")
    method     = result.get("detection_method", "rule-based")
    pct_fake   = round(score * 100)
    pct_real   = 100 - pct_fake
    emoji      = verdict_emoji(label)

    msg = (
        f"{emoji} <b>DeepShield Voice Analysis</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎙️ File: <code>{filename}</code>\n"
        f"🏷️ Verdict: <b>{label}</b>\n"
        f"📊 Synthetic probability: <b>{pct_fake}%</b>\n"
        f"✅ Authentic probability: <b>{pct_real}%</b>\n"
        f"🎯 Confidence: {round(confidence)}%\n"
        f"🔬 Method: {method}\n"
    )

    if ml_score is not None:
        msg += f"🤖 ML score: {round(ml_score * 100)}%\n"

    msg += "━━━━━━━━━━━━━━━━━━━━\n"

    signal_scores = result.get("signal_scores", {})
    if signal_scores:
        msg += "📡 <b>Signal breakdown:</b>\n"
        signal_labels = {
            "breathing":      "Breathing patterns",
            "pitch_variance": "Pitch variance",
            "formant":        "Formant naturalness",
            "spectral_flat":  "Spectral flatness",
            "hf_energy":      "High-freq energy",
            "silence_ratio":  "Silence ratio",
            "zcr_regularity": "ZCR regularity",
        }
        for sig, val in signal_scores.items():
            label_text = signal_labels.get(sig, sig)
            flag = "🔴" if val > 0.5 else "🟢"
            msg += f"  {flag} {label_text}: {round(val * 100)}%\n"
        msg += "\n"

    if "SYNTHETIC" in label.upper() or "FAKE" in label.upper():
        msg += (
            "❗ <b>This voice shows signs of AI cloning or TTS synthesis.</b>\n"
            "Do NOT trust this caller or recording.\n"
            "Report to: <a href='https://cybercrime.gov.in'>cybercrime.gov.in</a>"
        )
    else:
        msg += "This voice appears authentic. Stay alert! 🛡️"

    return msg


# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and generic text like 'hi'."""
    welcome_text = (
        "🛡️ <b>Welcome to DeepShield!</b>\n\n"
        "I can detect AI-generated deepfakes. Send me:\n\n"
        "📸 <b>Image</b> — I'll check if it's AI-generated or manipulated\n"
        "🎙️ <b>Voice message</b> — I'll check if it's AI-cloned or TTS\n"
        "📄 <b>Document</b> — Send image/audio as a file for analysis\n\n"
        "Just forward any suspicious media directly here.\n\n"
        "<i>Powered by DeepShield — Fighting AI scams in India</i> 🇮🇳"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🛡️ <b>DeepShield Help</b>\n\n"
        "<b>What I can analyse:</b>\n"
        "• JPG / PNG / WebP images\n"
        "• OGG / WAV voice messages\n"
        "• Files sent as documents\n\n"
        "<b>Commands:</b>\n"
        "/start — Welcome message\n"
        "/help — This help message\n"
        "/status — Check if bot is running\n\n"
        "<b>How to use:</b>\n"
        "Simply send or forward any suspicious image or voice message. "
        "I'll analyse it and tell you if it's AI-generated.\n\n"
        "<i>Results usually arrive in 15–30 seconds.</i>"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    status_text = (
        "✅ <b>DeepShield is online and ready!</b>\n\n"
        "🖼️ Image detector: Active\n"
        "🎙️ Voice detector: Active\n"
        "🤖 ML model: Loaded\n\n"
        "Send me a suspicious image or voice message to analyse."
    )
    await update.message.reply_text(status_text, parse_mode=ParseMode.HTML)


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming photos."""
    chat_id  = update.message.chat_id
    tmp_path = None

    try:
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text("⏳ <i>Analysing your image... (15–30s)</i>", parse_mode=ParseMode.HTML)

        # Get highest resolution photo
        photo   = update.message.photo[-1]
        tg_file = await context.bot.get_file(photo.file_id)

        # Download to temp file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg", dir=tempfile.gettempdir())
        tmp.close()
        tmp_path = tmp.name
        await tg_file.download_to_drive(tmp_path)

        logger.info(f"[IMAGE] Downloaded to {tmp_path}, calling detect_image()")

        # Run detection
        result = detect_image(tmp_path)
        reply  = format_image_reply(result, "image.jpg")

        await status_msg.edit_text(reply, parse_mode=ParseMode.HTML)
        logger.info(f"[IMAGE] Result sent: {result.get('label', 'UNKNOWN')}")

    except Exception as e:
        logger.error(f"[IMAGE ERROR] {e}")
        traceback.print_exc()
        await update.message.reply_text(
            f"❌ <b>Error analysing image:</b>\n<code>{str(e)[:200]}</code>\n\nPlease try again.",
            parse_mode=ParseMode.HTML
        )
    finally:
        cleanup(tmp_path)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming voice messages."""
    chat_id  = update.message.chat_id
    tmp_path = None

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        status_msg = await update.message.reply_text("⏳ <i>Analysing your voice message... (15–30s)</i>", parse_mode=ParseMode.HTML)

        # Telegram voice messages are OGG/Opus
        voice   = update.message.voice
        tg_file = await context.bot.get_file(voice.file_id)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg", dir=tempfile.gettempdir())
        tmp.close()
        tmp_path = tmp.name
        await tg_file.download_to_drive(tmp_path)

        logger.info(f"[VOICE] Downloaded to {tmp_path}, calling detect_voice()")

        result = detect_voice(tmp_path)
        reply  = format_voice_reply(result, "voice.ogg")

        await status_msg.edit_text(reply, parse_mode=ParseMode.HTML)
        logger.info(f"[VOICE] Result sent: {result.get('label', 'UNKNOWN')}")

    except Exception as e:
        logger.error(f"[VOICE ERROR] {e}")
        traceback.print_exc()
        await update.message.reply_text(
            f"❌ <b>Error analysing voice:</b>\n<code>{str(e)[:200]}</code>\n\nPlease try again.",
            parse_mode=ParseMode.HTML
        )
    finally:
        cleanup(tmp_path)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle files sent as documents (images or audio sent uncompressed)."""
    chat_id  = update.message.chat_id
    doc      = update.message.document
    mime     = (doc.mime_type or "").lower()
    tmp_path = None

    IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
    AUDIO_TYPES = {"audio/ogg", "audio/mpeg", "audio/wav", "audio/mp4",
                   "audio/amr", "audio/x-wav", "audio/wave"}

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        if mime in IMAGE_TYPES:
            ext = mime.split("/")[-1]
            if ext == "jpeg": ext = "jpg"
            status_msg = await update.message.reply_text("⏳ <i>Analysing your image file...</i>", parse_mode=ParseMode.HTML)
        elif mime in AUDIO_TYPES:
            ext = "ogg"
            if "wav" in mime: ext = "wav"
            elif "mpeg" in mime: ext = "mp3"
            status_msg = await update.message.reply_text("⏳ <i>Analysing your audio file...</i>", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(
                f"⚠️ Unsupported file type: <code>{mime}</code>\n\n"
                "Please send a <b>JPG/PNG image</b> or <b>OGG/WAV audio</b> file.",
                parse_mode=ParseMode.HTML
            )
            return

        tg_file = await context.bot.get_file(doc.file_id)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}", dir=tempfile.gettempdir())
        tmp.close()
        tmp_path = tmp.name
        await tg_file.download_to_drive(tmp_path)

        if mime in IMAGE_TYPES:
            result = detect_image(tmp_path)
            reply  = format_image_reply(result, doc.file_name or f"file.{ext}")
        else:
            result = detect_voice(tmp_path)
            reply  = format_voice_reply(result, doc.file_name or f"file.{ext}")

        await status_msg.edit_text(reply, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"[DOC ERROR] {e}")
        traceback.print_exc()
        await update.message.reply_text(
            f"❌ <b>Error analysing file:</b>\n<code>{str(e)[:200]}</code>\n\nPlease try again.",
            parse_mode=ParseMode.HTML
        )
    finally:
        cleanup(tmp_path)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Set your TELEGRAM_BOT_TOKEN in the .env file first!")
        return

    print("=" * 60)
    print("  DeepShield Telegram Bot — Starting up 🛡️")
    print("=" * 60)
    print("  Mode:   Polling (no ngrok needed)")
    print("  Status: ONLINE")
    print("=" * 60)

    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.PHOTO,   handle_image))
    app.add_handler(MessageHandler(filters.VOICE,   handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Send the Welcome message for any text input like "hi", "hello", etc.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()