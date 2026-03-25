import cv2
import numpy as np
import tempfile
import os
from image_detector import detect_image, rule_based_checks

def extract_frames(video_path, max_frames=10):
    """Extract evenly spaced frames from video"""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0

    # Pick evenly spaced frame indices
    indices = np.linspace(0, total_frames - 1, min(max_frames, total_frames), dtype=int)

    frames = []
    frame_paths = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Save frame to temp file
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            cv2.imwrite(tmp.name, frame)
            frames.append(frame)
            frame_paths.append(tmp.name)

    cap.release()
    return frames, frame_paths, duration, fps

def detect_video(video_path):
    """Analyze video for deepfake content frame by frame"""
    try:
        frames, frame_paths, duration, fps = extract_frames(video_path, max_frames=10)

        if not frames:
            return {"error": "Could not extract frames from video"}

        frame_scores = []
        frame_findings = []

        for i, path in enumerate(frame_paths):
            result = detect_image(path)
            if "error" not in result:
                frame_scores.append(result["score"])
                frame_findings.extend(result["findings"])
            os.unlink(path)  # cleanup temp frame

        if not frame_scores:
            return {"error": "Could not analyze frames"}

        avg_score = np.mean(frame_scores)
        max_score = np.max(frame_scores)
        suspicious_frames = sum(1 for s in frame_scores if s > 0.5)

        # Collect unique findings
        unique_findings = list(set([
            f for f in frame_findings if "No specific" not in f
        ]))

        # Final verdict — use max score for safety
        final_score = (avg_score * 0.6) + (max_score * 0.4)

        return {
            "score": final_score,
            "label": "SYNTHETIC" if final_score > 0.5 else "AUTHENTIC",
            "confidence": int(final_score * 100) if final_score > 0.5 else int((1 - final_score) * 100),
            "frame_scores": frame_scores,
            "suspicious_frames": suspicious_frames,
            "total_frames_analyzed": len(frame_scores),
            "duration": round(duration, 1),
            "findings": unique_findings if unique_findings else ["No specific anomalies found"]
        }

    except Exception as e:
        return {"error": str(e)}