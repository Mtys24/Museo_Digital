import os
import time
import gradio as gr
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

from figures import FIGURES
from tts import generate_audio, AUDIO_DIR
from wiki import search as wiki_search
from analytics import log_conversation

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = os.getenv("MODEL", "Qwen/Qwen2.5-7B-Instruct")
client = InferenceClient(model=MODEL_ID, token=HF_TOKEN) if HF_TOKEN else None

MAX_HISTORY = 10
ASSETS_DIR = os.path.abspath("assets")

SUGGESTED_QUESTIONS = [
    "Cuéntame sobre tu infancia",
    "¿Cuál fue tu mayor descubrimiento?",
    "¿Qué te gusta hacer en tu tiempo libre?",
    "¿Qué opinas del mundo actual?",
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
        cards += f"""
        <div class="character-card{cls}" data-name="{safe}" onclick="selectCharacter('{safe}')">
            <img src="/assets/{fig['avatar']}" alt="{name}">
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
            <div class="timeline-year">{e['year']}</div>
            <div class="timeline-item-title">{e['title']}</div>
            <div class="timeline-desc">{e['desc']}</div>
        </div>"""
        for e in events
    )
    return f"""
    <div class="bio-section">
        <div class="timeline-title">Línea de tiempo</div>
        <div class="timeline">{items}</div>
    </div>"""


def build_info_html(fig):
    timeline = build_timeline_html(fig)
    return f"""
    <div class="bio-section">
        <div class="bio-title-container">
            <span class="bio-emoji">{fig['emoji']}</span>
            <span class="bio-name">{fig['name']}</span>
        </div>
        <div class="bio-text">{fig['short_bio']}</div>
    </div>
    {timeline}"""


def on_select_figure(new_name, histories, current_figure, current_chat):
    histories[current_figure] = current_chat
    new_chat = histories.get(new_name, [])
    fig = FIGURES[new_name]
    return new_name, new_chat, None, build_character_cards(new_name), build_info_html(fig), histories


def on_submit(message, histories, figure_name, history):
    if not message.strip():
        yield history, None, histories
        return

    if not client:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": "Error: HF_TOKEN no configurado."})
        yield history, None, histories
        return

    fig = FIGURES.get(figure_name, list(FIGURES.values())[0])
    history.append({"role": "user", "content": message})
    yield history, None, histories

    messages = build_messages(history, fig["system_prompt"])

    wiki_result = wiki_search(message)
    if wiki_result:
        wiki_context = (
            f"Contexto histórico real de Wikipedia (artículo: {wiki_result['title']}):\n"
            f"{wiki_result['summary']}"
        )
        messages.insert(1, {"role": "system", "content": wiki_context})

    full_response = ""
    history.append({"role": "assistant", "content": ""})
    start_time = time.time()
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
            yield history, None, histories
    except Exception as e:
        history[-1]["content"] = f"Error: {str(e)[:200]}"
        yield history, None, histories
        return
    elapsed_ms = (time.time() - start_time) * 1000

    log_conversation(figure_name, message, full_response, elapsed_ms)

    audio_path = generate_audio(full_response, fig["voice"])
    histories[figure_name] = history
    yield history, audio_path.replace("\\", "/") if audio_path else None, histories


def make_suggestion_handler(question):
    def handler(histories, figure_name, history):
        yield from on_submit(question, histories, figure_name, history)
    return handler


def on_clear(histories, figure_name):
    histories[figure_name] = []
    return [], None, histories


with open(os.path.join(ASSETS_DIR, "style.css"), "r", encoding="utf-8") as f:
    CUSTOM_CSS = f.read()

JS_CODE = open(os.path.join(ASSETS_DIR, "app.js"), encoding="utf-8").read()

first_name = list(FIGURES.keys())[0]

with gr.Blocks(title="Museo Digital") as demo:

    gr.HTML(
        """<div id="header">
            <h1>\U0001f3db Museo Digital</h1>
            <p>Conversa con los grandes personajes de la historia</p>
        </div>"""
    )

    if not HF_TOKEN:
        gr.HTML(
            """<div style="text-align:center;color:#ef4444;padding:0.8rem;
            background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);
            border-radius:10px;margin-bottom:1rem;font-size:0.85rem">
            Configura HF_TOKEN en .env para usar la IA
        </div>"""
        )

    with gr.Row(equal_height=False):
        with gr.Column(scale=1, min_width=300):
            panel_cards = gr.HTML(build_character_cards(first_name))
            panel_info = gr.HTML(build_info_html(list(FIGURES.values())[0]))

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(height=420)
            audio_player = gr.Audio(
                label="Escuchar respuesta",
                autoplay=True,
                visible=True,
            )
            msg = gr.Textbox(
                placeholder="Escribe tu pregunta aquí...",
                show_label=False,
                container=False,
            )
            with gr.Row(elem_classes=["suggest-row"]):
                suggest_btns = []
                for q in SUGGESTED_QUESTIONS:
                    btn = gr.Button(q, size="sm", elem_classes=["suggest-btn"])
                    suggest_btns.append(btn)
            with gr.Row():
                clear_btn = gr.Button("Limpiar", variant="secondary")
                submit = gr.Button("Enviar", variant="primary")

    with gr.Column(elem_id="hidden-character"):
        hidden_selector = gr.Textbox(value=first_name, label="", interactive=True)

    figure_state = gr.State(first_name)
    histories_state = gr.State({})

    hidden_selector.change(
        fn=on_select_figure,
        inputs=[hidden_selector, histories_state, figure_state, chatbot],
        outputs=[figure_state, chatbot, audio_player, panel_cards, panel_info, histories_state],
        queue=False,
    )

    for btn, q in zip(suggest_btns, SUGGESTED_QUESTIONS):
        handler = make_suggestion_handler(q)
        btn.click(
            fn=handler,
            inputs=[histories_state, figure_state, chatbot],
            outputs=[chatbot, audio_player, histories_state],
            queue=True,
        )

    submit.click(
        fn=on_submit,
        inputs=[msg, histories_state, figure_state, chatbot],
        outputs=[chatbot, audio_player, histories_state],
        queue=True,
    ).then(fn=lambda: "", outputs=[msg])
    msg.submit(
        fn=on_submit,
        inputs=[msg, histories_state, figure_state, chatbot],
        outputs=[chatbot, audio_player, histories_state],
        queue=True,
    ).then(fn=lambda: "", outputs=[msg])

    clear_btn.click(
        fn=on_clear,
        inputs=[histories_state, figure_state],
        outputs=[chatbot, audio_player, histories_state],
        queue=False,
    )

    demo.load(
        fn=lambda: (first_name, {}, build_character_cards(first_name), build_info_html(list(FIGURES.values())[0]), [], None),
        outputs=[figure_state, histories_state, panel_cards, panel_info, chatbot, audio_player],
    )

if __name__ == "__main__":
    fastapi_app = FastAPI()
    fastapi_app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    fastapi_app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")
    app = gr.mount_gradio_app(
        fastapi_app,
        demo,
        path="/",
        theme=gr.themes.Base(),
        css=CUSTOM_CSS,
        js=JS_CODE,
        allowed_paths=[ASSETS_DIR, str(AUDIO_DIR)],
    )
    uvicorn.run(app, host="127.0.0.1", port=7861)
