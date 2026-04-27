import streamlit as st
import ollama
import requests
import re
from pathlib import Path
import os
import traceback

# =========================================================
# UI
# =========================================================

st.set_page_config(
    page_title="Олег + Worker — AI Dev System",
    layout="wide"
)

st.title("🧠 Олег + ⚙️ Worker — AI Dev System")


# =========================================================
# SESSION STATE
# =========================================================

if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None


def create_new_chat():
    chat_id = f"chat_{len(st.session_state.chats) + 1}"

    st.session_state.chats[chat_id] = {
        "title": f"Чат {len(st.session_state.chats) + 1}",
        "messages": []
    }

    st.session_state.current_chat_id = chat_id
    st.rerun()


def delete_chat(chat_id):
    if chat_id in st.session_state.chats:
        del st.session_state.chats[chat_id]

        if st.session_state.current_chat_id == chat_id:
            if st.session_state.chats:
                st.session_state.current_chat_id = list(
                    st.session_state.chats.keys()
                )[0]
            else:
                st.session_state.current_chat_id = None
                create_new_chat()

        st.rerun()


if not st.session_state.chats:
    create_new_chat()

if not st.session_state.current_chat_id:
    st.session_state.current_chat_id = list(
        st.session_state.chats.keys()
    )[0]

current_chat = st.session_state.chats[
    st.session_state.current_chat_id
]

current_messages = current_chat["messages"]


# =========================================================
# TTS
# =========================================================

@st.cache_resource
def load_tts_model():
    """
    Загружается ОДИН раз.
    Это очень важно.
    """
    import torch
    from chatterbox.tts_turbo import ChatterboxTurboTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔊 TTS device: {device}")

    model = ChatterboxTurboTTS.from_pretrained(
        device=device
    )

    return model


def speak_text(text, voice_type):
    if not text.strip():
        return

    try:
        import torchaudio as ta

        model = load_tts_model()

        # reference voice
        reference_voice = None

        if voice_type == "Мужской":
            if os.path.exists("male_voice.wav"):
                reference_voice = "male_voice.wav"

        elif voice_type == "Кавайный":
            if os.path.exists("kawaii_voice.wav"):
                reference_voice = "kawaii_voice.wav"

        # generate
        if reference_voice:
            wav = model.generate(
                text=text,
                audio_prompt_path=reference_voice
            )
        else:
            wav = model.generate(
                text=text
            )

        output_path = "tts_output.wav"

        ta.save(
            output_path,
            wav,
            24000
        )

        # автозапуск на Windows
        os.system(f'start "" "{output_path}"')

        print("✅ TTS выполнен")

    except Exception as e:
        print("❌ FULL TTS ERROR:")
        traceback.print_exc()
        print(e)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.header("⚙️ Настройки")

    workspace = st.text_input(
        "Workspace",
        value="./workspace"
    )

    os.makedirs(workspace, exist_ok=True)

    st.success(
        f"📂 {Path(workspace).absolute()}"
    )

    # -----------------------------
    # TTS
    # -----------------------------

    st.divider()
    st.header("🔊 TTS")

    tts_enabled = st.checkbox(
        "Включить озвучку",
        value=False
    )

    tts_voice = st.radio(
        "Голос",
        options=[
            "Мужской",
            "Кавайный"
        ],
        index=0
    )

    # -----------------------------
    # Ollama models
    # -----------------------------

    ollama_models = []

    try:
        resp = requests.get(
            "http://127.0.0.1:11434/api/tags",
            timeout=3
        )

        if resp.status_code == 200:
            ollama_models = [
                m["name"]
                for m in resp.json().get("models", [])
            ]

    except Exception:
        pass

    worker_model = st.selectbox(
        "Worker model",
        options=ollama_models or ["qwen2.5-coder:7b"]
    )

    oleg_model = st.selectbox(
        "Олег model",
        options=ollama_models or ["llama3:8b"]
    )

    temperature = st.slider(
        "Temperature",
        0.0,
        1.0,
        0.2
    )

    max_steps = st.slider(
        "Max worker steps",
        5,
        40,
        15
    )

    # -----------------------------
    # Chats
    # -----------------------------

    st.divider()
    st.header("💬 Чаты")

    if st.button(
        "➕ Новый чат",
        use_container_width=True
    ):
        create_new_chat()

    for chat_id, data in list(st.session_state.chats.items()):
        c1, c2 = st.columns([5, 1])

        with c1:
            if st.button(
                data["title"],
                key=f"open_{chat_id}",
                use_container_width=True
            ):
                st.session_state.current_chat_id = chat_id
                st.rerun()

        with c2:
            if st.button(
                "🗑️",
                key=f"del_{chat_id}"
            ):
                delete_chat(chat_id)


# =========================================================
# FILE SYSTEM
# =========================================================

