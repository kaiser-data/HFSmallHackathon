---
title: DAYDREAM
emoji: 🌙
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.16.0
app_file: app/app.py
pinned: true
license: mit
short_description: "Small models, big dreams: a dream game with your tiger"
tags:
  - track:thousand-token-wood
  - sponsor:openbmb-minicpm
  - sponsor:modal
  - badge:best-agent
  - badge:off-brand
  - badge:best-demo
---

# 🌙 DAYDREAM — *Press Your Luck, Keep Your Tiger*

A bedtime dream you **play** — a real, goal-driven story, dreamed in real time by a
**fleet of small models**, none bigger than fits on one GPU. Each world gives you a
**quest**; you pursue it by taking **gambits** (safe / bold / reckless) through surreal
scenes with your stuffed tiger **Hobbes**, who grows brave because of the bets you take
*together*. Code rolls the dice; the little models supply the soul. Reach the goal to
wake with the prize — or run out of lucidity and dissolve.

> **The thesis — small models, big dreams.** You don't own one giant brain; you command
> a *fleet of scrappy small minds*. In a dream, a small model's fuzziness isn't a bug —
> it's the aesthetic. **The constraint is the art.** Every model ≤32B, by design.

---

## 🏆 Submission tags
- **Track:** *An Adventure in Thousand Token Wood* (whimsical) — there's even a `Thousand Token Wood` world inside.
- **Sponsor prizes:** **OpenBMB / Best MiniCPM** (MiniCPM5-1B is our Keeper) · **Modal / Best Use** (4 services + a cost-guardian).
- **Bonus badges:** **Best Agent** (a coordinated multi-agent fleet) · **Off Brand** (custom dream-deck UI + live generated visuals) · **Best Demo**.

## ✨ What makes it different

1. **A real story, not a chat.** Every world is a quest with a visible goal; the Dreamweaver weaves *one coherent tale* that moves toward it each turn (forward on success, setback on failure) and resolves in a genuine climax — reach the prize, or the dream collapses.
2. **A fleet, not a chatbot.** Five small models — 🌌 Dreamweaver, 👁 Nightmare, 🐯 Hobbes, 🗺 Keeper, 🎨 Painter — each with one job, coordinated per turn. Every model ≤32B.
3. **Code owns the dice, models own the words.** Pass/fail and every reward is computed by a seeded, model-free resolver. The models *never* decide outcomes — so it's a **fair game**, not a story that flatters you. This is the heart of the design.
4. **Hobbes grows brave because of you.** A COURAGE meter rises when you survive bets made *with* him; his voice shifts cowering → steady → "I've got you." The "aww" is earned.
5. **The dream paints itself — fast.** A FLUX image renders each beat on-GPU in **~0.5s**; a pre-generated hero greets you the instant you arrive, then live per-beat images shift the scene. Choices and state run async, so a warm turn is **~5s** with narration streaming in under a second.
6. **Engineered for real Modal deployment.** Multi-backend (vLLM MoE + llama.cpp + FLUX) plus a **cloud cost-guardian** we built after a runaway-GPU lesson — scale-to-zero, hard container caps, a lease-based dead-man's-switch, and robustness so a cold/failed backend degrades gracefully instead of hanging a turn.
7. **Deterministic & shareable.** Same dream seed replays the same dice *and* the same images → *"beat my run, seed `abc123`."* Download your full run as a keepsake.

---

## 🧠 Architecture

DAYDREAM is a **fleet of small models refereed by code**: a deterministic Python core
owns the truth and the dice, while a handful of sub-32B models — each on its own Modal
GPU — supply only words and pixels. Three views:

### 1 · System — three layers, one rule

> **The rule:** outcomes flow *down* from code; only language flows *up* from models.

```mermaid
flowchart TB
    P([👤 Player])

    subgraph CODE["⚙️ Orchestration — Python · owns the truth"]
        direction LR
        ENGINE["DreamEngine<br/><i>turn loop</i>"]
        RESOLVER{{"🎲 Resolver<br/><i>seeded dice + rewards</i>"}}
        STATE[("🗺️ WorldState<br/><i>externalized memory</i>")]
    end

    subgraph FLEET["🤖 The Fleet — Modal serverless GPUs · every model ≤ 32B"]
        direction LR
        SPEC["🌌 Dreamweaver · 👁 Nightmare · 🐯 Hobbes<br/><b>Qwen3-30B-A3B</b> MoE on vLLM<br/><i>30B total · only 3B active/token</i>"]
        ROUTER["🗺 Keeper<br/><b>MiniCPM-1B</b> · llama.cpp"]
        VISION["🎨 Painter<br/><b>FLUX.1-schnell</b>"]
    end

    P -- "gambit (safe/bold/reckless)" --> ENGINE
    ENGINE --> RESOLVER -- "verdict" --> ENGINE
    ENGINE <-. "context slice ↔ patch" .-> STATE
    ENGINE == "narrate · react" ==> SPEC
    ENGINE -. "async" .-> ROUTER
    ENGINE -. "async" .-> VISION
    SPEC == "prose + 3 choices" ==> P
    VISION -. "image" .-> P
    ROUTER -. "state patch" .-> STATE

    classDef code fill:#1b1640,stroke:#7c5cff,color:#fff;
    classDef fleet fill:#241a4d,stroke:#9d7bff,color:#fff;
    classDef dice fill:#2a1022,stroke:#ff5c7c,color:#fff;
    classDef player fill:#0b0a1c,stroke:#cdbcff,color:#fff;
    class ENGINE,STATE code; class SPEC,ROUTER,VISION fleet; class RESOLVER dice; class P player;
```

### 2 · One turn — critical path vs. async (why it feels instant)

