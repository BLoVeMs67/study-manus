# remote别看了，远程浏览器要钱的

import os

from browser_use.llm.openai.chat import ChatOpenAI
from browser_use_sdk import BrowserUse
from dotenv import load_dotenv
from pathlib import Path

import asyncio
from browser_use import Browser, Agent, ChatBrowserUse

env_path = Path(__file__).parent / ".env"

load_dotenv(env_path)

client = BrowserUse(api_key=os.environ["POIXE_API_KEY"], base_url=os.environ["POIXE_BASE_URL"])

task = client.tasks.create_task(
    task="帮我看一下慕课网有哪些关于AI的体系课。",
    llm="gpt-4o-mini",
)

for step in task.stream():
    print(f"步骤{step.number}: ", step)
    print("=========================")