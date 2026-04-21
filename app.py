import streamlit as st
import ollama
from openai import OpenAI
import requests
import re
from pathlib import Path
import json
import os

st.set_page_config(page_title="Олег + Worker — Вайб Кодер", layout="wide")
st.title("🧠 Олег + ⚙️ Worker — Вайб Кодер")

# ====================== УПРАВЛЕНИЕ ЧАТАМИ ======================
if "chats" not in st.session_state:
    st.session_state.chats = {}
    st.session_state.current_chat_id = None

def create_new_chat():
    chat_id = f"chat_{len(st.session_state.chats)+1}"
    st.session_state.chats[chat_id] = {"title": f"Чат {len(st.session_state.chats)+1}", "messages": []}
    st.session_state.current_chat_id = chat_id
    st.rerun()

def delete_chat(chat_id):
    if chat_id in st.session_state.chats:
        del st.session_state.chats[chat_id]
        if st.session_state.current_chat_id == chat_id:
            st.session_state.current_chat_id = list(st.session_state.chats.keys())[0] if st.session_state.chats else None
            if not st.session_state.current_chat_id:
                create_new_chat()
        st.rerun()

if not st.session_state.chats:
    create_new_chat()

current_chat = st.session_state.chats[st.session_state.current_chat_id]
current_messages = current_chat["messages"]

