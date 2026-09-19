import time
from datetime import datetime, timezone
from typing import Dict, Any
from .base import BaseTool
from .registry import register_tool

@register_tool
class DateTimeTool(BaseTool):
    name = "datetime_info"
    description = (
        "Provides current live date, time, timezone, day of the week, and ISO timestamps. "
        "Call this whenever asked for today's date, current time, day, or calendar questions."
    )
    parameters = {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "enum": ["full", "date", "time", "iso"],
                "default": "full",
                "description": "Output format: 'full', 'date', 'time', or 'iso'."
            }
        },
        "required": []
    }

    async def run(self, format: str = "full", **kwargs) -> str:
        try:
            now_local = datetime.now()
            now_utc = datetime.now(timezone.utc)
            tz_name = time.tzname[time.daylight] if time.daylight else time.tzname[0]

            if format == "date":
                return now_local.strftime("📅 **Today's Date**: %A, %B %d, %Y")
            elif format == "time":
                return now_local.strftime(f"⏰ **Current Time**: %I:%M:%S %p ({tz_name})")
            elif format == "iso":
                return f"ISO 8601: `{now_local.isoformat()}`"

            day_of_year = now_local.timetuple().tm_yday
            week_num = now_local.isocalendar()[1]

            return (
                f"📅 **Live Date & Time Report**\n\n"
                f"- **Local Date**: {now_local.strftime('%A, %B %d, %Y')}\n"
                f"- **Local Time**: {now_local.strftime('%I:%M:%S %p')} ({tz_name})\n"
                f"- **UTC Time**: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"- **Day of Week**: {now_local.strftime('%A')}\n"
                f"- **Calendar Week**: Week {week_num} (Day {day_of_year} of {now_local.year})\n"
                f"- **ISO Timestamp**: `{now_local.isoformat()}`"
            )
        except Exception as e:
            return f"Error retrieving date/time: {str(e)}"
