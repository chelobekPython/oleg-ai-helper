# 🧠 Oleg + Worker — AI Dev System

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![Ollama](https://img.shields.io/badge/ollama-0.1+-green.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An intelligent AI-powered development system with voice control, code generation, and team-based task delegation. Oleg (Project Manager) delegates tasks to Worker (Code Generator) for automated software development.

📝 License
MIT License - See LICENSE file for details

📞 Support
Telegram - @I_am_Chotko

## 🌟 Features

### 🎯 Core Capabilities
- **Two AI Agent System**: Oleg (Manager) analyzes tasks and delegates, Worker (Engineer) writes production-ready code
- **Voice Control**: Speak commands starting with "Oleg" for hands-free operation
- **Multi-model Support**: Works with any Ollama model (Llama, Qwen, CodeLlama, etc.)
- **Automatic Code Generation**: Worker creates complete, ready-to-run files
- **Chat Persistence**: Save and manage multiple conversation threads
- **TTS Voice Output**: Hear Oleg's responses with Piper TTS

### 🌍 Multilingual Interface
- 🇷🇺 Russian (Русский)
- 🇬🇧 English
- 🇪🇸 Spanish (Español)
- 🇩🇪 German (Deutsch)
- 🇫🇷 French (Français)
- 🇨🇳 Chinese (中文)

### 🛠️ Technical Features
- **File Management**: Automatic workspace organization
- **Path Safety**: Prevents directory traversal attacks
- **Multiple Recognition Engines**: Google Speech + Sphinx fallback
- **Streaming Responses**: Real-time AI responses
- **Session Management**: Persistent chat history

## 📋 Prerequisites

### Required Software
- **Python 3.8+**
- **Ollama** (with downloaded models)
- **FFmpeg** (for voice input)
- **Piper TTS** (optional, for voice output)

### Installation

```bash
# Clone the repository
git clone https://github.com/chelobekPython/oleg-ai-helper
cd oleg-worker-ai-dev

# Install Python dependencies
pip install streamlit ollama requests speechrecognition pydub piper-tts

# Install FFmpeg (required for voice input)
# Windows (using winget)
winget install ffmpeg

# macOS (using homebrew)
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Install Ollama (if not already installed)
# Visit https://ollama.ai for installation instructions

# Pull required models
ollama pull llama3.2
ollama pull qwen2.5-coder:7b
```
📊 Performance Tips
Model Selection:
For better code: Use qwen2.5-coder or codellama
For faster responses: Use llama3.2 or mistral
For complex tasks: Use larger models (13B+)

Temperature Settings:
0.0-0.3: Consistent, predictable code
0.4-0.7: Balanced creativity
0.8-1.0: More experimental

Workspace Management:
Regularly clean old files
Use subdirectories for projects
Version control important outputs

🐛 Known Issues
- Voice recognition works best with Russian language
- TTS only supports Russian voices (Piper limitation)
- Large file generation may take time
- Some models may not follow WRITE format strictly

🎯 Roadmap
- Support for more voice languages
- Code execution sandbox
- Project templates
- Git integration
- Testing framework integration
- Docker support
- API mode
- Plugin system

⚡ Quick Demo
# Example: Creating a calculator
User: "Oleg, create a calculator with basic operations"

Oleg: I'll delegate this to Worker with specifications:
- Create calculator.py with add, subtract, multiply, divide
- Include user input handling
- Add error handling for division by zero

Worker: 
✅ calculator.py (2456 bytes)
✅ Successfully created files: 1
📁 calculator.py
# The file is automatically saved in your workspace folder!

Voice Output Setup (Optional)
For TTS voice output, download Piper voice models and create folder "voices":
Download from: https://huggingface.co/rhasspy/piper-voices
Place models in ./voices/ directory:
- ru_RU-ruslan-medium.onnx (Male voice)
- ru_RU-irina-medium.onnx (Female voice)
🚀 Quick Start
Start Ollama server:

```bash
ollama serve
```
Run the application:

```bash
streamlit run app.py
```
Open your browser at http://localhost:8501

Start using the system:
Type a request in the chat
Or use voice: Click "Start Recording" → Say "Oleg, create a calculator" → Click "Recognize"

🎯 System Architecture
```by_chotko
User Input (Voice/Text)
    ↓
Oleg (Project Manager)
    ↓
Task Analysis & Delegation
    ↓
Worker (Code Generator)
    ↓
File Creation in Workspace
    ↓
Return Results to User
```
⚙️ Configuration
Sidebar Settings
Setting	Description	Default
Workspace	Directory for generated files	./workspace
TTS Voice	Male/Female voice output	Disabled
Worker Model	Model for code generation	qwen2.5-coder:7b
Oleg Model	Model for task management	llama3.2
Temperature	Response creativity (0-1)	0.2
Max Worker Steps	Max attempts for code generation	15
Voice Recognition Tips
Speak clearly and at moderate speed

Pause briefly after saying "Oleg"

Use a quality microphone

Minimize background noise

Examples: "Oleg create file", "Oleg write code"

📁 Project Structure
```text
oleg-worker-ai-dev/
├── app.py                 # Main application
├── workspace/            # Generated files directory
├── voices/              # Piper TTS models (optional)
├── requirements.txt     # Python dependencies
├── README.md           # Documentation
└── LICENSE             # MIT License
```
🔧 Troubleshooting
FFmpeg Not Found
```bash
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```
Ollama Connection Error
```bash
# Check if Ollama is running
ollama serve
# Test connection
curl http://localhost:11434/api/tags
```
Models Not Available
```bash
# List installed models
ollama list
```
# Pull required models
```
ollama pull llama3.2
```
```
ollama pull qwen2.5-coder:7b
```
Voice Recognition Issues
Ensure microphone permissions are granted

Check FFmpeg installation

Try using a different microphone

Speak closer to the microphone

Reduce background noise

🎨 Advanced Usage
Custom System Prompts
You can modify the system prompts in the code:

OLEG_SYSTEM_PROMPT - Manager behavior

WORKER_SYSTEM_PROMPT - Code generation rules

Adding New Languages
Add translations to the UI_TRANSLATIONS dictionary:

```
'your_lang_code': {
    'app_title': 'Your Title',
    'voice_control': 'Voice Control',
    # ... add all keys
}
```
By Chotko with ❤️
-
_Если вы хотите бесплатное совместное сотрудничество или просто поболтать то напишите мне в тг @I_am_Chotko💕_
