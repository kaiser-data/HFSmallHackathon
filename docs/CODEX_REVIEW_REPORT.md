# Codex Review Report — DAYDREAM

## Scope

Reviewed DAYDREAM against `docs/CODEX_REVIEW_PROMPT.md`, focusing on:

- Correctness and robustness in small-model JSON handling, turn resolution, Keeper updates, and offline play.
- Gameplay clarity around code-owned dice, risk/reward tiers, Hobbes courage, and the win/loss loop.
- UX polish that improves the fairness story and first-turn confidence without adding GPU cost.
- Low-risk code quality improvements with targeted tests.

## Changes Made

Commit: `ba13970 Harden dream turn parsing and HUD`

### 1. Hardened Small-Model JSON Parsing

Updated `agents/base.py::loose_json`.

Before:

- Used a greedy regex over the first `{...}` span.
- Failed if the model emitted multiple objects, fenced JSON plus trailing text, or malformed braces before the real object.

After:

- Uses `json.JSONDecoder().raw_decode()` from each candidate `{`.
- Returns the first valid JSON object.
- Handles fenced JSON, prose wrappers, trailing chatter, and braces inside strings.

Why it matters:

Hobbes and Keeper are both small-model structured-output users. A brittle parser could silently degrade choices or state updates even when the model produced recoverable JSON.

### 2. Made Keeper Updates Safer Under Threading

Updated `agents/dream.py`.

Changes:

- Captures the world context once before launching the Keeper worker.
- Passes that context snapshot into `_update()` instead of rereading mutable state in the worker.
- Ignores non-dict Keeper patches.
- Catches Keeper worker exceptions so a bad router response does not break an otherwise valid turn.

Why it matters:

The Keeper is presentational memory, not game math. The turn should survive Keeper wobble because resolver-owned state remains authoritative.

### 3. Improved Dice and Risk Visibility

Updated `app/app.py`.

Changes:

- The HUD now keeps the last seeded roll visible after the chat bubble streams past.
- Gambit buttons now show fail chance, progress reward, and lucidity cost:
  - `5% fail · +10/-1`
  - `25% fail · +22/-2`
  - `40% fail · +40/-3`

Why it matters:

DAYDREAM’s strongest fairness claim is that code owns the dice. The UI now makes that legible before and after each choice, without relying on docs or narration.

### 4. Added Focused Tests

Added `tests/test_core.py`.

Covered:

- JSON extraction from fenced output.
- Recovery from malformed object before a valid object.
- Braces inside JSON strings.
- Deterministic resolver output by `(tier, seed, turn)`.
- Completion winning over same-turn lucidity drain.
- Keeper bad patch degradation.
- Gambit labels staying zipped to code-owned tiers.

## Validation

Passed:

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m compileall agents app endpoints.py
DAYDREAM_MOCK=1 .venv/bin/python - <<'PY'
from app.app import begin

gen = begin('token_wood', 'smoke-seed', [])
last = None
for idx, update in zip(range(80), gen):
    last = update
print('smoke-ok', bool(last), len(last) if last else 0)
PY
```

Result:

- 7 unit tests passed.
- Compile pass succeeded.
- Mock Gradio-facing startup/first-turn smoke returned a valid update tuple.
- Worktree was clean after commit.

## Gameplay Review

The current tier table is coherent for an 8-12 turn arc:

- Safe: reliable progress, no courage gain, low drama.
- Bold: meaningful middle lane with courage growth.
- Reckless: high-speed path that can win quickly but raises pressure.

The design choice that failures spend lucidity but do not add an extra lucidity penalty is good. It keeps reckless risky without making it a trap.

The biggest gameplay weakness is not the math itself; it is player perception. Before this change, the player had to infer the expected value of each tier. The new button labels make the tradeoff explicit and should improve trust.

## Concept Review

What is genuinely strong:

- **Code-owned dice, model-owned words** is the clearest differentiator. It makes the game fair, replayable, and easy to explain.
- **Externalized world state** is a practical answer to small-model coherence limits.
- **Fleet architecture** gives each small model a theatrical role instead of asking one model to do everything.
- **Hobbes courage** gives the mechanics an emotional payoff.

What is weaker:

- The player may not immediately see that a fleet is operating unless they read the README or infer it from speaker labels.
- Cold start is explained, but the waiting experience could feel more active.
- Hobbes’ courage currently affects voice and farewell well, but could be more visible moment to moment.

## Top Recommendations Not Implemented

1. Add a compact fleet activity strip showing Dreamweaver, Nightmare, Hobbes, Keeper, and FLUX lighting up as each contributes.
2. Add a Hobbes portrait or badge that changes with courage tier.
3. Run seeded Monte Carlo simulations over common play policies to quantify win rate, average turns, courage distribution, and reckless viability.

## Risk Notes

- No live Modal inference was exercised. Validation used unit tests and the `DAYDREAM_MOCK=1` path.
- The UI button labels are longer now. They should be checked visually on the hosted Space, especially on mobile.
- The parser is more robust but still intentionally returns only a top-level object; array-only structured output remains ignored by design.
