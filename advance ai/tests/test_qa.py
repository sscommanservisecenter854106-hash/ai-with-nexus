import sys
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from memory.store import MemoryStore
from memory.rag import DocumentRAG
from core.agent import AgentOrchestrator

async def run_qa_tests():
    sys.stdout.reconfigure(encoding='utf-8')
    mem = MemoryStore()
    rag = DocumentRAG()
    orch = AgentOrchestrator(mem, rag)

    test_questions = [
        "Bihar ki rajdhani kya hai?",
        "What is the capital of France?",
        "Bharat ka pradhan mantri kaun hai?",
        "What is RAG?",
        "calculate 125 * 8 + 40",
        "what time is it",
        "weather in Tokyo",
        "Who is the CEO of Apple?"
    ]

    print("==================================================")
    print(">>> Testing Nexus-AI Comprehensive QA Engine <<<")
    print("==================================================")

    for i, q in enumerate(test_questions, 1):
        sid = mem.create_session(f"QTest_{i}")
        evts = []

        async def cb(e):
            evts.append(e)

        await orch.run_stream(sid, q, cb)
        tokens = [e['data'] for e in evts if e['type'] == 'token']
        ans = ''.join(tokens).strip()

        assert len(ans) > 15, f"Query '{q}' returned insufficient answer: '{ans}'"
        first_line = ans.split('\n')[0]
        print(f"[{i}/{len(test_questions)}] Question: \"{q}\"")
        print(f"    Heading: {first_line}")
        print(f"    Length:  {len(ans)} chars")
        print(f"    Sample:  {ans[:120].replace(chr(10), ' ')}...")
        print()

    print("==================================================")
    print(">>> ALL 8 COMPREHENSIVE QA TESTS PASSED! <<<")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_qa_tests())
