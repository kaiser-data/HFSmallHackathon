"""DAYDREAM — Press Your Luck, Keep Your Tiger (Gradio command deck).

You take GAMBITS — safe/bold/reckless — through dreamlike worlds. CODE rolls the
dice (visibly, seeded); a fleet of small models supplies the voices. Survive on
LUCIDITY, climb PROGRESS to wake with the prize, and watch your companion Hobbes
grow brave (COURAGE) because of the bets you take together. Win or lose, the run
freezes into a shareable Dream Journal card.

Run locally with no backend:   DAYDREAM_MOCK=1 python app/app.py
Against Modal endpoints:        set MODAL_* env (see .env.example), python app/app.py
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import concurrent.futures  # noqa: E402
import gradio as gr  # noqa: E402
from agents.dream import DreamEngine  # noqa: E402
from agents.world import ENVIRONMENTS, LUCIDITY_START, COURAGE_MAX, TIER_TABLE  # noqa: E402
from agents.vision import dream_image  # noqa: E402

engine = DreamEngine()
# Paint each dream beat off the main thread so the picture renders *under* the
# narration (same overlap trick as the Keeper) — near-zero added latency per turn.
_IMG_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=2)

# Ambient dream music: a static looping track played IN-BROWSER — zero backend,
# zero latency, zero cold-start. Activates only if a (CC0/royalty-free) file is
# present, so the app never breaks without it. Drop one at assets/dream-ambient.mp3.
import os as _os  # noqa: E402
MUSIC_PATH = str(pathlib.Path(__file__).resolve().parent.parent / "assets" / "dream-ambient.mp3")
HAS_MUSIC = _os.path.exists(MUSIC_PATH)

SPEAKER = {
    "Dreamweaver": "🌌 *Dreamweaver*",
    "Nightmare": "👁 *Nightmare*",
    "Hobbes": "🐯 **Hobbes**",
}
TIER_FACE = {"safe": "🟢", "bold": "🟡", "reckless": "🔴"}
TIER_VARIANT = {"safe": "secondary", "bold": "primary", "reckless": "stop"}
MOOD_FACE = {"timid": "🙀", "warming": "😼", "brave": "😺"}
# Hobbes' bond made visible turn-to-turn — the emotional core of "Keep Your Tiger".
MOOD_PHRASE = {"timid": "cowering behind you",
               "warming": "finding his courage",
               "brave": "brave — “I've got you”"}
ENV_CHOICES = [(f"{e.emoji} {e.name}", k) for k, e in ENVIRONMENTS.items()]
NBTN = 3


def _meter(filled: int, total: int, on: str, off: str = "⬜") -> str:
    n = max(0, min(total, filled))
    return on * n + off * (total - n)


def state_md() -> str:
    s = engine.state
    if s is None:
        return "### 🌙 No dream yet\nPick a world, set a seed, and begin."
    luc = _meter(s.lucidity, LUCIDITY_START, "🟥")
    cour = _meter(s.courage, COURAGE_MAX, "🟨")
    prog = _meter(s.progress // 10, 10, "🟦")
    men = "🟪" * s.menace + ("  ⚠️ CLOSE" if s.nightmare_near else "")
    carry = ", ".join(s.inventory) if s.inventory else "—"
    tiger = MOOD_FACE[s.mood]
    roll = ""
    if engine.last_outcome is not None:
        o = engine.last_outcome
        face = {"success": "success", "partial": "partial", "fail": "fail"}[o.result]
        roll = (f"\n\n**🎲 Last roll:** {o.roll} vs fail ≤{o.fail_threshold} "
                f"→ **{face}** ({o.tier})")
    end = ""
    if s.complete:
        end = "\n\n✨ **YOU WAKE WITH THE PRIZE.**"
    elif s.lost:
        end = "\n\n💤 **LOST IN THE DREAM.**"
    return (f"### {s.emoji} {s.env_name}\n"
            f"**Where:** {s.location}\n\n"
            f"**🩵 Lucidity:** {luc} {s.lucidity}/{LUCIDITY_START}\n\n"
            f"**🎯 Progress:** {prog} {s.progress}%\n\n"
            f"**{tiger} Hobbes** — *{MOOD_PHRASE[s.mood]}*\n\n{cour} {s.courage}/{COURAGE_MAX}\n\n"
            f"**👁 Menace:** {men or '—'}\n\n"
            f"**Carrying:** {carry}  •  **Turn:** {s.turn}  •  **Seed:** `{s.seed}`"
            f"{roll}{end}")


def card_md() -> str:
    """The shareable Dream Journal — submission artifact + social post + beat-my-run."""
    s = engine.state
    if s is None or not s.over:
        return ""
    cause = ("woke with the prize 🏆" if s.complete
             else f"lost in the dream after {s.peak_menace} menace 💤")
    items = ", ".join(s.inventory) if s.inventory else "nothing but the dream"
    scars = ("; ".join(s.scars)) if s.scars else "no scars"
    return (
        f"## {s.emoji} DREAM JOURNAL — {s.env_name}\n"
        f"> *“{engine.farewell()}”* — 🐯 Hobbes\n\n"
        f"- **Outcome:** {cause}\n"
        f"- **Turns survived:** {s.turn}  •  **Progress:** {s.progress}%\n"
        f"- **Peak menace:** {s.peak_menace}  •  **Final courage:** {s.courage}/{COURAGE_MAX} ({s.mood})\n"
        f"- **Carried:** {items}\n"
        f"- **Scars:** {scars}\n\n"
        f"🎲 *Qwen narrating · MiniCPM keeping the world · code rolling the dice*\n\n"
        f"**Beat my run → seed `{s.seed}` in {s.emoji} {s.env_name}**"
    )


def _btn_updates():
    ups = []
    for i in range(NBTN):
        if i < len(engine.gambits):
            label, tier = engine.gambits[i]
            spec = TIER_TABLE[tier]
            fail = int(spec["fail_chance"] * 100)
            reward = int(spec["progress_reward"])
            cost = int(spec["lucidity_cost"])
            ups.append(gr.update(value=f"{TIER_FACE[tier]} {label} · {fail}% fail · +{reward}/-{cost}",
                                 variant=TIER_VARIANT[tier], visible=True))
        else:
            ups.append(gr.update(visible=False))
    return ups


def _hidden_btns():
    return [gr.update(visible=False) for _ in range(NBTN)]


def _card_updates():
    """(card markdown, card visibility, print-button visibility)."""
    over = engine.state is not None and engine.state.over
    return gr.update(value=card_md(), visible=over), gr.update(visible=over)


def _die_bubble() -> dict:
    o = engine.last_outcome
    face = {"success": "✨ SUCCESS", "partial": "〰 PARTIAL", "fail": "💥 FAIL"}[o.result]
    return {"role": "assistant",
            "content": f"🎲 **{o.roll}** vs fail ≤{o.fail_threshold} → {face}  *({o.tier})*"}


def _stream_turn(intent, tier, history):
    """Shared streaming loop -> [chatbot, state, btn1..N, intent, card, printbtn, dream]."""
    history = history or []
    history.append({"role": "user", "content": f"🧑‍🚀 {intent}"})
    yield history, state_md(), *_hidden_btns(), "", *_card_updates(), gr.update()

    current = None
    die_shown = False
    img_future = None
    for speaker, delta in engine.play(intent, tier):
        if img_future is None:
            # Outcome is decided by now (None on the arrival beat). Paint this beat in
            # a thread so the picture renders *under* the prose and lands ~for free.
            img_future = _IMG_POOL.submit(dream_image, engine.state, intent, engine.last_outcome)
        if not die_shown and engine.last_outcome is not None:
            die_shown = True                   # reveal the seeded roll the instant it's decided
            history.append(_die_bubble())
            yield history, gr.update(), *_hidden_btns(), "", *_card_updates(), gr.update()
        if speaker != current:
            current = speaker
            history.append({"role": "assistant", "content": SPEAKER.get(speaker, speaker) + ": "})
        history[-1]["content"] += delta
        yield history, gr.update(), *_hidden_btns(), "", *_card_updates(), gr.update()

    # Show the gambit buttons the INSTANT narration + Hobbes are done — don't make
    # the player wait on the slower image. (Buttons in ~8s, not ~17s.)
    yield history, state_md(), *_btn_updates(), "", *_card_updates(), gr.update()

    # Then let the dream image pop in when it's ready (often already painted under
    # the prose; at worst it lands a few seconds after the buttons).
    if img_future is not None:
        try:
            pic = img_future.result(timeout=120)
        except Exception:
            pic = None
        if pic is not None:
            yield history, gr.update(), *_btn_updates(), "", *_card_updates(), gr.update(value=pic, visible=True)


def begin(env_id, seed, history):
    engine.start(env_id, seed=(seed or "dream").strip())
    env = ENVIRONMENTS[env_id]
    history = [{"role": "assistant", "content": f"{env.emoji} *{env.opening}*"}]
    # Clear the prior dream's image on a fresh start.
    yield history, state_md(), *_hidden_btns(), "", *_card_updates(), gr.update(value=None, visible=False)
    yield from _stream_turn("(You arrive and take in the scene.)", None, history)


def take_turn(intent, history):
    if engine.state is None:
        yield history or [], "### 🌙 Pick a world and begin first.", *_hidden_btns(), "", *_card_updates(), gr.update()
        return
    if engine.state.over or not (intent or "").strip():
        yield history or [], state_md(), *_btn_updates(), "", *_card_updates(), gr.update()
        return
    yield from _stream_turn(intent.strip(), "bold", history)  # typed = a bold gamble


def make_choose(i):
    def _choose(history):
        if engine.state is not None and not engine.state.over and i < len(engine.gambits):
            label, tier = engine.gambits[i]
            yield from _stream_turn(label, tier, history)
        else:
            yield history or [], state_md(), *_btn_updates(), "", *_card_updates(), gr.update()
    return _choose


CSS = """
/* --- dream atmosphere: layered nebula + slow drift, pure CSS, no JS --- */
.gradio-container {
  background:
    radial-gradient(900px 500px at 15% -10%, rgba(124,92,255,.28), transparent 60%),
    radial-gradient(1000px 600px at 85% 0%, rgba(56,120,200,.22), transparent 55%),
    radial-gradient(1200px 800px at 50% 120%, rgba(180,80,200,.16), transparent 60%),
    #0b0a1c;
  background-attachment: fixed;
}
.gradio-container::before {  /* drifting star-dust */
  content: ""; position: fixed; inset: 0; pointer-events: none; opacity: .5; z-index: 0;
  background-image:
    radial-gradient(1.5px 1.5px at 20% 30%, #fff, transparent),
    radial-gradient(1.5px 1.5px at 70% 60%, #cdbcff, transparent),
    radial-gradient(1px 1px at 40% 80%, #fff, transparent),
    radial-gradient(1px 1px at 85% 25%, #bcd4ff, transparent),
    radial-gradient(1.5px 1.5px at 55% 15%, #fff, transparent);
  background-size: 600px 600px; animation: drift 90s linear infinite;
}
@keyframes drift { from {background-position: 0 0;} to {background-position: 600px 600px;} }
h1 { letter-spacing: .5px; text-shadow: 0 2px 24px rgba(124,92,255,.5); }
#deck {border-radius: 16px; backdrop-filter: blur(2px);
       box-shadow: 0 10px 40px rgba(0,0,0,.35), inset 0 0 0 1px rgba(124,92,255,.18);}
#card {border: 1px solid #7c5cff; border-radius: 14px; padding: 8px 16px;
       background: rgba(40,30,80,.45);}
/* the dream image is the HERO — large, glowing, gently breathing */
#dream {border-radius: 16px; border: 1px solid rgba(124,92,255,.6); overflow: hidden;
        box-shadow: 0 12px 50px rgba(124,92,255,.45); animation: breathe 7s ease-in-out infinite;}
#dream img {border-radius: 14px;}
@keyframes breathe { 0%,100% {box-shadow: 0 12px 50px rgba(124,92,255,.35);}
                     50% {box-shadow: 0 16px 64px rgba(124,92,255,.6);} }
/* warm-up banner shimmers so the cold-start feels like the dream forming */
#warmup {border-left: 3px solid #7c5cff; padding: 4px 14px; margin: -4px 0 6px;
         border-radius: 10px; font-size: .92em; position: relative; overflow: hidden;
         background: linear-gradient(90deg, rgba(124,92,255,.10), rgba(124,92,255,.22), rgba(124,92,255,.10));
         background-size: 200% 100%; animation: shimmer 3.5s ease-in-out infinite;}
@keyframes shimmer { 0% {background-position: 200% 0;} 100% {background-position: -200% 0;} }
.gr-button-primary { box-shadow: 0 6px 24px rgba(124,92,255,.4); }
/* fleet banner — makes the multi-model thesis legible at a glance */
#fleet {border: 1px solid rgba(124,92,255,.35); border-radius: 10px;
        padding: 4px 14px; margin: 2px 0; font-size: .9em;
        background: rgba(124,92,255,.07);}
