import streamlit as st
import ollama
import requests
import re
from pathlib import Path
import os
import wave
import traceback
import base64
import io
import tempfile
import time
import subprocess
from typing import Dict, List, Optional, Tuple

# Распознавание речи
import speech_recognition as sr
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

# =========================================================
# SYSTEM PROMPTS (ALWAYS IN ENGLISH FOR BEST PERFORMANCE)
# =========================================================

OLEG_SYSTEM_PROMPT = """
You are Oleg, a project manager and Team Lead.

YOUR ROLE:
- Analyze the user's task carefully
- Break down complex requests into manageable subtasks
- NEVER write code yourself - you are a manager, not a coder
- Delegate ALL code writing tasks to the Worker

COMMUNICATION STYLE:
- Be helpful, clear, and professional
- Ask clarifying questions when needed
- Explain your plan before delegating

WHEN TO DELEGATE TO WORKER:
If the task requires creating files, writing code, or building anything:
Use this exact format:
<DELEGATE_TO_WORKER>
Detailed technical specification with:
- List of files to create
- Complete description of each file's purpose
- Specific requirements and functionality
- Any dependencies or libraries needed
</DELEGATE_TO_WORKER>

WHEN TO RESPOND DIRECTLY:
- Answering questions about programming concepts
- Explaining how something works
- Giving advice or recommendations
- Tasks that don't require code creation

Remember: You are the manager. The Worker writes code. Work as a team!
"""

WORKER_SYSTEM_PROMPT = """
You are a Worker, a senior software engineer and code generator.

YOUR TASK:
Write complete, working code based on the technical specification provided.

CRITICAL RULES:
1. Output ONLY in WRITE blocks - NO explanations, NO comments outside blocks
2. Each file must be in its own <WRITE> block
3. Code must be complete and ready to run
4. Include necessary imports and dependencies
5. Use proper error handling

OUTPUT FORMAT:
<WRITE>path/to/file.ext
FULL FILE CONTENT HERE
</WRITE>

EXAMPLE:
<WRITE>src/main.py
import sys

def main():
    print("Hello World")

if __name__ == "__main__":
    main()
</WRITE>

<WRITE>requirements.txt
requests==2.28.0
</WRITE>

MULTIPLE FILES:
You can create as many files as needed. Just use multiple WRITE blocks.

QUALITY STANDARDS:
- Code should be production-ready
- Include docstrings and comments where helpful
- Follow language best practices
- Handle edge cases and errors

Remember: Only output WRITE blocks. No greetings, no explanations, no summaries.
"""

# =========================================================
# MULTILINGUAL UI TRANSLATIONS
# =========================================================

