"""
DeepShield — Grad-CAM Explainability Module
============================================
Generates a heatmap overlay on an image showing which regions
triggered the deepfake suspicion.

Strategy:
  - Uses ResNet-50 pretrained on ImageNet (already in torchvision)
  - Hooks into the last conv layer (layer4) to extract gradients
  - Produces a colour-mapped overlay (jet colormap, red = most suspicious)
  - No new model downloads needed — torchvision ships ResNet-50 weights

Returns:
  heatmap_path (str) — path to saved overlay PNG (caller must delete it)
  None              — if generation fails (non-fatal, detection still works)
"""

import os
import tempfile
import numpy as np
from PIL import Image

import torch
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms

# ── Colour palette ─────────────────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")          # headless — no display needed
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# ── Model (loaded once at import time) ─────────────────────────────────────
_model = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def _load_model():
    global _model
    if _model is not None:
        return _model
    try:
        weights = models.ResNet50_Weights.IMAGENET1K_V1
        _model = models.resnet50(weights=weights)
    except Exception:
        # Older torchvision fallback
        _model = models.resnet50(pretrained=True)
    _model.eval()
    _model.to(_device)
    return _model


# ── Transform ───────────────────────────────────────────────────────────────
_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std =[0.229, 0.224, 0.225]),
])


# ── Internal hook storage ────────────────────────────────────────────────────
_gradients  = []
_activations = []

def _save_gradient(grad):
    _gradients.append(grad)

def _forward_hook(module, input, output):
    _activations.append(output)
    output.register_hook(_save_gradient)


# ── Main public function ─────────────────────────────────────────────────────
def generate_gradcam(image_path: str, label: str = "SYNTHETIC") -> str | None:
    """
    Generate a Grad-CAM heatmap overlay for the given image.

    Args:
        image_path: Path to the input image (JPG / PNG / WebP).
        label:      Detection verdict — used only in the overlay title.

    Returns:
        Path to the saved heatmap PNG, or None on failure.
    """
    global _gradients, _activations

    try:
        # ── 1. Load image ────────────────────────────────────────────────
        img_pil = Image.open(image_path).convert("RGB")
        orig_w, orig_h = img_pil.size
        input_tensor = _transform(img_pil).unsqueeze(0).to(_device)

        # ── 2. Load model & register hooks ───────────────────────────────
        model = _load_model()
        _gradients.clear()
        _activations.clear()

        handle = model.layer4.register_forward_hook(_forward_hook)

        # ── 3. Forward pass ───────────────────────────────────────────────
        model.zero_grad()
        output = model(input_tensor)            # (1, 1000)
        pred_class = output.argmax(dim=1).item()
        score = output[0, pred_class]

        # ── 4. Backward pass ──────────────────────────────────────────────
        score.backward()
        handle.remove()

        # ── 5. Compute Grad-CAM ───────────────────────────────────────────
        gradients  = _gradients[0]               # (1, C, H, W)
        activations = _activations[0]            # (1, C, H, W)

        weights = gradients.mean(dim=[2, 3], keepdim=True)   # global avg pool
        cam = (weights * activations).sum(dim=1).squeeze(0)  # (H, W)
        cam = F.relu(cam)

        # Normalise to [0, 1]
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = torch.zeros_like(cam)

        cam_np = cam.detach().cpu().numpy()   # (H, W) in [0,1]

        # ── 6. Resize CAM to original image size ─────────────────────────
        from PIL import Image as PILImage
        cam_resized = np.array(
            PILImage.fromarray((cam_np * 255).astype(np.uint8)).resize(
                (orig_w, orig_h), PILImage.BILINEAR
            )
        ) / 255.0                             # back to [0,1]

        # ── 7. Apply jet colourmap ────────────────────────────────────────
        colormap   = cm.get_cmap("jet")
        heatmap_rgb = colormap(cam_resized)[:, :, :3]      # (H, W, 3) RGB
        heatmap_rgb = (heatmap_rgb * 255).astype(np.uint8)

        orig_np = np.array(img_pil)            # (H, W, 3) RGB

        # Blend: 55% original + 45% heatmap
        overlay = (0.55 * orig_np + 0.45 * heatmap_rgb).astype(np.uint8)

        # ── 8. Build figure with annotation ──────────────────────────────
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
        fig.patch.set_facecolor("#0f1117")

        for ax in axes:
            ax.set_facecolor("#0f1117")
            ax.axis("off")

        axes[0].imshow(orig_np)
        axes[0].set_title("Original", color="white", fontsize=12, pad=8)

        axes[1].imshow(overlay)
        title_color = "#ff4b4b" if "SYNTHETIC" in label.upper() else "#00c853"
        axes[1].set_title(
            f"Grad-CAM — {label}\n(red = most suspicious regions)",
            color=title_color, fontsize=10, pad=8
        )

        fig.suptitle(
            "🛡️ DeepShield Explainability",
            color="white", fontsize=13, y=1.01
        )
        plt.tight_layout()

        # ── 9. Save to temp file ──────────────────────────────────────────
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix="_gradcam.png",
            dir=tempfile.gettempdir()
        )
        plt.savefig(tmp.name, bbox_inches="tight", dpi=130,
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        tmp.close()

        return tmp.name

    except Exception as e:
        print(f"[GradCAM] Failed (non-fatal): {e}")
        try:
            plt.close("all")
        except Exception:
            pass
        return None