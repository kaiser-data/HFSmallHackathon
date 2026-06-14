"""Cloud-side cost guardian — the dead-man's-switch for the demo GPUs.

WHY THIS EXISTS: a keep-warm GPU (min_containers>=1) once cold-looped on a broken
model and quietly burned ~$200. Modal's dashboard "spend limit" is only an alert,
not a hard stop. So cost control has to be structural and cloud-side.

THE MODEL: the GPU endpoints are ALWAYS deployed scale-to-zero (min_containers=0),
so they cost nothing idle and CANNOT be left running — 5 min after the last
request they scale to zero on their own. "Keep warm for a demo" is therefore a
*pull*: this guardian sends a cheap warm-ping to the chosen endpoints every few
minutes, but ONLY while a lease is active. Forget to tear down, close your laptop,
lose wifi — the lease expires, the pings stop, and every GPU scales to zero within
~5 min, with zero dependence on your machine being awake.

  modal deploy modal_app/guardian.py                         # always-on, cheap CPU cron
  modal run modal_app/guardian.py::lease_set --minutes 30 --apps vllm,llamacpp
  modal run modal_app/guardian.py::lease_clear
  modal run modal_app/guardian.py::lease_status

(or just use the Makefile: make demo-up / make demo-down / make status / make stop)
"""
import os
import time
import urllib.request

import modal

app = modal.App("small-hack-guardian")

# Tiny shared state: when the lease expires and which apps to keep warm. A Modal
# Dict is free and lives server-side, so the lease survives your laptop sleeping.
state = modal.Dict.from_name("daydream-guardian", create_if_missing=True)

# Endpoint URLs derive from one workspace slug (see ../endpoints.py) so switching
# workspaces never edits this file. The slug is baked into the image at deploy
# from the local MODAL_WORKSPACE env (the Makefile passes it through).
WORKSPACE = os.environ.get("MODAL_WORKSPACE", "").strip()
MAX_LEASE_MIN = 120  # hard clamp: no single lease can exceed 2 hours

image = modal.Image.debian_slim(python_version="3.11").env({"MODAL_WORKSPACE": WORKSPACE})


def _targets() -> dict:
    """Warm-ping targets, derived from the workspace baked into the image env.

    Each request is cheap enough to NOT run heavy GPU compute but still resets the
    container's idle timer: GET /models for the LLM servers, and a keyless POST to
    FLUX (it 401s instantly without painting an image)."""
    ws = os.environ.get("MODAL_WORKSPACE", "").strip()
    if not ws:
        return {}
    return {
        "vllm":     (f"https://{ws}--small-hack-vllm-serve.modal.run/v1/models", "GET"),
        "llamacpp": (f"https://{ws}--small-hack-llamacpp-serve.modal.run/v1/models", "GET"),
        "flux":     (f"https://{ws}--small-hack-flux-flux-generate.modal.run", "POST"),
    }


def _ping(url: str, method: str) -> None:
    try:
        data = b"{}" if method == "POST" else None
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20)
    except Exception:
        pass  # any response (even 401/422/404) resets the idle timer — all we need


# Cron (not Period): a cron schedule is unaffected by redeploys, whereas
# Period resets its timer every deploy — and we redeploy the guardian alongside
# the GPU apps. "*/3 * * * *" = every 3 minutes, comfortably under the 5-min
# scaledown_window so a leased app never goes cold mid-demo.
@app.function(image=image, schedule=modal.Cron("*/3 * * * *"), timeout=120)
def keepalive():
    """Every 3 min: warm the leased apps, or do nothing if the lease has lapsed."""
    exp = state.get("expiry", 0.0)
    apps = state.get("apps", [])
    if time.time() >= exp or not apps:
        return  # lease inactive -> ping nothing -> GPUs scale to zero by themselves
    targets = _targets()
    for key in apps:
        if key in targets:
            _ping(*targets[key])


@app.function(image=image)
def lease_set(minutes: float = 30, apps: str = "vllm,llamacpp"):
    """Open/renew a warm lease, clamped to MAX_LEASE_MIN; warm the apps immediately."""
    minutes = max(0.0, min(float(minutes), MAX_LEASE_MIN))
    targets = _targets()
    keys = [a.strip() for a in apps.split(",") if a.strip() in targets]
    state["expiry"] = time.time() + minutes * 60
    state["apps"] = keys
    for k in keys:                       # warm now so the first demo turn isn't cold
        _ping(*targets[k])
    print(f"LEASE SET: {minutes:.0f} min, keeping warm {keys}. Warming now…")
    print("GPUs auto-scale-to-zero ~5 min after the lease lapses. 'make demo-down' to end early.")


@app.function(image=image)
def lease_clear():
    """End the lease now — GPUs scale to zero on their own within ~5 min."""
    state["expiry"] = 0.0
    state["apps"] = []
    print("LEASE CLEARED — GPUs will scale to zero within ~5 min.")


@app.function(image=image)
def lease_status():
    """Print whether anything is being kept warm and for how much longer."""
    exp = state.get("expiry", 0.0)
    apps = state.get("apps", [])
    rem = max(0.0, exp - time.time())
    if rem > 0:
        print(f"🟢 LEASE ACTIVE: {rem/60:.1f} min left, keeping warm {apps}")
    else:
        print("⚪ lease inactive — nothing is being kept warm (GPUs scale-to-zero).")
