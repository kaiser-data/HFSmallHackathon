"""Deploy DAYDREAM to the Build Small hackathon HF Space.

Uses the cached HF write token (from `hf auth login`). Creates the Space, sets the
MODAL_* secrets (the app derives endpoint URLs from MODAL_WORKSPACE), and uploads
the repo (excluding venv/cache/credits junk). Re-runnable.
"""
from huggingface_hub import create_repo, upload_folder, add_space_secret

REPO = "build-small-hackathon/daydream"

create_repo(REPO, repo_type="space", space_sdk="gradio", exist_ok=True)
print("space ready:", REPO)

secrets = {
    "MODAL_WORKSPACE": "martinkaiser-bln",
    "MODAL_VLLM_API_KEY": "local-dev-key",
    "MODAL_LLAMACPP_API_KEY": "local-dev-key",
    "MODAL_FLUX_API_KEY": "local-dev-key",
}
for k, v in secrets.items():
    add_space_secret(REPO, k, v)
    print("secret set:", k)

upload_folder(
    repo_id=REPO,
    repo_type="space",
    folder_path=".",
    ignore_patterns=[
        ".venv/*", ".git/*", "**/__pycache__/*", "__pycache__/*",
        "graphify-out/*", ".claude/*", ".env", "*.pyc", "*.png",
    ],
    commit_message="Deploy DAYDREAM — Thousand Token Wood (small-model dream fleet)",
)
print("uploaded ->", "https://huggingface.co/spaces/" + REPO)
