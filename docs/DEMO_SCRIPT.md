# 🎬 DAYDREAM — Demo Script (click-by-click)

**Live app:** https://huggingface.co/spaces/build-small-hackathon/daydream
**Target length:** ~2 minutes · **Goal:** show a fast, beautiful, *fair* story with the fleet.

---

## ⚙️ Before you hit record (one-time)
1. **Warm the GPUs** so there's zero cold-start on camera:
   ```
   make demo-up
   ```
   Wait ~2 min, then load the Space and do ONE throwaway turn to confirm it's snappy.
   *(vLLM is already pinned warm via `min_containers=1`, but this also warms FLUX + Keeper.)*
2. Set the window so the **chat (left)**, **dream image (top-right)**, and **HUD (right)** are all visible.

---

## 🎥 The run — what to click & say

### 0:00 — The hook (don't touch anything yet)
> *"This is DAYDREAM — a bedtime dream you play, dreamed live by a fleet of small
> models, none bigger than 32B. The twist: the code rolls the dice, the models only
> tell the story. So it's a fair game, not a chatbot."*

Point at the fleet line: *"Qwen MoE narrates, a 1-billion MiniCPM keeps the world, FLUX paints it."*

### 0:15 — Begin
- **World:** leave on **🏜 The Candy Desert** (or pick 🚀 The Red Planet for the rocket arc).
- **Seed:** leave **`abc123`** (deterministic — your rehearsed run replays identically).
- **Click → `Begin the dream 🌙`**

> *"I pick a world and a seed — same seed always replays the same dice, so runs are
> shareable."*

The **hero image appears instantly**; narration streams in under a second; the **quest** shows: *"Find what is humming under the dunes."*

### 0:30 — First gambit (show the fairness + risk)
Point at the three buttons: *"Each option shows its real odds — safe is 5% fail, reckless is 40% but worth +40."*
- **Click → 🟡 the BOLD option** (the middle button — its label is scene-specific, e.g. *"Dig where the sand hums"*).

> *"I gamble. Watch the die — 34 versus a fail line of 25 — the CODE decided that,
> live, before the model said a word."*

The story advances toward the goal; the **image repaints**; **Progress** ticks up.

### 0:50 — Type your own move (show open-ended play)
- **Click the text box, type:** `follow the hum deeper into the dunes`
- **Click → `Do it`**

> *"I'm not stuck with buttons — I can type anything, and the dream weaves it in."*

### 1:10 — A reckless beat (show Hobbes + stakes)
- **Click → 🔴 the RECKLESS option.**

> *"Hobbes, my tiger, reacts to every bet — and he grows braver as we survive risks
> together. Watch his mood here on the right."* (point at the 🐯 Hobbes meter)

If it fails, the **Nightmare** presses — call it out: *"Fail too much and the Nightmare closes in."*

### 1:30 — Toward the climax
- Take **1–2 more bold gambits** to push Progress toward 100 (or, for a clean rehearsed ending, keep the same seed and pre-walk the exact button sequence that wins).

> *"Reach 100% and you wake with the prize; run out of lucidity and the dream
> dissolves — both get a real climax, not a generic 'the end'."*

### 1:50 — The takeaway
- **Click → `📥 Download my story`** (show the file downloading).

> *"Every run is a downloadable story — small models, big dreams. Fair, fast, and
> entirely under 32B."*

---

## 🗣️ Three lines to land (the judge-memorable bits)
1. **"Code owns the dice, models own the words."** (the fairness differentiator)
2. **"A fleet of small minds, not one big brain — and a 30B MoE that fires only 3B per token."**
3. **"Same seed replays the same dream — beat my run."**

## 🧯 If something stalls on camera
- A turn hangs? It cold-started — the narrator **recovers on its own** (it'll stream after a beat). Keep talking; don't refresh.
- Worst case, it shows *"The dream wavers for a moment, then steadies"* and moves on — the game never crashes.

## 💸 After recording
```
make demo-down                 # ends the lease
MODAL_MIN_CONTAINERS=0 modal deploy modal_app/vllm_server.py   # stop the always-warm GPU $
```
