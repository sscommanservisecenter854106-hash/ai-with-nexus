import os
from pathlib import Path
from .base import BaseTool
from .registry import register_tool
from config import BASE_DIR

@register_tool
class FileManagerTool(BaseTool):
    name = "file_manager"
    description = (
        "Reads, writes, appends, and lists files within the workspace. "
        "Allows analyzing project files, saving notes, or reviewing scripts."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "write", "list", "append"],
                "description": "The file action to perform: 'read', 'write', 'list', or 'append'."
            },
            "path": {
                "type": "string",
                "description": "Relative file or directory path within the project workspace."
            },
            "content": {
                "type": "string",
                "description": "Content to write or append (required for write and append actions)."
            }
        },
        "required": ["action"]
    }

    def _resolve_safe_path(self, rel_path: str) -> Path:
        target = (BASE_DIR / rel_path).resolve()
        # Security: Prevent traversing above BASE_DIR
        if not str(target).startswith(str(BASE_DIR)):
            raise PermissionError("Access outside the project workspace is forbidden.")
        return target

    async def run(self, action: str = "list", path: str = ".", content: str = "", **kwargs) -> str:
        try:
            target = self._resolve_safe_path(path)

            if action == "list":
                if not target.exists():
                    return f"Path does not exist: {path}"
                if not target.is_dir():
                    return f"Path is a file, not a directory: {path}"

                items = []
                for p in sorted(target.iterdir()):
                    prefix = "[DIR] " if p.is_dir() else "[FILE]"
                    size_info = f" ({p.stat().st_size} bytes)" if p.is_file() else ""
                    rel = p.relative_to(BASE_DIR)
                    items.append(f"{prefix} {rel}{size_info}")

                return "\n".join(items) if items else "(Empty directory)"

            elif action == "read":
                if not target.exists():
                    return f"Error: File '{path}' does not exist."
                if target.is_dir():
                    return f"Error: '{path}' is a directory, not a file."
                # Limit read to 8000 chars to prevent prompt bloat
                text = target.read_text(encoding="utf-8", errors="replace")
                if len(text) > 8000:
                    return f"[Showing first 8000 characters of {path}]:\n" + text[:8000]
                return text

            elif action == "write":
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                return f"Successfully wrote {len(content)} characters to '{path}'."

            elif action == "append":
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "a", encoding="utf-8") as f:
                    f.write(content)
                return f"Successfully appended content to '{path}'."

            else:
                return f"Unknown action '{action}'. Supported actions: list, read, write, append."

        except Exception as e:
            return f"FileManager error: {str(e)}"