footer {visibility: hidden;}
"""

with gr.Blocks(title="DAYDREAM") as demo:
    gr.Markdown(
        "# 🌙 DAYDREAM — *Press Your Luck, Keep Your Tiger*\n"
        "Take **gambits** through a dream a fleet of small models is dreaming for you. "
        "Survive on **lucidity**, climb to the prize — and watch **Hobbes** grow brave "
        "because of the bets you take together. *Small models, big dreams.*"
    )
    gr.Markdown(
        "🤖 **The fleet dreaming this** &nbsp; "
        "🌌 Dreamweaver · 👁 Nightmare · 🐯 Hobbes &nbsp;—&nbsp; *Qwen3-30B-A3B "
        "(MoE, only 3B active/token)* &nbsp;•&nbsp; "
        "🗺 Keeper &nbsp;—&nbsp; *MiniCPM-1B* &nbsp;•&nbsp; "
        "🎨 Painter &nbsp;—&nbsp; *FLUX* &nbsp;•&nbsp; **every model ≤32B**",
        elem_id="fleet",
    )
    gr.Markdown(
        "> ⏳ **First turn waking the dream?** The models run on serverless GPUs that "
        "sleep when idle, so the **very first turn can take ~90s** to cold-start. "
        "After that, turns stream in a few seconds. Hang tight — the dream is loading. ✨",
        elem_id="warmup",
    )
    with gr.Row():
        with gr.Column(scale=3):
            chat = gr.Chatbot(height=440, show_label=False, elem_id="deck")
            with gr.Row():
                btns = [gr.Button(visible=False, size="sm") for _ in range(NBTN)]
            with gr.Row():
                intent = gr.Textbox(placeholder="…or say what you do (a bold gamble)",
                                    scale=8, show_label=False, autofocus=True)
                go = gr.Button("Do it", variant="primary", scale=1)
            card = gr.Markdown(visible=False, elem_id="card")
            printbtn = gr.Button("📸 Freeze the dream card", visible=False)
        with gr.Column(scale=2):
            dream_img = gr.Image(label="🌌 The dream", height=380, visible=False,
                                 interactive=False, elem_id="dream", show_label=False)
            world = gr.Dropdown(ENV_CHOICES, value="candy_desert", label="World")
            seed = gr.Textbox(value="abc123", label="Seed (shareable)")
            start = gr.Button("Begin the dream 🌙", variant="primary")
            panel = gr.Markdown(state_md())
            if HAS_MUSIC:  # looping ambient track; play once, it loops the session
                gr.Audio(MUSIC_PATH, loop=True, autoplay=False,
                         label="🎵 Dream music", elem_id="music")

    outs = [chat, panel, *btns, intent, card, printbtn, dream_img]
    start.click(begin, [world, seed, chat], outs)
    go.click(take_turn, [intent, chat], outs)
    intent.submit(take_turn, [intent, chat], outs)
    for i, b in enumerate(btns):
        b.click(make_choose(i), [chat], outs)
    printbtn.click(lambda: gr.update(visible=True), None, card)


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(primary_hue="indigo"), css=CSS)
