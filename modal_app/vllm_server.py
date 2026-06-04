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
MODEL_NAME = os.environ.get("VLLM_MODEL", "Qwen/Qwen3.5-27B-Instruct")
MODEL_REVISION = os.environ.get("VLLM_REVISION", "main")
GPU = os.environ.get("VLLM_GPU", "A100-40GB")  # H100/A100; 27B fits 1xA100-40/80
API_KEY = os.environ.get("VLLM_API_KEY", "local-dev-key")  # gate the endpoint

app = modal.App("small-hack-vllm")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm>=0.6.0", "huggingface_hub[hf_transfer]>=0.24")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

# cache weights across cold starts
hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu=GPU,
    volumes={"/root/.cache/huggingface": hf_cache},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    scaledown_window=300,        # keep warm 5 min between requests
    timeout=20 * 60,
)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=8000, startup_timeout=15 * 60)
def serve():
    import subprocess

    cmd = [
        "vllm", "serve", MODEL_NAME,
        "--revision", MODEL_REVISION,
        "--host", "0.0.0.0", "--port", "8000",
        "--api-key", API_KEY,
        "--max-model-len", os.environ.get("VLLM_MAX_LEN", "16384"),
        "--enable-auto-tool-choice",
        "--tool-call-parser", os.environ.get("VLLM_TOOL_PARSER", "hermes"),
    ]
    subprocess.Popen(" ".join(cmd), shell=True)
