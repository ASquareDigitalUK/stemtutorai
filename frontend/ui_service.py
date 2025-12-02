import gradio as gr
import requests
import base64
import os
from config import settings

# ==============================
# CONFIG: Backend API URLs
# ==============================

# Pull from config.py, never from os directly
BASE_URL = settings.TUTOR_URL.rstrip("/")
TUTOR_PORT = settings.TUTOR_PORT  # int from config
API_TUTOR_URL = f"{BASE_URL}/tutor"
API_WELCOME_URL = f"{BASE_URL}/welcome"

print(f"🔧 UI using Tutor backend: {API_TUTOR_URL}")

# ==============================
# LOAD BACKGROUND IMAGE
# ==============================
img_path = "static/bg-lesson.jpg"

encoded_bg = ""
if os.path.exists(img_path):
    with open(img_path, "rb") as f:
        encoded_bg = base64.b64encode(f.read()).decode()
else:
    print(f"⚠️ Background image not found at {img_path}")

background_css = f"""
#chat-container {{
    background-image: url("data:image/jpeg;base64,{encoded_bg}");
    background-size: cover;
    background-position: center;
    padding: 20px;
    border-radius: 12px;
}}

.chatbot {{
    background: rgba(255, 255, 255, 0.82) !important;
    border-radius: 12px !important;
}}

.user-bubble {{
    background: #daf1ff !important;
    color: #000 !important;
}}

.bot-bubble {{
    background: #fff8da !important;
    color: #000 !important;
}}
"""

# ==============================
# HELPERS
# ==============================

def show_login_loading():
    return gr.update(value="Sharpening pencils...", interactive=False)

def add_user_message(user_id, message, history):
    if not message.strip():
        return history, message
    return history + [{"role": "user", "content": message}], message


def chat_with_tutor(user_id, message, history):
    if not message.strip():
        return history, ""

    try:
        res = requests.post(
            API_TUTOR_URL,
            json={"user_id": user_id, "message": message},
            timeout=20,
        )
        data = res.json()
        reply = data.get("response") or ""
    except Exception as e:
        reply = f"⚠️ Error reaching Tutor backend: {e}"

    return history + [{"role": "assistant", "content": reply}], ""


def login_user(name):
    if not name.strip():
        return gr.update(), gr.update(visible=True), gr.update(visible=False), []

    try:
        res = requests.post(
            API_WELCOME_URL,
            json={"user_id": name, "message": ""},
            timeout=20,
        )
        welcome = res.json().get("welcome", f"Welcome {name}! 👋")
    except Exception as e:
        welcome = f"Welcome {name}! (Backend unavailable: {e})"

    initial_history = [{"role": "assistant", "content": welcome}]

    return (
        name,                      # state
        gr.update(visible=False),  # hide login
        gr.update(visible=True),   # show chat
        initial_history,
    )


# ==============================
# GRADIO APP
# ==============================

with gr.Blocks(css=background_css) as demo:
    gr.Markdown("<h1 style='text-align:center;'>STEM Learning Tutor</h1>")

    user_id_state = gr.State("")

    # LOGIN
    with gr.Column(visible=True, elem_id="login-box") as login_col:
        gr.Markdown("### Enter your name to begin")
        name_input = gr.Textbox(label="Your Name", placeholder="e.g. John")
        login_btn = gr.Button("Login", variant="primary")

    # ---------- CHAT ----------
    with gr.Column(visible=False, elem_id="chat-container") as chat_col:
        chatbox = gr.Chatbot(
            label="Tutor Chat",
            type="messages",
            height=500,
        )

        msg_input = gr.Textbox(placeholder="Type your message…", show_label=False)
        send_btn = gr.Button("Send", variant="primary")

        # Button click -> show loading -> run login_user
        login_btn.click(
            show_login_loading,
            inputs=None,
            outputs=login_btn
        ).then(
            login_user,
            inputs=name_input,
            outputs=[user_id_state, login_col, chat_col, chatbox]
        )

        # Enter key submit -> same behavior
        name_input.submit(
            show_login_loading,
            inputs=None,
            outputs=login_btn
        ).then(
            login_user,
            inputs=name_input,
            outputs=[user_id_state, login_col, chat_col, chatbox]
        )

        send_btn.click(
            add_user_message,
            inputs=[user_id_state, msg_input, chatbox],
            outputs=[chatbox, msg_input],
        ).then(
            chat_with_tutor,
            inputs=[user_id_state, msg_input, chatbox],
            outputs=[chatbox, msg_input],
        )

        msg_input.submit(
            add_user_message,
            inputs=[user_id_state, msg_input, chatbox],
            outputs=[chatbox, msg_input],
        ).then(
            chat_with_tutor,
            inputs=[user_id_state, msg_input, chatbox],
            outputs=[chatbox, msg_input],
        )

    # START UI
    if __name__ == "__main__":
        demo.launch(
            server_name=settings.UI_URL,
            server_port=int(settings.UI_PORT),
        )