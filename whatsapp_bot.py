"""
DeepShield — WhatsApp Bot (v3)
==============================
v2: Threading to prevent Twilio 15s timeout
v3: Grad-CAM heatmap sent as WhatsApp image attachment
    - Flask /heatmap/<filename> serves temp file publicly via ngrok
    - Heatmap deleted 90s after send (Twilio needs time to fetch it)
    - NGROK_BASE_URL read from .env — update after every ngrok restart
"""

import os
import time
import tempfile
import requests
import traceback
import threading
from flask import Flask, request, send_file
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# ── Load .env if present ──────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Local DeepShield modules ──────────────────────────────────────────────────
from image_detector import detect_image
from voice_detector import detect_voice

# ── Config ────────────────────────────────────────────────────────────────────
ACCOUNT_SID   = os.environ.get("TWILIO_ACCOUNT_SID",   "AC746ef1474889bb9f66adb4b862d7af64")
AUTH_TOKEN    = os.environ.get("TWILIO_AUTH_TOKEN",    "54c1208abdf8dc9e3d2bad54ba44b74e")
FROM_NUMBER   = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
NGROK_BASE_URL = os.environ.get(
    "NGROK_BASE_URL",
    "https://epigrammatically-handwoven-ka.ngrok-free.dev"  # ← update in .env after each ngrok restart
)

client = Client(ACCOUNT_SID, AUTH_TOKEN)
app    = Flask(__name__)

IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
AUDIO_TYPES = {"audio/ogg", "audio/mpeg", "audio/mp4", "audio/wav",
               "audio/amr", "audio/x-wav", "audio/wave"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def download_media(media_url: str, ext: str) -> str:
    print(f"[DEBUG] Downloading: {media_url}")
    resp = requests.get(media_url, auth=(ACCOUNT_SID, AUTH_TOKEN), timeout=30)
    resp.raise_for_status()
    print(f"[DEBUG] Downloaded {len(resp.content)} bytes")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}", dir=tempfile.gettempdir())
    tmp.write(resp.content)
    tmp.close()
    print(f"[DEBUG] Saved to: {tmp.name}")
    return tmp.name

def cleanup(path: str):
    try:
        os.remove(path)
    except Exception:
        pass

def delete_after_delay(path: str, delay_seconds: int = 90):
    """Delete a temp file after a delay — gives Twilio time to fetch it."""
    def _delete():
        time.sleep(delay_seconds)
        cleanup(path)
        print(f"[CLEANUP] Deleted heatmap: {path}")
    threading.Thread(target=_delete, daemon=True).start()

def verdict_emoji(label: str) -> str:
    label = label.upper()
    if "SYNTHETIC" in label or "FAKE" in label or "DEEPFAKE" in label:
        return "🚨"
    if "AUTHENTIC" in label or "REAL" in label:
        return "✅"
    return "⚠️"

def send_whatsapp_message(to: str, body: str, media_path: str = None):
    """
    Send a WhatsApp message, optionally with a heatmap image attachment.
    media_path must be a local file that Flask can serve via /heatmap/<filename>.
    """
    print(f"[DEBUG] Sending message to {to}")
    kwargs = dict(from_=FROM_NUMBER, to=to, body=body)

    if media_path and os.path.exists(media_path):
        filename   = os.path.basename(media_path)
        public_url = f"{NGROK_BASE_URL}/heatmap/{filename}"
        kwargs["media_url"] = [public_url]
        print(f"[DEBUG] Attaching heatmap: {public_url}")

    client.messages.create(**kwargs)
    print(f"[DEBUG] Message sent OK")

