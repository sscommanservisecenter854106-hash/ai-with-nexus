import asyncio
import websockets
import json
import urllib.parse
from memory.store import MemoryStore

async def test():
    store = MemoryStore()
    
    # Register a test user
    try:
        store.register_user("test@test.com", "testpassword123")
    except:
        pass
    auth_data = store.authenticate_user("test@test.com", "testpassword123")
    token = auth_data["token"]
    
    url = f"ws://localhost:8000/ws/chat?token={urllib.parse.quote(token)}"
    try:
        async with websockets.connect(url) as ws:
            with open("ws_log_2.txt", "w", encoding="utf-8") as f:
                f.write("Connected.\n")
                await ws.send(json.dumps({"session_id": "test_session_2", "message": "What is the weather in Tokyo?"}))
                while True:
                    msg = await ws.recv()
                    f.write(f"RECV: {msg}\n")
                    data = json.loads(msg)
                    if data.get("type") in ["done", "error"]: 
                        break
    except Exception as e:
        with open("ws_log_2.txt", "a", encoding="utf-8") as f:
            f.write(f"ERROR: {str(e)}\n")

asyncio.run(test())
