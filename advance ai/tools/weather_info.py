import urllib.parse
import httpx
from typing import Dict, Any
from .base import BaseTool
from .registry import register_tool

@register_tool
class WeatherInfoTool(BaseTool):
    name = "weather_info"
    description = (
        "Retrieves real-time global weather, temperature, humidity, wind speed, and conditions for any city or location worldwide. "
        "Operates completely free with zero API keys required."
    )
    parameters = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name, region, or country (e.g. 'Tokyo', 'London', 'New York', 'Mumbai', 'Paris', 'Sydney')."
            }
        },
        "required": ["location"]
    }

    async def run(self, location: str, **kwargs) -> str:
        loc = location.strip()
        if not loc:
            return "Error: Location cannot be empty."

        encoded_loc = urllib.parse.quote(loc)
        headers = {"User-Agent": "curl/7.68.0"}

        # 1. Primary provider: wttr.in (Fast, global, JSON API without keys)
        try:
            async with httpx.AsyncClient(headers=headers, timeout=8.0, follow_redirects=True) as client:
                url = f"https://wttr.in/{encoded_loc}?format=j1"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    curr = data.get("current_condition", [{}])[0]
                    area = data.get("nearest_area", [{}])[0]

                    city = area.get("areaName", [{}])[0].get("value", loc.title())
                    country = area.get("country", [{}])[0].get("value", "")
                    region = area.get("region", [{}])[0].get("value", "")

                    place_parts = [city]
                    if region and region != city:
                        place_parts.append(region)
                    if country:
                        place_parts.append(country)
                    place_str = ", ".join(place_parts)

                    temp_c = curr.get("temp_C", "N/A")
                    feels_c = curr.get("FeelsLikeC", "N/A")
                    desc = curr.get("weatherDesc", [{}])[0].get("value", "Clear")
                    humidity = curr.get("humidity", "N/A")
                    wind_kmph = curr.get("windspeedKmph", "N/A")
                    precip_mm = curr.get("precipMM", "0.0")
                    uv_index = curr.get("uvIndex", "N/A")

                    return (
                        f"🌍 **Live Weather Report: {place_str}**\n"
                        f"- **Conditions**: {desc}\n"
                        f"- **Temperature**: {temp_c}°C (Feels like {feels_c}°C)\n"
                        f"- **Humidity**: {humidity}%\n"
                        f"- **Wind Speed**: {wind_kmph} km/h\n"
                        f"- **Precipitation**: {precip_mm} mm\n"
                        f"- **UV Index**: {uv_index}"
                    )
        except Exception:
            pass

        # 2. Fallback provider: wttr.in clean one-liner
        try:
            async with httpx.AsyncClient(headers=headers, timeout=6.0, follow_redirects=True) as client:
                url = f"https://wttr.in/{encoded_loc}?format=3"
                resp = await client.get(url)
                if resp.status_code == 200 and resp.text.strip():
                    return f"🌍 **Live Weather**: {resp.text.strip()}"
        except Exception as e:
            return f"Error retrieving live weather for '{loc}': {str(e)}"

        return f"Could not retrieve weather data for '{loc}' at this time. Please try again."
