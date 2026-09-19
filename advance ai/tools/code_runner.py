import sys
import asyncio
import subprocess
import tempfile
from pathlib import Path
from .base import BaseTool
from .registry import register_tool

@register_tool
class CodeRunnerTool(BaseTool):
    name = "code_runner"
    description = (
        "Executes arbitrary Python code in an isolated subprocess and returns standard output and errors. "
        "Useful for data analysis, complex calculations, algorithmic tasks, text processing, and simulations."
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Valid executable Python 3 source code."
            }
        },
        "required": ["code"]
    }

    async def run(self, code: str = "", **kwargs) -> str:
        if not code.strip():
            return "Error: No code provided to execute."

        # Write to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            # Run using asyncio subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15.0)
                out_str = stdout.decode("utf-8", errors="replace").strip()
                err_str = stderr.decode("utf-8", errors="replace").strip()

                result = []
                if out_str:
                    result.append(f"[Output]:\n{out_str}")
                if err_str:
                    result.append(f"[Errors/Warnings]:\n{err_str}")
                if not result:
                    result.append("[Execution completed with no output (return code 0)]")

                return "\n".join(result)
            except asyncio.TimeoutError:
                process.kill()
                return "Error: Code execution timed out after 15 seconds."
        except Exception as e:
            return f"Error executing Python code: {str(e)}"
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
