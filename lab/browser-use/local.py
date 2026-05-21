import os

from browser_use.llm.openai.chat import ChatOpenAI
from dotenv import load_dotenv
from pathlib import Path

import asyncio
from browser_use import Browser, Agent, ChatBrowserUse

env_path = Path(__file__).parent / ".env"

load_dotenv(env_path)

async def example():
    # 1.初始化浏览器实例和llm实例
    browser = Browser()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("POIXE_API_KEY"),
        base_url=os.getenv("POIXE_BASE_URL"),
    )

    # 2.构建Browser-use智能体
    agent = Agent(
        task="帮我看一下itjc8.com有哪些关于AI的体系课，不要保存文件，直接总结返回结果。",
        llm=llm,
        browser=browser,
    )

    # 3.运行agent并返回结果
    return await agent.run()

if __name__ == "__main__":
    history = asyncio.run(example())
    print(history)