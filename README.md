# 🌙 DAYDREAM — wander dreamlike worlds with a fleet of small models

Built for the **Small Hackathon** (Gradio · Hugging Face). Track: *An Adventure in
Thousand Token Wood*. You + an AI companion (**Hobbes**) drift through dreamlike
environments conjured live by a **fleet of small-model agents**. You steer with a
word; Hobbes reacts and escalates the big choices. Light mission + free wander.

> **The thesis:** you don't own one giant brain — you command a *fleet of scrappy
> small minds*. And in a dream, a small model's fuzziness isn't a bug, it's the
> aesthetic. **The constraint is the art.** ≤32B total, by design.

## How it plays
1. Pick a world (Candy Desert, Sunken City, Rain Street, Red Planet, Thousand Token Wood).
2. The **Dreamweaver** narrates; **Mischief** bends the rules; **Hobbes** reacts and
   offers 2–3 choices (or type your own intent).
3. A tiny **Keeper** agent tracks externalized world-state (location, inventory,
   mission progress) so the small models stay coherent. Reach the dream's resolution — or just wander.

## The fleet (agent-first)
| Agent | Role | Backend | Job |
|---|---|---|---|
| 🌌 Dreamweaver | specialist | Modal vLLM (Qwen3.5-27B) | narrate the world |
| 🃏 Mischief | specialist | Modal vLLM | inject surreal twists |
| 🐯 Hobbes | specialist | Modal vLLM | companion + escalate choices |
| 🗺 Keeper | router | Modal llama.cpp (MiniCPM5-1B) | structured world-state updates |

Backends are OpenAI-compatible → swap models or go "Off the Grid" via env, no code change.

## Quickstart (offline, no backend)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DAYDREAM_MOCK=1 python app/app.py      # fully playable with templated agents
```

## Run against Modal inference
```bash
pip install modal && modal token new
modal deploy modal_app/vllm_server.py       # Dreamweaver / Mischief / Hobbes
modal deploy modal_app/llamacpp_server.py   # Keeper (Llama Champion badge 🦙)
cp .env.example .env                         # paste the printed URLs/keys
python app/app.py
```

## Deploy as a HF Space
Symlink `app/app.py` → `app.py` at repo root, push to a Space, set the `MODAL_*`
secrets from `.env.example`. `requirements.txt` is Space-ready.

## Bonus badges in reach
🦙 **Llama Champion** (Keeper via llama.cpp) · 🎨 **Off-Brand** (dream UI) ·
📡 **Open trace** (share a dream run) · 📓 **Field Notes** · MiniCPM5-1B → OpenBMB prize.
**Stretch:** doodle→dream via MiniCPM-V vision.

## Layout
| Path | What |
|---|---|
| `agents/dream.py` | DAYDREAM fleet engine (Dreamweaver · Mischief · Hobbes · Keeper) |
| `agents/world.py` | Environments (Mission skins) + externalized `WorldState` |
| `agents/base.py` | Tiny streaming/JSON Agent + `DAYDREAM_MOCK` offline mode |
| `agents/registry.py` | role→backend map (OpenAI-compatible) |
| `app/app.py` | Gradio command-deck UI |
| `modal_app/*.py` | Modal vLLM + llama.cpp inference endpoints |
| `docs/CONCEPTS.md` | concept exploration that led here |
