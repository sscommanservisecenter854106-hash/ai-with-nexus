import asyncio
import websockets
import json
import urllib.parse
from memory.store import MemoryStore

async def test():
    store = MemoryStore()
    try:
        store.register_user("test@test.com", "testpassword123")
    except:
        pass
    auth_data = store.authenticate_user("test@test.com", "testpassword123")
    token = auth_data["token"]
    
    url = f"ws://localhost:8000/ws/chat?token={urllib.parse.quote(token)}"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"message": "output nahi aa raha hai"}))
        while True:
            msg = await ws.recv()
            print("RECV:", msg.encode("utf-8"))
            data = json.loads(msg)
            if data.get("type") in ["done", "error"]:
                break

asyncio.run(test())