UI_TRANSLATIONS = {
    'ru': {
        # Main
        'app_title': 'Олег + Worker — AI Dev System',
        'oleg_worker_system': 'Олег + Worker — AI Dev System',
        
        # FFmpeg
        'ffmpeg_not_found': '❌ FFmpeg не найден! Голосовой ввод может не работать.',
        'ffmpeg_install_info': 'Установка: winget install ffmpeg',
        'ffmpeg_found': '✅ FFmpeg найден',
        
        # Voice control
        'voice_control': '🎤 Голосовое управление',
        'voice_control_hint': 'Нажмите "Начать запись", скажите команду (например: "Олег, создай файл hello.py"), затем нажмите "Распознать"',
        'start_recording': '🎙️ Начать запись',
        'stop_recording': '⏹️ Остановить запись',
        'cancel': '❌ Отмена',
        'recording_in_progress': '🔴 **Идет запись...** Говорите четко. Начните с "Олег"',
        'recording_complete': '✅ Запись завершена! Нажмите "Распознать"',
        'recording_cancelled': 'Запись отменена',
        'speech_recognition': '📝 Распознавание речи',
        'recognize_text': '🔍 Распознать текст',
        'recognizing': 'Распознаю речь...',
        'recognized_google': '🎤 Распознано (Google): {}',
        'recognized_engine': '🎤 Распознано ({}): {}',
        'oleg_detected': '✅ Обнаружено обращение к Олегу!',
        'command': '📝 Команда: **{}**',
        'command_sent': '✅ Команда отправлена в чат!',
        'no_command': '⚠️ Команда не распознана. Скажите что-нибудь после "Олег"',
        'command_examples': "Примеры: 'Олег создай файл', 'Олег напиши код'",
        'oleg_not_detected': '👂 Не обнаружено обращение "Олег"',
        'pronunciation_examples': 'Примеры правильного произношения:',
        'send_to_chat': '📤 Отправить в чат',
        'try_again': '🔄 Попробовать снова',
        'recognition_failed': '❌ Не удалось распознать текст',
        'recognition_failed_services': '❌ Не удалось распознать речь ни одним сервисом',
        'clear_recording': '🗑️ Очистить запись',
        'recording_error': '❌ Ошибка конвертации аудио',
        
        # Sidebar
        'settings': '⚙️ Настройки',
        'workspace': 'Рабочая папка',
        'workspace_folder': '📂 {}',
        'tts_settings': '🔊 TTS — Озвучка',
        'enable_tts': 'Включить озвучку ответов',
        'voice': 'Голос',
        'male': 'Мужской',
        'female': 'Женский',
        'ollama_models': '🤖 Модели Ollama',
        'ollama_connection_error': '⚠️ Не удалось подключиться к Ollama',
        'worker_model': 'Модель Worker (исполнитель)',
        'oleg_model': 'Модель Олег (менеджер)',
        'models_not_found': 'Модели не найдены. Загрузите через ollama pull',
        'temperature': 'Температура (креативность)',
        'max_worker_steps': 'Максимум шагов Worker',
        'chats': '💬 Чаты',
        'new_chat': '➕ Новый чат',
        'clear_chat': '🗑️ Очистить чат',
        'language_selector': '🌍 Язык интерфейса',
        
        # Worker functions
        'file_too_short': '❌ Слишком короткий файл',
        'file_saved': '✅ {} ({} байт)',
        'path_escape': '⛔ Обнаружена попытка выхода за пределы рабочей папки',
        'worker_no_files': '❌ Worker не создал файлы',
        'worker_file_too_short': '⚠️ {}: слишком короткий (<50 символов)',
        'worker_success': '\n\n✅ Успешно создано файлов: {}\n📁 {}',
        'worker_task_failed': '\n\n❌ Worker не справился с задачей',
        'worker_working': '⚙️ Worker работает над задачей...',
        'worker_log': '📋 Лог выполнения Worker',
        
        # Chat
        'chat_title': 'Чат {}',
        'type_message': '💬 Напишите сообщение или используйте голосовой ввод выше...',
        'ollama_error': '❌ Ошибка подключения к Ollama: {}',
        'worker_result': '**Worker (исполнитель):**\n```\n{}\n```',
        
        # Instructions
        'instructions': """
💡 **Как использовать голосовое управление:**

1. Нажмите **'Начать запись'**
2. Скажите: **'Олег, напиши мне калькулятор на Python'** (обязательно начните с 'Олег')
3. Нажмите **'Остановить запись'**
4. Нажмите **'Распознать текст'**
5. Команда автоматически отправится в чат если распознано 'Олег'

**Дополнительные функции:**
- 🔊 **TTS озвучка** - ответы Олега озвучиваются голосом
- 💾 **Сохранение чатов** - все чаты сохраняются в сессии
- ⚙️ **Worker** - автоматически пишет код по заданию
- 📁 **Workspace** - файлы создаются в выбранной папке
- 🎯 **Множественное распознавание** - Google + Sphinx
- 🌍 **Мультиязычный интерфейс** - выберите язык в боковой панели

**Советы для лучшего распознавания:**
- Говорите четко и не слишком быстро
- Делайте паузу после слова 'Олег'
- Используйте качественный микрофон
- Избегайте фонового шума

**Примеры команд:**
- "Олег, создай файл hello.py"
- "Олег, напиши калькулятор на Python"
- "Олег, сделай todo-лист с сохранением"

Или используйте обычный текстовой ввод внизу экрана.
""",
    },
    'en': {
        'app_title': 'Oleg + Worker — AI Dev System',
        'oleg_worker_system': 'Oleg + Worker — AI Dev System',
        'ffmpeg_not_found': '❌ FFmpeg not found! Voice input may not work.',
        'ffmpeg_install_info': 'Install: winget install ffmpeg',
        'ffmpeg_found': '✅ FFmpeg found',
        'voice_control': '🎤 Voice Control',
        'voice_control_hint': 'Click "Start Recording", say a command (e.g., "Oleg, create file hello.py"), then click "Recognize"',
        'start_recording': '🎙️ Start Recording',
        'stop_recording': '⏹️ Stop Recording',
        'cancel': '❌ Cancel',
        'recording_in_progress': '🔴 **Recording...** Speak clearly. Start with "Oleg"',
        'recording_complete': '✅ Recording complete! Click "Recognize"',
        'recording_cancelled': 'Recording cancelled',
        'speech_recognition': '📝 Speech Recognition',
        'recognize_text': '🔍 Recognize Text',
        'recognizing': 'Recognizing speech...',
        'recognized_google': '🎤 Recognized (Google): {}',
        'recognized_engine': '🎤 Recognized ({}): {}',
        'oleg_detected': '✅ Oleg detected!',
        'command': '📝 Command: **{}**',
        'command_sent': '✅ Command sent to chat!',
        'no_command': '⚠️ No command recognized. Say something after "Oleg"',
        'command_examples': "Examples: 'Oleg create file', 'Oleg write code'",
        'oleg_not_detected': '👂 "Oleg" not detected',
        'pronunciation_examples': 'Correct pronunciation examples:',
        'send_to_chat': '📤 Send to Chat',
        'try_again': '🔄 Try Again',
        'recognition_failed': '❌ Failed to recognize text',
        'recognition_failed_services': '❌ Failed to recognize speech by any service',
        'clear_recording': '🗑️ Clear Recording',
        'recording_error': '❌ Audio conversion error',
        'settings': '⚙️ Settings',
        'workspace': 'Workspace',
        'workspace_folder': '📂 {}',
        'tts_settings': '🔊 TTS — Voice Output',
        'enable_tts': 'Enable voice output',
        'voice': 'Voice',
        'male': 'Male',
        'female': 'Female',
        'ollama_models': '🤖 Ollama Models',
        'ollama_connection_error': '⚠️ Cannot connect to Ollama',
        'worker_model': 'Worker Model',
        'oleg_model': 'Oleg Model',
        'models_not_found': 'Models not found. Load via ollama pull',
        'temperature': 'Temperature',
        'max_worker_steps': 'Max worker steps',
        'chats': '💬 Chats',
        'new_chat': '➕ New Chat',
        'clear_chat': '🗑️ Clear Chat',
        'language_selector': '🌍 Interface Language',
        'file_too_short': '❌ File too short',
        'file_saved': '✅ {} ({} bytes)',
        'path_escape': '⛔ Path escape detected',
        'worker_no_files': '❌ Worker created no files',
        'worker_file_too_short': '⚠️ {}: too short (<50 chars)',
        'worker_success': '\n\n✅ Successfully created files: {}\n📁 {}',
        'worker_task_failed': '\n\n❌ Worker failed to complete task',
        'worker_working': '⚙️ Worker working on task...',
        'worker_log': '📋 Worker Execution Log',
        'chat_title': 'Chat {}',
        'type_message': '💬 Type a message or use voice input above...',
        'ollama_error': '❌ Ollama connection error: {}',
        'worker_result': '**Worker:**\n```\n{}\n```',
        'instructions': """
💡 **How to use voice control:**

1. Click **'Start Recording'**
2. Say: **'Oleg, write me a calculator in Python'** (must start with 'Oleg')
3. Click **'Stop Recording'**
4. Click **'Recognize Text'**
5. Command automatically sends to chat if 'Oleg' is detected

**Additional features:**
- 🔊 **TTS voice output** - Oleg's responses are voiced
- 💾 **Chat saving** - all chats are saved in session
- ⚙️ **Worker** - automatically writes code based on assignment
- 📁 **Workspace** - files are created in the selected folder
- 🎯 **Multiple recognition engines** - Google + Sphinx
- 🌍 **Multilingual interface** - select language in sidebar

**Tips for better recognition:**
- Speak clearly and not too fast
- Pause after the word 'Oleg'
- Use a quality microphone
- Avoid background noise

**Command examples:**
- "Oleg, create file hello.py"
- "Oleg, write a calculator in Python"
- "Oleg, make a todo list with saving"

Or use regular text input at the bottom of the screen.
""",
    },
    'es': {
        'app_title': 'Oleg + Worker — Sistema AI Dev',
        'voice_control': '🎤 Control por Voz',
        'start_recording': '🎙️ Iniciar Grabación',
        'stop_recording': '⏹️ Detener Grabación',
        'recognize_text': '🔍 Reconocer Texto',
        'oleg_detected': '✅ ¡Oleg detectado!',
        'command': '📝 Comando: **{}**',
        'command_sent': '✅ Comando enviado al chat!',
        'settings': '⚙️ Configuraciones',
        'workspace': 'Espacio de Trabajo',
        'enable_tts': 'Habilitar Voz',
        'new_chat': '➕ Nuevo Chat',
        'clear_chat': '🗑️ Limpiar',
        'type_message': '💬 Escriba un mensaje o use entrada de voz arriba...',
        'language_selector': '🌍 Idioma de Interfaz',
        'chat_title': 'Chat {}',
        'instructions': """
💡 **Cómo usar el control por voz:**

1. Haga clic en **'Iniciar Grabación'**
2. Diga: **'Oleg, escríbeme una calculadora en Python'**
3. Haga clic en **'Detener Grabación'**
4. Haga clic en **'Reconocer Texto'**

**Comandos de ejemplo:**
- "Oleg, crea archivo hello.py"
- "Oleg, escribe una calculadora en Python"
""",
    },
    'de': {
        'app_title': 'Oleg + Worker — AI Dev System',
        'voice_control': '🎤 Sprachsteuerung',
        'start_recording': '🎙️ Aufnahme Starten',
        'stop_recording': '⏹️ Aufnahme Stoppen',
        'recognize_text': '🔍 Text Erkennen',
        'oleg_detected': '✅ Oleg erkannt!',
        'command': '📝 Befehl: **{}**',
        'command_sent': '✅ Befehl an Chat gesendet!',
        'settings': '⚙️ Einstellungen',
        'workspace': 'Arbeitsbereich',
        'enable_tts': 'Sprachausgabe Aktivieren',
        'new_chat': '➕ Neuer Chat',
        'clear_chat': '🗑️ Löschen',
        'type_message': '💬 Nachricht eingeben oder Sprachsteuerung oben verwenden...',
        'language_selector': '🌍 Sprache',
        'chat_title': 'Chat {}',
    },
    'fr': {
        'app_title': 'Oleg + Worker — Système AI Dev',
        'voice_control': '🎤 Contrôle Vocal',
        'start_recording': '🎙️ Démarrer Enregistrement',
        'stop_recording': '⏹️ Arrêter Enregistrement',
        'recognize_text': '🔍 Reconnaître Texte',
        'oleg_detected': '✅ Oleg détecté!',
        'command': '📝 Commande: **{}**',
        'command_sent': '✅ Commande envoyée au chat!',
        'settings': '⚙️ Paramètres',
        'workspace': 'Espace de Travail',
        'enable_tts': 'Activer la Synthèse Vocale',
        'new_chat': '➕ Nouvelle Discussion',
        'clear_chat': '🗑️ Effacer',
        'type_message': '💬 Écrivez un message ou utilisez la saisie vocale ci-dessus...',
        'language_selector': '🌍 Langue',
        'chat_title': 'Chat {}',
    },
    'zh': {
        'app_title': 'Oleg + Worker — AI开发系统',
        'voice_control': '🎤 语音控制',
        'start_recording': '🎙️ 开始录音',
        'stop_recording': '⏹️ 停止录音',
        'recognize_text': '🔍 识别文本',
        'oleg_detected': '✅ 检测到Oleg!',
        'command': '📝 命令: **{}**',
        'command_sent': '✅ 命令已发送到聊天!',
        'settings': '⚙️ 设置',
        'workspace': '工作区',
        'enable_tts': '启用语音输出',
        'new_chat': '➕ 新聊天',
        'clear_chat': '🗑️ 清除',
        'type_message': '💬 输入消息或使用上方的语音输入...',
        'language_selector': '🌍 界面语言',
        'chat_title': '聊天 {}',
    }
}

