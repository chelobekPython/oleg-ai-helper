"""
Олег + Worker — AI Dev System PRO Ultimate - ПОЛНАЯ ВЕРСИЯ
Все функции восстановлены: кнопка +, выбор папки, все возможности
"""

import sys
import os
import re
import tempfile
import subprocess
import shutil
import threading
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque
import logging

try:
    import requests
    import ollama
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QPushButton, QComboBox, QLabel, QSplitter,
        QTreeWidget, QTreeWidgetItem, QTabWidget, QGroupBox, QCheckBox,
        QSlider, QSpinBox, QMessageBox, QProgressBar, QScrollArea,
        QFileDialog, QMenu, QStatusBar, QInputDialog, QFrame, QSizePolicy,
        QLineEdit, QToolBar
    )
    from PyQt6.QtCore import (
        Qt, QThread, pyqtSignal, QTimer, QSize, QSettings,
        QUrl, QPoint, QPropertyAnimation, QEasingCurve
    )
    from PyQt6.QtGui import (
        QFont, QColor, QTextCharFormat, QSyntaxHighlighter,
        QDesktopServices, QAction, QTextCursor, QFontMetrics, QTextOption,
        QIcon
    )
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Установите необходимые библиотеки:")
    print("pip install PyQt6 requests ollama")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
}
QTextEdit, QPlainTextEdit, QTextBrowser {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    border-radius: 5px;
}
QPushButton {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    border-radius: 5px;
    padding: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #3a3a3a;
}
QPushButton:pressed {
    background-color: #1a1a1a;
}
QPushButton#sendBtn {
    background-color: #667eea;
    border: none;
}
QPushButton#sendBtn:hover {
    background-color: #7b8ff5;
}
QComboBox, QSpinBox, QSlider, QLineEdit {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    border-radius: 3px;
    padding: 5px;
}
QTabWidget::pane {
    border: 1px solid #3a3a3a;
    background-color: #1e1e1e;
}
QTabBar::tab {
    background-color: #2d2d2d;
    color: #ffffff;
    padding: 8px 15px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #1e1e1e;
    border-bottom: 2px solid #667eea;
}
QTabBar::tab:hover {
    background-color: #3a3a3a;
}
QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background-color: #667eea;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #7b8ff5;
}
QMenuBar {
    background-color: #2d2d2d;
    color: #ffffff;
}
QMenu {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3a3a3a;
}
QMenu::item:selected {
    background-color: #667eea;
}
QStatusBar {
    background-color: #2d2d2d;
    color: #ffffff;
}
QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QProgressBar {
    border: none;
    height: 3px;
    background: #2d2d2d;
    border-radius: 2px;
}
QProgressBar::chunk {
    background: #667eea;
    border-radius: 2px;
}
QToolBar {
    background-color: #2d2d2d;
    border: none;
    spacing: 5px;
    padding: 5px;
}
"""


class TTSEngine(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.text_queue = deque()
        self.is_running = True
        self.is_speaking = False
        self.piper_path = None
        self.model_path = None
        self.find_piper()
        
    def find_piper(self):
        possible_paths = [
            "./piper/piper.exe", "./piper/piper",
            "C:/piper/piper.exe", "/usr/local/bin/piper",
            "/usr/bin/piper"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                self.piper_path = path
                model_dir = Path(path).parent / "models"
                if model_dir.exists():
                    models = list(model_dir.glob("*.onnx"))
                    if models:
                        self.model_path = str(models[0])
                        logger.info(f"Piper найден: {self.piper_path}")
                        return
        logger.warning("Piper TTS не найден")
        
    def add_text(self, text):
        if self.piper_path and self.model_path and text.strip():
            clean_text = re.sub(r'[*_#`>]', '', text)
            if clean_text:
                self.text_queue.append(clean_text[:500])
                if not self.is_speaking and not self.isRunning():
                    self.start()
                
    def run(self):
        self.is_speaking = True
        while self.is_running and self.text_queue:
            text = self.text_queue.popleft()
            try:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    audio_file = tmp_file.name
                
                cmd = [self.piper_path, "--model", self.model_path, "--output_file", audio_file]
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.stdin.write(text.encode('utf-8'))
                process.stdin.close()
                process.wait(timeout=10)
                
                if Path(audio_file).exists():
                    if sys.platform == "win32":
                        import winsound
                        winsound.PlaySound(audio_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    elif sys.platform == "linux":
                        subprocess.run(["aplay", audio_file], capture_output=True)
                    elif sys.platform == "darwin":
                        subprocess.run(["afplay", audio_file], capture_output=True)
                    self.msleep(100)
                
                Path(audio_file).unlink(missing_ok=True)
            except Exception as e:
                logger.error(f"TTS ошибка: {e}")
        self.is_speaking = False
        self.finished.emit()
        
    def stop(self):
        self.is_running = False
        self.text_queue.clear()


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.keywords = {
            'and', 'as', 'assert', 'async', 'await', 'break', 'class',
            'continue', 'def', 'del', 'elif', 'else', 'except', 'False',
            'finally', 'for', 'from', 'global', 'if', 'import', 'in',
            'is', 'lambda', 'None', 'nonlocal', 'not', 'or', 'pass',
            'raise', 'return', 'True', 'try', 'while', 'with', 'yield'
        }
        
        self.builtins = {
            'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes', 'callable',
            'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir',
            'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format',
            'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex',
            'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
            'list', 'locals', 'map', 'max', 'min', 'next', 'object', 'oct',
            'open', 'ord', 'pow', 'print', 'property', 'range', 'repr', 'reversed',
            'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str',
            'sum', 'super', 'tuple', 'type', 'vars', 'zip'
        }
        
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor(86, 156, 214))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)
        
        self.builtin_format = QTextCharFormat()
        self.builtin_format.setForeground(QColor(78, 201, 176))
        
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor(206, 145, 120))
        
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor(106, 153, 85))
        self.comment_format.setFontItalic(True)
        
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor(181, 206, 168))
        
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor(220, 220, 170))
        self.function_format.setFontWeight(QFont.Weight.Bold)
        
        self.decorator_format = QTextCharFormat()
        self.decorator_format.setForeground(QColor(197, 134, 192))
        
        self.class_format = QTextCharFormat()
        self.class_format.setForeground(QColor(78, 201, 176))
        self.class_format.setFontWeight(QFont.Weight.Bold)
        
    def highlightBlock(self, text):
        try:
            for match in re.finditer(r'^@\w+', text):
                self.setFormat(match.start(), match.end() - match.start(), self.decorator_format)
            
            for word in self.keywords:
                pattern = rf'\b{word}\b'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    self.setFormat(match.start(), match.end() - match.start(), self.keyword_format)
            
            for word in self.builtins:
                pattern = rf'\b{word}\b'
                for match in re.finditer(pattern, text):
                    self.setFormat(match.start(), match.end() - match.start(), self.builtin_format)
            
            in_string = False
            start = 0
            for i, char in enumerate(text):
                if char in '"\'' and (i == 0 or text[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        start = i
                    else:
                        self.setFormat(start, i - start + 1, self.string_format)
                        in_string = False
            
            comment_start = text.find('#')
            if comment_start != -1:
                self.setFormat(comment_start, len(text) - comment_start, self.comment_format)
            
            for match in re.finditer(r'\b\d+\b', text):
                self.setFormat(match.start(), match.end() - match.start(), self.number_format)
            
            for match in re.finditer(r'\bdef\s+(\w+)', text):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.function_format)
            
            for match in re.finditer(r'\bclass\s+(\w+)', text):
                self.setFormat(match.start(1), match.end(1) - match.start(1), self.class_format)
        except Exception as e:
            logger.error(f"Highlight error: {e}")


class MessageWidget(QWidget):
    def __init__(self, role, content, parent=None):
        super().__init__(parent)
        self.role = role
        self.full_content = content
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)
        
        header = QHBoxLayout()
        
        avatar = QLabel()
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {'#667eea' if self.role == 'user' else '#4facfe'};
            border-radius: 18px;
            font-size: 18px;
        """)
        avatar.setText("👤" if self.role == "user" else "🤖")
        
        name_label = QLabel("Вы" if self.role == "user" else "Олег AI")
        name_label.setStyleSheet("color: #e0e0e0; font-size: 14px; font-weight: bold;")
        
        self.time_label = QLabel(datetime.now().strftime("%H:%M"))
        self.time_label.setStyleSheet("color: #888; font-size: 11px;")
        
        header.addWidget(avatar)
        header.addWidget(name_label)
        header.addWidget(self.time_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setPlainText(self.full_content)
        self.content_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {'#2d2d2d' if self.role == 'user' else '#1e1e1e'};
                border-radius: 12px;
                padding: 15px;
                border: 1px solid #3a3a3a;
                font-size: 14px;
                line-height: 1.6;
            }}
        """)
        
        self.content_text.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.content_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        layout.addWidget(self.content_text)
        
        if self.role == "assistant":
            buttons = QHBoxLayout()
            buttons.addStretch()
            
            copy_btn = QPushButton("📋 Копировать")
            copy_btn.setFixedSize(100, 28)
            copy_btn.setStyleSheet("""
                QPushButton {
                    background: #3a3a3a;
                    border: none;
                    border-radius: 5px;
                    font-size: 11px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background: #4a4a4a;
                }
            """)
            copy_btn.clicked.connect(self.copy_content)
            
            speak_btn = QPushButton("🔊 Озвучить")
            speak_btn.setFixedSize(100, 28)
            speak_btn.setStyleSheet("""
                QPushButton {
                    background: #3a3a3a;
                    border: none;
                    border-radius: 5px;
                    font-size: 11px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background: #4a4a4a;
                }
            """)
            speak_btn.clicked.connect(self.speak_content)
            
            buttons.addWidget(copy_btn)
            buttons.addWidget(speak_btn)
            layout.addLayout(buttons)
        
        self.setLayout(layout)
        
    def copy_content(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.full_content)
        
    def speak_content(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'tts_engine'):
                parent.tts_engine.add_text(self.full_content)
                break
            parent = parent.parent()
        
    def update_content(self, new_content):
        try:
            self.full_content = new_content
            self.content_text.setPlainText(new_content)
            cursor = self.content_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.content_text.setTextCursor(cursor)
        except Exception as e:
            logger.error(f"Update content error: {e}")


class WorkerLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.full_log = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QWidget()
        header.setStyleSheet("background-color: #1a3a1a; border-radius: 5px;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title = QLabel("⚙️ Worker Activity Log")
        title.setStyleSheet("font-weight: bold; color: #4caf50; font-size: 13px;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header.setLayout(header_layout)
        layout.addWidget(header)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                border: 1px solid #2a2a2a;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        self.log_text.setMinimumHeight(200)
        
        layout.addWidget(self.log_text)
        
        control_panel = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑️ Очистить лог")
        self.clear_btn.setFixedSize(120, 30)
        self.clear_btn.clicked.connect(self.clear_log)
        
        self.auto_scroll = QCheckBox("Авто-прокрутка")
        self.auto_scroll.setChecked(True)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["Все логи", "Только действия", "Только ошибки", "Только рассуждения"])
        self.log_level.setFixedWidth(130)
        self.log_level.currentTextChanged.connect(self.filter_logs)
        
        control_panel.addWidget(self.clear_btn)
        control_panel.addWidget(self.auto_scroll)
        control_panel.addStretch()
        control_panel.addWidget(QLabel("Фильтр:"))
        control_panel.addWidget(self.log_level)
        
        layout.addLayout(control_panel)
        self.setLayout(layout)
        
    def add_log(self, text, log_type="info"):
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            color_map = {
                "info": "#888888",
                "success": "#4caf50",
                "error": "#f44336",
                "warning": "#ff9800",
                "action": "#2196f3",
                "thinking": "#9c27b0",
                "step": "#00bcd4",
                "file": "#ffc107",
                "command": "#ff5722"
            }
            
            icon_map = {
                "info": "ℹ️",
                "success": "✅",
                "error": "❌",
                "warning": "⚠️",
                "action": "🔧",
                "thinking": "💭",
                "step": "📌",
                "file": "📄",
                "command": "💻"
            }
            
            color = color_map.get(log_type, "#888888")
            icon = icon_map.get(log_type, "•")
            
            formatted = f'<span style="color:#666;">[{timestamp}]</span> <span style="color:{color};">{icon} {text}</span><br>'
            
            self.full_log.append({
                "timestamp": timestamp,
                "text": text,
                "type": log_type,
                "formatted": formatted
            })
            
            current_filter = self.log_level.currentText()
            if self.should_show(current_filter, log_type):
                self.log_text.insertHtml(formatted)
                
                if self.auto_scroll.isChecked():
                    cursor = self.log_text.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.log_text.setTextCursor(cursor)
        except Exception as e:
            logger.error(f"Add log error: {e}")
    
    def should_show(self, filter_type, log_type):
        if filter_type == "Все логи":
            return True
        elif filter_type == "Только действия":
            return log_type in ["action", "file", "command"]
        elif filter_type == "Только ошибки":
            return log_type in ["error"]
        elif filter_type == "Только рассуждения":
            return log_type in ["thinking", "step"]
        return True
    
    def filter_logs(self):
        try:
            self.log_text.clear()
            current_filter = self.log_level.currentText()
            
            for log in self.full_log:
                if self.should_show(current_filter, log["type"]):
                    self.log_text.insertHtml(log["formatted"])
            
            if self.auto_scroll.isChecked():
                cursor = self.log_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.log_text.setTextCursor(cursor)
        except Exception as e:
            logger.error(f"Filter logs error: {e}")
        
    def clear_log(self):
        try:
            self.log_text.clear()
            self.full_log.clear()
            self.add_log("🧹 Лог очищен", "info")
        except Exception as e:
            logger.error(f"Clear log error: {e}")


class RealAIWorker(QThread):
    response_chunk = pyqtSignal(str)
    response_complete = pyqtSignal(str)
    worker_log = pyqtSignal(str, str)
    worker_progress = pyqtSignal(str)
    worker_step = pyqtSignal(int, int, str)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.messages = []
        self.model = "llama3.2"
        self.worker_model = "qwen2.5-coder:7b"
        self.temperature = 0.2
        self.max_steps = 15
        self.workspace = "./workspace"
        self.allow_shell = False
        self.is_running = True
        
    def configure(self, messages, model, worker_model, temperature, max_steps, workspace, allow_shell):
        self.messages = messages
        self.model = model
        self.worker_model = worker_model
        self.temperature = temperature
        self.max_steps = max_steps
        self.workspace = workspace
        self.allow_shell = allow_shell
        
    def stop(self):
        self.is_running = False
        
    def safe_emit_log(self, text, log_type="info"):
        try:
            self.worker_log.emit(text, log_type)
        except Exception as e:
            logger.error(f"Emit log error: {e}")
        
    def run(self):
        try:
            last_user_msg = ""
            for msg in reversed(self.messages):
                if msg.get('role') == 'user':
                    last_user_msg = msg.get('content', '')
                    break
            
            if not last_user_msg:
                self.error_occurred.emit("Нет сообщения для обработки")
                return
            
            system_prompt = """
Ты SWAGY — профессиональный AI помощник разработчика.

ПРАВИЛА РАБОТЫ:
1. Всегда анализируй задачу и определяй, что нужно сделать
2. Если задача требует создания/изменения файлов или написания кода — делегируй Worker'у
3. Отвечай пользователю понятно и структурированно
4. Тебе ЗАПРЕЩЕНО писать код самостоятельно не под каким предлогом. Главная твоя цель - это делегировать!
5. Если задача пользователя требует написания кода или действия на его устройстве - делегируй!
6. Чтобы делегировать используй тэг <DELEGATE_TO_WORKER>!

<DELEGATE_TO_WORKER>
[Четкое описание задачи для Worker включая:]
- Что нужно создать/изменить
- Требования к реализации
- Ожидаемый результат
- Необходимые файлы и их содержимое
- Конкретные действия для выполнения воркеру (пример: сначала создай файл, а затем выполни shell команду)
- Ты не пишешь никакой код (даже просто ради примера)
</DELEGATE_TO_WORKER>

Worker может:
- Создавать, читать, редактировать файлы
- Выполнять Python код
- Выполнять shell команды (если разрешено)
- Работать с файловой системой
- Просматривать список файлов в директории"""
            
            full_response = ""
            self.response_chunk.emit("🤔 **Анализирую задачу...**\n\n")
            
            try:
                stream = ollama.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": last_user_msg}
                    ],
                    options={"temperature": self.temperature},
                    stream=True
                )
                
                for chunk in stream:
                    if not self.is_running:
                        return
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        full_response += content
                        self.response_chunk.emit(content)
                
                delegate_match = re.search(r'<DELEGATE_TO_WORKER>(.*?)</DELEGATE_TO_WORKER>', 
                                          full_response, re.DOTALL | re.IGNORECASE)
                
                if delegate_match and self.is_running:
                    task = delegate_match.group(1).strip()
                    
                    self.safe_emit_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
                    self.safe_emit_log("🚀 Worker запущен", "success")
                    self.safe_emit_log(f"📝 Получена задача: {task[:200]}...", "action")
                    self.safe_emit_log(f"📁 Рабочая директория: {self.workspace}", "info")
                    self.safe_emit_log(f"⚙️ Максимум шагов: {self.max_steps}", "info")
                    self.safe_emit_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
                    
                    self.worker_progress.emit(f"\n\n---\n### 🤖 **Worker приступил к выполнению задачи**\n**Рабочая директория:** `{self.workspace}`\n---\n\n")
                    
                    worker_result = self.run_worker_task(task)
                    
                    self.safe_emit_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
                    self.safe_emit_log("✅ Worker завершил работу", "success")
                    self.safe_emit_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
                    
                    self.worker_progress.emit(f"\n\n---\n### ✅ **Worker завершил выполнение**\n---\n\n")
                    if worker_result:
                        self.worker_progress.emit(worker_result)
                
                self.response_complete.emit(full_response)
                
            except Exception as e:
                error_msg = f"Ошибка AI: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                
        except Exception as e:
            error_msg = f"Критическая ошибка: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            self.finished.emit()
    
    def run_worker_task(self, task):
        try:
            workspace_path = Path(self.workspace)
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            logs = []
            actions_log = []
            
            system_prompt = f"""Ты Worker — эксперт по разработке с доступом к файловой системе.

