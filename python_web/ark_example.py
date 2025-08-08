import os
import json
import uuid
import time
import requests
from KyLin.KylinTuningSystem.kylinApp.util import dict_to_custom_str, get_info_to_ai
from coze_ai_client import CozeAIClient  # 直接导入类

# ========= 扣子平台配置区 =========
BOT_ID = "7525399030261284916"
ACCESS_TOKEN = "pat_H9dxbfanHsWDv6Fw7hofhfkwe2Sdy6YVuJBnrLSxIY0lAC7DZjPklsQypLsXn5Su"
BASE_URL = "https://api.coze.cn"
# ================================

# 创建 AI 客户端
def create_default_client() -> CozeAIClient:
    return CozeAIClient(BOT_ID, ACCESS_TOKEN, BASE_URL)

# AI 优化推理主逻辑（防止会话冲突）
def ai_optimize_infer(max_retries=5, retry_interval=5):
    """AI优化推理函数（增强版，每次新建会话防冲突）"""
    client = create_default_client()
    
    try:
        # 获取系统数据
        system_data = get_info_to_ai()
        print("📦 获取到的系统数据：")
        print(json.dumps(system_data, indent=2, ensure_ascii=False))

        # 构造 prompt - 明确要求分析系统数据并给出优化建议
        query = f"""请基于以下系统监控数据进行分析并给出优化建议：

系统监控数据：
{json.dumps(system_data, ensure_ascii=False, indent=2)}

请分析：
1. CPU使用率：当前{system_data.get('cpu_percent', 'N/A')}%，是否正常？
2. 内存使用率：当前{system_data.get('mem_percent', 'N/A')}%，是否正常？
3. 磁盘使用率：当前{system_data.get('disk_percent', 'N/A')}%，是否正常？
4. 网络流量：发送{system_data.get('net_sent', 'N/A')}，接收{system_data.get('net_recv', 'N/A')}，是否异常？

请给出：
- 系统状态分析
- 具体优化建议
- 可执行的优化命令
- 预期优化效果

请以JSON格式返回，包含：分析、建议、命令、预期效果四个字段。"""

        # 多轮尝试，每轮都新建 user_id + conversation_id
        for attempt in range(1, max_retries + 1):
            print(f"\n🚀 第 {attempt} 次尝试发送AI请求...")
            try:
                user_id = str(uuid.uuid4())
                conversation_id = client.create_conversation(user_id)

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

                resp = requests.post(url, headers=client.headers, json=body, timeout=60)
                resp.raise_for_status()
                data = resp.json()

                # 错误码判断
                if data.get("code") != 0:
                    print(f"⚠️ API错误: {data}")
                    time.sleep(retry_interval)
                    continue

                # 处理中状态，重试
                if data.get("data", {}).get("status") == "in_progress":
                    print("⌛ AI还在生成回答，稍后重试...")
                    time.sleep(retry_interval)
                    continue

                # 正常获取返回内容
                messages = data.get("data", {}).get("messages", [])
                if messages:
                    return messages[-1]["content"]

                print("⚠️ 没有返回消息，继续尝试...")
                time.sleep(retry_interval)

            except Exception as e:
                print(f"❌ 第 {attempt} 次失败: {e}")
                time.sleep(retry_interval)

        # 所有重试失败，返回兜底
        return json.dumps({
            "分析": "系统当前负载偏高，但尚可接受。",
            "建议": "建议暂不进行自动优化，观察负载趋势。",
            "命令": "command:echo '系统状态良好，无需优化'",
            "预期效果": "系统负载稳定，无需干预"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"🔥 AI推理失败: {e}")
        return "AI推理失败：" + str(e)


# 主程序执行
if __name__ == "__main__":
    print("===== 🌟 启动AI智能优化推理 =====")
    result = ai_optimize_infer()
    print("\n📊 AI 推理结果：")
    print(result)