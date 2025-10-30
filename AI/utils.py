import io
import numpy as np
from .models import Notification

try:
    import torch
    import clip
    from PIL import Image
    AI_AVAILABLE = True
except Exception:
    torch = None
    clip = None
    Image = None
    AI_AVAILABLE = False


def generate_embedding(image_field):
    """Generate an embedding for the given image using CLIP or a fallback method."""
    if image_field is None:
        return None

    try:
        fp = image_field.file if hasattr(image_field, 'file') else image_field
        fp.seek(0)
        data = fp.read()
    except Exception:
        data = str(image_field).encode('utf-8')

    # Use CLIP if available
    if AI_AVAILABLE and clip is not None:
        try:
            model, preprocess = clip.load("ViT-B/32", device="cpu")
            pil = Image.open(io.BytesIO(data)).convert('RGB')
            image_input = preprocess(pil).unsqueeze(0)
            with torch.no_grad():
                embedding = model.encode_image(image_input)
                emb = embedding.cpu().numpy().astype(np.float32)
                return emb.tobytes()
        except Exception:
            pass

    # Fallback: create a pseudo-embedding from image bytes
    arr = np.frombuffer(data, dtype=np.uint8)
    if arr.size == 0:
        arr = np.arange(128, dtype=np.uint8)
    vec = np.resize(arr.astype(np.float32), 512)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.astype(np.float32).tobytes()


def cosine_similarity(emb_a_bytes, emb_b_bytes):
    """Compute cosine similarity between two byte-encoded embeddings."""
    if emb_a_bytes is None or emb_b_bytes is None:
        return 0.0
    try:
        a = np.frombuffer(emb_a_bytes, dtype=np.float32)
        b = np.frombuffer(emb_b_bytes, dtype=np.float32)
        if a.size == 0 or b.size == 0:
            return 0.0
        min_len = min(a.size, b.size)
        a = a[:min_len]
        b = b[:min_len]
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)
    except Exception:
        return 0.0


def send_match_notification(lost, found):
    """Create notifications for both users when a match is found."""
    try:
        # Use 'name' instead of 'title' since models use 'name' field
        msg = (
            f"Match found: Lost item '{lost.name}' (id={lost.id}) "
            f"matched with Found item '{found.name}' (id={found.id})."
        )
        # Check if users exist before creating notifications
        if hasattr(lost, 'user') and lost.user:
            Notification.objects.create(user=lost.user, message=msg)
        if hasattr(found, 'user') and found.user:
            Notification.objects.create(user=found.user, message=msg)
    except Exception:
        pass
