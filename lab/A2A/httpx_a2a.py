import uuid

import httpx
from a2a.types import Message, Role, Part, SendMessageRequest


async def main() -> None:
    base_url = "http://localhost:9999"

    async with httpx.AsyncClient(timeout=600) as httpx_client:
        agent_card_response = await httpx_client.get(f"{base_url}/.well-known/agent-card.json")
        agent_card_response.raise_for_status()
        agent_card = agent_card_response.json()
        print("Agent Card:", agent_card)

        #url = agent_card["supportedInterfaces"][0]["url"]
        url = "http://localhost:9999"
        if url == "":
            return
        # print("POST url:", url)
        # message = Message(
        #     role=Role.ROLE_USER,
        #     message_id=str(uuid.uuid4()),
        #     parts=[Part(text="帮我随机生成10个字符串")],
        # )
        #
        # request = SendMessageRequest(message=message)

        request_body = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "SendMessage",
            "params": {
                "message": {
                    "messageId": "1",
                    "role": "ROLE_USER",
                    "parts": [
                        {"text": "帮我生成10个随机数"}
                    ]
                }
            }
        }

        agent_response = await httpx_client.post(f"{url}", json=request_body)
        agent_response.raise_for_status()
        print("Agent Response:", agent_response.json())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())