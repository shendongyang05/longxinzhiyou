import json
import sys
import uuid
import requests
from sseclient import SSEClient

# ========= 配置区 =========
BOT_ID = "7525399030261284916"
ACCESS_TOKEN = "pat_H9dxbfanHsWDv6Fw7hofhfkwe2Sdy6YVuJBnrLSxIY0lAC7DZjPklsQypLsXn5Su"
BASE_URL = "https://api.coze.cn"
# =========================

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type":  "application/json"
}

def create_conversation(user_id: str) -> str:
    """创建会话并返回 conversation_id"""
    url = f"{BASE_URL}/v1/conversation/create"
    body = {
        "bot_id": BOT_ID,
        "user_id": user_id,
        "auto_save_history": True
    }
    resp = requests.post(url, headers=HEADERS, json=body, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(data)
    return data["data"]["id"]

def chat_stream(conversation_id: str, user_id: str, query: str):
    """流式对话：逐字打印 AI 回答"""
    url = f"{BASE_URL}/v3/chat?conversation_id={conversation_id}"
    body = {
        "bot_id": BOT_ID,
        "user_id": user_id,
        "additional_messages": [
            {"role": "user", "content": query, "content_type": "text"}
        ],
        "stream": True,
        "auto_save_history": True
    }
    response = requests.post(url, headers=HEADERS, json=body, stream=True)
    client = SSEClient(response)
    print("Answer: ", end="", flush=True)
    for event in client.events():
        if event.event == "conversation.message.delta":
            data = json.loads(event.data)
            print(data["content"], end="", flush=True)
    print()  # 换行

def chat_sync(conversation_id: str, user_id: str, query: str) -> str:
    """非流式对话：直接返回完整回答"""
    url = f"{BASE_URL}/v3/chat?conversation_id={conversation_id}"
    body = {
        "bot_id": BOT_ID,
        "user_id": user_id,
        "additional_messages": [
            {"role": "user", "content": query, "content_type": "text"}
        ],
        "stream": False,
        "auto_save_history": True
    }
    resp = requests.post(url, headers=HEADERS, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(data)
    return data["data"]["messages"][-1]["content"]

def main():
    user_id = str(uuid.uuid4())          # 每次启动脚本视为一个新用户
    conversation_id = create_conversation(user_id)
    print("=== 已连接龙芯智优国产操作系统智能体，输入 exit 退出 ===")
    while True:
        try:
            print("\nQuestion:")
            lines = []
            while True:
                line = input()
                if line == '':
                    break
                lines.append(line)
            q = '\n'.join(lines).strip()
            if q.lower() in {"exit", "quit"}:
                break
            # 想体验流式就调 chat_stream，想直接拿结果就 chat_sync
            chat_stream(conversation_id, user_id, q)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    main()