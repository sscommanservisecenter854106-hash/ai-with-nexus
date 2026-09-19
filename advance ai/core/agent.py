import asyncio
import json
from typing import List, Dict, Any, Callable, Awaitable, Optional
from config import load_config, DEFAULT_CONFIG
from tools.registry import ToolRegistry
from memory.store import MemoryStore
from memory.rag import DocumentRAG
from core.providers import (
    BaseLLMProvider,
    GeminiProvider,
    OpenAIProvider,
    OllamaProvider,
    LocalFallbackProvider,
    SelfAIProvider
)

class AgentOrchestrator:
    def __init__(self, memory_store: MemoryStore, rag: DocumentRAG):
        self.memory_store = memory_store
        self.rag = rag

    def get_provider(self) -> BaseLLMProvider:
        cfg = load_config()
        active = cfg.get("active_provider", "self_ai")

        if active in ["local", "self_ai"]:
            return SelfAIProvider()
        elif active == "gemini":
            key = cfg.get("gemini_api_key", "").strip()
            if key:
                return GeminiProvider(api_key=key, model=cfg.get("gemini_model", "gemini-2.0-flash"))
        elif active == "openai":
            key = cfg.get("openai_api_key", "").strip()
            if key:
                return OpenAIProvider(api_key=key, model=cfg.get("openai_model", "gpt-4o-mini"))
        elif active == "groq":
            key = cfg.get("groq_api_key", "").strip()
            if key:
                return OpenAIProvider(
                    api_key=key,
                    model=cfg.get("groq_model", "llama-3.3-70b-versatile"),
                    base_url="https://api.groq.com/openai/v1"
                )
        elif active == "ollama":
            return OllamaProvider(
                base_url=cfg.get("ollama_base_url", "http://localhost:11434"),
                model=cfg.get("ollama_model", "llama3")
            )

        # Default self-contained AI provider
        return SelfAIProvider()

    async def run_stream(
        self,
        session_id: str,
        user_message: str,
        event_callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ):
        """
        Runs the ReAct agent loop, emitting real-time events to the callback:
        - {"type": "thought", "data": "..."}
        - {"type": "tool_start", "name": "...", "args": {...}}
        - {"type": "tool_end", "name": "...", "result": "..."}
        - {"type": "token", "data": "..."}
        - {"type": "done", "session_id": "..."}
        """
        cfg = load_config()
        provider = self.get_provider()
        enabled_tools = cfg.get("enabled_tools", DEFAULT_CONFIG.get("enabled_tools", [
            "code_runner", "web_search", "file_manager", "calculator", "system_info", "weather_info"
        ]))
        tools_schema = ToolRegistry.get_schemas(enabled_tools)

        # 1. Save user message to memory store
        self.memory_store.add_message(session_id, role="user", content=user_message)

        # 2. Check RAG for relevant knowledge context
        rag_hits = self.rag.search(user_message, top_k=3)
        rag_context = ""
        if rag_hits:
            rag_context = "\n\nRelevant Knowledge Base Information:\n" + "\n---\n".join(
                [f"[{hit['source']} (relevance: {hit['score']})]:\n{hit['text']}" for hit in rag_hits]
            )

        # 3. Assemble conversation history
        past_msgs = self.memory_store.get_messages(session_id, limit=12)
        formatted_messages: List[Dict[str, str]] = []

        # System persona
        system_persona = cfg.get("system_persona", "")
        if rag_context:
            system_persona += rag_context

        formatted_messages.append({"role": "system", "content": system_persona})

        for m in past_msgs:
            if m["role"] in ["user", "assistant"]:
                formatted_messages.append({"role": m["role"], "content": m["content"]})

        # ReAct loop control
        max_turns = 4
        current_turn = 0
        all_thoughts: List[str] = []
        executed_tool_calls: List[dict] = []
        final_content = ""

        while current_turn < max_turns:
            current_turn += 1

            # Request generation from provider
            try:
                response = await provider.generate(
                    messages=formatted_messages,
                    tools_schema=tools_schema,
                    temperature=float(cfg.get("temperature", 0.7))
                )
            except Exception as e:
                err_msg = f"Provider Error: {str(e)}"
                await event_callback({"type": "token", "data": f"\n\n⚠️ {err_msg}"})
                final_content += f"\n\n⚠️ {err_msg}"
                break

            # Handle reasoning / thought
            if response.thought:
                all_thoughts.append(response.thought)
                await event_callback({"type": "thought", "data": response.thought})

            # Handle tool calls
            if response.tool_calls:
                for tc in response.tool_calls:
                    t_name = tc.get("name")
                    t_args = tc.get("args") or {}
                    await event_callback({"type": "tool_start", "name": t_name, "args": t_args})

                    # Execute tool
                    tool_output = await ToolRegistry.execute(t_name, **t_args)

                    await event_callback({"type": "tool_end", "name": t_name, "result": tool_output})
                    executed_tool_calls.append({"name": t_name, "args": t_args, "result": tool_output})

                    # Feed tool observation back to messages
                    formatted_messages.append({
                        "role": "system",
                        "content": f"Tool Observation ({t_name}):\n{tool_output}"
                    })

                # Continue the ReAct loop to allow model to interpret tool output
                continue

            # Model produced final content
            if response.content:
                final_content = response.content
                # Stream out content in small chunks for smooth typing effect
                chunk_size = 12
                for i in range(0, len(final_content), chunk_size):
                    chunk = final_content[i:i + chunk_size]
                    await event_callback({"type": "token", "data": chunk})
                    await asyncio.sleep(0.015)
                break

            break

        # Fallback if model produced no content after turns
        if not final_content:
            final_content = "I have processed your query. Please let me know if you would like me to explain further or help with anything else!"
            await event_callback({"type": "token", "data": final_content})

        # Save assistant message to memory store
        joined_thoughts = "\n\n".join(all_thoughts)
        self.memory_store.add_message(
            session_id=session_id,
            role="assistant",
            content=final_content,
            thoughts=joined_thoughts,
            tool_calls=executed_tool_calls
        )

        await event_callback({"type": "done", "session_id": session_id})
