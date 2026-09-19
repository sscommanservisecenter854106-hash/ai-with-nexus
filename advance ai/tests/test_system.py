import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import load_config, save_config
from tools.registry import ToolRegistry
import tools.code_runner
import tools.web_search
import tools.file_manager
import tools.calculator
from memory.store import MemoryStore
from memory.rag import DocumentRAG
from core.agent import AgentOrchestrator

async def run_tests():
    print(">>> [1/6] Testing Configuration System...")
    cfg = load_config()
    assert "active_provider" in cfg
    assert "enabled_tools" in cfg
    print("    [PASS] Config loaded successfully.")

    print(">>> [2/6] Testing Tool Registry & Calculator...")
    all_tools = ToolRegistry.list_all()
    assert len(all_tools) >= 4
    calc_res = await ToolRegistry.execute("calculator", expression="sqrt(144) + 2**8")
    assert "268" in calc_res or "268.0" in calc_res, f"Expected 268, got {calc_res}"
    print(f"    [PASS] Calculator tool returned: {calc_res}")

    print(">>> [3/6] Testing Code Runner Sandbox...")
    code_res = await ToolRegistry.execute("code_runner", code="print(sum([1, 2, 3, 4, 5]))")
    assert "15" in code_res, f"Expected 15, got {code_res}"
    print(f"    [PASS] Code runner returned: {code_res}")

    print(">>> [4/6] Testing Memory Store & SQLite Persistence...")
    store = MemoryStore()
    sess_id = store.create_session("Test Session")
    store.add_message(sess_id, role="user", content="Hello Nexus!")
    store.add_message(sess_id, role="assistant", content="Hello! How can I help you?", thoughts="Initial greeting")
    msgs = store.get_messages(sess_id)
    assert len(msgs) == 2
    assert msgs[0]["content"] == "Hello Nexus!"
    print("    [PASS] Memory store persisted and retrieved conversation messages.")

    print(">>> [5/6] Testing Document RAG Retrieval...")
    rag = DocumentRAG()
    sample_text = (
        "Quantum computing is a rapidly-emerging technology that harnesses the laws of quantum mechanics "
        "to solve problems too complex for classical computers. Qubits can exist in superposition."
    )
    rag.add_document("quantum_notes.txt", sample_text)
    hits = rag.search("What is quantum computing and superposition?")
    assert len(hits) > 0
    assert "quantum" in hits[0]["text"].lower()
    print(f"    [PASS] RAG retrieved {len(hits)} matching chunk(s) with score {hits[0]['score']}.")

    print(">>> [6/6] Testing Autonomous Agent Orchestrator ReAct Loop...")
    orchestrator = AgentOrchestrator(store, rag)
    collected_events = []

    async def test_callback(event):
        collected_events.append(event)

    # Ask for computation through agent loop
    await orchestrator.run_stream(
        session_id=sess_id,
        user_message="Please compute 45 * 12",
        event_callback=test_callback
    )

    event_types = [e["type"] for e in collected_events]
    print(f"    Agent emitted events: {set(event_types)}")
    assert "done" in event_types
    assert "token" in event_types or "tool_start" in event_types
    print("    [PASS] Autonomous ReAct agent loop executed successfully!")

    print("\n=============================================")
    print(">>> ALL 6 SYSTEM VERIFICATION TESTS PASSED! <<<")
    print("=============================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
