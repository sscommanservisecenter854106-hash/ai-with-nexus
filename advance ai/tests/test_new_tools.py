import sys
import asyncio
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from tools.registry import ToolRegistry
import tools.code_runner
import tools.web_search
import tools.file_manager
import tools.calculator
import tools.system_info
import tools.weather_info
import tools.datetime_info
from core.self_ai import SelfAIEngine

async def run_tests():
    print("==================================================")
    print(">>> Testing Nexus-AI Expanded Toolset & Engine <<<")
    print("==================================================")

    # 1. Verify all 7 tools are registered
    print("\n[1/6] Verifying Tool Registry...")
    tools = [t.name for t in ToolRegistry.list_all()]
    print(f"    Registered tools: {tools}")
    expected_tools = ["code_runner", "web_search", "file_manager", "calculator", "system_info", "weather_info", "datetime_info"]
    for t in expected_tools:
        assert t in tools, f"Tool '{t}' missing from registry!"
    print(f"    [PASS] All {len(expected_tools)} tools successfully registered.")

    # 2. Test SystemInfoTool
    print("\n[2/5] Testing SystemInfoTool...")
    sys_res = await ToolRegistry.execute("system_info", query_type="all")
    assert "Operating System" in sys_res
    assert "Python Runtime" in sys_res
    assert "CPU Cores" in sys_res
    assert "Disk Space" in sys_res
    print("    [PASS] SystemInfoTool returned comprehensive diagnostics.")

    # 3. Test WeatherInfoTool
    print("\n[3/6] Testing WeatherInfoTool...")
    w_res = await ToolRegistry.execute("weather_info", location="Paris")
    assert "Weather" in w_res or "Temperature" in w_res or "Conditions" in w_res
    print(f"    [PASS] WeatherInfoTool returned live data: {w_res.splitlines()[0]}")

    # 4. Test DateTimeTool
    print("\n[4/6] Testing DateTimeTool...")
    dt_res = await ToolRegistry.execute("datetime_info", format="full")
    assert "Date" in dt_res and "Time" in dt_res
    print(f"    [PASS] DateTimeTool returned live report: {dt_res.splitlines()[0]}")

    # 5. Test SelfAIEngine Routing
    print("\n[5/6] Testing Autonomous Intent Routing...")
    q_sys = SelfAIEngine.process_query("what are the system hardware specs and available disk space?", [])
    assert len(q_sys["tool_calls"]) == 1
    assert q_sys["tool_calls"][0]["name"] == "system_info"
    print("    [PASS] System diagnostics routed to system_info tool.")

    q_w = SelfAIEngine.process_query("what is the live weather in Tokyo right now?", [])
    assert len(q_w["tool_calls"]) == 1
    assert q_w["tool_calls"][0]["name"] == "weather_info"
    assert "tokyo" in q_w["tool_calls"][0]["args"]["location"].lower()
    print("    [PASS] Weather query routed to weather_info tool.")

    q_dt = SelfAIEngine.process_query("what is today date and current time?", [])
    assert len(q_dt["tool_calls"]) == 1
    assert q_dt["tool_calls"][0]["name"] == "datetime_info"
    print("    [PASS] Date/time query routed to datetime_info tool.")

    # 6. Test Expanded Knowledge Graph
    print("\n[6/6] Testing Expanded Knowledge Graph Nodes...")
    nodes_to_test = ["dijkstra", "jwt", "asyncio", "kubernetes", "lora", "diffusion"]
    for node in nodes_to_test:
        res = SelfAIEngine.process_query(f"explain {node}", [])
        assert len(res["content"]) > 50, f"Node '{node}' returned insufficient content"
    print(f"    [PASS] All {len(nodes_to_test)} knowledge nodes validated.")

    print("\n==================================================")
    print(">>> ALL 6 ENHANCEMENT VERIFICATION TESTS PASSED! <<<")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
