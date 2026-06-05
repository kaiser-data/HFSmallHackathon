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

import gradio as gr  # noqa: E402
from agents.dream import DreamEngine  # noqa: E402
from agents.world import ENVIRONMENTS, LUCIDITY_START, COURAGE_MAX  # noqa: E402

engine = DreamEngine()

SPEAKER = {
    "Dreamweaver": "🌌 *Dreamweaver*",
    "Nightmare": "👁 *Nightmare*",
    "Hobbes": "🐯 **Hobbes**",
}
TIER_FACE = {"safe": "🟢", "bold": "🟡", "reckless": "🔴"}
TIER_VARIANT = {"safe": "secondary", "bold": "primary", "reckless": "stop"}
MOOD_FACE = {"timid": "🙀", "warming": "😼", "brave": "😺"}
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
    end = ""
    if s.complete:
        end = "\n\n✨ **YOU WAKE WITH THE PRIZE.**"
    elif s.lost:
        end = "\n\n💤 **LOST IN THE DREAM.**"
    return (f"### {s.emoji} {s.env_name}\n"
            f"**Where:** {s.location}\n\n"
            f"**🩵 Lucidity:** {luc} {s.lucidity}/{LUCIDITY_START}\n\n"
            f"**🎯 Progress:** {prog} {s.progress}%\n\n"
            f"**{tiger} Hobbes ({s.mood}):** {cour} {s.courage}/{COURAGE_MAX}\n\n"
            f"**👁 Menace:** {men or '—'}\n\n"
            f"**Carrying:** {carry}  •  **Turn:** {s.turn}  •  **Seed:** `{s.seed}`{end}")


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
            ups.append(gr.update(value=f"{TIER_FACE[tier]} {label}",
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
    """Shared streaming loop -> [chatbot, state, btn1..N, intent, card, printbtn]."""
    history = history or []
    history.append({"role": "user", "content": f"🧑‍🚀 {intent}"})
    yield history, state_md(), *_hidden_btns(), "", *_card_updates()

    current = None
    die_shown = False
    for speaker, delta in engine.play(intent, tier):
        if not die_shown:                      # reveal the seeded roll the instant it's decided
            die_shown = True
            if engine.last_outcome is not None:
                history.append(_die_bubble())
                yield history, gr.update(), *_hidden_btns(), "", *_card_updates()
        if speaker != current:
            current = speaker
            history.append({"role": "assistant", "content": SPEAKER.get(speaker, speaker) + ": "})
        history[-1]["content"] += delta
        yield history, gr.update(), *_hidden_btns(), "", *_card_updates()

    yield history, state_md(), *_btn_updates(), "", *_card_updates()


def begin(env_id, seed, history):
    engine.start(env_id, seed=(seed or "dream").strip())
    env = ENVIRONMENTS[env_id]
    history = [{"role": "assistant", "content": f"{env.emoji} *{env.opening}*"}]
    yield history, state_md(), *_hidden_btns(), "", *_card_updates()
    yield from _stream_turn("(You arrive and take in the scene.)", None, history)


def take_turn(intent, history):
    if engine.state is None:
        yield history or [], "### 🌙 Pick a world and begin first.", *_hidden_btns(), "", *_card_updates()
        return
    if engine.state.over or not (intent or "").strip():
        yield history or [], state_md(), *_btn_updates(), "", *_card_updates()
        return
    yield from _stream_turn(intent.strip(), "bold", history)  # typed = a bold gamble


def make_choose(i):
    def _choose(history):
        if engine.state is not None and not engine.state.over and i < len(engine.gambits):
            label, tier = engine.gambits[i]
            yield from _stream_turn(label, tier, history)
        else:
            yield history or [], state_md(), *_btn_updates(), "", *_card_updates()
    return _choose


CSS = """
.gradio-container {background: radial-gradient(1200px 600px at 50% -10%, #2a2350, #0d0b1f 60%);}
#deck {border-radius: 16px;}
#card {border: 1px solid #6c5ce7; border-radius: 14px; padding: 8px 16px;
       background: rgba(40,30,80,.45);}
footer {visibility: hidden;}
"""

with gr.Blocks(title="DAYDREAM") as demo:
    gr.Markdown(
        "# 🌙 DAYDREAM — *Press Your Luck, Keep Your Tiger*\n"
        "Take **gambits** through a dream a fleet of small models is dreaming for you. "
        "Survive on **lucidity**, climb to the prize — and watch **Hobbes** grow brave "
        "because of the bets you take together. *Small models, big dreams.*"
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
        with gr.Column(scale=1):
            world = gr.Dropdown(ENV_CHOICES, value="candy_desert", label="World")
            seed = gr.Textbox(value="abc123", label="Seed (shareable)")
            start = gr.Button("Begin the dream 🌙", variant="primary")
            panel = gr.Markdown(state_md())

    outs = [chat, panel, *btns, intent, card, printbtn]
    start.click(begin, [world, seed, chat], outs)
    go.click(take_turn, [intent, chat], outs)
    intent.submit(take_turn, [intent, chat], outs)
    for i, b in enumerate(btns):
        b.click(make_choose(i), [chat], outs)
    printbtn.click(lambda: gr.update(visible=True), None, card)


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(primary_hue="indigo"), css=CSS)
