# DAYDREAM — Demo Cheat-Sheet

Outcomes are **deterministic by `(seed, turn)`** — the die roll depends only on
the seed and turn number, not on which tier you pick (the tier only sets the
fail threshold the roll is compared against). So these scripted runs replay
identically every time, on any machine, in `DAYDREAM_MOCK=1` or against real
models. The card's "beat my run: seed …" is honest.

Both runs use **World: 🏜 The Candy Desert**. Set the seed in the right-hand
panel, click **Begin the dream**, then press buttons in the order below.
(Arrival is turn 1 — no roll. The first gambit is turn 2.)

---

## 🏆 Triumphant ending — seed `w0`  (~4 turns, the safe demo)

Two clutch reckless wins; Hobbes climbs from timid → **brave**.

| Press | Tier | Roll | Result | Progress | Hobbes |
|------|------|-----:|--------|---------:|--------|
| 1 | 🟡 BOLD | 97 | success | 22% | courage 1 |
| 2 | 🔴 RECKLESS | 69 | **CLUTCH WIN** | 62% | courage 3 |
| 3 | 🔴 RECKLESS | 86 | **CLUTCH WIN** | **100% — WAKE** | courage 5 (brave) |

Farewell: *“We made it. I was brave because you were.”*

---

## 💤 Poignant ending — seed `dd36`  (~7 turns, the emotional demo)

Big early win, then greed, the Nightmare closing in, bleeding out *just shy* of
the prize.

| Press | Tier | Roll | Result | Progress | Menace |
|------|------|-----:|--------|---------:|-------|
| 1 | 🟡 BOLD | 49 | success | 22% | 0 |
| 2 | 🔴 RECKLESS | 87 | **CLUTCH WIN** | 62% | 0 |
| 3 | 🔴 RECKLESS | 20 | fail | 62% | 2 |
| 4 | 🔴 RECKLESS | 39 | fail | 62% | 4 |
| 5 | 🔴 RECKLESS | 14 | fail | 62% | 6 — 👁 **NIGHTMARE** |
| 6 | 🔴 RECKLESS | 23 | fail | 62% | 8 — **LOST IN THE DREAM** |

Farewell: *“I tried to be brave… for you. Almost got there.”*

---

### Suggested live flow (3 min)
1. Open on `w0`, narrate "small models, big dreams," meet timid Hobbes.
2. Tap BOLD — Qwen narrates, the **seeded die** rolls (code-owned, visible).
3. Tap RECKLESS — Hobbes begs you off the red button — **clutch win**, he brightens.
4. Tap RECKLESS again — **wake with the prize**, Hobbes is brave.
5. Tap **📸 Freeze the dream card** → that PNG is the submission *and* the social
   post, with the seed printed: *beat my run.*

Want the tear-jerker instead? Run `dd36` and let greed kill you at the Nightmare.