def safe_path(filename: str) -> Path:
    base = Path(workspace).resolve()
    target = (base / filename).resolve()

    if not str(target).startswith(str(base)):
        raise ValueError("⛔ Path escape detected")

    target.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    return target


def write_file(filename, content):
    try:
        if len(content.strip()) < 50:
            return "❌ Слишком короткий файл"

        path = safe_path(filename)

        path.write_text(
            content,
            encoding="utf-8"
        )

        if path.stat().st_size < 50:
            return "❌ Файл записался пустым"

        return f"✅ {filename} ({path.stat().st_size} bytes)"

    except Exception as e:
        return f"❌ {e}"


# =========================================================
# PROMPTS
# =========================================================

OLEG_PROMPT = """
Ты — менеджер проектов.

ТВОЯ РОЛЬ:
- НЕ писать код
- анализировать задачу
- делегировать Worker'у

Если пользователь просит что-то создать —
ты ОБЯЗАН делегировать.

Формат:

Хорошо, делегирую Worker'у

<DELEGATE_TO_WORKER>
Подробное ТЗ:
- что сделать
- какие файлы
- требования
</DELEGATE_TO_WORKER>

НИКОГДА не пиши код.
"""

WORKER_PROMPT = """
You are a universal software engineer.

STRICT RULES:

1. Output ONLY in WRITE blocks

2. Format:

<WRITE>filename.ext
FULL FILE CONTENT
</WRITE>

3. Multiple files allowed

4. Each file must be COMPLETE

5. No explanations

6. Minimum 100 chars

7. Code must be runnable
"""


# =========================================================
# WORKER
# =========================================================

def run_worker(task):
    messages = [
        {
            "role": "system",
            "content": WORKER_PROMPT
        },
        {
            "role": "user",
            "content": task
        }
    ]

    logs = []

    for step in range(max_steps):
        try:
            response = ollama.chat(
                model=worker_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": 8192,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            )

            text = response["message"]["content"]

            if not text or len(text) < 20:
                logs.append(f"Step {step}: пустой ответ")
                messages.append({
                    "role": "user",
                    "content": "Return FULL files in WRITE blocks"
                })
                continue

            logs.append(f"Step {step}: {len(text)} chars")

            matches = re.findall(
                r"<WRITE>(.*?)\n([\s\S]*?)</WRITE>",
                text
            )

            if not matches:
                logs.append("❌ Нет WRITE блоков")
                messages.append({
                    "role": "user",
                    "content": "Use WRITE blocks only"
                })
                continue

            success = []

            for filename, content in matches:
                filename = filename.strip()
                content = content.strip()

                if len(content) < 100:
                    logs.append(f"⚠️ {filename} слишком короткий")
                    continue

                result = write_file(
                    filename,
                    content
                )

                logs.append(result)

                if "✅" in result:
                    success.append(filename)

            if success:
                return (
                    "\n".join(logs)
                    + f"\n\n✅ Создано: {', '.join(success)}"
                )

        except Exception as e:
            return f"❌ Worker error: {e}"

    return "\n".join(logs) + "\n\n❌ Worker не справился"


# =========================================================
# CHAT HISTORY
# =========================================================

for msg in current_messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


# =========================================================
# CHAT INPUT
# =========================================================

prompt = st.chat_input("Напиши задачу...")

if prompt:
    # user message
    current_messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""

        oleg_messages = [
            {
                "role": "system",
                "content": OLEG_PROMPT
            }
        ]

        for m in current_messages:
            oleg_messages.append(m)

        try:
            stream = ollama.chat(
                model=oleg_model,
                messages=oleg_messages,
                stream=True,
                options={
                    "temperature": 0
                }
            )

            for chunk in stream:
                content = chunk["message"].get(
                    "content",
                    ""
                )

                full += content
                placeholder.markdown(full + "▌")

            placeholder.markdown(full)

        except Exception as e:
            full = f"❌ Ошибка Ollama: {e}"
            placeholder.markdown(full)

        # assistant message сохраняем ВСЕГДА
        current_messages.append({
            "role": "assistant",
            "content": full
        })

        # TTS
        if tts_enabled:
            speak_text(full, tts_voice)

        # Worker delegation
        match = re.search(
            r"<DELEGATE_TO_WORKER>(.*?)</DELEGATE_TO_WORKER>",
            full,
            re.DOTALL
        )

        if match:
            st.info("⚙️ Worker работает...")

            task = match.group(1)

            with st.expander(
                "Лог Worker",
                expanded=True
            ):
                result = run_worker(task)
                st.code(result)

            current_messages.append({
                "role": "system",
                "content": result
            })


# =========================================================
# FOOTER
# =========================================================

st.caption("🚀 Universal AI Dev System + Fixed TTS + Multi-message Chat")
