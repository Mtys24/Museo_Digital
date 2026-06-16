import os
import gradio as gr
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

from figures import FIGURES
from tts import generate_audio
from wiki import search as wiki_search

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = os.getenv("MODEL", "Qwen/Qwen2.5-7B-Instruct")
client = InferenceClient(model=MODEL_ID, token=HF_TOKEN) if HF_TOKEN else None

MAX_HISTORY = 10

SUGGESTED_QUESTIONS = [
    "Cu\u00e9ntame sobre tu infancia",
    "\u00bfCu\u00e1l fue tu mayor descubrimiento?",
    "\u00bfQu\u00e9 te gusta hacer en tu tiempo libre?",
    "\u00bfQu\u00e9 opinas del mundo actual?",
]


def build_messages(history, system_prompt):
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-(MAX_HISTORY - 1) * 2:]:
        messages.append(msg)
    return messages


def build_character_cards(active_name):
    cards = '<div class="character-grid">'
    for name, fig in FIGURES.items():
        cls = " active" if name == active_name else ""
        safe = name.replace("'", "\\'")
        avatar = f"assets/{fig['avatar']}"
        cards += f"""
        <div class="character-card{cls}" data-name="{safe}" onclick="selectCharacter('{safe}')">
            <img src="/file={avatar}" alt="{name}" loading="lazy">
            <div class="character-card-info">
                <div class="character-card-name">{fig['emoji']} {name}</div>
                <div class="character-card-era">{fig['era']}</div>
            </div>
        </div>"""
    cards += "</div>"
    return cards


def build_timeline_html(fig):
    events = fig.get("timeline", [])
    if not events:
        return ""
    items = "".join(
        f"""<div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-year">{e["year"]}</div>
            <div class="timeline-item-title">{e["title"]}</div>
            <div class="timeline-desc">{e["desc"]}</div>
        </div>"""
        for e in events
    )
    return f"""<div class="timeline-title">L\u00ednea de tiempo</div>
    <div class="timeline">{items}</div>"""


def build_info_html(fig):
    timeline = build_timeline_html(fig)
    return f"""<div class="bio-title-container">
        <span class="bio-emoji">{fig['emoji']}</span>
        <span class="bio-name">{fig['name']}</span>
    </div>
    <div class="bio-text">{fig['short_bio']}</div>
    {timeline}"""


def get_initial_outputs():
    name = list(FIGURES.keys())[0]
    fig = list(FIGURES.values())[0]
    return name, build_character_cards(name), build_info_html(fig), [], None


def on_select_figure(name):
    fig = FIGURES[name]
    return name, build_character_cards(name), build_info_html(fig)


def on_submit(message, history, figure_name):
    if not message.strip():
        yield history, None
        return

    if not client:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": "Error: HF_TOKEN no configurado."})
        yield history, None
        return

    fig = FIGURES.get(figure_name, list(FIGURES.values())[0])
    history.append({"role": "user", "content": message})
    yield history, None

    messages = build_messages(history, fig["system_prompt"])
    wiki_result = wiki_search(message)
    if wiki_result:
        wiki_context = (
            f"Contexto hist\u00f3rico real de Wikipedia (art\u00edculo: {wiki_result['title']}):\n"
            f"{wiki_result['summary']}"
        )
        messages.insert(1, {"role": "system", "content": wiki_context})

    full_response = ""
    history.append({"role": "assistant", "content": ""})
    try:
        stream = client.chat_completion(
            messages=messages,
            max_tokens=512,
            temperature=0.8,
            top_p=0.9,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_response += delta
            history[-1]["content"] = full_response
            yield history, None
    except Exception as e:
        history[-1]["content"] = f"Error: {str(e)[:200]}"
        yield history, None
        return

    audio_path = generate_audio(full_response, fig["voice"])
    yield history, audio_path


def make_suggestion_handler(question):
    def handler(history, figure_name):
        yield from on_submit(question, history, figure_name)
    return handler


ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
CSS_PATH = os.path.join(ASSETS_DIR, "style.css")
with open(CSS_PATH, "r", encoding="utf-8") as f:
    CUSTOM_CSS = f.read()

with gr.Blocks(
    title="Museo Digital - Personajes Hist\u00f3ricos",
) as demo:
    first_name = list(FIGURES.keys())[0]

    gr.HTML(
        """<div id="header">
            <h1>\U0001f3db Museo Digital</h1>
            <p>Conversa con los grandes personajes de la historia</p>
        </div>"""
    )

    # gr.HTML(f"""<script>{open('assets/app.js', encoding='utf-8').read()}</script>""")

    if not HF_TOKEN:
        gr.HTML(
            """<div class="glass-panel" style="text-align:center;color:#ef4444;margin:0 0 1rem 0">
            \u26a0 Configura HF_TOKEN en .env para usar la IA
        </div>"""
        )

    with gr.Row():
        with gr.Column(scale=1, min_width=300):
            panel_cards = gr.HTML(build_character_cards(first_name))
            panel_info = gr.HTML(build_info_html(list(FIGURES.values())[0]))

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(height=400)
            audio_player = gr.Audio(label="\U0001f50a Escuchar respuesta", autoplay=False)
            msg = gr.Textbox(label="Tu mensaje", placeholder="Escribe tu pregunta aqu\u00ed...")
            with gr.Row():
                suggest_btns = []
                for q in SUGGESTED_QUESTIONS:
                    btn = gr.Button(q, size="sm")
                    suggest_btns.append(btn)
            with gr.Row():
                gr.ClearButton([chatbot, audio_player, msg], value="Limpiar")
                submit = gr.Button("Enviar", variant="primary")

    with gr.Column(elem_id="hidden-character"):
        hidden_selector = gr.Textbox(
            value=first_name,
            label="",
            interactive=True,
        )

    figure_state = gr.State(first_name)

    hidden_selector.change(
        fn=on_select_figure,
        inputs=hidden_selector,
        outputs=[figure_state, panel_cards, panel_info],
        queue=False,
    )

    for btn, q in zip(suggest_btns, SUGGESTED_QUESTIONS):
        handler = make_suggestion_handler(q)
        btn.click(
            fn=handler,
            inputs=[chatbot, figure_state],
            outputs=[chatbot, audio_player],
            queue=True,
        )

    submit.click(
        fn=on_submit,
        inputs=[msg, chatbot, figure_state],
        outputs=[chatbot, audio_player],
        queue=True,
    )
    msg.submit(
        fn=on_submit,
        inputs=[msg, chatbot, figure_state],
        outputs=[chatbot, audio_player],
        queue=True,
    )

    demo.load(fn=get_initial_outputs, outputs=[figure_state, panel_cards, panel_info, chatbot, audio_player])


if __name__ == "__main__":
    demo.launch(
        debug=False,
        server_name="127.0.0.1",
        server_port=7861,
        theme=gr.themes.Base(),
        # css=CUSTOM_CSS,
    )
