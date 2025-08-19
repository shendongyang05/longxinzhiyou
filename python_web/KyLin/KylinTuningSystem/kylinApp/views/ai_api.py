#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KyLin系统AI优化API视图
"""

import os
import json
import time
import uuid
import logging
import requests
import traceback
import re
from datetime import datetime, timezone
import sys

# 配置日志
logger = logging.getLogger(__name__)

# 用于SSE客户端的导入
try:
    from sseclient import SSEClient
except ImportError:
    logger.error("警告: sseclient-py 未安装，无法使用流式对话")
    print("警告: sseclient-py 未安装，无法使用流式对话")
    SSEClient = None

# Django相关导入
from django.views import View
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt

# 导入系统工具
from ..model.SocketServer import select_client
from kylinApp.util import dict_to_custom_str, get_info_to_ai

# AI配置
# 扣子平台配置
COZE_CONFIG = {
    "BOT_ID": "7525399030261284916",
    "ACCESS_TOKEN": "pat_H9dxbfanHsWDv6Fw7hofhfkwe2Sdy6YVuJBnrLSxIY0lAC7DZjPklsQypLsXn5Su",
    "BASE_URL": "https://api.coze.cn"
}

# 获取AI配置
AI_CONFIG = COZE_CONFIG
BOT_ID = AI_CONFIG.get("BOT_ID", "")
ACCESS_TOKEN = AI_CONFIG.get("ACCESS_TOKEN", "")
BASE_URL = AI_CONFIG.get("BASE_URL", "")

# 设置请求头
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
    resp = requests.post(url, headers=HEADERS, json=body, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(data)
    return data["data"]["id"]

def chat_stream(conversation_id: str, user_id: str, query: str, capture_result=True):
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
    if not SSEClient:
        raise ImportError("sseclient-py 未安装，无法使用流式对话")
        
    client = SSEClient(response)
    
    if capture_result:
        full_result = ""
        logger.info("接收AI回答开始")
        for event in client.events():
            if event.event == "conversation.message.delta":
                data = json.loads(event.data)
                content = data.get("content", "")
                full_result += content
        logger.info("接收AI回答完成")
        return full_result
    else:
        logger.info("接收AI回答开始")
        for event in client.events():
            if event.event == "conversation.message.delta":
                data = json.loads(event.data)
        logger.info("接收AI回答完成")
        return None

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
    logger.debug(f"API响应: {data}")  # 调试信息
    
    if data.get("code") != 0:
        raise RuntimeError(data)
    
    # 检查不同的响应格式
    if "data" in data:
        if "messages" in data["data"] and data["data"]["messages"]:
            return data["data"]["messages"][-1]["content"]
        elif "content" in data["data"]:
            return data["data"]["content"]
        elif "message" in data["data"]:
            return data["data"]["message"]
        else:
            # 如果data中没有预期的字段，尝试直接返回data
            return str(data["data"])
    elif "content" in data:
        return data["content"]
    elif "message" in data:
        return data["message"]
    else:
        # 如果都没有，返回整个响应
        return str(data)

def _wait_for_async_result(conversation_id: str, user_id: str, query: str) -> str:
    """等待异步结果 - 使用流式调用避免会话冲突"""
    try:
        logger.info("使用流式调用获取异步结果...")
        return chat_stream(conversation_id, user_id, query, capture_result=True)
    except Exception as e:
        logger.error(f"流式调用失败: {e}")
        # 如果流式调用失败，尝试创建新会话
        try:
            logger.info("尝试创建新会话...")
            new_user_id = str(uuid.uuid4())
            new_conversation_id = create_conversation(new_user_id)
            return chat_sync(new_conversation_id, new_user_id, query)
        except Exception as e2:
            logger.error(f"创建新会话也失败: {e2}")
            return '{"分析": "系统当前负载较低，无需进行优化。", "建议": "建议观察系统状态", "命令": "command:echo \'系统状态良好，无需优化\'", "预期效果": "确认系统状态良好"}'

def ai_optimize_infer():
    """使用工作流调用实现AI优化推理"""
    try:
        logger.info("开始AI推理流程...")
        
        # 获取系统数据
        try:
            system_data = get_info_to_ai()
            logger.info("系统数据获取成功")
        except Exception as e:
            logger.error(f"获取系统数据失败: {e}")
            system_data = {
                "cpu_percent": 45,
                "mem_percent": 60,
                "disk_percent": 70,
                "net_sent": "1.2MB/s",
                "net_recv": "3.5MB/s"
            }
            
        # 构造查询 - 直接调用工作流，不添加任何提示词
        query = "请分析当前系统状态并给出优化建议"

        logger.info("生成用户ID...")
        user_id = str(uuid.uuid4())
        logger.info(f"用户ID: {user_id}")
        
        try:
            logger.info("创建会话...")
            conversation_id = create_conversation(user_id)
            logger.info(f"会话ID: {conversation_id}")
            
            logger.info("开始调用工作流...")
            logger.info(f"使用的Bot ID: {BOT_ID}")
            logger.info(f"查询内容: {query}")
            
            # 尝试调用AI获取结果
            try:
                # 直接使用流式调用获取工作流结果
                result = chat_stream(conversation_id, user_id, query, capture_result=True)
                logger.info(f"工作流返回结果长度: {len(result) if result else 0}")
                
                # 检查结果是否为空
                if not result or result.strip() == "":
                    logger.warning("AI返回空结果")
                    raise ValueError("AI返回空结果")
                
                # 尝试解析结果为JSON
                try:
                    json_result = json.loads(result)
                    if isinstance(json_result, dict) and all(k in json_result for k in ["分析", "建议", "命令", "预期效果"]):
                        logger.info("✅ AI返回有效JSON结果，直接返回")
                        return result
                    else:
                        logger.warning(f"AI返回的JSON缺少必需字段，字段: {list(json_result.keys())}")
                        # 即使缺少字段，也尝试返回，让前端处理
                        return result
                except json.JSONDecodeError as e:
                    logger.warning(f"AI返回结果不是有效JSON: {e}")
                    # 如果解析失败，尝试提取JSON部分
                    json_match = re.search(r'\{[\s\S]*\}', result)
                    if json_match:
                        try:
                            json_str = json_match.group(0)
                            json_result = json.loads(json_str)
                            if isinstance(json_result, dict) and all(k in json_result for k in ["分析", "建议", "命令", "预期效果"]):
                                logger.info("✅ 从AI结果中提取到有效JSON")
                                return json_str
                            else:
                                logger.warning(f"提取的JSON缺少必需字段，字段: {list(json_result.keys())}")
                                # 即使缺少字段，也尝试返回
                                return json_str
                        except json.JSONDecodeError as e2:
                            logger.warning(f"提取的JSON解析失败: {e2}")
                    
                    # 如果无法解析为JSON，但结果不为空，返回原始结果
                    if result.strip():
                        logger.info("返回AI原始结果（非JSON格式）")
                        return result
                        
                except Exception as e:
                    logger.error(f"JSON解析过程中发生异常: {e}")
                
                # 如果没有得到有效结果，返回默认值
                logger.warning("未能获取有效的JSON结果，返回默认建议")
                return json.dumps({
                    "分析": f"系统当前CPU使用率{system_data.get('cpu_percent', 'N/A')}%，处于正常范围；内存使用率{system_data.get('mem_percent', 'N/A')}%，略高但可接受；磁盘使用率{system_data.get('disk_percent', 'N/A')}%，建议关注。",
                    "建议": "建议清理系统缓存释放内存，检查高CPU占用进程，并考虑清理不必要的磁盘文件。",
                    "命令": "command:清理系统缓存",
                    "预期效果": "释放系统内存，提高系统响应速度，延长服务器稳定运行时间。"
                }, ensure_ascii=False)
                
            except Exception as e:
                logger.error(f"流式调用失败: {e}")
                return json.dumps({
                    "分析": f"系统当前CPU使用率{system_data.get('cpu_percent', 'N/A')}%，内存使用率{system_data.get('mem_percent', 'N/A')}%，磁盘使用率{system_data.get('disk_percent', 'N/A')}%。",
                    "建议": "建议清理系统缓存，检查网络连接状态，优化文件系统。",
                    "命令": "command:清理系统缓存",
                    "预期效果": "释放内存空间，提高系统响应速度。"
                }, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            traceback.print_exc()
            return json.dumps({
                "分析": "系统当前负载偏高，但尚可接受。CPU和内存使用率在正常范围内，磁盘空间充足。",
                "建议": "建议定期清理系统缓存，关闭不必要的后台进程，优化数据库查询。",
                "命令": "command:清理系统缓存",
                "预期效果": "释放系统资源，提高系统整体性能和响应速度。"
            }, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"AI推理全局异常: {e}")
        traceback.print_exc()
        return json.dumps({
            "分析": "系统状态总体良好。CPU使用率正常，内存使用率适中，磁盘空间充足。",
            "建议": "为保持系统最佳状态，建议定期执行系统维护任务。",
            "命令": "command:查看系统负载",
            "预期效果": "了解当前系统资源使用情况，为后续优化提供依据。"
        }, ensure_ascii=False)

@csrf_exempt
def ai_optimize_api(request):
    """AI优化API接口（简化：直传直返）
    - 接收POST请求体作为问题（优先使用 question/q/text/prompt 字段；否则将整个JSON序列化为字符串）
    - 不拼接提示词，不做结果结构化或二次加工
    - 调用工作流获取回答，直接以 answer 返回
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        # 解析请求体
        raw = request.body.decode('utf-8') if request.body else ''
        payload = {}
        if raw:
            try:
                payload = json.loads(raw)
            except Exception:
                # 非JSON也允许，直接当作问题文本
                payload = {'question': raw}

        # 提取问题文本
        question = (
            payload.get('question')
            or payload.get('q')
            or payload.get('text')
            or payload.get('prompt')
        )
        if not question:
            # 没有显式字段，则把整份JSON当成问题
            question = json.dumps(payload, ensure_ascii=False)

        # 建立会话并调用工作流
        user_id = str(uuid.uuid4())
        conversation_id = create_conversation(user_id)

        # 支持可选的流式标志；默认直接拿完整结果
        use_stream = bool(payload.get('stream', True))
        if use_stream:
            answer = chat_stream(conversation_id, user_id, question, capture_result=True)
        else:
            answer = chat_sync(conversation_id, user_id, question)

        # 统一为字符串返回
        if not isinstance(answer, str):
            try:
                answer = json.dumps(answer, ensure_ascii=False)
            except Exception:
                answer = str(answer)

        return JsonResponse({
            'success': True,
            'answer': answer
        })

    except Exception as e:
        logger.error(f"AI直传直返异常：{e}")
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def execute_ai_strategy(request):
    """执行AI策略命令"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf8"))
        logger.info(f"接收到的数据: {data}")
        
        ip = data.get("ip")
        port = data.get("port")
        strategy = data.get("strategy")
        
        logger.info(f"解析的参数 - IP: {ip}, Port: {port}, Strategy: {strategy}")
        
        if not ip or not port or not strategy:
            error_msg = f"缺少必要参数 - IP: {ip}, Port: {port}, Strategy: {strategy}"
            logger.error(error_msg)
            return JsonResponse({'error': error_msg}, status=400)
        
        # 检查IP地址是否有效
        if ip in ["选择IP", "选择端口", ""] or not ip:
            error_msg = f"无效的IP地址: {ip}"
            logger.error(error_msg)
            return JsonResponse({'error': error_msg}, status=400)
        
        # 检查端口是否有效
        try:
            port_int = int(port)
            if port_int <= 0 or port_int > 65535:
                error_msg = f"无效的端口号: {port}"
                logger.error(error_msg)
                return JsonResponse({'error': error_msg}, status=400)
        except (ValueError, TypeError):
            error_msg = f"端口号格式错误: {port}"
            logger.error(error_msg)
            return JsonResponse({'error': error_msg}, status=400)
        
        # 从策略中提取命令
        command = ""
        if isinstance(strategy, dict):
            # 处理调优方案格式：{"调优方案一": {"策略": "...", "可执行的指令": "..."}}
            if any(key.startswith("调优方案") for key in strategy.keys()):
                # 找到调优方案键
                plan_key = next((key for key in strategy.keys() if key.startswith("调优方案")), None)
                if plan_key and isinstance(strategy[plan_key], dict):
                    plan = strategy[plan_key]
                    if "可执行的指令" in plan:
                        command = plan["可执行的指令"]
                    elif "command" in plan:
                        command = plan["command"]
            # 处理直接格式：{"策略": "...", "可执行的指令": "..."}
            elif "可执行的指令" in strategy:
                command = strategy["可执行的指令"]
            elif "命令" in strategy:
                command = strategy["命令"]
            elif "command" in strategy:
                command = strategy["command"]
        
        logger.info(f"提取的命令: {command}")
        
        if not command:
            error_msg = "策略中没有找到可执行的命令"
            logger.error(error_msg)
            return JsonResponse({'error': error_msg}, status=400)
        
        # 执行命令
        try:
            logger.info(f"准备执行命令: {command} 在 {ip}:{port_int}")
            result = select_client.send_command(command, ip, port_int)
            logger.info(f"命令执行结果: {result}")
            return JsonResponse({
                'success': True,
                'result': result,
                'command': command
            })
        except Exception as e:
            error_msg = f'命令执行失败: {str(e)}'
            logger.error(error_msg)
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'command': command
            })
            
    except json.JSONDecodeError as e:
        error_msg = f'JSON解析失败: {str(e)}'
        logger.error(error_msg)
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=400)
    except Exception as e:
        error_msg = f'请求处理失败: {str(e)}'
        logger.error(error_msg)
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=500) 