ДОСТУПНЫЕ ТЭГИ:

1. <WRITE>filename.py
содержимое файла
</WRITE>

2. <READ>filename.py</READ>

3. <APPEND>filename.py
добавляемый код
</APPEND>

4. <EDIT>filename.py
поиск: текст для поиска
замена: текст для замены
</EDIT>

5. <PYTHON>
print("Hello World")
</PYTHON>

6. <SHELL>ls -la</SHELL> {"(РАЗРЕШЕНО)" if self.allow_shell else "(ЗАПРЕЩЕНО)"}

7. <LIST>.</LIST> - показывает список файлов и папок в указанной директории (путь относительно рабочей директории)

Рабочая директория: {self.workspace}
Все пути указывай относительно этой директории.

Для завершения работы просто выполни все необходимые действия. Worker автоматически завершится, когда задача будет выполнена."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task}
            ]
            
            for step in range(self.max_steps):
                if not self.is_running:
                    break
                
                try:
                    step_num = step + 1
                    step_desc = f"Шаг {step_num}/{self.max_steps}"
                    self.worker_step.emit(step_num, self.max_steps, step_desc)
                    self.safe_emit_log(f"📌 {step_desc} - Worker анализирует...", "step")
                    
                    self.safe_emit_log(f"💭 Worker размышляет...", "thinking")
                    
                    response = ollama.chat(
                        model=self.worker_model,
                        messages=messages,
                        options={"temperature": 0.2}
                    )
                    content = response['message']['content']
                    
                    for line in content.split('\n')[:3]:
                        if line.strip():
                            self.safe_emit_log(f"   {line[:100]}", "thinking")
                    
                    logs.append(f"--- Шаг {step + 1} ---\n{content}\n")
                    
                    # LIST - новая команда для просмотра содержимого директории
                    list_matches = re.findall(r'<LIST>(.*?)</LIST>', content, re.DOTALL)
                    for dir_path in list_matches:
                        dir_path = dir_path.strip() if dir_path.strip() else "."
                        target_path = workspace_path / dir_path
                        
                        self.safe_emit_log(f"📂 Просмотр директории: {dir_path}", "file")
                        
                        if target_path.exists() and target_path.is_dir():
                            try:
                                items = []
                                for item in sorted(target_path.iterdir()):
                                    if item.name.startswith('.') and item.name != '.':
                                        continue
                                    item_type = "📁" if item.is_dir() else "📄"
                                    items.append(f"{item_type} {item.name}")
                                
                                if items:
                                    dir_listing = "\n".join(items)
                                    result = f"**Содержимое директории `{dir_path}`:**\n```\n{dir_listing}\n```\nВсего элементов: {len(items)}"
                                    self.safe_emit_log(f"✅ Найдено {len(items)} элементов", "success")
                                else:
                                    result = f"**Директория `{dir_path}` пуста**"
                                    self.safe_emit_log(f"⚠️ Директория пуста", "warning")
                                
                                logs.append(f"📂 Просмотрена директория: {dir_path}\n")
                                actions_log.append(f"  📂 Просмотрена: {dir_path}")
                                messages.append({"role": "assistant", "content": result})
                            except Exception as e:
                                self.safe_emit_log(f"❌ Ошибка чтения директории: {str(e)}", "error")
                                messages.append({"role": "assistant", "content": f"Ошибка при чтении директории: {e}"})
                        else:
                            self.safe_emit_log(f"⚠️ Директория не найдена: {dir_path}", "warning")
                            messages.append({"role": "assistant", "content": f"Директория {dir_path} не найдена"})
                    
                    # READ
                    read_matches = re.findall(r'<READ>(.*?)</READ>', content, re.DOTALL)
                    for filename in read_matches:
                        filename = filename.strip()
                        if filename:
                            filepath = workspace_path / filename
                            self.safe_emit_log(f"📖 Чтение файла: {filename}", "file")
                            
                            if filepath.exists() and filepath.is_file():
                                try:
                                    file_content = filepath.read_text(encoding='utf-8')
                                    preview = file_content[:300] + ("\n..." if len(file_content) > 300 else "")
                                    self.safe_emit_log(f"✅ Файл прочитан", "success")
                                    result = f"**Содержимое {filename}:**\n```\n{preview}\n```"
                                    logs.append(f"✅ Прочитан: {filename}\n")
                                    actions_log.append(f"  📖 Прочитан: {filename}")
                                    messages.append({"role": "assistant", "content": result})
                                except Exception as e:
                                    self.safe_emit_log(f"❌ Ошибка чтения: {str(e)}", "error")
                                    messages.append({"role": "assistant", "content": f"Ошибка при чтении: {e}"})
                            else:
                                self.safe_emit_log(f"⚠️ Файл не найден: {filename}", "warning")
                    
                    # WRITE
                    write_matches = re.findall(r'<WRITE>(.*?)\n(.*?)</WRITE>', content, re.DOTALL)
                    for match in write_matches:
                        if len(match) >= 2:
                            filename = match[0].strip()
                            file_content = match[1].strip()
                            if filename and file_content:
                                try:
                                    filepath = workspace_path / filename
                                    filepath.parent.mkdir(parents=True, exist_ok=True)
                                    filepath.write_text(file_content, encoding='utf-8')
                                    self.safe_emit_log(f"✍️ Создан/обновлен файл: {filename}", "action")
                                    logs.append(f"✅ Создан/обновлен: {filename}\n")
                                    actions_log.append(f"  ✍️ Записан: {filename}")
                                    messages.append({"role": "assistant", "content": f"✅ Файл {filename} успешно создан/обновлен"})
                                except Exception as e:
                                    self.safe_emit_log(f"❌ Ошибка записи: {str(e)}", "error")
                    
                    # APPEND
                    append_matches = re.findall(r'<APPEND>(.*?)\n(.*?)</APPEND>', content, re.DOTALL)
                    for match in append_matches:
                        if len(match) >= 2:
                            filename = match[0].strip()
                            append_content = match[1].strip()
                            if filename and append_content:
                                filepath = workspace_path / filename
                                if filepath.exists():
                                    try:
                                        with open(filepath, 'a', encoding='utf-8') as f:
                                            f.write('\n' + append_content)
                                        self.safe_emit_log(f"➕ Добавлено в файл: {filename}", "action")
                                        logs.append(f"➕ Добавлено в: {filename}\n")
                                        actions_log.append(f"  ➕ Добавлено в: {filename}")
                                        messages.append({"role": "assistant", "content": f"➕ Данные добавлены в {filename}"})
                                    except Exception as e:
                                        self.safe_emit_log(f"❌ Ошибка добавления: {str(e)}", "error")
                                else:
                                    self.safe_emit_log(f"⚠️ Файл {filename} не существует", "warning")
                    
                    # EDIT
                    edit_matches = re.findall(r'<EDIT>(.*?)поиск:(.*?)замена:(.*?)</EDIT>', content, re.DOTALL)
                    for match in edit_matches:
                        if len(match) >= 3:
                            filename = match[0].strip()
                            search_text = match[1].strip()
                            replace_text = match[2].strip()
                            if filename and search_text:
                                filepath = workspace_path / filename
                                if filepath.exists():
                                    try:
                                        original = filepath.read_text(encoding='utf-8')
                                        if search_text in original:
                                            modified = original.replace(search_text, replace_text)
                                            filepath.write_text(modified, encoding='utf-8')
                                            self.safe_emit_log(f"✏️ Отредактирован файл: {filename}", "action")
                                            logs.append(f"✏️ Отредактирован: {filename}\n")
                                            actions_log.append(f"  ✏️ Отредактирован: {filename}")
                                            messages.append({"role": "assistant", "content": f"✏️ Файл {filename} отредактирован"})
                                        else:
                                            self.safe_emit_log(f"⚠️ Текст для замены не найден", "warning")
                                    except Exception as e:
                                        self.safe_emit_log(f"❌ Ошибка редактирования: {str(e)}", "error")
                    
                    # SHELL
                    if self.allow_shell:
                        shell_matches = re.findall(r'<SHELL>(.*?)</SHELL>', content, re.DOTALL)
                        for cmd in shell_matches:
                            cmd = cmd.strip()
                            dangerous = ['rm -rf /', 'dd if=', 'mkfs', 'format']
                            if cmd and not any(d in cmd.lower() for d in dangerous):
                                self.safe_emit_log(f"💻 Выполнение команды: {cmd}", "command")
                                try:
                                    result = subprocess.run(cmd, shell=True, capture_output=True,
                                                           text=True, timeout=30, cwd=str(workspace_path))
                                    output = result.stdout[:300] if result.stdout else result.stderr[:300]
                                    if result.returncode == 0:
                                        self.safe_emit_log(f"✅ Команда выполнена", "success")
                                    else:
                                        self.safe_emit_log(f"⚠️ Ошибка выполнения", "warning")
                                    logs.append(f"💻 Выполнена команда: {cmd}\n")
                                    actions_log.append(f"  💻 Выполнено: {cmd[:50]}")
                                    messages.append({"role": "assistant", "content": f"Результат:\n{output}"})
                                except Exception as e:
                                    self.safe_emit_log(f"❌ Ошибка: {str(e)}", "error")
                    
                    # PYTHON
                    python_matches = re.findall(r'<PYTHON>(.*?)</PYTHON>', content, re.DOTALL)
                    for python_code in python_matches:
                        python_code = python_code.strip()
                        if python_code:
                            self.safe_emit_log(f"🐍 Выполнение Python кода", "action")
                            try:
                                result = subprocess.run([sys.executable, '-c', python_code], 
                                                       capture_output=True, text=True, timeout=30, 
                                                       cwd=str(workspace_path))
                                output = result.stdout[:300] if result.stdout else result.stderr[:300]
                                if result.returncode == 0:
                                    self.safe_emit_log(f"✅ Код выполнен", "success")
                                else:
                                    self.safe_emit_log(f"⚠️ Ошибка выполнения", "error")
                                logs.append(f"🐍 Выполнен Python код\n")
                                actions_log.append(f"  🐍 Выполнен Python код")
                                messages.append({"role": "assistant", "content": f"Результат:\n{output}"})
                            except Exception as e:
                                self.safe_emit_log(f"❌ Ошибка: {str(e)}", "error")
                    
                    # Проверяем, выполнены ли все действия
                    if any([write_matches, edit_matches, append_matches, list_matches, read_matches, python_matches, shell_matches]):
                        messages.append({"role": "assistant", "content": content})
                        # Проверяем, нужно ли продолжать
                        messages.append({"role": "user", "content": "Если задача выполнена полностью, просто заверши работу. Если нужно сделать еще что-то, продолжай."})
                    else:
                        messages.append({"role": "assistant", "content": content})
                        messages.append({"role": "user", "content": "Продолжи выполнение задачи. Используй доступные теги для работы с файлами."})
                    
                    # Ограничиваем длину истории
                    if len(messages) > 15:
                        messages = [messages[0]] + messages[-14:]
                    
                    # Автоматическое завершение, если нет активности
                    if not any([write_matches, edit_matches, append_matches, list_matches, read_matches, python_matches, shell_matches]):
                        # Если нет действий на шаге, возможно задача выполнена
                        if step > 0 and step_num >= 3:
                            self.safe_emit_log("✅ Worker завершил работу (нет активных действий)", "success")
                            break
                
                except Exception as e:
                    logger.error(f"Worker step error: {e}")
                    self.safe_emit_log(f"❌ Ошибка на шаге {step+1}: {str(e)}", "error")
                    logs.append(f"❌ Ошибка: {str(e)}\n")
                    continue
            
            if len(actions_log) > 0:
                self.safe_emit_log(f"\n📊 Выполненные действия:", "info")
                for action in actions_log:
                    self.safe_emit_log(f"  {action}", "info")
                self.safe_emit_log(f"\n✅ Всего выполнено действий: {len(actions_log)}", "success")
            else:
                logs.append("⚠️ Worker не выполнил никаких действий")
                self.safe_emit_log(f"⚠️ Worker не выполнил никаких действий за {self.max_steps} шагов", "warning")
            
            return '\n'.join(logs)
            
        except Exception as e:
            error_msg = f"Критическая ошибка Worker: {str(e)}"
            logger.error(error_msg)
            self.safe_emit_log(error_msg, "error")
            return f"❌ Ошибка выполнения: {str(e)}"


