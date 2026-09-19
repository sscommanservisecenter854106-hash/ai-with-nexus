import os
import sys
import shutil
import platform
from typing import Dict, Any
from .base import BaseTool
from .registry import register_tool

@register_tool
class SystemInfoTool(BaseTool):
    name = "system_info"
    description = (
        "Retrieves host system diagnostics, hardware resources, and operating environment info. "
        "Returns operating system, architecture, Python version, CPU core count, and disk space usage."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "enum": ["all", "disk", "cpu", "os"],
                "default": "all",
                "description": "Specific diagnostic category to query ('all', 'disk', 'cpu', 'os')."
            }
        },
        "required": []
    }

    async def run(self, query_type: str = "all", **kwargs) -> str:
        try:
            results = []

            # 1. OS & Architecture
            if query_type in ["all", "os"]:
                os_name = platform.system()
                os_release = platform.release()
                os_version = platform.version()
                arch = platform.machine()
                py_ver = sys.version.split()[0]
                results.append(f"🖥️ **Operating System**: {os_name} {os_release} ({arch})")
                results.append(f"🐍 **Python Runtime**: v{py_ver} ({sys.executable})")

            # 2. CPU Specs
            if query_type in ["all", "cpu"]:
                cpu_count = os.cpu_count() or "Unknown"
                processor = platform.processor() or "Generic"
                results.append(f"⚡ **CPU Cores**: {cpu_count} logical cores ({processor})")

            # 3. Disk Space
            if query_type in ["all", "disk"]:
                cwd = os.getcwd()
                total, used, free = shutil.disk_usage(cwd)
                gb = 1024 ** 3
                pct_used = (used / total) * 100 if total > 0 else 0
                results.append(
                    f"💾 **Disk Space ({cwd})**:\n"
                    f"   - Total: {total / gb:.2f} GB\n"
                    f"   - Used:  {used / gb:.2f} GB ({pct_used:.1f}%)\n"
                    f"   - Free:  {free / gb:.2f} GB"
                )
            # 4. Hostname & Network
            if query_type in ["all", "os", "network"]:
                import socket
                hostname = platform.node() or socket.gethostname()
                try:
                    local_ip = socket.gethostbyname(hostname)
                except Exception:
                    local_ip = "127.0.0.1"
                results.append(f"🌐 **Hostname / Node**: `{hostname}` (LAN IP: `{local_ip}`)")

            return "\n".join(results)
        except Exception as e:
            return f"Error retrieving system diagnostics: {str(e)}"
