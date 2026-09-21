import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"BROWSER LOG: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        await page.goto('http://localhost:8000')
        await page.click('#auth-guest-btn')
        await page.wait_for_timeout(1000)
        await page.fill('#user-input', 'output nahi aa raha hai')
        await page.click('#send-btn')
        await page.wait_for_timeout(5000)
        html = await page.locator('.message-content').last.inner_html()
        with open("dom.html", "w", encoding="utf-8") as f:
            f.write(html)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
