import asyncio
from core.providers import SelfAIProvider
from config import DEFAULT_CONFIG

async def test():
    p = SelfAIProvider(ollama_fallback=False)
    resp = await p.generate([{"role": "user", "content": "What is the capital of India?"}])
    print("Content:")
    print(resp.content)

asyncio.run(test())
