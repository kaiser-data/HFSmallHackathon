"""Single source of truth for Modal endpoint URLs.

Modal's deployed web URLs are deterministic: they're built from the WORKSPACE
slug + the app/function name. So instead of hardcoding three full URLs (which
break the moment you switch workspaces — e.g. moving to the credit workspace),
we derive them all from one value: MODAL_WORKSPACE.

Switching workspaces is then a one-line change (MODAL_WORKSPACE=... in .env),
not a code edit across registry.py / vision.py / guardian.py.

Explicit MODAL_*_URL env vars still win if set, so nothing here removes the
escape hatch for a non-standard URL.
"""
from __future__ import annotations

# app name -> the web-endpoint label Modal appends after "<workspace>--".
# vLLM/llama.cpp expose @modal.web_server functions named `serve`; FLUX exposes
# a class endpoint (class Flux, method generate) -> "<app>-flux-generate".
_SUFFIX = {
    "vllm":     "small-hack-vllm-serve",
    "llamacpp": "small-hack-llamacpp-serve",
    "flux":     "small-hack-flux-flux-generate",
}


def derive(workspace: str) -> dict[str, str]:
    """Map a workspace slug -> {vllm, llamacpp, flux} base URLs."""
    ws = (workspace or "").strip()
    base = {k: f"https://{ws}--{suf}.modal.run" for k, suf in _SUFFIX.items()}
    # The OpenAI-compatible servers live under /v1; FLUX is a bare POST endpoint.
    base["vllm"] += "/v1"
    base["llamacpp"] += "/v1"
    return base
