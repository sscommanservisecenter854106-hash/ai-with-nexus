import re
import html
import httpx
from html.parser import HTMLParser
from .base import BaseTool
from .registry import register_tool

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ["script", "style", "noscript"]:
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ["script", "style", "noscript"]:
            self.skip = False

    def handle_data(self, d):
        if not self.skip:
            self.fed.append(d)

    def get_text(self):
        text = " ".join(self.fed)
        text = re.sub(r"\s+", " ", text).strip()
        return html.unescape(text)

@register_tool
class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Searches the web for up-to-date information, news, documentation, or facts, "
        "and can also scrape readable text from a specific target URL."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string to look up on the web."
            },
            "url": {
                "type": "string",
                "description": "Optional specific URL to fetch and extract content from."
            }
        }
    }

    async def run(self, query: str = "", url: str = "", **kwargs) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        }

        # If a URL is explicitly requested, fetch and scrape it
        if url and url.startswith("http"):
            try:
                async with httpx.AsyncClient(headers=headers, timeout=12.0, follow_redirects=True) as client:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        return f"Failed to fetch URL: HTTP {resp.status_code}"
                    extractor = HTMLTextExtractor()
                    extractor.feed(resp.text)
                    content = extractor.get_text()
                    # Limit output to 3000 chars
                    return f"[Content from {url}]:\n{content[:3000]}"
            except Exception as e:
                return f"Error fetching URL '{url}': {str(e)}"

        if not query.strip():
            return "Error: Neither query nor URL provided."

        # DuckDuckGo HTML search
        try:
            search_url = "https://html.duckduckgo.com/html/"
            data = {"q": query}
            async with httpx.AsyncClient(headers=headers, timeout=12.0, follow_redirects=True) as client:
                resp = await client.post(search_url, data=data)
                if resp.status_code != 200:
                    # Fallback to DuckDuckGo instant API
                    api_url = f"https://api.duckduckgo.com/?q={query}&format=json"
                    api_resp = await client.get(api_url)
                    if api_resp.status_code == 200:
                        api_data = api_resp.json()
                        abstract = api_data.get("AbstractText", "")
                        heading = api_data.get("Heading", "")
                        if abstract:
                            return f"Result for '{query}':\n{heading}\n{abstract}"
                    return f"Web search returned HTTP status {resp.status_code}."

                raw_html = resp.text

                # Extract result titles and snippets from DDG HTML
                # Pattern matches class="result__snippet" and class="result__url"
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', raw_html, re.DOTALL)
                titles = re.findall(r'<a class="result__url[^>]*>(.*?)</a>', raw_html, re.DOTALL)

                results = []
                for i in range(min(5, len(snippets))):
                    s_extractor = HTMLTextExtractor()
                    s_extractor.feed(snippets[i])
                    snip = s_extractor.get_text()

                    title_str = ""
                    if i < len(titles):
                        t_extractor = HTMLTextExtractor()
                        t_extractor.feed(titles[i])
                        title_str = t_extractor.get_text()

                    results.append(f"Result {i+1} ({title_str}):\n{snip}")

                if results:
                    return "\n\n".join(results)
                else:
                    return f"No direct search results found for: '{query}'."

        except Exception as e:
            return f"Search error for '{query}': {str(e)}"