```mermaid
sequenceDiagram
    autonumber
    actor P as 👤 Player
    participant C as ⚙️ Resolver
    participant D as 🌌 Dreamweaver
    participant H as 🐯 Hobbes
    participant K as 🗺 Keeper
    participant F as 🎨 FLUX

    P->>C: pick gambit
    C->>C: roll seeded dice → verdict
    Note over C: the outcome is FIXED before any model speaks — the game is fair

    C->>D: narrate this verdict
    D-->>P: streams prose · first words in ~0.4s

    par off the critical path (async)
        C-)K: patch world-state (background)
        C-)F: paint the beat (~0.5s on GPU)
    end

    D->>H: finished scene
    H-->>P: reaction + 3 fresh gambits · ~5s
    F--)P: dream image fades in
    Note over P,F: you wait only for narration + choices (~5s) —<br/>state and image never block the turn
```

### 3 · The fairness spine — code owns the dice

```mermaid
flowchart LR
    G["gambit + seed + turn"] --> R{{"🎲 resolve()<br/>pure · deterministic"}}
    R --> V["verdict<br/>success / partial / fail<br/>+ reward magnitudes"]
    V --> A["apply()<br/>move LUCIDITY · PROGRESS<br/>· COURAGE · MENACE"]
    V --> N["🌌 model narrates<br/><i>the words, not the outcome</i>"]
    A --> S[("WorldState")]
    classDef c fill:#2a1022,stroke:#ff5c7c,color:#fff;
    classDef m fill:#241a4d,stroke:#9d7bff,color:#fff;
    class R,V,A c; class N m;
```
*Same `(seed, turn)` → same dice → **"beat my run, seed `abc123`"** is honest. A model can never decide whether you succeed.*

---

## 🎮 How it plays

1. Pick a world (Candy Desert, Sunken City, Rain Street, Red Planet, Thousand Token Wood) and a seed. A hero image and your **quest** greet you instantly.
2. Pursue the quest: take a **gambit** — 🟢 safe / 🟡 bold / 🔴 reckless (each shows its odds + reward) — or type your own action. Hobbes' three options are concrete, scene-specific steps toward the goal.
3. The **Dreamweaver** narrates the outcome the dice already decided, moving the story toward the goal; the **Nightmare** presses when menace climbs; **Hobbes** reacts in his current mood and offers the next steps; the **Keeper** updates world-state; the **Painter** repaints the scene.
4. Climb **PROGRESS** to 100 to wake with the prize, or run out of **LUCIDITY** and dissolve — both end in a climactic beat. Watch **COURAGE** turn Hobbes brave along the way. Win or lose, the run freezes into a shareable Dream Journal you can download.

## 🤖 The fleet
*Full design + diagrams: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.*

| Agent | Role | Backend (≤32B each) | Job |
|---|---|---|---|
| 🌌 Dreamweaver | specialist | Modal vLLM · Qwen3-30B-A3B (MoE, 3B active) | narrate the pre-decided outcome |
| 👁 Nightmare | specialist | Modal vLLM · Qwen3-30B-A3B (MoE, 3B active) | press the dread when menace is high |
| 🐯 Hobbes | specialist | Modal vLLM · Qwen3-30B-A3B (MoE, 3B active) | companion; voice keyed to COURAGE; offer gambits |
| 🗺 Keeper | router | Modal llama.cpp · **MiniCPM5-1B** | structured world-state (location, items, memory) |
| 🎨 dream image | vision | Modal · FLUX.1-schnell | paint each beat, in parallel under the narration |

Backends are OpenAI-compatible → swap models or run "off the grid" via one env var, no code change.

## 🧠 Why it stays coherent on small models
The **world-state lives in code**, outside the models (`agents/world.py`). Each turn the engine
feeds each agent a compact slice of truth, so a 1B router can keep a consistent world that a
single small context never could. The **resolver** (`agents/resolver.py`) owns all game math,
seeded by `(seed, turn)` — fair, replayable, and impossible for a model to fudge.

## ☁️ Best Use of Modal — and a cost story
DAYDREAM runs **four Modal services** (vLLM, llama.cpp, FLUX, and a guardian). After a
keep-warm GPU once cold-looped and burned real money, we made cost control *structural*:
- **Scale-to-zero + `max_containers=1`** on every GPU app — $0 idle, no fan-out.
- A **cloud guardian**: a cheap cron that warm-pings endpoints **only while a time-boxed lease is active** — so warmth is a *pull*, not a pin. Forget to tear down? The lease expires and everything scales to zero on its own, independent of your laptop.
- A `make` control surface: `make status` (apps + lease + live spend tracker), `make stop` (panic), `make demo-up/down`.

All endpoint URLs derive from one `MODAL_WORKSPACE` slug, so moving workspaces is a one-line change.

## 🚀 Run it
**Offline (no backend, fully playable):**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DAYDREAM_MOCK=1 python app/app.py
```
**Against Modal inference:** set `MODAL_WORKSPACE` + keys in `.env` (see `.env.example`), then `make deploy && python app/app.py`.

## 🗂 Layout
| Path | What |
|---|---|
| `agents/dream.py` | the fleet engine (Dreamweaver · Nightmare · Hobbes · Keeper) |
| `agents/resolver.py` | seeded, model-free dice + reward math (code owns the game) |
| `agents/world.py` | environments + externalized `WorldState` |
| `agents/vision.py` | per-beat dream-image prompts + FLUX client |
| `agents/base.py` | tiny streaming/JSON Agent + `DAYDREAM_MOCK` offline mode |
| `app/app.py` | Gradio dream-deck UI |
| `modal_app/*.py` | Modal vLLM · llama.cpp · FLUX · guardian |

*Small models, big dreams.* 🌙
