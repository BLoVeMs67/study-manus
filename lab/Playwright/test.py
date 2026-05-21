import asyncio

from playwright.async_api import async_playwright


async def example() -> None:
    # 1.创建一个playwright异步实例
    async with async_playwright() as playwright:
        # 2.连接到cdp获取浏览器实例
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
        default_context = browser.contexts[0]

        # 3.获取当前上下文的第一个页面
        page = default_context.pages[0]
        print("页面标题:", await page.title())
        print("页面URL:", page.url)

        # 4.新增页面并且跳转到imooc.com
        page = await default_context.new_page()
        await page.goto("https://www.imooc.com")

        # 5.在页面上执行js获取结果
        href = await page.evaluate('() => document.location.href')
        print("js执行结果:", href)

        # 6.截图
        await page.screenshot(path="resources/screenshot.png")
        await page.screenshot(path="resources/screenshot-full.png", full_page=True)

if __name__ == "__main__":
    asyncio.run(example())