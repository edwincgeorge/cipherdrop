import io
import math
import random
import hashlib
import time
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from itsdangerous import URLSafeTimedSerializer
 
# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY   = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"  # change this!
CAPTCHA_TTL  = 120          # seconds before a challenge expires
IMG_W, IMG_H = 320, 180     # image dimensions
TOLERANCE    = 28           # px radius for a valid click
NUM_DISTRACTORS = 5         # number of fake shapes alongside the target
# ──────────────────────────────────────────────────────────────────────────────

serializer = URLSafeTimedSerializer(SECRET_KEY)

SHAPE_LABELS = {
    "circle":    "circle",
    "triangle":  "triangle",
    "square":    "square",
    "star":      "star",
    "diamond":   "diamond",
    "cross":     "cross",
}

PALETTE = [
    (220, 80,  80),   # red
    (80,  160, 220),  # blue
    (80,  200, 120),  # green
    (240, 180, 60),   # amber
    (180, 100, 220),  # purple
    (240, 120, 60),   # orange
    (60,  200, 200),  # teal
]


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _draw_circle(draw, cx, cy, r, color):
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)

def _draw_square(draw, cx, cy, r, color):
    draw.rectangle([cx-r, cy-r, cx+r, cy+r], fill=color)

def _draw_triangle(draw, cx, cy, r, color):
    pts = [
        (cx, cy - r),
        (cx - r, cy + r),
        (cx + r, cy + r),
    ]
    draw.polygon(pts, fill=color)

def _draw_diamond(draw, cx, cy, r, color):
    pts = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
    draw.polygon(pts, fill=color)

def _draw_star(draw, cx, cy, r, color):
    pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        radius = r if i % 2 == 0 else r * 0.45
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    draw.polygon(pts, fill=color)

def _draw_cross(draw, cx, cy, r, color):
    t = r // 3
    draw.rectangle([cx-t, cy-r, cx+t, cy+r], fill=color)
    draw.rectangle([cx-r, cy-t, cx+r, cy+t], fill=color)

DRAW_FN = {
    "circle":   _draw_circle,
    "square":   _draw_square,
    "triangle": _draw_triangle,
    "diamond":  _draw_diamond,
    "star":     _draw_star,
    "cross":    _draw_cross,
}


# ── Noise background ──────────────────────────────────────────────────────────

def _noise_background(img_w, img_h):
    """Creates a subtle grid + gradient background."""
    img = Image.new("RGB", (img_w, img_h), (18, 18, 22))
    draw = ImageDraw.Draw(img)
    # Grid lines
    for x in range(0, img_w, 20):
        draw.line([(x, 0), (x, img_h)], fill=(30, 30, 36), width=1)
    for y in range(0, img_h, 20):
        draw.line([(0, y), (img_w, y)], fill=(30, 30, 36), width=1)
    # Random noise dots
    for _ in range(180):
        x, y = random.randint(0, img_w), random.randint(0, img_h)
        r = random.randint(1, 2)
        c = random.randint(35, 55)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(c, c, c+8))
    return img


# ── Challenge generation ──────────────────────────────────────────────────────

def generate_challenge() -> dict:
    """
    Returns:
      {
        "image_b64": "<base64 PNG>",
        "token":     "<signed token containing answer>",
        "prompt":    "Click the star"
      }
    """
    img = _noise_background(IMG_W, IMG_H)
    draw = ImageDraw.Draw(img)

    # Pick target shape + color
    target_shape = random.choice(list(SHAPE_LABELS.keys()))
    target_color = random.choice(PALETTE)

    # Generate non-overlapping positions
    positions = []
    all_shapes = [target_shape] + random.choices(
        [s for s in SHAPE_LABELS if s != target_shape], k=NUM_DISTRACTORS
    )
    random.shuffle(all_shapes)
    target_idx = all_shapes.index(target_shape)

    margin = 34
    attempts = 0
    placed = []
    for shape in all_shapes:
        for _ in range(60):
            cx = random.randint(margin, IMG_W - margin)
            cy = random.randint(margin, IMG_H - margin)
            # Ensure shapes don't overlap too much
            if all(math.hypot(cx-px, cy-py) > margin * 1.8 for px, py in placed):
                placed.append((cx, cy))
                break
        else:
            # fallback: place anyway
            placed.append((random.randint(margin, IMG_W-margin),
                           random.randint(margin, IMG_H-margin)))

    # Draw shapes
    for i, (shape, (cx, cy)) in enumerate(zip(all_shapes, placed)):
        r = random.randint(14, 20)
        if i == target_idx:
            color = target_color
            tx, ty = cx, cy   # correct answer coordinates
        else:
            # Pick a different color for distractors
            color = random.choice([c for c in PALETTE if c != target_color])
        # Draw subtle shadow
        DRAW_FN[shape](draw, cx+2, cy+2, r, (10, 10, 12))
        DRAW_FN[shape](draw, cx, cy, r, color)

    # Slight blur to make it harder to parse programmatically
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))

    # Encode to base64
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    import base64
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    # Sign the answer (coordinates + shape + timestamp)
    payload = {"x": tx, "y": ty, "shape": target_shape, "ts": int(time.time())}
    token = serializer.dumps(payload, salt="captcha-answer")

    return {
        "image_b64": img_b64,
        "token":     token,
        "prompt":    f"Click the <strong>{SHAPE_LABELS[target_shape]}</strong>",
    }


# ── Validation ────────────────────────────────────────────────────────────────

def validate_click(token: str, click_x: float, click_y: float) -> tuple[bool, str]:
    """
    Validates user's click against the signed token.
    Returns (success: bool, reason: str)
    """
    try:
        payload = serializer.loads(token, salt="captcha-answer", max_age=CAPTCHA_TTL)
    except Exception as e:
        return False, f"Token invalid or expired: {e}"

    dist = math.hypot(click_x - payload["x"], click_y - payload["y"])
    if dist <= TOLERANCE:
        return True, "ok"
    return False, f"Clicked too far from target ({dist:.0f}px, tolerance={TOLERANCE}px)"
