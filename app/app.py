"""Gradio app — HF Space entrypoint for 'The Council' (Pitch A).

Streams a live multiagent debate. Repoint to another pitch by swapping the
orchestrator import; the backend wiring (Modal vLLM + llama.cpp) is unchanged.

Run locally:   python app/app.py
On a Space:    rename/symlink to app.py at repo root, set Space secrets:
               MODAL_VLLM_BASE_URL, MODAL_VLLM_API_KEY, MODAL_VLLM_MODEL,
               MODAL_LLAMACPP_BASE_URL, MODAL_LLAMACPP_API_KEY, MODAL_LLAMACPP_MODEL
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import gradio as gr  # noqa: E402
from agents.orchestrator import default_council  # noqa: E402

COUNCIL = default_council()

AVATARS = {
    "The Optimist": "🌞",
    "The Skeptic": "🌧️",
    "The Pragmatist": "🔧",
    "The Chair": "⚖️",
}


def run_council(question, history):
    """Stream council turns into the chatbot as separate speaker bubbles."""
    history = history or []
    if not question or not question.strip():
        yield history, ""
        return

    history.append({"role": "user", "content": question})
    yield history, ""

    current_speaker = None
    for speaker, delta in COUNCIL.deliberate(question.strip()):
        if speaker != current_speaker:
            current_speaker = speaker
            tag = f"{AVATARS.get(speaker, '🗣️')} **{speaker}**\n\n"
            history.append({"role": "assistant", "content": tag})
        history[-1]["content"] += delta
        yield history, ""


with gr.Blocks(title="The Council", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# ⚖️ The Council\n"
        "Ask anything. A council of tiny specialist agents will debate it and "
        "hand down a verdict you can screenshot. *Small models, big opinions.*"
    )
    chat = gr.Chatbot(type="messages", height=460, show_label=False)
    with gr.Row():
        q = gr.Textbox(placeholder="Should I repaint my bike shed teal?",
                       scale=8, show_label=False, autofocus=True)
        send = gr.Button("Convene ⚖️", variant="primary", scale=1)

    gr.Examples(
        ["Should I repaint my bike shed teal?",
         "Is it too late to learn the cello at 40?",
         "Should I name my sourdough starter?"],
        inputs=q,
    )

    send.click(run_council, [q, chat], [chat, q])
    q.submit(run_council, [q, chat], [chat, q])


if __name__ == "__main__":
    demo.launch()
