# Concept Pitches — Small Hackathon Multiagent System

Constraints recap: ≤32B total params · Gradio app on a HF Space · demo video + social post.
Inference: Modal GPU (vLLM, OpenAI-compatible) + llama.cpp on Modal (Llama Champion badge).
Models: mix of newest small open-weight specialists (June 2026).

Bonus badges in reach with our stack: **llama.cpp** (Modal llama.cpp path), **Open trace**
(publish agent traces to the Hub), **Custom UI** (custom Gradio frontend), **Field Notes** (blog).

---

## Pitch A — "The Council" (Thousand Token Wood)  ⭐ recommended

A whimsical decision oracle. You ask a life question ("should I repaint my bike shed teal?")
and a **council of tiny specialist agents** debates it in real time, each with a distinct
persona + model, then a chair synthesizes a verdict you can watch unfold.

- **Why it wins:** AI is load-bearing (the debate *is* the product), genuinely delightful,
  multiagent is the whole point — not plumbing. Easy to demo, easy to show a friend.
- **Agents:**
  - Router/Chair — MiniCPM5-1B (tiny, fast turn-taking + tool calls) → OpenBMB special prize
  - The Optimist / The Skeptic / The Pragmatist — Qwen3.5-27B with persona prompts
  - The Historian (retrieval) — small model + web/wiki tool
- **Total budget:** one 27B served via vLLM on Modal + 1B router ≈ under 32B.
- **Delight levers:** live streaming speech bubbles, a "gavel" verdict, shareable transcript card.

## Pitch B — "Backyard Helpdesk" (Backyard AI)

A multiagent assistant tuned for ONE real person you know (e.g. a parent running an Etsy shop /
a neighbor with a rental). A **triage agent** routes their plain-language request to specialists:
a Writer (listings/replies), a Numbers agent (pricing/tax math via tool), a Scheduler.

- **Why it wins:** Hits Backyard rubric — specific, real person, honest small-model fit.
  Requires a real user, which is the gating judging criterion.
- **Agents:** Triage (MiniCPM5-1B) → Writer (Qwen3.5-27B) / Calc (small + Python tool) /
  Organizer. Tool use is the small-model leverage.
- **Risk:** needs a committed real user who'll actually use it during the window.

## Pitch C — "Thousand Token Wood: The Game" (Thousand Token Wood)

A tiny text-adventure where the **world is run by cooperating agents**: a Narrator, a
World-State keeper (enforces rules via tools, prevents hallucinated inventory), and a
Mischief agent that injects surprises. You wander a procedurally-described wood.

- **Why it wins:** On-theme name, AI is the experience, strong originality. World-State
  agent solves the classic "LLM forgets the rules" problem — a real multiagent justification.
- **Agents:** Narrator (Qwen3.5-27B) + World-State (MiniCPM5-1B, strict JSON tool calls) +
  Mischief (Gemma 4, low-frequency). Optional MiniCPM-V for "look at this drawing" inputs.

---

## Recommendation
**Pitch A (The Council)** for the cleanest delight-per-effort and the best multiagent
justification, with **Pitch B** as the pivot if you have a willing real user (better cash-prize
odds, since Backyard's bar is "they actually used it"). Both reuse the same orchestration code.

---

## ✅ Chosen direction: DAYDREAM
After exploring real-problem and funny fleets, we converged on a **dreamlike,
game-like fleet** (Calvin-&-Hobbes energy): a companion + shifting environments +
light mission, where dream-logic forgives small-model quirks. See README.