# Language options with flags
LANGUAGES = {
    'ru': '🇷🇺 Русский',
    'en': '🇬🇧 English',
    'es': '🇪🇸 Español',
    'de': '🇩🇪 Deutsch',
    'fr': '🇫🇷 Français',
    'zh': '🇨🇳 中文'
}

def get_ui_text(key: str, lang: str = 'ru') -> str:
    """Get translated UI text for current language"""
    return UI_TRANSLATIONS.get(lang, UI_TRANSLATIONS['ru']).get(key, UI_TRANSLATIONS['ru'].get(key, key))

# =========================================================
# FFMPEG CHECK
# =========================================================
def is_ffmpeg_installed():
    """Check if FFmpeg is installed on the system"""
    try:
        if os.name == 'nt':
            result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True)
        else:
            result = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=3)
        return result.returncode == 0
    except:
        return False

# Configure FFmpeg paths for Windows
if os.name == 'nt':
    possible_paths = [
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        os.path.expanduser("~\\scoop\\shims"),
        os.path.expanduser("~\\AppData\\Local\\Microsoft\\WinGet\\Packages\\")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")

ffmpeg_ok = is_ffmpeg_installed()

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(page_title="Oleg + Worker — AI Dev System", layout="wide")

# Initialize language in session state
if "language" not in st.session_state:
    st.session_state.language = 'en'  # Default to English for better AI performance

# Get current language
current_lang = st.session_state.language
_ = lambda key: get_ui_text(key, current_lang)

st.title(_('app_title'))

# Show FFmpeg status
if not ffmpeg_ok:
    st.sidebar.error(_('ffmpeg_not_found'))
    st.sidebar.info(_('ffmpeg_install_info'))
else:
    st.sidebar.success(_('ffmpeg_found'))

# =========================================================
# SESSION STATE
# =========================================================
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tts_enabled" not in st.session_state:
    st.session_state.tts_enabled = False
if "tts_voice" not in st.session_state:
    st.session_state.tts_voice = "male"
if "max_steps" not in st.session_state:
    st.session_state.max_steps = 15

def create_new_chat():
    chat_id = f"chat_{len(st.session_state.chats) + 1}"
    chat_title = _('chat_title').format(len(st.session_state.chats) + 1)
    st.session_state.chats[chat_id] = {"title": chat_title, "messages": []}
    st.session_state.current_chat_id = chat_id
    st.rerun()

def delete_chat(chat_id):
    if chat_id in st.session_state.chats:
        del st.session_state.chats[chat_id]
        if st.session_state.current_chat_id == chat_id:
            if st.session_state.chats:
                st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
            else:
                create_new_chat()
        st.rerun()

if not st.session_state.chats:
    create_new_chat()
if not st.session_state.current_chat_id:
    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

current_chat = st.session_state.chats[st.session_state.current_chat_id]
current_messages = current_chat["messages"]

# =========================================================
# TTS - PIPER
# =========================================================
@st.cache_resource
def load_piper_voice(voice_type: str):
    try:
        from piper.voice import PiperVoice
        voices_dir = Path("voices")
        voices_dir.mkdir(exist_ok=True)
        # Use Russian voices for TTS (since Piper primarily has Russian models)
        model_name = "ru_RU-ruslan-medium.onnx" if voice_type == "male" else "ru_RU-irina-medium.onnx"
        model_path = voices_dir / model_name
        if not model_path.exists():
            st.warning("Piper voice model not found in voices/ folder")
            st.info("Download from: https://huggingface.co/rhasspy/piper-voices")
            return None
        return PiperVoice.load(str(model_path))
    except Exception as e:
        st.warning(f"TTS unavailable: {e}")
        return None

def speak_text(text: str, voice_type: str):
    if not text or not text.strip():
        return
    if not st.session_state.tts_enabled:
        return
    
    voice = load_piper_voice(voice_type)
    if not voice:
        return
    
    try:
        # Clean text for TTS (keep Russian characters)
        cleaned = re.sub(r'[^а-яА-ЯёЁ0-9\s.,!?;:\-—«»"\'()]+', ' ', text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()[:2000] or "Test voice output."

        output_path = Path("tts_output.wav")
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(voice.config.sample_rate)
            voice.synthesize_wav(cleaned, wav_file)

        if output_path.stat().st_size > 100:
            with open(output_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<audio autoplay controls><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"TTS error: {e}")

# =========================================================
# AUDIO PROCESSING FUNCTIONS
# =========================================================
def convert_audio_to_wav(audio_bytes):
    """Convert audio to WAV with proper parameters"""
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        # Convert to mono, 16kHz (optimal for recognition)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio = audio.set_sample_width(2)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            audio.export(tmp.name, format="wav")
            return tmp.name
    except CouldntDecodeError as e:
        st.error(f"❌ Decoding error: {e}")
        if not ffmpeg_ok:
            st.info("💡 Install FFmpeg: winget install ffmpeg")
        return None
    except Exception as e:
        st.error(f"Conversion error: {e}")
        return None

def recognize_speech_with_multiple_engines(audio_file_path):
    """Recognize speech using multiple engines (optimized for Russian)"""
    recognizer = sr.Recognizer()
    
    with sr.AudioFile(audio_file_path) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        audio = recognizer.record(source)
        
        results = []
        
        # Google Speech Recognition (best for Russian)
        try:
            text = recognizer.recognize_google(audio, language="ru-RU")
            results.append(("google", text))
        except:
            pass
        
        # Sphinx (offline)
        try:
            text = recognizer.recognize_sphinx(audio, language="ru-RU")
            results.append(("sphinx", text))
        except:
            pass
        
        return results

# =========================================================
# VOICE CONTROL UI
# =========================================================
st.subheader(_('voice_control'))
st.caption(_('voice_control_hint'))

# Recording state
if "recording" not in st.session_state:
    st.session_state.recording = False
if "recorded_audio" not in st.session_state:
    st.session_state.recorded_audio = None

col1, col2, col3 = st.columns(3)

with col1:
    if st.button(_('start_recording'), type="primary", use_container_width=True):
        st.session_state.recording = True
        st.rerun()

with col2:
    if st.button(_('stop_recording'), use_container_width=True):
        st.session_state.recording = False
        st.rerun()

with col3:
    if st.button(_('cancel'), use_container_width=True):
        st.session_state.recording = False
        st.session_state.recorded_audio = None
        st.success(_('recording_cancelled'))

# Show recording interface
if st.session_state.recording:
    st.info(_('recording_in_progress'))
    
    audio_value = st.audio_input("Microphone recording", key="live_recording")
    
    if audio_value is not None:
        st.session_state.recorded_audio = audio_value
        st.session_state.recording = False
        st.success(_('recording_complete'))
        st.rerun()

# Recognize recorded audio
if st.session_state.recorded_audio is not None:
    st.divider()
    st.subheader(_('speech_recognition'))
    
    col_recognize, col_clear = st.columns(2)
    
    with col_recognize:
        if st.button(_('recognize_text'), use_container_width=True, type="primary"):
            with st.spinner(_('recognizing')):
                try:
                    audio_bytes = st.session_state.recorded_audio.getvalue()
                    wav_file = convert_audio_to_wav(audio_bytes)
                    
                    if wav_file:
                        results = recognize_speech_with_multiple_engines(wav_file)
                        os.unlink(wav_file)
                        
                        if results:
                            text = None
                            for engine, recognized_text in results:
                                if engine == "google":
                                    text = recognized_text
                                    st.info(_('recognized_google').format(text))
                                    break
                            
                            if not text and results:
                                text = results[0][1]
                                st.info(_('recognized_engine').format(results[0][0], text))
                            
                            if text:
                                text_lower = text.lower()
                                
                                # Oleg trigger words (Russian)
                                oleg_variants = ["олег", "алех", "олeг", "oleg", "алег", "олиг", "але", "оле"]
                                
                                found_oleg = False
                                command = text_lower
                                
                                for variant in oleg_variants:
                                    if variant in text_lower:
                                        found_oleg = True
                                        command = re.sub(fr'{variant}\s*[,.]*\s*', '', text_lower, flags=re.IGNORECASE).strip()
                                        if command.startswith(variant):
                                            command = command[len(variant):].strip()
                                        break
                                
                                if not found_oleg and any(text_lower.strip().startswith(v) for v in oleg_variants):
                                    found_oleg = True
                                    for variant in oleg_variants:
                                        if text_lower.strip().startswith(variant):
                                            command = text_lower[len(variant):].strip()
                                            break
                                
                                if found_oleg:
                                    st.success(_('oleg_detected'))
                                    
                                    if command and len(command) > 0:
                                        st.info(_('command').format(command))
                                        
                                        current_messages.append({"role": "user", "content": command})
                                        st.session_state.recorded_audio = None
                                        st.success(_('command_sent'))
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.warning(_('no_command'))
                                        st.caption(_('command_examples'))
                                else:
                                    st.warning(_('oleg_not_detected'))
                                    st.caption(_('pronunciation_examples'))
                                    
                                    st.text_area("Recognized text:", text, height=100)
                                    
                                    col_btn1, col_btn2 = st.columns(2)
                                    with col_btn1:
                                        if st.button(_('send_to_chat'), use_container_width=True):
                                            current_messages.append({"role": "user", "content": text})
                                            st.session_state.recorded_audio = None
                                            st.rerun()
                                    with col_btn2:
                                        if st.button(_('try_again'), use_container_width=True):
                                            st.session_state.recorded_audio = None
                                            st.rerun()
                            else:
                                st.error(_('recognition_failed'))
                        else:
                            st.error(_('recognition_failed_services'))
                    else:
                        st.error(_('recording_error'))
                        
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    st.code(traceback.format_exc())
    
    with col_clear:
        if st.button(_('clear_recording'), use_container_width=True):
            st.session_state.recorded_audio = None
            st.rerun()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    # Language selector
    st.header(_('language_selector'))
    selected_lang = st.selectbox(
        "",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        index=list(LANGUAGES.keys()).index(current_lang)
    )
    if selected_lang != current_lang:
        st.session_state.language = selected_lang
        st.rerun()
    
    st.divider()
    
    st.header(_('settings'))
    workspace = st.text_input(_('workspace'), value="./workspace")
    os.makedirs(workspace, exist_ok=True)
    st.success(_('workspace_folder').format(Path(workspace).absolute()))
    
    st.divider()
    st.header(_('tts_settings'))
    st.session_state.tts_enabled = st.checkbox(_('enable_tts'), value=st.session_state.tts_enabled)
    if st.session_state.tts_enabled:
        voice_options = ["male", "female"]
        voice_labels = [_('male'), _('female')]
        selected_voice_idx = 0 if st.session_state.tts_voice == "male" else 1
        st.session_state.tts_voice = st.radio(_('voice'), options=voice_options, format_func=lambda x: _('male') if x == "male" else _('female'), index=selected_voice_idx)
    
    st.divider()
    st.header(_('ollama_models'))
    
    ollama_models = []
    try:
        resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            ollama_models = [m["name"] for m in resp.json().get("models", [])]
    except:
        st.warning(_('ollama_connection_error'))
        ollama_models = ["llama3.2", "qwen2.5-coder:7b"]
    
    if ollama_models:
        worker_model = st.selectbox(_('worker_model'), options=ollama_models, key="worker_model")
        oleg_model = st.selectbox(_('oleg_model'), options=ollama_models, key="oleg_model")
    else:
        worker_model = "qwen2.5-coder:7b"
        oleg_model = "llama3.2"
        st.error(_('models_not_found'))
    
    temperature = st.slider(_('temperature'), 0.0, 1.0, 0.2, 0.05)
    st.session_state.max_steps = st.slider(_('max_worker_steps'), 5, 40, st.session_state.max_steps, 1)
    
    st.divider()
    st.header(_('chats'))
    
    col_new, col_clear_all = st.columns(2)
    with col_new:
        if st.button(_('new_chat'), use_container_width=True):
            create_new_chat()
    with col_clear_all:
        if st.button(_('clear_chat'), use_container_width=True):
            if current_messages:
                current_messages.clear()
                st.rerun()
    
    st.divider()
    
    # Show last 10 chats
    for chat_id, data in list(st.session_state.chats.items())[-10:]:
        c1, c2 = st.columns([5, 1])
        with c1:
            if st.button(data["title"], key=f"open_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with c2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                delete_chat(chat_id)

# =========================================================
# WORKER FUNCTIONS
# =========================================================
def safe_path(filename: str) -> Path:
    base = Path(workspace).resolve()
    target = (base / filename).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError(_('path_escape'))
    target.parent.mkdir(parents=True, exist_ok=True)
    return target

def write_file(filename, content):
    try:
        if len(content.strip()) < 50:
            return _('file_too_short')
        path = safe_path(filename)
        path.write_text(content, encoding="utf-8")
        return _('file_saved').format(filename, path.stat().st_size)
    except Exception as e:
        return f"❌ {e}"

def run_worker(task):
    messages = [
        {"role": "system", "content": WORKER_SYSTEM_PROMPT},
        {"role": "user", "content": task}
    ]
    logs = []
    
    for step in range(st.session_state.max_steps):
        try:
            response = ollama.chat(
                model=worker_model,
                messages=messages,
                options={"temperature": temperature, "num_predict": 8192}
            )
            text = response["message"]["content"]
            matches = re.findall(r"<WRITE>(.*?)\n([\s\S]*?)</WRITE>", text, re.DOTALL)
            
            if not matches:
                if step == st.session_state.max_steps - 1:
                    logs.append(_('worker_no_files'))
                continue
            
            success = []
            for filename, content in matches:
                filename = filename.strip()
                content = content.strip()
                
                if len(content) < 50:
                    logs.append(_('worker_file_too_short').format(filename))
                    continue
                    
                result = write_file(filename, content)
                logs.append(result)
                
                if "✅" in result:
                    success.append(filename)
            
            if success:
                return "\n".join(logs) + _('worker_success').format(len(success), ', '.join(success))
                
        except Exception as e:
            logs.append(f"❌ Worker Error: {e}")
            return "\n".join(logs)
    
    return "\n".join(logs) + _('worker_task_failed')

# =========================================================
# MAIN CHAT INTERFACE
# =========================================================
# Display message history
for msg in current_messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Text input field
prompt = st.chat_input(_('type_message'))

if prompt:
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        oleg_messages = [{"role": "system", "content": OLEG_SYSTEM_PROMPT}]
        for m in current_messages:
            if m["role"] != "system":
                oleg_messages.append(m)
        
        try:
            stream = ollama.chat(
                model=oleg_model,
                messages=oleg_messages,
                stream=True,
                options={"temperature": temperature}
            )
            for chunk in stream:
                content = chunk["message"].get("content", "")
                full_response += content
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except Exception as e:
            full_response = _('ollama_error').format(e)
            placeholder.markdown(full_response)
        
        current_messages.append({"role": "assistant", "content": full_response})
        
        # Voice output
        if st.session_state.tts_enabled:
            speak_text(full_response, st.session_state.tts_voice)
        
        # Check for worker delegation
        match = re.search(r"<DELEGATE_TO_WORKER>(.*?)</DELEGATE_TO_WORKER>", full_response, re.DOTALL)
        if match:
            st.info(_('worker_working'))
            task = match.group(1).strip()
            with st.expander(_('worker_log'), expanded=True):
                result = run_worker(task)
                st.code(result)
                current_messages.append({"role": "assistant", "content": _('worker_result').format(result)})
                st.rerun()

# =========================================================
# INSTRUCTIONS
# =========================================================
st.divider()
st.info(_('instructions'))