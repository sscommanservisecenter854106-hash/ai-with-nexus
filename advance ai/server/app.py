import json
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect,
    UploadFile, File, HTTPException, Depends, Query, Header
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from config import BASE_DIR, UPLOAD_DIR, load_config, save_config
from tools.registry import ToolRegistry
# Ensure tools are imported so that decorators register them
import tools.code_runner
import tools.web_search
import tools.file_manager
import tools.calculator
import tools.system_info
import tools.weather_info
import tools.datetime_info

from memory.store import MemoryStore
from memory.rag import DocumentRAG
from core.agent import AgentOrchestrator

app = FastAPI(title="Nexus-AI Autonomous Platform", version="1.0.0")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: http: ws: wss: data: blob:; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'self' ws: wss: http: https:;"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response

# Initialize core instances
memory_store = MemoryStore()
document_rag = DocumentRAG()
agent = AgentOrchestrator(memory_store, document_rag)

FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Auth Security Scheme
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")
    token = credentials.credentials
    user = memory_store.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please log in again.")
    return user

# --- Authentication Models & Routes ---

class AuthRegisterModel(BaseModel):
    email: str
    password: str

class AuthLoginModel(BaseModel):
    email: str
    password: str

@app.post("/api/auth/register")
async def register(data: AuthRegisterModel):
    try:
        result = memory_store.register_user(data.email, data.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(data: AuthLoginModel):
    result = memory_store.authenticate_user(data.email, data.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password. Please try again.")
    return result

@app.get("/api/auth/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    return {"user": user}

@app.post("/api/auth/logout")
async def logout(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if credentials:
        memory_store.delete_token(credentials.credentials)
    return {"message": "Logged out successfully."}

# --- Core App Routes ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Nexus-AI Frontend is loading...</h1>")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%236366f1" stroke-width="2.2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>'
    return Response(content=svg, media_type="image/svg+xml")

@app.get("/api/status")
async def get_status():
    cfg = load_config()
    all_tools = ToolRegistry.list_all()
    rag_sources = document_rag.list_sources()
    return {
        "status": "online",
        "active_provider": cfg.get("active_provider", "local"),
        "total_tools": len(all_tools),
        "tools": [t.name for t in all_tools],
        "enabled_tools": cfg.get("enabled_tools", []),
        "rag_documents": len(rag_sources),
        "rag_chunks": len(document_rag.documents)
    }

@app.get("/api/config")
async def get_config(user: Dict[str, Any] = Depends(get_current_user)):
    cfg = load_config()
    # Mask API keys for security in UI display
    safe_cfg = cfg.copy()
    for key in ["gemini_api_key", "openai_api_key", "groq_api_key"]:
        val = safe_cfg.get(key, "")
        if val and len(val) > 8:
            safe_cfg[key] = val[:4] + "..." + val[-4:]
    return {"config": safe_cfg, "raw": cfg}

class ConfigUpdateModel(BaseModel):
    active_provider: str = "local"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    gemini_model: str = "gemini-2.0-flash"
    openai_model: str = "gpt-4o-mini"
    groq_model: str = "llama-3.3-70b-versatile"
    ollama_model: str = "llama3"
    temperature: float = 0.7
    system_persona: str = ""
    enabled_tools: List[str] = []

@app.post("/api/config")
async def update_config(data: ConfigUpdateModel, user: Dict[str, Any] = Depends(get_current_user)):
    current = load_config()
    update_data = data.model_dump()

    # Don't overwrite existing API key if masked string is passed back
    for key in ["gemini_api_key", "openai_api_key", "groq_api_key"]:
        if "..." in update_data.get(key, ""):
            update_data[key] = current.get(key, "")

    saved = save_config(update_data)
    return {"message": "Configuration updated successfully", "config": saved}

@app.get("/api/sessions")
async def list_sessions(user: Dict[str, Any] = Depends(get_current_user)):
    return {"sessions": memory_store.list_sessions(user_id=user["id"])}

class SessionCreateModel(BaseModel):
    title: str = "New Conversation"

@app.post("/api/sessions")
async def create_session(data: SessionCreateModel, user: Dict[str, Any] = Depends(get_current_user)):
    session_id = memory_store.create_session(title=data.title, user_id=user["id"])
    return {"session_id": session_id, "title": data.title}

@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    messages = memory_store.get_messages(session_id, user_id=user["id"])
    return {"session_id": session_id, "messages": messages}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    deleted = memory_store.delete_session(session_id, user_id=user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...), user: Dict[str, Any] = Depends(get_current_user)):
    allowed_exts = [".txt", ".md", ".py", ".csv", ".json", ".log", ".html"]
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Allowed: {', '.join(allowed_exts)}"
        )

    dest_path = UPLOAD_DIR / file.filename
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        content = dest_path.read_text(encoding="utf-8", errors="replace")
        chunks_count = document_rag.add_document(file.filename, content)
        return {
            "message": f"Successfully indexed '{file.filename}' into RAG knowledge memory.",
            "chunks": chunks_count,
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.get("/api/rag/sources")
async def get_rag_sources(user: Dict[str, Any] = Depends(get_current_user)):
    return {"sources": document_rag.list_sources()}

@app.delete("/api/rag/clear")
async def clear_rag(user: Dict[str, Any] = Depends(get_current_user)):
    document_rag.clear()
    return {"message": "RAG Knowledge Base cleared."}

@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, token: Optional[str] = Query(None)):
    await websocket.accept()

    # Authenticate WebSocket
    user = None
    if token:
        user = memory_store.get_user_by_token(token)

    # If token not in query param, wait briefly for an auth message
    if not user:
        try:
            raw_init = await asyncio.wait_for(websocket.receive_text(), timeout=4.0)
            init_data = json.loads(raw_init)
            t = init_data.get("token")
            if t:
                user = memory_store.get_user_by_token(t)
        except Exception:
            pass

    if not user:
        await websocket.send_json({
            "type": "error",
            "data": "Authentication required. Please sign in with your email to access Nexus-AI."
        })
        await websocket.close(code=1008)
        return

    user_id = user["id"]

    try:
        while True:
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)

            session_id = data.get("session_id")
            user_message = data.get("message", "").strip()

            if not session_id:
                session_id = memory_store.create_session("New Conversation", user_id=user_id)
                await websocket.send_json({"type": "session_created", "session_id": session_id})

            if not user_message:
                continue

            # Callback handler for streaming events to client
            async def event_callback(event: Dict[str, Any]):
                await websocket.send_json(event)

            # Run ReAct agent loop
            await agent.run_stream(
                session_id=session_id,
                user_message=user_message,
                event_callback=event_callback
            )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass
