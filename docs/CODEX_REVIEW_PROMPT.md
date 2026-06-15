# Codex review & improvement brief — DAYDREAM

> Paste this to OpenAI Codex (connected to the GitHub repo
> `kaiser-data/HFSmallHackathon`). It asks Codex to review the project AND make
> concrete improvements as commits. (Codex-attributed commits also qualify this
> entry for the hackathon's OpenAI Codex prize.)

---

You are reviewing **DAYDREAM**, a submission for the *Build Small* hackathon
(Hugging Face × Gradio, models ≤32B that run on personal/serverless hardware).
Work directly in the repo, make focused commits with clear messages, and open a
short summary of what you changed and why.

## What DAYDREAM is
A bedtime dream you *play*: you take **gambits** (safe/bold/reckless) through
surreal worlds with your stuffed tiger **Hobbes**, who grows brave as you survive
bets made together. It is dreamed in real time by a **fleet of small models**, each
with one job — and a **deterministic, model-free resolver** owns all dice and
rewards, so the game is fair and replayable.

- **Stack:** Gradio UI (`app/app.py`) → a `DreamEngine` orchestrator
  (`agents/dream.py`) → Modal serverless GPU endpoints (`modal_app/*.py`).
- **The fleet:** 🌌 Dreamweaver (narrate), 👁 Nightmare (menace), 🐯 Hobbes
  (companion + 3 choices, JSON), 🗺 Keeper (world-state, JSON), 🎨 FLUX (per-beat
  image). Narrator = Qwen3-30B-A3B MoE on vLLM; Keeper = MiniCPM5-1B on llama.cpp.
- **Two principles:** (1) *code owns the dice, models own the words*
  (`agents/resolver.py`, seeded by `(seed, turn)`); (2) *world-state is externalized*
  (`agents/world.py`) and fed to each agent in compact slices so small models stay
  coherent.
- See `docs/ARCHITECTURE.md` for diagrams. `DAYDREAM_MOCK=1 python app/app.py`
  runs the whole thing offline with templated agents (no GPU) — use it to test.

## Constraints to respect
- Every model must stay **≤32B params** (the MoE is 30B total / 3B active — keep it
  under the cap; don't swap in anything bigger).
- Don't break the offline `DAYDREAM_MOCK=1` path — it must stay fully playable.
- Keep backends OpenAI-compatible and config-driven (`MODAL_WORKSPACE` derives URLs
  via `endpoints.py`). Don't hardcode endpoint URLs.
- The resolver must remain the *only* place game outcomes are decided — never let a
  model decide pass/fail or rewards.

## What I want from you (review + improve, in priority order)

1. **Correctness & robustness.** Hunt real bugs: JSON-parsing edge cases from small
   models (`loose_json`), retry/degrade paths in `agents/base.py`, state mutations
   in `resolver.apply`, race conditions in the threaded Keeper/image overlap in
   `dream.py`. Fix what you find; add a few targeted tests if cheap.

2. **Gameplay depth & balance.** Review the tier math in `world.py` (`TIER_TABLE`)
   and `resolver.py`. Are safe/bold/reckless each a meaningful, viable choice across
   a ~8–12 turn arc? Is the COURAGE→mood→farewell loop satisfying? Propose and
   implement small, high-leverage improvements (e.g. Hobbes mechanically reacting to
   his mood, clearer risk/reward signaling).

3. **UX / "Off Brand" polish.** The live Space cold-starts (~48s first turn) then
   runs fast (~4s). Improve how that feels: a more cinematic "dream forming" loader,
   better meter/HUD presentation, making the seeded **dice roll visible** (it's the
   fairness story), and optionally a Hobbes portrait that changes with courage.
   Pure-frontend, no-GPU wins are ideal.

4. **Code quality.** Tighten naming, remove dead code, improve docstrings/types
   where it genuinely helps. Don't over-refactor working code under deadline.

5. **The idea itself.** In your summary, critique the concept and pitch: what's
   genuinely novel (the code-owned-dice fairness engine, the MoE "fleet within a
   fleet"), what's weak, and 3 concrete things that would most raise its chances
   across the tracks (whimsical *Thousand Token Wood*, *Best Agent*, *Off Brand*,
   OpenBMB/MiniCPM, Modal).

## How to work
- Make small, reviewable commits with descriptive messages.
- Validate every change against the `DAYDREAM_MOCK=1` offline path before committing.
- If you change agent prompts or tier math, explain the before/after reasoning.
- End with a concise summary: bugs fixed, improvements made, and your top 3
  recommendations you did *not* implement (so I can decide).
