"""Modal endpoint serving a GGUF model through llama.cpp  ->  Llama Champion badge.

llama.cpp's server is OpenAI-compatible, so the same agent client works.
Deploy:  modal deploy modal_app/llamacpp_server.py

Use this for the tiny router/specialist (e.g. MiniCPM5-1B GGUF -> OpenBMB prize)
or to run the whole thing "Off the Grid" on a single small quantized model.
"""
import os
import modal

# a small GGUF repo + the specific quantized file inside it
GGUF_REPO = os.environ.get("GGUF_REPO", "openbmb/MiniCPM5-1B-GGUF")
GGUF_FILE = os.environ.get("GGUF_FILE", "MiniCPM5-1B-Q4_K_M.gguf")  # exact case as on HF
GPU = os.environ.get("LLAMACPP_GPU", "T4")  # 1B quantized is tiny; T4 is plenty
API_KEY = os.environ.get("LLAMACPP_API_KEY", "local-dev-key")

app = modal.App("small-hack-llamacpp")

image = (
    modal.Image.from_registry("ghcr.io/ggml-org/llama.cpp:server-cuda", add_python="3.11")
    .pip_install("huggingface_hub[hf_transfer]>=0.24")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu=GPU,
    volumes={"/root/.cache/huggingface": hf_cache},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    scaledown_window=300,
    timeout=20 * 60,
)
@modal.concurrent(max_inputs=16)
@modal.web_server(port=8080, startup_timeout=10 * 60)
def serve():
    import subprocess
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(repo_id=GGUF_REPO, filename=GGUF_FILE,
                           local_dir="/root/.cache/huggingface/gguf")
    cmd = [
        "/app/llama-server",
        "-m", path,
        "--host", "0.0.0.0", "--port", "8080",
        "-ngl", "999",            # offload all layers to GPU
        "-c", os.environ.get("LLAMACPP_CTX", "8192"),
        "--api-key", API_KEY,
        "--jinja",                # enable tool-call template parsing
    ]
    subprocess.Popen(" ".join(cmd), shell=True)
