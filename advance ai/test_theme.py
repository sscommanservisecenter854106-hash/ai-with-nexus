import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"BROWSER LOG: {msg.text}"))
        
        await page.goto('http://localhost:8000')
        await page.click('#auth-guest-btn')
        await page.wait_for_timeout(1000)
        
        # Inject some markdown code via JS directly to bypass chat typing for speed
        await page.evaluate('''
            const markdown = `
### Python Code Example
\`\`\`python
def calculate_sum(a, b):
    """This function adds two numbers."""
    return a + b
    
print(calculate_sum(5, 10))
\`\`\`
            `;
            window.app.currentAssistantMessageEl = document.createElement('div');
            window.app.currentAssistantMessageEl.className = 'chat-message message-assistant';
            window.app.currentContentEl = document.createElement('div');
            window.app.currentContentEl.className = 'message-content';
            window.app.currentAssistantMessageEl.appendChild(window.app.currentContentEl);
            document.getElementById('chat-messages').appendChild(window.app.currentAssistantMessageEl);
            
            window.app.currentContentEl.innerHTML = window.app.renderMarkdown(markdown);
        ''')
        
        await page.wait_for_timeout(500)
        await page.screenshot(path='screenshot_dark_mode.png')
        
        # Click the theme toggle button
        await page.click('#theme-toggle-btn')
        await page.wait_for_timeout(500)
        await page.screenshot(path='screenshot_light_mode.png')
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
