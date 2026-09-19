# 🚀 NEXUS-AI: Custom Autonomous Intelligence Platform

Nexus-AI is a full-stack, modular, multimodal AI agent and assistant platform designed from scratch. It features real-time reasoning loops, an extensible sandboxed tool ecosystem, hybrid memory (SQLite + RAG vector retrieval), and a futuristic cyber-glass dark interface with voice input/output.

---

## ✨ Key Features

1. **Autonomous ReAct Agent Loop**:
   - Live multi-step reasoning (`Reason -> Act -> Observe -> Finish`).
   - Collapsible **🧠 Agent Thoughts** accordion showing transparent step-by-step thinking.

2. **Built-in Tool Ecosystem (7 Autonomous Tools)**:
   - 🐍 **Python Sandbox (`code_runner`)**: Runs arbitrary Python 3 code in an isolated subprocess with timeout and returns stdout/stderr.
   - 🖥️ **System Monitor (`system_info`)**: Safely inspects host OS, Python runtime, CPU cores, LAN IP, and real-time disk space.
   - 🌤️ **Live Global Weather (`weather_info`)**: Queries live temperature, wind speed, humidity, and forecasts worldwide with zero API keys.
   - 📅 **Live Date & Time (`datetime_info`)**: Instant live date, calendar week, UTC/local clock, day of the week, and ISO timestamps.
   - 🌐 **Live Web Search (`web_search`)**: Queries the live web and scrapes target URLs for real-time information.
   - 📁 **Workspace File Manager (`file_manager`)**: Read, write, append, and list files inside your project directory safely.
   - 🧮 **Scientific Calculator (`calculator`)**: Evaluates mathematical and trigonometric expressions with exact precision.

3. **Nexus Self-AI & Multi-Provider Architecture**:
   - 🤖 **Nexus Self-AI Engine**: 100% self-hosted, private, and offline out-of-the-box with **zero API keys required**. Features conversational memory, embedded knowledge graph across algorithms, web dev, AI/ML, and DevOps, plus autonomous tool routing in English and Hindi.
   - 🦙 **Ollama Local LLMs**: Zero-API offline neural generation (Llama 3, Phi-3, DeepSeek, Mistral) running directly on your hardware.
   - 🌐 **Cloud Providers (Optional)**: Optional connectors for Google Gemini, OpenAI, or Groq if desired.

4. **Hybrid Memory & RAG Knowledge Base**:
   - Persistent SQLite conversation history across multiple chat sessions.
   - Drag-and-drop document upload (`.txt`, `.md`, `.py`, `.csv`, `.json`).
   - In-memory BM25 semantic chunking & keyword retrieval with smart stop-word filtering.

5. **Futuristic Cyber-Glass Web Interface**:
   - Sleek dark theme with neon cyan & purple accents.
   - Real-time token streaming via WebSockets.
   - 🔒 **Email Auth Gate & 1-Click Offline Guest Access**: Full account isolation or instant 1-click local guest demo.
   - 📋 **Interactive Code Blocks**: Syntax headers with 1-click clipboard copy buttons.
   - 📦 **Conversation Export**: Download active conversations as Markdown (`.md`) or structured JSON (`.json`).
   - 🗑️ **Conversation Reset**: 1-click clean canvas reset with confirmation.
   - 🎙️ Voice Input (Web Speech API speech-to-text).
   - 🔊 Audio Output (Speech synthesis TTS).
   - In-app **⚙️ Settings modal** to customize system prompts, temperature, and switch providers.

6. **Production & Multi-Cloud Deployment**:
   - Pre-configured for **Render.com** (`render.yaml`), **Docker Compose** (`docker-compose.yml`), **Railway/Heroku** (`Procfile`), and self-hosted VPS (Nginx + Systemd).
   - See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions.

---

## 🚀 How to Run

### Option 1: One-Click Launcher (Windows)
Double-click `run.bat` in this folder. It will start the server and open your default browser automatically.

### Option 2: Command Line
```powershell
python run.py
```
Or with Uvicorn directly:
```powershell
python -m uvicorn server.app:app --host 127.0.0.1 --port 8000 --reload
```

Once started, open your browser at:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📁 Project Structure

```
advance ai/
├── config.py                 # System configuration & runtime settings
├── requirements.txt          # Python dependencies
├── run.py                    # Launcher with auto browser opening
├── run.bat                   # Windows batch launcher script
├── core/
│   ├── __init__.py
│   ├── providers.py          # LLM Provider adapters (Gemini, OpenAI, Groq, Ollama, Local)
│   └── agent.py              # Autonomous ReAct agent orchestrator
├── tools/
│   ├── __init__.py
│   ├── base.py               # Base tool definition
│   ├── registry.py           # Tool registry & execution manager
│   ├── code_runner.py        # Sandboxed Python code executor
│   ├── web_search.py         # DuckDuckGo search & URL scraper
│   ├── file_manager.py       # Workspace file reader & writer
│   └── calculator.py         # Safe AST math expression evaluator
├── memory/
│   ├── __init__.py
│   ├── store.py              # SQLite session & message persistence
│   └── rag.py                # Document ingestion & BM25 vector retriever
├── server/
│   ├── __init__.py
│   └── app.py                # FastAPI ASGI backend & WebSocket streaming
├── frontend/
│   ├── index.html            # Cyber-glass UI layout & modals
│   └── static/
│       ├── styles.css        # Glassmorphism dark styling & glowing animations
│       └── app.js            # WebSocket client, speech, & session state
└── tests/
    └── test_system.py        # Automated test suite for all modules
```

---

## 🧪 Verification & Testing

To run the automated test suite:
```powershell
python tests/test_system.py
```
All 6 core subsystems are tested: configuration, calculator, python runner, SQLite persistence, RAG retrieval, and ReAct agent loop.
