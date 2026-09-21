import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://localhost:8000')
        await page.click('#auth-guest-btn')
        await page.wait_for_timeout(1000)
        await page.fill('#user-input', 'output nahi aa raha hai')
        await page.click('#send-btn')
        await page.wait_for_timeout(3000)
        await page.screenshot(path='screenshot.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
