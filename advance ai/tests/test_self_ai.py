import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.self_ai import SelfAIEngine

def test_self_ai():
    print("Testing Nexus Self-AI Engine (Zero-API)...")

    # 1. Test Greeting
    res1 = SelfAIEngine.process_query("hello nexus", [])
    assert "Nexus Self-AI" in res1["content"]
    print("  [PASS] Greeting recognized.")

    # 2. Test Math Intent
    res2 = SelfAIEngine.process_query("calculate sqrt(144) + 50", [])
    assert len(res2["tool_calls"]) == 1
    assert res2["tool_calls"][0]["name"] == "calculator"
    print("  [PASS] Math calculation routed to Calculator tool.")

    # 3. Test Code Execution Intent
    res3 = SelfAIEngine.process_query("run python code to test math", [])
    assert len(res3["tool_calls"]) == 1
    assert res3["tool_calls"][0]["name"] == "code_runner"
    print("  [PASS] Code execution routed to Code Runner sandbox.")

    # 4. Test Knowledge Graph (RAG)
    res4 = SelfAIEngine.process_query("what is rag in artificial intelligence?", [])
    assert "Retrieval-Augmented Generation" in res4["content"]
    print("  [PASS] Knowledge graph retrieved RAG architecture explanation.")

    # 5. Test Conversational Memory (Name extraction)
    messages = [
        {"role": "user", "content": "Hello, my name is Raghu"},
        {"role": "assistant", "content": "Nice to meet you Raghu!"},
        {"role": "user", "content": "What is my name?"}
    ]
    res5 = SelfAIEngine.process_query("what is my name?", messages)
    assert "Raghu" in res5["content"]
    print("  [PASS] Conversational memory remembered user name 'Raghu'.")

    # 6. Test RAG Context synthesis
    rag_context = "--- \n[quantum_paper.txt]: Qubits exhibit quantum entanglement and superposition.\n---"
    res6 = SelfAIEngine.process_query("What does the uploaded document say about qubits?", [], rag_context=rag_context)
    assert "Uploaded Knowledge Base" in res6["content"]
    assert "qubits" in res6["content"].lower()
    print("  [PASS] RAG context synthesized accurately from document chunk.")

    print("\n>>> ALL SELF-AI TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_self_ai()