def format_image_reply(result: dict, filename: str) -> str:
    print(f"[DEBUG] Image result: {result}")
    score      = result.get("deepfake_score", result.get("score", 0))
    label      = result.get("label", "UNKNOWN")
    confidence = result.get("confidence", abs(score - 0.5) * 200)
    method     = result.get("method", result.get("source", "rule-based"))
    pct_fake   = round(score * 100)
    pct_real   = 100 - pct_fake
    emoji      = verdict_emoji(label)

    msg = (
        f"{emoji} *DeepShield Image Analysis*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 File: {filename}\n"
        f"🏷️ Verdict: *{label}*\n"
        f"📊 Synthetic probability: {pct_fake}%\n"
        f"✅ Authentic probability: {pct_real}%\n"
        f"🎯 Confidence: {round(confidence)}%\n"
        f"🔬 Method: {method}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
    )

    findings = result.get("findings", [])
    if findings:
        msg += "⚠️ *Suspicious signals:*\n"
        for f in findings[:4]:
            msg += f"  • {f}\n"
        msg += "\n"

    if "SYNTHETIC" in label.upper() or "FAKE" in label.upper():
        msg += (
            "❗ *AI manipulation detected.*\n"
            "Do NOT share this content.\n"
            "Report: cybercrime.gov.in\n\n"
            "🔬 _Heatmap showing suspicious regions attached above_ ☝️"
        )
    else:
        msg += "This media appears authentic. Stay vigilant! 🛡️"

    return msg

def format_voice_reply(result: dict, filename: str) -> str:
    print(f"[DEBUG] Voice result: {result}")
    score      = result.get("score", 0)
    label      = result.get("label", "UNKNOWN")
    confidence = result.get("confidence", abs(score - 0.5) * 200)
    ml_score   = result.get("ml_score")
    method     = result.get("detection_method", "rule-based")
    pct_fake   = round(score * 100)
    pct_real   = 100 - pct_fake
    emoji      = verdict_emoji(label)

    msg = (
        f"{emoji} *DeepShield Voice Analysis*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎙️ File: {filename}\n"
        f"🏷️ Verdict: *{label}*\n"
        f"📊 Synthetic probability: {pct_fake}%\n"
        f"✅ Authentic probability: {pct_real}%\n"
        f"🎯 Confidence: {round(confidence)}%\n"
        f"🔬 Method: {method}\n"
    )
    if ml_score is not None:
        msg += f"🤖 ML score: {round(ml_score * 100)}%\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"

    if "SYNTHETIC" in label.upper() or "FAKE" in label.upper():
        msg += "❗ *AI voice detected.*\nDo NOT trust this caller.\nReport: cybercrime.gov.in"
    else:
        msg += "This voice appears authentic. Stay alert! 🛡️"

    return msg

# ── Background processing thread ──────────────────────────────────────────────

def process_media_background(sender: str, media_items: list):
    results_sent = 0
    for i, (media_url, media_type) in enumerate(media_items):
        tmp_path = None
        try:
            print(f"[BG] Processing item {i}: type={media_type}")

            if media_type in IMAGE_TYPES:
                ext = media_type.split("/")[-1]
                if ext == "jpeg":
                    ext = "jpg"
                tmp_path = download_media(media_url, ext)
                filename = f"media_{i+1}.{ext}"

                print(f"[BG] Calling detect_image({tmp_path})")
                result = detect_image(tmp_path)

                heatmap_path = result.get("heatmap_path")   # None if Grad-CAM failed
                reply = format_image_reply(result, filename)

                # Send verdict + heatmap attachment (if available)
                send_whatsapp_message(sender, reply, media_path=heatmap_path)
                results_sent += 1

                # Schedule heatmap deletion after 90s (Twilio must fetch first)
                if heatmap_path and os.path.exists(heatmap_path):
                    delete_after_delay(heatmap_path, delay_seconds=90)

            elif media_type in AUDIO_TYPES:
                ext = "ogg"
                if "wav"  in media_type: ext = "wav"
                elif "mpeg" in media_type: ext = "mp3"
                elif "mp4"  in media_type: ext = "mp4"
                tmp_path = download_media(media_url, ext)
                filename = f"voice_{i+1}.{ext}"

                print(f"[BG] Calling detect_voice({tmp_path})")
                result = detect_voice(tmp_path)
                reply  = format_voice_reply(result, filename)
                send_whatsapp_message(sender, reply)   # no heatmap for voice
                results_sent += 1

            else:
                print(f"[BG] Unsupported type: {media_type}")
                send_whatsapp_message(
                    sender,
                    f"⚠️ Unsupported file type: {media_type}\n"
                    "Please send a JPG/PNG image or OGG/WAV voice note."
                )

        except Exception as e:
            print(f"[BG ERROR] Exception on media {i}:")
            traceback.print_exc()
            send_whatsapp_message(
                sender,
                f"❌ Error analysing file {i+1}:\n_{str(e)[:300]}_\n\nPlease try again."
            )
        finally:
            if tmp_path:
                cleanup(tmp_path)

    if results_sent == 0:
        send_whatsapp_message(
            sender,
            "⚠️ Could not process the media.\n"
            "Please send a JPG/PNG image or OGG/WAV voice note."
        )

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/heatmap/<filename>", methods=["GET"])
def serve_heatmap(filename: str):
    """
    Temporarily serve a Grad-CAM heatmap PNG so Twilio can fetch and
    deliver it to WhatsApp. File is deleted 90s after the message is sent.
    """
    # Safety: only serve files that look like our temp heatmaps
    if not filename.endswith("_gradcam.png"):
        return "Not found", 404
    path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(path):
        return "Not found", 404
    print(f"[HEATMAP] Serving: {path}")
    return send_file(path, mimetype="image/png")

@app.route("/webhook", methods=["POST"])
def webhook():
    sender    = request.form.get("From", "")
    num_media = int(request.form.get("NumMedia", 0))
    body_text = request.form.get("Body", "").strip().lower()

    print(f"\n[WEBHOOK] From={sender} | NumMedia={num_media} | Body='{body_text}'")

    # ── Text only ─────────────────────────────────────────────────────────────
    if num_media == 0:
        if any(w in body_text for w in ["hi", "hello", "help", "start", "namaste"]):
            reply = (
                "🛡️ *Welcome to DeepShield!*\n\n"
                "I can detect AI-generated deepfakes. Send me:\n\n"
                "📸 *Image* — I'll check if it's AI-generated or manipulated\n"
                "🎙️ *Voice note* — I'll check if it's an AI-cloned or TTS voice\n\n"
                "Just forward any suspicious media directly here.\n"
                "_Powered by DeepShield — Fighting AI scams in India_ 🇮🇳"
            )
        else:
            reply = (
                "🛡️ *DeepShield* is ready!\n\n"
                "Send me a suspicious *image* or *voice note* and I'll analyse it.\n"
                "Type *help* for more info."
            )
        resp = MessagingResponse()
        resp.message(reply)
        return str(resp)

    # ── Media received ────────────────────────────────────────────────────────
    media_items = []
    for i in range(num_media):
        url   = request.form.get(f"MediaUrl{i}", "")
        mtype = request.form.get(f"MediaContentType{i}", "").lower()
        print(f"[WEBHOOK] Media {i}: type={mtype} | url={url[:80]}")
        media_items.append((url, mtype))

    # Ack immediately — Twilio has a 15s webhook timeout
    try:
        send_whatsapp_message(sender, "⏳ Received! Analysing... (15–30s)")
    except Exception as e:
        print(f"[WARN] Ack failed: {e}")

    # Spawn background thread for detection
    threading.Thread(
        target=process_media_background,
        args=(sender, media_items),
        daemon=True
    ).start()

    print("[WEBHOOK] Returning 200 to Twilio, processing in background")
    return str(MessagingResponse())   # empty TwiML = 200 OK instantly

@app.route("/health", methods=["GET"])
def health():
    return {"status": "DeepShield WhatsApp bot v3 running 🛡️"}, 200

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  DeepShield WhatsApp Bot v3 — Starting up 🛡️")
    print("=" * 60)
    print(f"  From:      {FROM_NUMBER}")
    print(f"  Ngrok URL: {NGROK_BASE_URL}")
    print(f"  Webhook:   POST /webhook")
    print(f"  Heatmap:   GET  /heatmap/<filename>")
    print(f"  Health:    GET  /health")
    print()
    print("  ⚠️  After ngrok restart, update NGROK_BASE_URL in .env")
    print("      AND update Twilio sandbox webhook URL")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)