class ChatTab(QWidget):
    def __init__(self, tab_id, main_window):
        super().__init__()
        self.tab_id = tab_id
        self.main_window = main_window
        self.messages = []
        self.current_assistant_message = ""
        self.current_assistant_widget = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setStyleSheet("border: none; background-color: #1e1e1e;")
        
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: #1e1e1e;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(20)
        self.chat_layout.addStretch()
        
        self.chat_area.setWidget(self.chat_container)
        chat_layout.addWidget(self.chat_area)
        
        indicators = QHBoxLayout()
        self.typing_label = QLabel("🤖 Олег печатает...")
        self.typing_label.setVisible(False)
        self.typing_label.setStyleSheet("background: #2d2d2d; padding: 8px 15px; border-radius: 20px; font-size: 12px;")
        
        self.worker_step_label = QLabel("")
        self.worker_step_label.setVisible(False)
        self.worker_step_label.setStyleSheet("background: #1e3a3a; padding: 8px 15px; border-radius: 20px; color: #4caf50; font-size: 12px;")
        
        indicators.addWidget(self.typing_label)
        indicators.addWidget(self.worker_step_label)
        indicators.addStretch()
        chat_layout.addLayout(indicators)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        chat_layout.addWidget(self.progress_bar)
        
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-top: 1px solid #3a3a3a;
            }
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 15, 20, 15)
        
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("💬 Введите вашу задачу... (Ctrl+Enter для отправки)")
        self.input_field.setMaximumHeight(120)
        self.input_field.setMinimumHeight(80)
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 10px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        
        buttons = QHBoxLayout()
        self.send_btn = QPushButton("📤 Отправить")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setMinimumHeight(40)
        self.send_btn.clicked.connect(self.send_message)
        
        self.clear_btn = QPushButton("🗑️ Очистить")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear_chat)
        
        buttons.addWidget(self.clear_btn)
        buttons.addStretch()
        buttons.addWidget(self.send_btn)
        
        input_layout.addWidget(self.input_field)
        input_layout.addLayout(buttons)
        chat_layout.addWidget(input_frame)
        
        self.worker_log = WorkerLogWidget()
        self.worker_log.setVisible(True)
        
        main_splitter.addWidget(chat_container)
        main_splitter.addWidget(self.worker_log)
        main_splitter.setSizes([500, 250])
        main_splitter.setHandleWidth(2)
        
        layout.addWidget(main_splitter)
        self.setLayout(layout)
        
        self.add_message("assistant", 
            f"👋 **Привет! Я Олег — ваш AI помощник разработчика.**\n\n"
            f"📁 **Текущая рабочая папка:** `{self.main_window.workspace_path}`\n\n"
            f"✨ **Мои возможности:**\n"
            f"• Создавать и редактировать файлы\n"
            f"• Писать код на Python\n"
            f"• Выполнять сложные задачи через Worker\n\n"
            f"💡 **Просто опишите, что нужно сделать!**")
    
    def add_message(self, role, content):
        try:
            self.typing_label.setVisible(False)
            message = MessageWidget(role, content)
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, message)
            
            QTimer.singleShot(50, lambda: self.chat_area.verticalScrollBar().setValue(
                self.chat_area.verticalScrollBar().maximum()))
            
            self.messages.append({"role": role, "content": content})
            return message
        except Exception as e:
            logger.error(f"Add message error: {e}")
            return None
    
    def update_last_message(self, new_content):
        try:
            for i in range(self.chat_layout.count() - 2, -1, -1):
                item = self.chat_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and isinstance(widget, MessageWidget) and widget.role == "assistant":
                        widget.update_content(new_content)
                        QTimer.singleShot(10, lambda: self.chat_area.verticalScrollBar().setValue(
                            self.chat_area.verticalScrollBar().maximum()))
                        return widget
            return None
        except Exception as e:
            logger.error(f"Update message error: {e}")
            return None
    
    def send_message(self):
        try:
            message = self.input_field.toPlainText().strip()
            if not message:
                return
            
            self.add_message("user", message)
            self.input_field.clear()
            
            self.start_generation()
            
            messages_history = []
            for i in range(self.chat_layout.count() - 1):
                item = self.chat_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and isinstance(widget, MessageWidget):
                        role = "user" if widget.role == "user" else "assistant"
                        messages_history.append({"role": role, "content": widget.full_content})
            
            self.main_window.process_with_ai(self.tab_id, messages_history)
        except Exception as e:
            logger.error(f"Send message error: {e}")
            self.on_ai_error(str(e))
    
    def clear_chat(self):
        try:
            reply = QMessageBox.question(self, "Очистить чат", "Очистить все сообщения?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                while self.chat_layout.count() > 1:
                    item = self.chat_layout.takeAt(0)
                    if item and item.widget():
                        item.widget().deleteLater()
                self.messages.clear()
                self.worker_log.clear_log()
                self.add_message("assistant", f"✨ Чат очищен! Рабочая папка: `{self.main_window.workspace_path}`")
        except Exception as e:
            logger.error(f"Clear chat error: {e}")
    
    def start_generation(self):
        try:
            self.send_btn.setEnabled(False)
            self.typing_label.setVisible(True)
            self.current_assistant_message = ""
            self.current_assistant_widget = None
            if hasattr(self.main_window, 'worker_status'):
                self.main_window.worker_status.setText("🔄 AI генерирует ответ...")
        except Exception as e:
            logger.error(f"Start generation error: {e}")
    
    def finish_generation(self):
        try:
            self.send_btn.setEnabled(True)
            self.typing_label.setVisible(False)
            self.worker_step_label.setVisible(False)
            self.progress_bar.setVisible(False)
            self.current_assistant_widget = None
            if hasattr(self.main_window, 'worker_status'):
                self.main_window.worker_status.setText("💤 Готов")
        except Exception as e:
            logger.error(f"Finish generation error: {e}")
    
    def on_ai_chunk(self, chunk):
        try:
            self.current_assistant_message += chunk
            if self.current_assistant_widget is None:
                self.current_assistant_widget = self.add_message("assistant", self.current_assistant_message)
            else:
                self.update_last_message(self.current_assistant_message)
        except Exception as e:
            logger.error(f"AI chunk error: {e}")
    
    def on_ai_complete(self, full_response):
        try:
            self.current_assistant_message = full_response
            self.update_last_message(full_response)
            self.finish_generation()
        except Exception as e:
            logger.error(f"AI complete error: {e}")
    
    def on_worker_log(self, text, log_type):
        try:
            self.worker_log.add_log(text, log_type)
        except Exception as e:
            logger.error(f"Worker log error: {e}")
    
    def on_worker_progress(self, progress):
        try:
            self.current_assistant_message += progress
            self.update_last_message(self.current_assistant_message)
        except Exception as e:
            logger.error(f"Worker progress error: {e}")
    
    def on_worker_step(self, current, total, description):
        try:
            self.worker_step_label.setText(f"⚙️ Worker: {description}")
            self.worker_step_label.setVisible(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            
            if current == total:
                QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))
        except Exception as e:
            logger.error(f"Worker step error: {e}")
    
    def on_ai_error(self, error):
        try:
            self.add_message("assistant", f"❌ **Ошибка:** {error}")
            self.finish_generation()
        except Exception as e:
            logger.error(f"AI error callback error: {e}")


class FilesTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.current_file = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        new_file_btn = QPushButton("📄 Новый файл")
        new_file_btn.clicked.connect(self.create_new_file)
        new_folder_btn = QPushButton("📁 Новая папка")
        new_folder_btn.clicked.connect(self.create_new_folder)
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.refresh_files)
        open_btn = QPushButton("📂 Открыть папку")
        open_btn.clicked.connect(self.open_workspace)
        choose_workspace_btn = QPushButton("📁 Выбрать рабочую папку")
        choose_workspace_btn.clicked.connect(self.choose_workspace)
        
        for btn in [new_file_btn, new_folder_btn, refresh_btn, open_btn, choose_workspace_btn]:
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #2d2d2d; border-radius: 5px; padding: 5px;")
        info_layout = QHBoxLayout(info_frame)
        self.workspace_label = QLabel(f"📁 Текущая рабочая папка: {self.main_window.workspace_path}")
        self.workspace_label.setStyleSheet("color: #aaa; font-size: 11px;")
        info_layout.addWidget(self.workspace_label)
        info_layout.addStretch()
        layout.addWidget(info_frame)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("📁 Файлы проекта")
        self.file_tree.setMinimumWidth(300)
        self.file_tree.itemDoubleClicked.connect(self.open_file)
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_context_menu)
        splitter.addWidget(self.file_tree)
        
        editor_widget = QWidget()
        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        self.file_name_label = QLabel("📄 Нет файла")
        editor_layout.addWidget(self.file_name_label)
        
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Courier New", 11))
        self.highlighter = PythonHighlighter(self.code_editor.document())
        
        editor_buttons = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.save_file)
        run_btn = QPushButton("▶️ Выполнить")
        run_btn.clicked.connect(self.run_code)
        
        editor_buttons.addWidget(save_btn)
        editor_buttons.addWidget(run_btn)
        editor_buttons.addStretch()
        
        editor_layout.addWidget(self.code_editor)
        editor_layout.addLayout(editor_buttons)
        editor_widget.setLayout(editor_layout)
        splitter.addWidget(editor_widget)
        
        splitter.setSizes([350, 650])
        layout.addWidget(splitter)
        
        self.setLayout(layout)
        self.refresh_files()
    
    def choose_workspace(self):
        new_path = QFileDialog.getExistingDirectory(
            self, 
            "Выберите рабочую папку", 
            str(self.main_window.workspace_path),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if new_path:
            self.main_window.workspace_path = Path(new_path)
            self.main_window.workspace_path.mkdir(parents=True, exist_ok=True)
            self.main_window.settings.setValue("workspace", str(self.main_window.workspace_path))
            self.update_workspace_display()
            self.main_window.status_bar.showMessage(f"Рабочая папка изменена: {self.main_window.workspace_path}", 3000)
    
    def update_workspace_display(self):
        self.workspace_label.setText(f"📁 Текущая рабочая папка: {self.main_window.workspace_path}")
        self.refresh_files()
    
    def refresh_files(self):
        try:
            self.file_tree.clear()
            self.populate_tree(self.main_window.workspace_path, self.file_tree.invisibleRootItem())
        except Exception as e:
            logger.error(f"Refresh files error: {e}")
    
    def populate_tree(self, path, parent_item):
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith('.') or item.name == '__pycache__':
                    continue
                
                tree_item = QTreeWidgetItem(parent_item)
                tree_item.setText(0, item.name)
                tree_item.setData(0, Qt.ItemDataRole.UserRole, str(item))
                
                if item.is_dir():
                    self.populate_tree(item, tree_item)
        except PermissionError:
            pass
        except Exception as e:
            logger.error(f"Populate tree error: {e}")
    
    def open_file(self, item, column):
        try:
            path = Path(item.data(0, Qt.ItemDataRole.UserRole))
            if path.is_file():
                content = path.read_text(encoding='utf-8')
                self.code_editor.setText(content)
                self.current_file = path
                self.file_name_label.setText(f"📄 {path.name}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть: {e}")
    
    def show_context_menu(self, position):
        item = self.file_tree.itemAt(position)
        if item:
            menu = QMenu()
            open_action = menu.addAction("📂 Открыть")
            delete_action = menu.addAction("🗑️ Удалить")
            rename_action = menu.addAction("✏️ Переименовать")
            
            action = menu.exec(self.file_tree.viewport().mapToGlobal(position))
            
            if action == open_action:
                self.open_file(item, 0)
            elif action == delete_action:
                self.delete_file(item)
            elif action == rename_action:
                self.rename_file(item)
    
    def delete_file(self, item):
        try:
            path = Path(item.data(0, Qt.ItemDataRole.UserRole))
            reply = QMessageBox.question(self, "Подтверждение", f"Удалить {path.name}?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)
                self.refresh_files()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось удалить: {e}")
    
    def rename_file(self, item):
        try:
            old_path = Path(item.data(0, Qt.ItemDataRole.UserRole))
            new_name, ok = QInputDialog.getText(self, "Переименовать", "Новое имя:", text=old_path.name)
            if ok and new_name:
                new_path = old_path.parent / new_name
                old_path.rename(new_path)
                self.refresh_files()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось переименовать: {e}")
    
    def create_new_file(self):
        try:
            name, ok = QInputDialog.getText(self, "Новый файл", "Имя файла:")
            if ok and name:
                filepath = self.main_window.workspace_path / name
                filepath.write_text("", encoding='utf-8')
                self.refresh_files()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать: {e}")
    
    def create_new_folder(self):
        try:
            name, ok = QInputDialog.getText(self, "Новая папка", "Имя папки:")
            if ok and name:
                folderpath = self.main_window.workspace_path / name
                folderpath.mkdir(parents=True, exist_ok=True)
                self.refresh_files()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать: {e}")
    
    def open_workspace(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.main_window.workspace_path.absolute())))
    
    def save_file(self):
        try:
            if self.current_file:
                self.current_file.write_text(self.code_editor.toPlainText(), encoding='utf-8')
                self.main_window.status_bar.showMessage(f"Сохранен: {self.current_file.name}", 3000)
                self.code_editor.document().setModified(False)
            else:
                filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", 
                                                          str(self.main_window.workspace_path), 
                                                          "Python Files (*.py);;All Files (*.*)")
                if filepath:
                    self.current_file = Path(filepath)
                    self.save_file()
                    self.refresh_files()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить: {e}")
    
    def run_code(self):
        try:
            code = self.code_editor.toPlainText()
            if not code.strip():
                return
            
            self.main_window.switch_to_chat_tab()
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run([sys.executable, temp_file], capture_output=True, text=True, timeout=30)
            output = result.stdout if result.stdout else result.stderr
            
            if output:
                self.main_window.add_message_to_current_chat("assistant", 
                    f"📊 **Результат:**\n```python\n{output[:1000]}\n```")
            else:
                self.main_window.add_message_to_current_chat("assistant", "✅ Код выполнен успешно")
            
            os.unlink(temp_file)
        except Exception as e:
            self.main_window.add_message_to_current_chat("assistant", f"❌ **Ошибка:**\n```\n{str(e)}\n```")


class SettingsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        workspace_group = QGroupBox("📁 Рабочая папка")
        workspace_layout = QVBoxLayout()
        
        workspace_path_layout = QHBoxLayout()
        self.workspace_path_edit = QLineEdit()
        self.workspace_path_edit.setText(str(self.main_window.workspace_path))
        self.workspace_path_edit.setReadOnly(True)
        
        choose_workspace_btn = QPushButton("📂 Выбрать")
        choose_workspace_btn.clicked.connect(self.choose_workspace)
        
        open_workspace_btn = QPushButton("📁 Открыть")
        open_workspace_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.main_window.workspace_path))))
        
        workspace_path_layout.addWidget(QLabel("Путь:"))
        workspace_path_layout.addWidget(self.workspace_path_edit)
        workspace_path_layout.addWidget(choose_workspace_btn)
        workspace_path_layout.addWidget(open_workspace_btn)
        
        workspace_layout.addLayout(workspace_path_layout)
        workspace_group.setLayout(workspace_layout)
        layout.addWidget(workspace_group)
        
        models_group = QGroupBox("🤖 Модели AI")
        models_layout = QVBoxLayout()
        
        oleg_layout = QHBoxLayout()
        oleg_layout.addWidget(QLabel("Модель Олега:"))
        self.oleg_model = QComboBox()
        oleg_layout.addWidget(self.oleg_model)
        oleg_layout.addStretch()
        models_layout.addLayout(oleg_layout)
        
        worker_layout = QHBoxLayout()
        worker_layout.addWidget(QLabel("Модель Worker:"))
        self.worker_model = QComboBox()
        worker_layout.addWidget(self.worker_model)
        worker_layout.addStretch()
        models_layout.addLayout(worker_layout)
        
        load_btn = QPushButton("🔄 Загрузить модели")
        load_btn.clicked.connect(self.main_window.load_models)
        models_layout.addWidget(load_btn)
        
        models_group.setLayout(models_layout)
        layout.addWidget(models_group)
        
        params_group = QGroupBox("⚙️ Параметры")
        params_layout = QVBoxLayout()
        
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(20)
        self.temp_label = QLabel("0.20")
        self.temp_slider.valueChanged.connect(lambda v: self.temp_label.setText(f"{v/100:.2f}"))
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_label)
        params_layout.addLayout(temp_layout)
        
        steps_layout = QHBoxLayout()
        steps_layout.addWidget(QLabel("Max Worker Steps:"))
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(1, 30)
        self.steps_spin.setValue(15)
        steps_layout.addWidget(self.steps_spin)
        steps_layout.addStretch()
        params_layout.addLayout(steps_layout)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        extra_group = QGroupBox("🔧 Дополнительно")
        extra_layout = QVBoxLayout()
        
        self.allow_shell = QCheckBox("Разрешить shell команды")
        self.auto_save = QCheckBox("Автосохранение файлов")
        self.auto_save.setChecked(True)
        self.tts_enabled = QCheckBox("Включить TTS озвучку")
        
        extra_layout.addWidget(self.allow_shell)
        extra_layout.addWidget(self.auto_save)
        extra_layout.addWidget(self.tts_enabled)
        
        extra_group.setLayout(extra_layout)
        layout.addWidget(extra_group)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.save_settings)
        reset_btn = QPushButton("🔄 Сбросить")
        reset_btn.clicked.connect(self.reset_settings)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def choose_workspace(self):
        new_path = QFileDialog.getExistingDirectory(
            self, 
            "Выберите рабочую папку", 
            str(self.main_window.workspace_path),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if new_path:
            self.main_window.workspace_path = Path(new_path)
            self.main_window.workspace_path.mkdir(parents=True, exist_ok=True)
            self.main_window.settings.setValue("workspace", str(self.main_window.workspace_path))
            self.workspace_path_edit.setText(str(self.main_window.workspace_path))
            
            for i in range(self.main_window.tab_widget.count()):
                widget = self.main_window.tab_widget.widget(i)
                if isinstance(widget, FilesTab):
                    widget.update_workspace_display()
                    break
            
            self.main_window.status_bar.showMessage(f"Рабочая папка изменена: {self.main_window.workspace_path}", 3000)
    
    def save_settings(self):
        try:
            self.main_window.settings.setValue("workspace", str(self.main_window.workspace_path))
            self.main_window.settings.setValue("oleg_model", self.oleg_model.currentText())
            self.main_window.settings.setValue("worker_model", self.worker_model.currentText())
            self.main_window.settings.setValue("temperature", self.temp_slider.value())
            self.main_window.settings.setValue("max_steps", self.steps_spin.value())
            self.main_window.settings.setValue("allow_shell", self.allow_shell.isChecked())
            self.main_window.settings.setValue("auto_save", self.auto_save.isChecked())
            self.main_window.settings.setValue("tts_enabled", self.tts_enabled.isChecked())
            
            self.main_window.temp_value = self.temp_slider.value() / 100
            self.main_window.max_steps_value = self.steps_spin.value()
            self.main_window.allow_shell = self.allow_shell.isChecked()
            self.main_window.on_tts_toggled(self.tts_enabled.isChecked())
            
            QMessageBox.information(self, "Настройки", "Настройки сохранены!")
        except Exception as e:
            logger.error(f"Save settings error: {e}")
    
    def reset_settings(self):
        try:
            reply = QMessageBox.question(self, "Сброс", "Сбросить настройки?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.temp_slider.setValue(20)
                self.steps_spin.setValue(15)
                self.allow_shell.setChecked(False)
                self.auto_save.setChecked(True)
                self.tts_enabled.setChecked(False)
                self.save_settings()
        except Exception as e:
            logger.error(f"Reset settings error: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Олег + Worker — AI Dev System PRO")
        self.setGeometry(100, 100, 1400, 900)
        
        self.settings = QSettings("OlegWorker", "AI_System")
        saved_workspace = self.settings.value("workspace", "./workspace")
        self.workspace_path = Path(saved_workspace)
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        self.temp_value = 0.2
        self.max_steps_value = 15
        self.allow_shell = False
        
        self.chat_tabs = {}
        self.next_tab_id = 1
        self.active_workers = {}
        
        self.tts_engine = TTSEngine()
        
        self.init_ui()
        self.load_models()
        self.check_ollama_status()
        
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_ollama_status)
        self.status_timer.start(30000)
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        central.setLayout(layout)
        
        self.create_menu_bar()
        self.create_top_toolbar()
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self.tab_widget)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.ollama_status = QLabel("🔄 Проверка Ollama...")
        self.worker_status = QLabel("💤 Готов")
        self.workspace_status = QLabel(f"📁 {self.workspace_path}")
        
        self.status_bar.addWidget(self.ollama_status)
        self.status_bar.addWidget(self.worker_status)
        self.status_bar.addWidget(self.workspace_status)
        self.status_bar.addPermanentWidget(QLabel("✨ AI Dev System v7.0"))
        
        self.add_new_chat_tab()
        
        QTimer.singleShot(100, self.create_plus_button)
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("📁 Файл")
        
        new_chat_action = QAction("💬 Новый чат", self)
        new_chat_action.triggered.connect(self.add_new_chat_tab)
        file_menu.addAction(new_chat_action)
        
        file_menu.addSeparator()
        
        open_workspace_action = QAction("📂 Открыть рабочую папку", self)
        open_workspace_action.triggered.connect(self.open_workspace_folder)
        file_menu.addAction(open_workspace_action)
        
        choose_workspace_action = QAction("📁 Выбрать рабочую папку", self)
        choose_workspace_action.triggered.connect(self.choose_workspace_folder)
        file_menu.addAction(choose_workspace_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        tools_menu = menubar.addMenu("🔧 Инструменты")
        
        settings_action = QAction("⚙️ Настройки", self)
        settings_action.triggered.connect(self.add_settings_tab)
        tools_menu.addAction(settings_action)
        
        files_action = QAction("📁 Файлы", self)
        files_action.triggered.connect(self.add_files_tab)
        tools_menu.addAction(files_action)
        
        help_menu = menubar.addMenu("❓ Помощь")
        
        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_top_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        new_chat_btn = QPushButton("💬 Новый чат")
        new_chat_btn.clicked.connect(self.add_new_chat_tab)
        toolbar.addWidget(new_chat_btn)
        
        toolbar.addSeparator()
        
        settings_btn = QPushButton("⚙️ Настройки")
        settings_btn.clicked.connect(self.add_settings_tab)
        toolbar.addWidget(settings_btn)
        
        files_btn = QPushButton("📁 Файлы")
        files_btn.clicked.connect(self.add_files_tab)
        toolbar.addWidget(files_btn)
        
        toolbar.addSeparator()
        
        open_workspace_btn = QPushButton("📂 Открыть папку")
        open_workspace_btn.clicked.connect(self.open_workspace_folder)
        toolbar.addWidget(open_workspace_btn)
        
        choose_workspace_btn = QPushButton("📁 Выбрать папку")
        choose_workspace_btn.clicked.connect(self.choose_workspace_folder)
        toolbar.addWidget(choose_workspace_btn)
        
        toolbar.addSeparator()
        
        self.tts_tool_btn = QPushButton("🔊 TTS")
        self.tts_tool_btn.setCheckable(True)
        self.tts_tool_btn.toggled.connect(self.on_tts_toggled)
        toolbar.addWidget(self.tts_tool_btn)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        self.model_combo = QComboBox()
        self.model_combo.setFixedWidth(200)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        toolbar.addWidget(QLabel("Модель:"))
        toolbar.addWidget(self.model_combo)
    
    def create_plus_button(self):
        self.plus_button = QPushButton("+")
        self.plus_button.setFixedSize(35, 25)
        self.plus_button.setStyleSheet("""
            QPushButton {
                background: #2d2d2d;
                border: none;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
                color: #aaa;
            }
            QPushButton:hover {
                background: #667eea;
                color: white;
            }
        """)
        self.plus_button.clicked.connect(self.show_plus_menu)
        
        self.plus_button.setParent(self.tab_widget)
        self.plus_button.raise_()
        
        self.update_plus_button_position()
    
    def update_plus_button_position(self):
        try:
            if hasattr(self, 'plus_button') and self.plus_button and self.plus_button.parent():
                tab_bar = self.tab_widget.tabBar()
                if tab_bar and tab_bar.isVisible():
                    x = tab_bar.width() - self.plus_button.width() - 5
                    y = (tab_bar.height() - self.plus_button.height()) // 2
                    self.plus_button.move(x, y)
                    self.plus_button.raise_()
        except Exception as e:
            logger.error(f"Update button position error: {e}")
    
    def show_plus_menu(self):
        menu = QMenu()
        
        new_chat = menu.addAction("💬 Новый чат")
        new_chat.triggered.connect(self.add_new_chat_tab)
        
        menu.addSeparator()
        
        settings = menu.addAction("⚙️ Настройки")
        settings.triggered.connect(self.add_settings_tab)
        
        files = menu.addAction("📁 Файлы")
        files.triggered.connect(self.add_files_tab)
        
        menu.addSeparator()
        
        open_workspace = menu.addAction("📂 Открыть папку")
        open_workspace.triggered.connect(self.open_workspace_folder)
        
        choose_workspace = menu.addAction("📁 Выбрать папку")
        choose_workspace.triggered.connect(self.choose_workspace_folder)
        
        pos = self.plus_button.mapToGlobal(self.plus_button.rect().bottomLeft())
        menu.exec(pos)
    
    def open_workspace_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.workspace_path.absolute())))
    
    def choose_workspace_folder(self):
        new_path = QFileDialog.getExistingDirectory(
            self, 
            "Выберите рабочую папку", 
            str(self.workspace_path),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if new_path:
            self.workspace_path = Path(new_path)
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            self.settings.setValue("workspace", str(self.workspace_path))
            self.workspace_status.setText(f"📁 {self.workspace_path}")
            
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if isinstance(widget, FilesTab):
                    widget.update_workspace_display()
                elif isinstance(widget, SettingsTab):
                    widget.workspace_path_edit.setText(str(self.workspace_path))
                elif isinstance(widget, ChatTab):
                    widget.add_message("assistant", f"📁 **Рабочая папка изменена на:** `{self.workspace_path}`")
            
            self.status_bar.showMessage(f"Рабочая папка изменена: {self.workspace_path}", 3000)
    
    def on_model_changed(self, model_name):
        self.model_label.setText(f"🧠 {model_name}")
    
    def show_about(self):
        QMessageBox.about(self, "О программе",
            "<h2>Олег + Worker — AI Dev System PRO</h2>"
            "<p>Версия 7.0 - Стабильная версия</p>"
            "<p>Мощная система для разработки с AI ассистентом</p>"
            "<br>"
            "<h3>Возможности:</h3>"
            "<ul>"
            "<li>Интеллектуальный AI помощник на базе Ollama</li>"
            "<li>Worker с доступом к файловой системе</li>"
            "<li>Поддержка просмотра содержимого директорий через тег LIST</li>"
            "<li>Встроенный редактор кода с подсветкой синтаксиса</li>"
            "<li>TTS озвучка ответов (Piper)</li>"
            "<li>Множество чатов в одном окне</li>"
            "</ul>"
            "<br>"
            "<p>© 2024 - AI Dev System</p>")
    
    def add_new_chat_tab(self):
        tab_id = f"chat_{self.next_tab_id}"
        self.next_tab_id += 1
        
        chat_tab = ChatTab(tab_id, self)
        self.chat_tabs[tab_id] = chat_tab
        
        index = self.tab_widget.addTab(chat_tab, f"💬 Чат {self.next_tab_id - 1}")
        self.tab_widget.setCurrentIndex(index)
        
        QTimer.singleShot(10, self.update_plus_button_position)
        return tab_id
    
    def add_settings_tab(self):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "⚙️ Настройки":
                self.tab_widget.setCurrentIndex(i)
                return
        
        settings_tab = SettingsTab(self)
        self.tab_widget.addTab(settings_tab, "⚙️ Настройки")
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
        QTimer.singleShot(10, self.update_plus_button_position)
    
    def add_files_tab(self):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "📁 Файлы":
                self.tab_widget.setCurrentIndex(i)
                return
        
        files_tab = FilesTab(self)
        self.tab_widget.addTab(files_tab, "📁 Файлы")
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
        QTimer.singleShot(10, self.update_plus_button_position)
    
    def close_tab(self, index):
        tab_text = self.tab_widget.tabText(index)
        
        if tab_text.startswith("💬") and len(self.chat_tabs) == 1:
            QMessageBox.information(self, "Нельзя закрыть", "Оставьте хотя бы один чат открытым")
            return
        
        widget = self.tab_widget.widget(index)
        
        for tab_id, tab in list(self.chat_tabs.items()):
            if tab == widget:
                if tab_id in self.active_workers:
                    self.active_workers[tab_id].stop()
                    del self.active_workers[tab_id]
                del self.chat_tabs[tab_id]
                break
        
        self.tab_widget.removeTab(index)
        QTimer.singleShot(10, self.update_plus_button_position)
    
    def get_current_chat_tab(self):
        current = self.tab_widget.currentWidget()
        if isinstance(current, ChatTab):
            return current
        return None
    
    def switch_to_chat_tab(self):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i).startswith("💬"):
                self.tab_widget.setCurrentIndex(i)
                break
    
    def add_message_to_current_chat(self, role, message):
        chat = self.get_current_chat_tab()
        if chat:
            chat.add_message(role, message)
    
    def process_with_ai(self, tab_id, messages):
        try:
            ai_worker = RealAIWorker()
            
            oleg_model = "llama3.2"
            worker_model = "qwen2.5-coder:7b"
            
            for i in range(self.tab_widget.count()):
                widget = self.tab_widget.widget(i)
                if isinstance(widget, SettingsTab):
                    if widget.oleg_model.count() > 0:
                        oleg_model = widget.oleg_model.currentText()
                    if widget.worker_model.count() > 0:
                        worker_model = widget.worker_model.currentText()
                    self.temp_value = widget.temp_slider.value() / 100
                    self.max_steps_value = widget.steps_spin.value()
                    self.allow_shell = widget.allow_shell.isChecked()
                    break
            
            if self.model_combo.currentText():
                oleg_model = self.model_combo.currentText()
            
            ai_worker.configure(
                messages=messages,
                model=oleg_model,
                worker_model=worker_model,
                temperature=self.temp_value,
                max_steps=self.max_steps_value,
                workspace=str(self.workspace_path),
                allow_shell=self.allow_shell
            )
            
            chat_tab = self.chat_tabs.get(tab_id)
            if chat_tab:
                ai_worker.response_chunk.connect(chat_tab.on_ai_chunk)
                ai_worker.response_complete.connect(chat_tab.on_ai_complete)
                ai_worker.worker_log.connect(chat_tab.on_worker_log)
                ai_worker.worker_progress.connect(chat_tab.on_worker_progress)
                ai_worker.worker_step.connect(chat_tab.on_worker_step)
                ai_worker.error_occurred.connect(chat_tab.on_ai_error)
                ai_worker.finished.connect(lambda: self.cleanup_worker(tab_id))
            
            self.active_workers[tab_id] = ai_worker
            ai_worker.start()
        except Exception as e:
            logger.error(f"Process with AI error: {e}")
            chat_tab = self.chat_tabs.get(tab_id)
            if chat_tab:
                chat_tab.on_ai_error(str(e))
    
    def cleanup_worker(self, tab_id):
        if tab_id in self.active_workers:
            del self.active_workers[tab_id]
    
    def load_models(self):
        def load():
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_names = [m['name'] for m in models]
                    
                    self.model_combo.clear()
                    for model in model_names:
                        self.model_combo.addItem(model)
                    
                    for i in range(self.tab_widget.count()):
                        widget = self.tab_widget.widget(i)
                        if isinstance(widget, SettingsTab):
                            widget.oleg_model.clear()
                            widget.worker_model.clear()
                            for model in model_names:
                                widget.oleg_model.addItem(model)
                                widget.worker_model.addItem(model)
                    
                    if model_names:
                        self.model_label = QLabel(f"🧠 {model_names[0]}")
                        self.ollama_status.setText(f"✅ Ollama: {len(models)} моделей")
                        self.ollama_status.setStyleSheet("color: #4caf50;")
                    else:
                        self.ollama_status.setText("⚠️ Нет моделей")
                        self.ollama_status.setStyleSheet("color: #ff9800;")
                else:
                    self.ollama_status.setText("❌ Ollama не отвечает")
                    self.ollama_status.setStyleSheet("color: #f44336;")
            except Exception as e:
                self.ollama_status.setText("❌ Ollama не запущен")
                self.ollama_status.setStyleSheet("color: #f44336;")
        
        thread = threading.Thread(target=load)
        thread.daemon = True
        thread.start()
    
    def check_ollama_status(self):
        def check():
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    self.ollama_status.setText(f"✅ Ollama: {len(models)} моделей")
                    self.ollama_status.setStyleSheet("color: #4caf50;")
                else:
                    self.ollama_status.setText("❌ Ollama ошибка")
                    self.ollama_status.setStyleSheet("color: #f44336;")
            except:
                self.ollama_status.setText("❌ Ollama offline")
                self.ollama_status.setStyleSheet("color: #f44336;")
        
        thread = threading.Thread(target=check)
        thread.daemon = True
        thread.start()
    
    def on_tts_toggled(self, checked):
        self.settings.setValue("tts_enabled", str(checked))
        if not checked:
            self.tts_engine.stop()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Oleg Worker AI System")
    app.setStyleSheet(DARK_STYLE)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()