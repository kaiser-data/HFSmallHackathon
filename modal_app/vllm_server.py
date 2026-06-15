"""Modal GPU endpoint serving a small open-weight model via vLLM.

Exposes an OpenAI-compatible API so the agents can talk to it with the stock
`openai` client. Deploy:  modal deploy modal_app/vllm_server.py
The printed URL + "/v1" becomes MODAL_VLLM_BASE_URL for the Gradio app.

Model is intentionally a variable: swap MODEL_NAME for any <=32B HF repo.
Default keeps us well under the 32B budget so a second small agent model fits.
"""
import os
import modal

# --- pick your specialist; must keep TOTAL (all agents) <= 32B params ---
# Qwen3.5-27B in FP8 (~27GB) + the 1B MiniCPM router = 28B total, fits 1xA100-40GB.
MODEL_NAME = os.environ.get("VLLM_MODEL", "Qwen/Qwen3.5-27B-FP8")
MODEL_REVISION = os.environ.get("VLLM_REVISION", "main")
GPU = os.environ.get("VLLM_GPU", "A100-40GB")  # FP8 27B weights ~27GB; fits 40GB w/ KV cache
API_KEY = os.environ.get("VLLM_API_KEY", "local-dev-key")  # gate the endpoint

app = modal.App("small-hack-vllm")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm>=0.22.0", "huggingface_hub[hf_transfer]>=0.24")  # current vLLM for Qwen3.5 arch
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        # The slim image has the CUDA runtime but no nvcc. FlashInfer JIT-compiles
        # a sampler kernel at startup and crashes ("Could not find nvcc"). Force
        # FlashAttention + the native sampler so nothing needs the CUDA compiler;
        # the mamba/GDN path already uses Triton (self-compiling).
        "VLLM_ATTENTION_BACKEND": "FLASH_ATTN",
        "VLLM_USE_FLASHINFER_SAMPLER": "0",
        # CRITICAL: serve() reads these at RUNTIME inside the container, where the
        # local .env does NOT exist — so we must BAKE the chosen values into the
        # image env here (this .env() call runs client-side at deploy, capturing
        # the local values). Without this, the container falls back to defaults and
        # silently serves the wrong model. (Decorator args like gpu= bake fine;
        # function-body os.environ reads do not.)
        "VLLM_MODEL": MODEL_NAME,
        "VLLM_REVISION": MODEL_REVISION,
        "VLLM_MAX_LEN": os.environ.get("VLLM_MAX_LEN", "8192"),
        "VLLM_EAGER": os.environ.get("VLLM_EAGER", "0"),
    })
)

# cache weights across cold starts
hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu=GPU,
    volumes={"/root/.cache/huggingface": hf_cache},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    scaledown_window=300,        # scale to zero 5 min after the last request
    min_containers=0,            # NEVER pin a GPU; warmth is leased via the guardian
    max_containers=1,            # hard cap: a bug/loop can never fan out to N GPUs
    timeout=20 * 60,
)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=8000, startup_timeout=15 * 60)
def serve():
    import subprocess

    # The app uses plain chat completions + JSON-in-text (loose_json), never the
    # tools API — so no --enable-auto-tool-choice / --tool-call-parser here; they
    # add a model-template dependency for a feature we don't use.
    cmd = [
        "vllm", "serve", MODEL_NAME,
        "--revision", MODEL_REVISION,
        "--host", "0.0.0.0", "--port", "8000",
        "--api-key", API_KEY,
        "--max-model-len", os.environ.get("VLLM_MAX_LEN", "8192"),
    ]
    # Eager mode skips torch.compile + cudagraph capture. It was needed for the 27B
    # (capture blew the startup window + memory on a 40GB card), but a small ~7-8B
    # model captures graphs in seconds — so default to graphs ON for ~1.5-2x faster
    # decode. Set VLLM_EAGER=1 to force eager again on a big model.
    if os.environ.get("VLLM_EAGER", "0") == "1":
        cmd.append("--enforce-eager")
    subprocess.Popen(" ".join(cmd), shell=True)
