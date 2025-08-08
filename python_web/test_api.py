#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 直接验证AI接口
"""

import json
import uuid
import requests
from sseclient import SSEClient

# 完全复制aaa.py的配置
BOT_ID = "7525399030261284916"
ACCESS_TOKEN = "pat_H9dxbfanHsWDv6Fw7hofhfkwe2Sdy6YVuJBnrLSxIY0lAC7DZjPklsQypLsXn5Su"
BASE_URL = "https://api.coze.cn"
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def create_conversation(user_id: str) -> str:
    """创建会话并返回 conversation_id"""
    url = f"{BASE_URL}/v1/conversation/create"
    body = {
        "bot_id": BOT_ID,
        "user_id": user_id,
        "auto_save_history": True
    }
    print(f"发送请求: {url}")
    print(f"请求体: {body}")
    
    resp = requests.post(url, headers=HEADERS, json=body, timeout=10)
    print(f"状态码: {resp.status_code}")
    resp.raise_for_status()
    data = resp.json()
    print(f"响应数据: {data}")
    
    if data.get("code") != 0:
        raise RuntimeError(data)
    return data["data"]["id"]

def chat_stream(conversation_id: str, user_id: str, query: str, capture=True):
    """流式对话：逐字打印 AI 回答，可选择捕获完整结果"""
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
    print(f"发送流式请求: {url}")
    print(f"请求体: {body}")
    
    response = requests.post(url, headers=HEADERS, json=body, stream=True)
    print(f"状态码: {response.status_code}")
    
    client = SSEClient(response)
    full_result = "" if capture else None
    
    print("Answer: ", end="", flush=True)
    for event in client.events():
        if event.event == "conversation.message.delta":
            data = json.loads(event.data)
            content = data.get("content", "")
            print(content, end="", flush=True)
            if capture and content:
                full_result += content
    print()  # 换行
    return full_result

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
    print(f"发送同步请求: {url}")
    print(f"请求体: {body}")
    
    resp = requests.post(url, headers=HEADERS, json=body, timeout=30)
    print(f"状态码: {resp.status_code}")
    resp.raise_for_status()
    
    data = resp.json()
    print(f"响应数据: {data}")
    
    if data.get("code") != 0:
        raise RuntimeError(data)
    return data["data"]["messages"][-1]["content"]

def main():
    # 模拟系统数据
    system_data = {
        "cpu": {
            "percent": 78.5,
            "count": 8,
            "user_time": 3600,
            "system_time": 1800,
            "idle_time": 9800,
            "wait_io": 560
        },
        "memory": {
            "percent": 85.2,
            "total": "16GB",
            "used": "13.6GB",
            "free": "2.4GB" 
        },
        "disk": {
            "percent": 62.5,
            "total": "500GB",
            "used": "312.5GB",
            "free": "187.5GB"
        }
    }
    
    # 构造 prompt 强调中文回答
    query = f"""我需要你基于下面的系统性能数据，提供系统优化建议和可执行的命令。请务必使用中文回答，不要使用英文回复。

系统数据：
{json.dumps(system_data, ensure_ascii=False, indent=2)}

请提供：
1. 系统性能分析
2. 具体的优化建议
3. 可执行的Linux命令（以command:开头）
4. 预期效果

请以JSON格式返回，包含"分析"、"建议"、"命令"、"预期效果"等字段。
这是一个很重要的任务，请确保使用中文回复，并提供准确的系统调优建议。"""

    print("====== 开始测试 ======")
    user_id = str(uuid.uuid4())
    print(f"用户ID: {user_id}")
    
    try:
        conversation_id = create_conversation(user_id)
        print(f"会话创建成功: {conversation_id}")
        
        # 获取完整结果
        print("\n开始流式对话并捕获结果...")
        result = chat_stream(conversation_id, user_id, query, capture=True)
        
        print("\n完整结果:")
        print("-" * 50)
        print(result)
        print("-" * 50)
        
        # 如果结果中包含某些不符合要求的关键词，尝试同步对话
        if "适用版本" in result or len(result) < 100:
            print("\n流式结果不满足要求，尝试发送继续指令...")
            continue_result = chat_stream(
                conversation_id, 
                user_id, 
                "请继续提供系统优化建议，必须是中文JSON格式，包含分析、建议、命令和预期效果字段", 
                capture=True
            )
            
            print("\n继续指令结果:")
            print("-" * 50)
            print(continue_result)
            print("-" * 50)
            
        print("\n测试完成")
    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 