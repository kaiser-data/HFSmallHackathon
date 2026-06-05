"""DAYDREAM — Gradio command deck.

You + an AI companion (Hobbes) wander dreamlike worlds conjured by a fleet of
small-model agents. Light mission + free wander; Hobbes escalates the choices.

Run locally with no backend:   DAYDREAM_MOCK=1 python app/app.py
Against Modal endpoints:        set MODAL_* env (see .env.example), python app/app.py
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import gradio as gr  # noqa: E402
from agents.dream import DreamEngine  # noqa: E402
from agents.world import ENVIRONMENTS  # noqa: E402

engine = DreamEngine()

SPEAKER = {
    "Dreamweaver": "🌌 *Dreamweaver*",
    "Mischief": "🃏 *Mischief*",
    "Hobbes": "🐯 **Hobbes**",
}
ENV_CHOICES = [(f"{e.emoji} {e.name}", k) for k, e in ENVIRONMENTS.items()]
NBTN = 3


def state_md() -> str:
    s = engine.state
    if s is None:
        return "### 🌙 No dream yet\nPick a world and begin."
    bar = "🟦" * (s.progress // 10) + "⬜" * (10 - s.progress // 10)
    carry = ", ".join(s.inventory) if s.inventory else "—"
    done = "\n\n✨ **The dream resolves.**" if s.complete else ""
    return (f"### {s.emoji} {s.env_name}\n"
            f"**Where:** {s.location}\n\n"
            f"**Mission:** {s.mission}\n\n"
            f"**Progress:** {bar} {s.progress}%\n\n"
            f"**Carrying:** {carry}\n\n"
            f"**Turn:** {s.turn}{done}")


def _btn_updates():
    ups = []
    for i in range(NBTN):
        if i < len(engine.choices):
            ups.append(gr.update(value=engine.choices[i], visible=True))
        else:
            ups.append(gr.update(visible=False))
    return ups


def _hidden_btns():
    return [gr.update(visible=False) for _ in range(NBTN)]


def _stream_turn(intent, history):
    """Shared streaming loop -> yields [chatbot, state, btn1..btnN, textbox]."""
    history = history or []
    history.append({"role": "user", "content": f"🧑‍🚀 {intent}"})
    yield history, state_md(), *_hidden_btns(), ""

    current = None
    for speaker, delta in engine.play(intent):
        if speaker != current:
            current = speaker
            history.append({"role": "assistant", "content": SPEAKER.get(speaker, speaker) + ": "})
        history[-1]["content"] += delta
        yield history, gr.update(), *_hidden_btns(), ""

    yield history, state_md(), *_btn_updates(), ""


def begin(env_id, history):
    engine.start(env_id)
    env = ENVIRONMENTS[env_id]
    history = [{"role": "assistant", "content": f"{env.emoji} *{env.opening}*"}]
    yield history, state_md(), *_hidden_btns(), ""
    yield from _stream_turn("(You arrive and take in the scene.)", history)


def take_turn(intent, history):
    if engine.state is None:
        yield history or [], "### 🌙 Pick a world and begin first.", *_hidden_btns(), ""
        return
    if not (intent or "").strip():
        yield history or [], state_md(), *_btn_updates(), ""
        return
    yield from _stream_turn(intent.strip(), history)


def make_choose(i):
    def _choose(history):
        if i < len(engine.choices):
            yield from _stream_turn(engine.choices[i], history)
        else:
            yield history or [], state_md(), *_btn_updates(), ""
    return _choose


CSS = """
.gradio-container {background: radial-gradient(1200px 600px at 50% -10%, #2a2350, #0d0b1f 60%);}
#deck {border-radius: 16px;}
footer {visibility: hidden;}
"""

with gr.Blocks(title="DAYDREAM") as demo:
    gr.Markdown(
        "# 🌙 DAYDREAM\n"
        "Wander dreamlike worlds with your companion **Hobbes**. A fleet of small "
        "models conjures the world; you steer with a word. *Small models, big dreams.*"
    )
    with gr.Row():
        with gr.Column(scale=3):
            chat = gr.Chatbot(height=470, show_label=False, elem_id="deck")
            with gr.Row():
                btns = [gr.Button(visible=False, size="sm") for _ in range(NBTN)]
            with gr.Row():
                intent = gr.Textbox(placeholder="…or say what you do next",
                                    scale=8, show_label=False, autofocus=True)
                go = gr.Button("Do it", variant="primary", scale=1)
        with gr.Column(scale=1):
            world = gr.Dropdown(ENV_CHOICES, value="candy_desert", label="World")
            start = gr.Button("Begin the dream 🌙", variant="primary")
            panel = gr.Markdown(state_md())

    outs = [chat, panel, *btns, intent]
    start.click(begin, [world, chat], outs)
    go.click(take_turn, [intent, chat], outs)
    intent.submit(take_turn, [intent, chat], outs)
    for i, b in enumerate(btns):
        b.click(make_choose(i), [chat], outs)


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(primary_hue="indigo"), css=CSS)