# ====================== НАСТРОЙКИ ======================
with st.sidebar:
    st.header("⚙️ Настройки")
    workspace = st.text_input("Папка workspace", value=r"C:\MyProjects")
    os.makedirs(workspace, exist_ok=True)
    st.success(f"📂 Workspace: **{Path(workspace).absolute()}**")

    ollama_models = []
    try:
        resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            ollama_models = [m['name'] for m in resp.json().get('models', [])]
    except:
        pass

    ollama_model = st.selectbox("Модель Олега", options=ollama_models or ["llama3.2"], index=0)
   
    lmstudio_url = st.text_input("URL LM Studio", value="http://localhost:1234/v1")
    worker_model = st.selectbox("Модель Worker", options=["qwen2.5-coder", "deepseek-coder-v2"], index=0)
    temperature = st.slider("Температура", 0.0, 1.0, 0.2, step=0.05)
    max_steps = st.slider("Макс. шагов Worker", 5, 60, 40)
    st.divider()
    st.header("💬 Чаты")
    if st.button("➕ Новый чат", use_container_width=True, type="primary"):
        create_new_chat()
    for chat_id, data in list(st.session_state.chats.items()):
        col1, col2 = st.columns([5,1])
        with col1:
            if st.button(data["title"], key=f"sw_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                delete_chat(chat_id)

# ====================== КЛИЕНТЫ ======================
client_worker = OpenAI(base_url=lmstudio_url, api_key="lm-studio")

# ====================== ИНСТРУМЕНТЫ ======================
def sanitize_filename(name: str) -> str:
    """Удаляет запрещенные символы из имен файлов/папок для Windows"""
    invalid_chars = r'<>:"/\|?*'
    for c in invalid_chars:
        name = name.replace(c, '')
    return name.strip()

def safe_path(filename: str) -> str:
    # Санитайзим каждый компонент пути
    path = Path(filename)
    sanitized_parts = [sanitize_filename(part) for part in path.parts]
    sanitized_path = Path(*sanitized_parts)
   
    full = Path(workspace) / sanitized_path
    if not str(full.resolve()).startswith(str(Path(workspace).resolve())):
        raise ValueError("⛔ Запрещено выходить за пределы workspace!")
    full.parent.mkdir(parents=True, exist_ok=True)
    return str(full)

def tool_list_files():
    """Список файлов и папок в корне workspace"""
    p = Path(workspace)
    if not p.exists():
        return "❌ Workspace folder not found"
    
    items = []
    for item in sorted(p.iterdir()):
        if item.is_dir():
            items.append(f"📁 {item.name}/")
        else:
            items.append(f"📄 {item.name}")
    
    return "\n".join(items) or "📂 Workspace is empty"

def tool_read_file(filename: str):
    p = safe_path(filename)
    path_obj = Path(p)
    if not path_obj.exists():
        return f"❌ {filename} не найден"
    if path_obj.is_dir():
        return f"❌ {filename} является папкой. Используй tool_read_directory для чтения папок"
    return path_obj.read_text(encoding="utf-8")

def tool_read_directory(dirname: str):
    p = safe_path(dirname)
    path_obj = Path(p)
    if not path_obj.exists():
        return f"❌ Папка {dirname} не найдена"
    if not path_obj.is_dir():
        return f"❌ {dirname} не является папкой"
    return "\n".join(f.name for f in path_obj.iterdir()) or f"Папка {dirname} пуста"

def tool_write_file(filename: str, content: str):
    p = safe_path(filename)
    Path(p).write_text(content, encoding="utf-8")
    return f"✅ Файл **{filename}** создан/обновлён"

def tool_delete_file(filename: str):
    p = safe_path(filename)
    if Path(p).exists():
        Path(p).unlink()
        return f"🗑️ **{filename}** удалён"
    return f"Файл {filename} не найден"

def tool_create_directory(dirname: str):
    path = Path(workspace) / dirname
    path.mkdir(parents=True, exist_ok=True)
    return f"📁 Папка **{dirname}** создана"

tools = {
    "list_files": tool_list_files,
    "read_file": tool_read_file,
    "read_directory": tool_read_directory,
    "write_file": tool_write_file,
    "delete_file": tool_delete_file,
    "create_directory": tool_create_directory,
}

# ====================== ПРОМПТ ДЛЯ WORKER ======================
WORKER_SYSTEM_PROMPT = r"""You are an AI that uses XML tags to interact with tools. Follow these rules:

Tools:
<LIST></LIST> - List files in workspace (root)
<READ>filename</READ> - Read file content
<READ_DIR>dirname</READ_DIR> - List files inside specific directory
<WRITE>filename
content
</WRITE> - Write/overwrite file
<DELETE>filename</DELETE> - Delete file
<MKDIR>dirname</MKDIR> - Create folder

Rules:
1. Respond ONLY in English
2. Format: Exactly two lines:
   Line 1: [Thought]: (your analysis)
   Line 2: [Action]: (one XML tag)
3. Always start with <LIST></LIST>
4. Only one action per response

Example:
[Thought]: Checking current files
[Action]: <LIST></LIST>
[Thought]: No game folder, creating project
[Action]: <MKDIR>snake_game</MKDIR>
[Thought]: Now creating main.py
[Action]: <WRITE>snake_game/main.py
import pygame
...
</WRITE>
[Thought]: Task completed
[Final Answer]: Project snake_game created successfully"""

# ====================== ПРОМПТ ДЛЯ ОЛЕГА ======================
OLEG_SYSTEM_PROMPT = """Ты — Олег, вайб-менеджер.
ПРАВИЛО №1: Если пользователь пишет «Создай проект», «Сделай игру», «Создай змейку», «Сохрани на диск» или любую похожую фразу — ТЫ НИКОГДА НЕ ПИШЕШЬ КОД САМ.
Ты ОБЯЗАН сразу использовать тег:
<DELEGATE_TO_WORKER>
Подробное описание задачи для Worker
</DELEGATE_TO_WORKER>
Пример:
<DELEGATE_TO_WORKER>Создай полный проект игры Змейка на Pygame в папке snake_game. Включи main.py, requirements.txt и README.md.</DELEGATE_TO_WORKER>
Ты можешь только общаться с пользователем и делегировать. Никогда не давай готовый код в ответе."""

# ====================== WORKER ======================
def run_worker(task_prompt: str):
    messages = [
        {"role": "system", "content": WORKER_SYSTEM_PROMPT},
        {"role": "user", "content": task_prompt}
    ]
    steps = []
    for _ in range(max_steps):
        try:
            resp = client_worker.chat.completions.create(
                model=worker_model,
                messages=messages,
                temperature=temperature,
                max_tokens=4096
            )
            text = resp.choices[0].message.content.strip()
            steps.append(text)
        except Exception as e:
            error_msg = f"❌ Ошибка при вызове Worker: {str(e)}"
            steps.append(error_msg)
            return "\n\n".join(steps) + "\n\nWorker завершил с ошибкой"

        # Ищем блок [Action]
        action_pattern = r'\[Action\]:\s*<(\w+)>(.*?)</\1>'
        action_match = re.search(action_pattern, text, re.DOTALL)
       
        if action_match:
            tag_name = action_match.group(1).lower()
            tag_content = action_match.group(2).strip()
           
            # Обработка тегов
            if tag_name == "read":
                result = tools["read_file"](tag_content)
            elif tag_name == "read_dir":
                result = tools["read_directory"](tag_content)
            elif tag_name == "write":
                if '\n' in tag_content:
                    filename, content = tag_content.split('\n', 1)
                    filename = filename.strip()
                    # НЕ strip() content — сохраняем отступы кода!
                    result = tools["write_file"](filename, content)
                else:
                    result = f"❌ WRITE: Неверный формат"
            elif tag_name == "delete":
                result = tools["delete_file"](tag_content)
            elif tag_name == "mkdir":
                result = tools["create_directory"](tag_content)
            elif tag_name == "list":
                result = tools["list_files"]()
            elif tag_name == "help":
                result = "ℹ️ Помощь: Используй <LIST></LIST>, <READ>, <READ_DIR>, <WRITE> и т.д."
            else:
                result = f"❌ Неизвестный тег: {tag_name}"
           
            steps.append(f"✅ {tag_name} → {result}")
            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "user", "content": result})
            continue

        # Проверяем на завершение задачи
        final_answer_match = re.search(r'\[Final Answer\]:\s*(.+)', text)
        if final_answer_match:
            answer = final_answer_match.group(1).strip()
            return "\n\n".join(steps) + f"\n\n**Worker завершил:** {answer}"

    return "\n\n".join(steps) + "\n\nWorker завершил по лимиту"

# ====================== ЧАТ ======================
for msg in current_messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("Напиши Олегу..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        ollama_response = ollama.chat(
            model=ollama_model,
            messages=[{"role": "system", "content": OLEG_SYSTEM_PROMPT}] +
                      [{"role": m["role"], "content": m["content"]} for m in current_messages],
            stream=True
        )
        
        for chunk in ollama_response:
            content = chunk['message'].get('content', '')
            if content:
                full_response += content
                placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)

        delegate_match = re.search(r'<DELEGATE_TO_WORKER>(.*?)</DELEGATE_TO_WORKER>', full_response, re.DOTALL)
        if delegate_match:
            st.info("🔄 **Олег делегировал задачу Worker’у**")
            worker_prompt = delegate_match.group(1).strip()
            with st.expander("👀 Полный trace Worker’а", expanded=True):
                worker_result = run_worker(worker_prompt)
                st.code(worker_result, language="markdown")
            current_messages.append({"role": "assistant", "content": full_response})
            current_messages.append({"role": "system", "content": f"**Worker выполнил:**\n{worker_result}"})
        else:
            current_messages.append({"role": "assistant", "content": full_response})

st.caption("✅ Олег теперь ОБЯЗАН делегировать Worker’у • Проект Змейка будет создан на диске")