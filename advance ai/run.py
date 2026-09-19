import os
import sys
import time
import socket
import webbrowser
import threading

# Force UTF-8 encoding on Windows to prevent UnicodeEncodeError in cmd.exe
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    return start_port

def open_browser(port: int):
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    print(f"\n[Nexus-AI] Opening browser interface at {url}...")
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    port = find_available_port(8000)
    
    print("=" * 60)
    print("   [NEXUS-AI] Autonomous Multimodal Platform")
    print(f"   Starting local server on http://127.0.0.1:{port}")
    print("=" * 60)

    # Launch browser in a background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Run Uvicorn ASGI server
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
