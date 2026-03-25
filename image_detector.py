import requests
import cv2
import numpy as np
from PIL import Image

API_USER = "385880270"      # ← paste your sightengine api_user here
API_SECRET = "EeF4uhXTnHAFvnAsYQH77vwdfjPCbvrD"  # ← paste your sightengine api_secret here

def check_image_api(image_path):
    """Send image to Sightengine API for deepfake detection"""
    try:
        with open(image_path, 'rb') as f:
            response = requests.post(
                'https://api.sightengine.com/1.0/check.json',
                files={'media': f},
                data={
                    'models': 'deepfake',
                    'api_user': API_USER,
                    'api_secret': API_SECRET
                }
            )
        result = response.json()

        if result.get('status') == 'success':
            fake_score = result.get('type', {}).get('deepfake', 0.5)
            return fake_score
        else:
            # API error - fall back to rule-based only
            return None

    except Exception:
        return None

def rule_based_checks(image_path):
    """Local rule-based analysis as explainability layer"""
    findings = []
    try:
        img = cv2.imread(image_path)
        if img is None:
            return ["Could not read image"]

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Smoothness check
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 50:
            findings.append("Unusual smoothness — AI faces are often over-smoothed")

        # Noise check
        noise = np.std(
            gray.astype(float) -
            cv2.GaussianBlur(gray, (5, 5), 0).astype(float)
        )
        if noise < 2.0:
            findings.append("Very low noise pattern — consistent with GAN-generated images")

        # Color imbalance
        b, g, r = cv2.split(img)
        if abs(int(np.mean(r)) - int(np.mean(b))) > 25:
            findings.append("Color channel imbalance detected in skin tones")

        # Edge density
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size
        if edge_density < 0.01:
            findings.append("Suspiciously clean edges — may indicate AI generation")

    except Exception as e:
        findings.append(f"Analysis error: {str(e)}")

    return findings if findings else ["No specific anomalies detected"]

def detect_image(image_path):
    """Main detection function combining API + rule-based"""

    # Try API first
    api_score = check_image_api(image_path)

    # Rule-based findings (always run for explainability)
    findings = rule_based_checks(image_path)

    if api_score is not None:
        # Use API score (much more accurate)
        final_score = api_score
        source = "AI model"
    else:
        # Fallback: rule-based only
        rule_hits = len([f for f in findings if "No specific" not in f])
        final_score = min(0.3 + (rule_hits * 0.15), 0.95)
        source = "rule-based analysis"

    return {
        "score": final_score,
        "label": "SYNTHETIC" if final_score > 0.5 else "AUTHENTIC",
        "confidence": int(final_score * 100) if final_score > 0.5 else int((1 - final_score) * 100),
        "findings": findings if final_score > 0.4 else ["No anomalies detected — content appears authentic"],
        "source": source
    }