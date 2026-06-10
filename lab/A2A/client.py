import uuid
from typing import Any

import httpx
from a2a.client import A2ACardResolver, create_client, ClientConfig
from a2a.types import SendMessageRequest, Message, Role, Part
import grpc
async def main() -> None:
    base_url = "http://localhost:9999"

    # 创建httpx客户端上下文
    async with httpx.AsyncClient() as httpx_client:
        # 创建Agent卡片解析器
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        card = await resolver.get_agent_card()
        # print("Agent Card:", card)

        config = ClientConfig(
            grpc_channel_factory=grpc.aio.insecure_channel
        )

        # 创建一个a2a客户端
        client = await create_client(card, client_config=config)

        # 发送消息载体
        # send_message_payload: dict[str, Any] = {
        #     "message": {
        #         "message_id": uuid.uuid4().hex,
        #         "role": "ROLE_USER",
        #         "part": [
        #             {"text": "帮我随机生成10个字符串"}
        #         ]
        #     }
        # }
        message = Message(
            role=Role.ROLE_USER,
            message_id=str(uuid.uuid4()),
            parts=[Part(text="帮我随机生成10个字符串")],
        )

        request = SendMessageRequest(message=message)

        response = client.send_message(request)

        print(response)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())