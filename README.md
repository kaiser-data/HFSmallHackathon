# Small Hackathon — Multiagent on Modal 🍄⚖️

A multiagent system built for the **Small Hackathon** (Gradio · Hugging Face).
Small models (≤32B total), Gradio frontend on a HF Space, agent inference on **Modal**.

> Default build: **"The Council"** (Thousand Token Wood track) — a council of tiny
> specialist agents debates your question live and hands down a screenshot-able verdict.
> See [`docs/CONCEPTS.md`](docs/CONCEPTS.md) for all three pitches.

## Architecture

```
HF Space (Gradio)  ──OpenAI API──▶  Modal vLLM   (Qwen3.5-27B specialist voices)
   app/app.py                       Modal llama.cpp (MiniCPM5-1B router/chair)
        │
        ▼
   agents/  ── base.Agent · orchestrator.Council · registry (role→backend)
```

Both backends are OpenAI-compatible, so swapping models or running "Off the Grid"
is a config change, not a code change.

## Bonus badges in reach
- 🦙 **Llama Champion** — router served via llama.cpp on Modal
- 📡 **Open trace** — publish agent traces to the Hub
- 🎨 **Off-Brand** — custom Gradio theme/UI
- 📓 **Field Notes** — write-up of what we learned
- OpenBMB special prize — MiniCPM5-1B as the tiny router

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in Modal URLs/keys after deploy

# 1) deploy inference on Modal
pip install modal && modal token new
modal deploy modal_app/vllm_server.py        # prints the specialist URL
modal deploy modal_app/llamacpp_server.py    # prints the router URL  (Llama badge)

# 2) run the Gradio app locally against those endpoints
python app/app.py
```

## Deploy as a HF Space
Symlink `app/app.py` to `app.py` at repo root, push to a Space, and set the
`MODAL_*` secrets from `.env.example`. `requirements.txt` is Space-ready.

## Layout
| Path | What |
|---|---|
| `modal_app/vllm_server.py` | Modal GPU vLLM endpoint (big specialist) |
| `modal_app/llamacpp_server.py` | Modal llama.cpp GGUF endpoint (tiny router) |
| `agents/` | Agent base, Council orchestrator, backend registry |
| `app/app.py` | Gradio Space entrypoint |
| `docs/CONCEPTS.md` | The three concept pitches + recommendation |
