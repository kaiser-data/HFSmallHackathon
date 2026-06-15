# 🎬 DAYDREAM — Demo (the *exciting* cut)

Not a tutorial. A **90-second story** where the magic shows itself. Lead with feeling,
let the tech land underneath. **Live:** https://huggingface.co/spaces/build-small-hackathon/daydream

> **Prep:** `make demo-up`, wait ~2 min, do one throwaway turn. Find a seed (try a few)
> where the BOLD path nearly kills you then wins — a comeback is the whole show.

---

## The cold open (0:00–0:10) — hook before you explain anything
Screen already on **The Red Planet**, hero image glowing. **Don't say "this is a game."**

> *"Your tin rocket is dying on a red dune. Something tall is walking toward you. And
> the only one with you… is a stuffed tiger who's terrified."*

*(beat)*

> *"Every word of this is being dreamed, live, by models small enough to run on one GPU."*

**Now** click **Begin** — narration streams in under a second, the quest appears.

## The turn (0:10–0:30) — show the one thing nobody else has
Point at the dice as you click **🔴 the reckless option**:

> *"Watch — I gamble. **The code rolls the die, not the AI.** 34 against a fail-line of
> 25. That number decided my fate before the story said a single word. It's a real
> game — it can't cheat to flatter me."*

The scene repaints. Progress jumps. *Let the image land on screen — don't talk over it.*

## The near-death (0:30–0:55) — stakes + your tiger
Take another **reckless** bet. When lucidity drops / the Nightmare presses:

> *"Too greedy. The Nightmare's closing in — I'm one bad roll from never waking up."*

Point at Hobbes' meter shifting:

> *"But here's the heart of it: Hobbes. He started cowering. Every risk we survive
> **together**, he gets braver — look, 'finding his courage.' The game is about earning
> a friend's trust."*

## The comeback + climax (0:55–1:20)
Pull back to a **bold** or **safe** play, push Progress to 100:

> *"One more. Come on…"* — Progress hits 100, the Dreamweaver narrates the *actual*
> triumphant ending, and Hobbes says his line.

> *"'We made it. I was brave because you were.'"* *(let it sit — that's the aww)*

## The drop (1:20–1:30) — the tech, fast, while they're still smiling
Quick, punchy, over the Dream Journal:

> *"A fleet of five small models — a 30-billion MoE that fires only 3B per token,
> a 1B world-keeper, FLUX painting every beat in half a second. All under 32B. Fair
> dice in code. Same seed replays the same dream."*

Click **📥 Download my story**:

> *"And you keep the whole thing. **Small models. Big dreams.**"*

---

## Why this beats the boring cut
- **Opens on a feeling**, not a feature list — the judge is *in the dream* before they know it's a demo.
- **The dice moment is the star** — it's the one genuinely novel idea; give it a beat to breathe.
- **Hobbes carries the emotion** — the timid→brave arc + the farewell is your "aww," and aww wins Community Choice.
- **Tech comes LAST, fast** — they're already sold; you're just explaining *how* the thing they loved works.

## Director's notes
- **Silence is your friend.** When the image renders or the climax narrates, *stop talking.* Let it land.
- **React out loud.** "Oh no." "Come on…" "Yes!" A demo where the presenter *feels* it sells the feeling.
- **One run, one arc.** Don't tour features. Tell one story with a near-death and a comeback.
- If a run doesn't give you drama, **reroll the seed** until one does, then lock that seed.

## After recording
```
make demo-down
MODAL_MIN_CONTAINERS=0 modal deploy modal_app/vllm_server.py   # stop the warm-GPU $
```
