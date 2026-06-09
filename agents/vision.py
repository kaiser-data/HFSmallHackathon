"""Dream-image painter — turns one beat into a picture via the FLUX Modal endpoint.

Kept out of the engine on purpose: the engine owns narrative + game math, the app
owns presentation, and a picture is presentation. The app fires `dream_image()` in
a thread the moment a beat's outcome is known, so the image paints *under* the
Dreamweaver's narration and lands by the time the prose finishes.

Determinism stays honest: the picture is seeded by (dream seed, turn), so the same
shared seed replays the same images alongside the same dice.

Offline: with DAYDREAM_MOCK=1 (or no MODAL_FLUX_URL set) this returns a tinted
placeholder so the whole UI is playable with no GPU backend.
"""
from __future__ import annotations
import io
import os
import sys
import pathlib
import hashlib

import httpx

from .world import ENVIRONMENTS

# Derive the FLUX URL from MODAL_WORKSPACE when not set explicitly (see endpoints.py).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from endpoints import derive as _derive_urls  # noqa: E402

_WS = os.environ.get("MODAL_WORKSPACE", "").strip()
FLUX_URL = (os.environ.get("MODAL_FLUX_URL", "").strip()
            or (_derive_urls(_WS)["flux"] if _WS else ""))
FLUX_KEY = os.environ.get("MODAL_FLUX_API_KEY", "local-dev-key")
MOCK = bool(os.environ.get("DAYDREAM_MOCK")) or not FLUX_URL
TIMEOUT = float(os.environ.get("DAYDREAM_IMG_TIMEOUT", "60"))

# A beat's verdict tints the whole frame — the same lever the Nightmare uses in prose.
OUTCOME_TINT = {
    "success": "luminous hopeful light, vivid and triumphant",
    "partial": "uncertain wavering half-light, shifting and unresolved",
    "fail": "ominous encroaching shadows, the nightmare creeping in, cold dread",
}
STYLE = "dreamlike, painterly, cinematic lighting, highly detailed, surreal, no text"


def _seed_int(seed: str, turn: int) -> int:
    """Stable per-(seed, turn) image seed — mirrors resolver._rng's contract."""
    return int(hashlib.sha256(f"{seed}:{turn}".encode()).hexdigest(), 16) % (2**32)


def build_prompt(state, intent: str, outcome) -> str:
    """World art-direction + what the dreamer did + the verdict's tint."""
    env = ENVIRONMENTS.get(state.env_id)
    base = (env.visual if env and env.visual else f"a surreal dream of {state.env_name}")
    tint = OUTCOME_TINT.get(getattr(outcome, "result", None), "dawning first light, arrival")
    deed = (intent or "").strip()[:160]
    return f"{base}. {deed}. {tint}. {STYLE}"


def _placeholder(state):
    """A tinted gradient stand-in so the UI works with no backend (mock mode)."""
    try:
        from PIL import Image
    except Exception:
        return None
    tints = {"candy_desert": (60, 40, 70), "sunken_city": (12, 40, 60),
             "noir_alley": (20, 16, 40), "red_planet": (70, 30, 24),
             "token_wood": (28, 40, 30)}
    top = tints.get(getattr(state, "env_id", ""), (40, 30, 70))
    h = w = 256
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):                       # simple vertical gradient -> dark
        f = y / h
        row = tuple(int(c * (1 - 0.7 * f)) for c in top)
        for x in range(w):
            px[x, y] = row
    return img


def dream_image(state, intent: str, outcome):
    """Paint this beat. Returns a PIL image, or None on any failure (UI tolerates None)."""
    if MOCK:
        return _placeholder(state)
    payload = {"prompt": build_prompt(state, intent, outcome),
               "key": FLUX_KEY,
               "seed": _seed_int(state.seed, state.turn)}
    try:
        r = httpx.post(FLUX_URL, json=payload, timeout=TIMEOUT)
        r.raise_for_status()
        from PIL import Image
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None  # never break a turn for a missing picture
