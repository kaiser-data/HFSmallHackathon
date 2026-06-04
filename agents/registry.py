"""Backend + model registry.

Each logical agent points at a (base_url, api_key, model) triple. Backends are
OpenAI-compatible, so the same client code hits Modal vLLM or Modal llama.cpp.
Configure via env so the HF Space never hardcodes URLs/keys.
"""
import os
from functools import lru_cache
from openai import OpenAI

# --- backends: filled from Space secrets / .env ---
VLLM_BASE_URL = os.environ.get("MODAL_VLLM_BASE_URL", "http://localhost:8000/v1")
VLLM_API_KEY = os.environ.get("MODAL_VLLM_API_KEY", "local-dev-key")
VLLM_MODEL = os.environ.get("MODAL_VLLM_MODEL", "Qwen/Qwen3.5-27B-Instruct")

LLAMACPP_BASE_URL = os.environ.get("MODAL_LLAMACPP_BASE_URL", "http://localhost:8080/v1")
LLAMACPP_API_KEY = os.environ.get("MODAL_LLAMACPP_API_KEY", "local-dev-key")
LLAMACPP_MODEL = os.environ.get("MODAL_LLAMACPP_MODEL", "minicpm5-1b")

# logical-agent -> backend mapping. Swap freely; total params must stay <= 32B.
REGISTRY = {
    # big specialist (debate voices, narrator, writer) on vLLM
    "specialist": {"base_url": VLLM_BASE_URL, "api_key": VLLM_API_KEY, "model": VLLM_MODEL},
    # tiny fast router / state-keeper on llama.cpp (OpenBMB MiniCPM -> sponsor prize + badge)
    "router":     {"base_url": LLAMACPP_BASE_URL, "api_key": LLAMACPP_API_KEY, "model": LLAMACPP_MODEL},
}


@lru_cache(maxsize=None)
def get_client(role: str) -> tuple[OpenAI, str]:
    """Return (client, model_name) for a logical role."""
    cfg = REGISTRY.get(role)
    if cfg is None:
        raise KeyError(f"Unknown agent role '{role}'. Known: {list(REGISTRY)}")
    client = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"], timeout=120.0)
    return client, cfg["model"]
