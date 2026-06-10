# uv add a2a-sdk[http-server] openai uvicorn fastapi
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from openai import AsyncOpenAI
from a2a.types import Message, Part, Role

class DeepSeekAgent:
    @classmethod
    async def invoke(cls, query: str) -> str:
        client = AsyncOpenAI(
            base_url="https://api.deepseek.com",
            api_key="sk-07ed93b0a3fa4c4eaff9ce677eef9d6b"
        )

        response = await client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[{"role": "user", "content": query}]
        )

        return f"推理内容：{response.choices[0].message.reasoning_content}\n\n答案：{response.choices[0].message.content}"

class DeepSeekAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = DeepSeekAgent()

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        # query = context.message.parts[0].root.text
        query = context.get_user_input()
        answer = await self.agent.invoke(query)
        #await event_queue.enqueue_event(Message(answer))
        await event_queue.enqueue_event(
            Message(
                role=Role.ROLE_AGENT,
                parts=[Part(text=answer)]
            )
        )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception("暂不支持取消")
