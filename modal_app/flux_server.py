"""Modal GPU endpoint that paints a dream beat — the fleet's eyes.

A fast, guidance-distilled image model (FLUX.1-schnell by default, Apache-2.0 and
ungated) turns one beat's prompt into a picture. The app fires this *in parallel*
with the Dreamweaver's narration (same overlap trick as the Keeper), so the image
lands by the time the prose finishes — near-zero added wait on a turn.

POST {"prompt": str, "key": str, "seed": int?}  ->  image/png bytes
The optional seed keeps "beat my run, seed abc123" honest: same dream seed +
turn -> same picture, deterministic like the dice.

Deploy:  modal deploy modal_app/flux_server.py
Then the printed URL becomes MODAL_FLUX_URL for the Gradio app.
"""
import io
import os
import modal

# schnell is 1-4 step, guidance-free, Apache-2.0, ungated — ideal for fast dreams.
MODEL = os.environ.get("FLUX_MODEL", "black-forest-labs/FLUX.1-schnell")
GPU = os.environ.get("FLUX_GPU", "A100-40GB")
STEPS = int(os.environ.get("FLUX_STEPS", "2"))      # schnell is guidance-distilled; 2 steps is the speed/quality sweet spot
SIZE = int(os.environ.get("FLUX_SIZE", "640"))      # square; smaller = faster (640 ≈ 2x faster than 768 in pixels)
# FLUX bf16 (~34GB across transformer+T5+VAE) is tight on 40GB, so offload module
# weights to CPU and stream them to the GPU per step. Adds a little latency but
# fits comfortably; set FLUX_OFFLOAD=0 on an 80GB card for full-speed (~2s).
OFFLOAD = os.environ.get("FLUX_OFFLOAD", "1") == "1"
API_KEY = os.environ.get("FLUX_API_KEY", "local-dev-key")

app = modal.App("small-hack-flux")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "diffusers>=0.31", "transformers>=4.44", "accelerate>=0.34",
        "sentencepiece>=0.2", "protobuf>=4.25",
        "torch>=2.4", "huggingface_hub[hf_transfer]>=0.24", "fastapi[standard]",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)


# FLUX.1-schnell's HF repo is gated (Apache-2.0 weights, but terms-gated), so the
# container needs a real HF token to download. Stored as a named Modal secret of
# type "Hugging Face" (which provides HF_TOKEN) so the token never lives in this
# repo or a deploy command. Override the name via FLUX_HF_SECRET if yours differs.
hf_secret = modal.Secret.from_name(os.environ.get("FLUX_HF_SECRET", "huggingface-secret"))


@app.cls(
    image=image,
    gpu=GPU,
    volumes={"/root/.cache/huggingface": hf_cache},
    secrets=[hf_secret],
    scaledown_window=300,        # scale to zero 5 min after the last request
    min_containers=0,            # NEVER pin a GPU; warmth is leased via the guardian
    max_containers=1,            # hard cap: a bug/loop can never fan out to N GPUs
    timeout=20 * 60,
)
@modal.concurrent(max_inputs=1)  # one offloaded pipe at a time; a turn paints one beat
class Flux:
    @modal.enter()
    def load(self):
        import torch
        from diffusers import FluxPipeline

        self.pipe = FluxPipeline.from_pretrained(MODEL, torch_dtype=torch.bfloat16)
        if OFFLOAD:
            self.pipe.enable_model_cpu_offload()
        else:
            self.pipe.to("cuda")

    @modal.fastapi_endpoint(method="POST", docs=False)
    def generate(self, data: dict):
        import torch
        from fastapi import Response

        if data.get("key") != API_KEY:
            return Response(content=b"unauthorized", status_code=401)
        prompt = (data.get("prompt") or "a surreal lucid dream, painterly")[:500]

        gen = None
        if (sd := data.get("seed")) is not None:
            gen = torch.Generator("cpu").manual_seed(int(sd) % (2**32))

        img = self.pipe(
            prompt,
            num_inference_steps=STEPS,
            guidance_scale=0.0,                # schnell is guidance-distilled
            height=SIZE, width=SIZE,
            max_sequence_length=256,
            generator=gen,
        ).images[0]

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")
