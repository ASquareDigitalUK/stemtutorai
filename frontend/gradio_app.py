import gradio as gr
import requests
import base64
import os

# ==============================
# CONFIG: Backend API URLs
# ==============================
# Default to your Cloud Run backend; can be overridden with BACKEND_URL env var
BACKEND_URL = os.environ.get(
    "BACKEND_URL",
    "https://aitutor-service-755245699668.europe-west3.run.app",
).rstrip("/")

API_TUTOR_URL = f"{BACKEND_URL}/tutor"
API_WELCOME_URL = f"{BACKEND_URL}/welcome"

# ==============================
# LOAD BACKGROUND IMAGE
# ==============================
# We’ll ship bg-lesson.jpg in the Docker image under /app/static
img_path = "static/bg-lesson.jpg"

encoded_bg = ""
if os.path.exists(img_path):
    with open(img_path, "rb") as f:
        encoded_bg = base64.b64encode(f.read()).decode()
else:
    print(f"⚠️ Background image not found at {img_path}. UI will still work.")

background_css = f"""
#chat-container {{
    background-image: url("data:image/jpeg;base64,{encoded_bg}") if "{encoded_bg}" else "none";
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
    border-radius: 10px;
    padding: 8px 12px;
}}

.bot-bubble {{
    background: #fff8da !important;
    color: #000 !important;
    border-radius: 10px;
    padding: 8px 12px;
}}
"""

# ==============================
# HELPERS
# ==============================

def add_user_message(user_id, message, history):
    if not message or not message.strip():
        return history, message
    history = history + [{"role": "user", "content": message}]
    return history, message


def chat_with_tutor(user_id, message, history):
    if not message or not message.strip():
        return history, ""

    try:
        res = requests.post(
            API_TUTOR_URL,
            json={"user_id": user_id, "message": message},
            timeout=20,
        )
        data = res.json()
        reply = data.get("response", "(no reply)")
        if reply is None:
            reply = ""
            print("WARNING: Backend returned None reply. Using empty string.")
    except Exception as e:
        reply = f"⚠️ Error contacting tutor API: {e}"

    history = history + [{"role": "assistant", "content": reply}]
    return history, ""  # clear input


def login_user(name):
    if not name:
        return gr.update(), gr.update(visible=True), gr.update(visible=False), []

    try:
        res = requests.post(
            API_WELCOME_URL,
            json={"user_id": name, "message": ""},
            timeout=20,
        )
        welcome = res.json().get("welcome", f"Welcome {name}! 👋")
    except Exception as e:
        welcome = f"Welcome {name}! (Welcome service unavailable: {e})"

    initial_history = [{"role": "assistant", "content": welcome}]

    return (
        name,                      # user_id_state
        gr.update(visible=False),  # hide login box
        gr.update(visible=True),   # show chat UI
        initial_history,
    )


# ==============================
# GRADIO APP
# ==============================

with gr.Blocks(css=background_css) as demo:
    gr.Markdown("<h1 style='text-align:center;'>AI Learning Tutor</h1>")

    user_id_state = gr.State("")

    # ---------- LOGIN ----------
    with gr.Column(visible=True, elem_id="login-box") as login_col:
        gr.Markdown("### Enter your name to begin learning")
        name_input = gr.Textbox(label="Your Name", placeholder="e.g. Vijay")
        login_btn = gr.Button("Login", variant="primary")
        login_status = gr.Markdown("")

    # ---------- CHAT ----------
    with gr.Column(visible=False, elem_id="chat-container") as chat_col:
        chatbox = gr.Chatbot(
            label="Tutor Chat",
            type="messages",
            height=500,
            elem_classes=["chatbot"],
        )

        msg_input = gr.Textbox(
            placeholder="Type your message…",
            show_label=False,
        )

        send_btn = gr.Button("Send", variant="primary")

    # Login wiring
    login_btn.click(
        login_user,
        inputs=name_input,
        outputs=[user_id_state, login_col, chat_col, chatbox],
    )

    # Chat wiring: button click
    send_btn.click(
        add_user_message,
        inputs=[user_id_state, msg_input, chatbox],
        outputs=[chatbox, msg_input],
    ).then(
        chat_with_tutor,
        inputs=[user_id_state, msg_input, chatbox],
        outputs=[chatbox, msg_input],
    )

    # Chat wiring: Enter key
    msg_input.submit(
        add_user_message,
        inputs=[user_id_state, msg_input, chatbox],
        outputs=[chatbox, msg_input],
    ).then(
        chat_with_tutor,
        inputs=[user_id_state, msg_input, chatbox],
        outputs=[chatbox, msg_input],
    )

# IMPORTANT for Cloud Run: bind to PORT env
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)

