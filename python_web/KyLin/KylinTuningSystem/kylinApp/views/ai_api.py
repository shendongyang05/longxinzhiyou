#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KyLin系统AI优化API视图

这个模块提供了与AI服务（扣子平台）交互的API接口，包括：
- 会话管理
- 流式对话
- 同步对话
- AI优化推理
- 策略执行

主要功能：
1. 创建和管理AI对话会话
2. 支持流式和非流式AI对话
3. 系统状态分析和优化建议
4. 执行AI生成的优化策略
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

# 配置日志记录器
logger = logging.getLogger(__name__)

# 尝试导入SSE客户端，用于流式对话
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

# 导入系统工具模块
from ..model.SocketServer import select_client
from kylinApp.util import dict_to_custom_str, get_info_to_ai

# ==================== AI配置区域 ====================
# 扣子平台配置信息
COZE_CONFIG = {
    "BOT_ID": "7525399030261284916",  # 机器人ID
    "ACCESS_TOKEN": "pat_g66hT0gq8592rgYgnGTW7l6T7bturLPbYpYbgsk1j7Zd7kFvPiMIc6Ha5VlHphFk",  # 访问令牌
    "BASE_URL": "https://api.coze.cn"  # API基础URL
}

# 获取AI配置（当前使用扣子平台配置）
AI_CONFIG = COZE_CONFIG
BOT_ID = AI_CONFIG.get("BOT_ID", "")
ACCESS_TOKEN = AI_CONFIG.get("ACCESS_TOKEN", "")
BASE_URL = AI_CONFIG.get("BASE_URL", "")

# 设置HTTP请求头
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",  # Bearer认证
    "Content-Type": "application/json"  # JSON内容类型
}

# ==================== 核心功能函数 ====================

def create_conversation(user_id: str) -> str:
    """
    创建AI对话会话
    
    Args:
        user_id (str): 用户唯一标识符
        
    Returns:
        str: 会话ID
        
    Raises:
        RuntimeError: 当API调用失败时
    """
    url = f"{BASE_URL}/v1/conversation/create"
    body = {
        "bot_id": BOT_ID,
        "user_id": user_id,
        "auto_save_history": True  # 自动保存对话历史
    }
    
    # 发送POST请求创建会话
    resp = requests.post(url, headers=HEADERS, json=body, timeout=10)
    resp.raise_for_status()  # 检查HTTP状态码
    
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(data)
    
    return data["data"]["id"]

def chat_stream(conversation_id: str, user_id: str, query: str, capture_result=True):
    """
    流式对话：逐字打印AI回答
    
    Args:
        conversation_id (str): 会话ID
        user_id (str): 用户ID
        query (str): 用户查询内容
        capture_result (bool): 是否捕获完整结果
        
    Returns:
        str or None: 如果capture_result为True返回完整结果，否则返回None
        
    Raises:
        ImportError: 当sseclient-py未安装时
    """
    url = f"{BASE_URL}/v3/chat?conversation_id={conversation_id}"
    body = {
        "bot_id": BOT_ID,
        "user_id": user_id,
        "additional_messages": [
            {"role": "user", "content": query, "content_type": "text"}
        ],
        "stream": True,  # 启用流式响应
        "auto_save_history": True
    }
    
    try:
        # 发送流式请求
        response = requests.post(url, headers=HEADERS, json=body, stream=True, timeout=30)
        response.raise_for_status()  # 检查HTTP状态码
        
        # 检查SSE客户端是否可用
        if not SSEClient:
            raise ImportError("sseclient-py 未安装，无法使用流式对话")
            
        # 创建SSE客户端处理流式响应
        client = SSEClient(response)
        
        if capture_result:
            # 捕获完整结果模式
            full_result = ""
            logger.info("接收AI回答开始")
            
            # 遍历所有SSE事件
            for event in client.events():
                if event.event == "conversation.message.delta":
                    try:
                        data = json.loads(event.data)
                        content = data.get("content", "")
                        if content:
                            full_result += content
                            logger.debug(f"收到内容片段: {content}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"解析SSE事件数据失败: {e}, 原始数据: {event.data}")
                        continue
                elif event.event == "conversation.message.complete":
                    logger.info("AI回答完成")
                    break
                elif event.event == "error":
                    logger.error(f"SSE事件错误: {event.data}")
                    break
                    
            logger.info(f"接收AI回答完成，总长度: {len(full_result)}")
            return full_result if full_result.strip() else None
        else:
            # 仅打印模式，不返回结果
            logger.info("接收AI回答开始")
            for event in client.events():
                if event.event == "conversation.message.delta":
                    try:
                        data = json.loads(event.data)
                        content = data.get("content", "")
                        if content:
                            print(content, end='', flush=True)
                    except json.JSONDecodeError:
                        continue
            logger.info("接收AI回答完成")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("请求超时")
        raise RuntimeError("请求超时，请稍后重试")
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        raise RuntimeError(f"请求失败: {e}")
    except Exception as e:
        logger.error(f"流式对话异常: {e}")
        raise e

def chat_sync(conversation_id: str, user_id: str, query: str) -> str:
    """
    非流式对话：直接返回完整回答
    
    Args:
        conversation_id (str): 会话ID
        user_id (str): 用户ID
        query (str): 用户查询内容
        
    Returns:
        str: AI的完整回答
        
    Raises:
        RuntimeError: 当API调用失败时
    """
    url = f"{BASE_URL}/v3/chat?conversation_id={conversation_id}"
    body = {
        "bot_id": BOT_ID,
        "user_id": user_id,
        "additional_messages": [
            {"role": "user", "content": query, "content_type": "text"}
        ],
        "stream": False,  # 禁用流式响应
        "auto_save_history": True
    }
    
    # 发送同步请求
    resp = requests.post(url, headers=HEADERS, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    logger.debug(f"API响应: {data}")  # 调试信息
    
    if data.get("code") != 0:
        raise RuntimeError(data)
    
    # 检查不同的响应格式并提取内容
    if "data" in data:
        if "messages" in data["data"] and data["data"]["messages"]:
            content = data["data"]["messages"][-1]["content"]
            if isinstance(content, str) and content.strip():
                return content
        elif "content" in data["data"]:
            content = data["data"]["content"]
            if isinstance(content, str) and content.strip():
                return content
        elif "message" in data["data"]:
            content = data["data"]["message"]
            if isinstance(content, str) and content.strip():
                return content
        else:
            # 如果data中没有预期的字段，尝试直接返回data
            data_str = str(data["data"])
            if data_str and data_str.strip():
                return data_str
    elif "content" in data:
        content = data["content"]
        if isinstance(content, str) and content.strip():
            return content
    elif "message" in data:
        content = data["message"]
        if isinstance(content, str) and content.strip():
            return content
    
    # 如果没有找到有效的响应内容，记录日志并返回None
    logger.warning(f"未找到有效的响应内容，完整响应: {data}")
    return None

def _wait_for_async_result(conversation_id: str, user_id: str, query: str) -> str:
    """
    等待异步结果 - 使用流式调用避免会话冲突
    
    Args:
        conversation_id (str): 会话ID
        user_id (str): 用户ID
        query (str): 查询内容
        
    Returns:
        str: AI回答结果或默认建议
    """
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
            # 返回默认建议
            return '{"分析": "系统当前负载较低，无需进行优化。", "建议": "建议观察系统状态", "命令": "command:echo \'系统状态良好，无需优化\'", "预期效果": "确认系统状态良好"}'

def ai_optimize_infer():
    """
    使用工作流调用实现AI优化推理
    
    这个函数会：
    1. 获取系统状态数据
    2. 调用AI工作流进行分析
    3. 返回结构化的优化建议
        
    Returns:
        str: JSON格式的优化建议，包含分析、建议、命令和预期效果
    """
    try:
        logger.info("开始AI推理流程...")
        
        # 获取系统数据
        try:
            system_data = get_info_to_ai()
            logger.info("系统数据获取成功")
        except Exception as e:
            logger.error(f"获取系统数据失败: {e}")
            # 使用默认系统数据
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
                    # 检查是否包含必需的字段
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

# ==================== API接口函数 ====================

@csrf_exempt
def ai_optimize_api(request):
    """
    AI优化API接口（简化：直传直返）
    
    功能说明：
    - 接收POST请求体作为问题（优先使用 question/q/text/prompt 字段；否则将整个JSON序列化为字符串）
    - 不拼接提示词，不做结果结构化或二次加工
    - 调用工作流获取回答，直接以 answer 返回
    
    Args:
        request: Django HTTP请求对象
        
    Returns:
        JsonResponse: 包含success状态和answer回答的JSON响应
        
    HTTP方法:
        POST: 发送问题到AI服务
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

        # 提取问题文本（按优先级顺序）
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
    """
    执行AI策略命令
    
    这个接口用于执行AI生成的优化策略中的具体命令。
    支持多种策略格式，能够自动提取可执行的命令并远程执行。
    
    Args:
        request: Django HTTP请求对象，包含IP、端口和策略信息
        
    Returns:
        JsonResponse: 包含执行结果的JSON响应
        
    HTTP方法:
        POST: 发送策略执行请求
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    try:
        # 解析请求数据
        data = json.loads(request.body.decode("utf8"))
        logger.info(f"接收到的数据: {data}")
        
        # 提取必要参数
        ip = data.get("ip")
        port = data.get("port")
        strategy = data.get("strategy")
        
        logger.info(f"解析的参数 - IP: {ip}, Port: {port}, Strategy: {strategy}")
        
        # 参数验证
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
        
        # 从策略中提取命令（支持多种策略格式）
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

@csrf_exempt
def doubao_chat(request):
    """
    AI聊天接口（使用Groq API）
    
    这个接口用于处理前端AI小助手的聊天请求，将请求转发到Groq API。
    
    Args:
        request: Django HTTP请求对象，包含message和system_context
        
    Returns:
        JsonResponse: 包含success状态和response回答的JSON响应
        
    HTTP方法:
        POST: 发送聊天消息
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    try:
        # 解析请求数据
        data = json.loads(request.body.decode("utf8"))
        user_message = data.get('message', '')
        system_context = data.get('system_context', '')
        
        if not user_message:
            return JsonResponse({
                'success': False, 
                'error': '消息内容不能为空'
            }, status=400)
        
        # 构建消息数组
        messages = []
        if system_context:
            messages.append({
                "role": "system",
                "content": system_context
            })
        
        messages.append({
            "role": "user", 
            "content": user_message
        })
        #aaaa
        # 调用Groq API
        try: 
            logger.info("调用Groq API...")
            groq_url = "https://api.groq.com/openai/v1/chat/completions"
            groq_headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer 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"
            }
            groq_data = {
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": messages
            }
            
            response = requests.post(
                groq_url, 
                headers=groq_headers, 
                json=groq_data, 
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 提取AI回复
            if "choices" in result and len(result["choices"]) > 0:
                ai_response = result["choices"][0]["message"]["content"]
                logger.info(f"Groq API调用成功，响应长度: {len(ai_response)}")
                return JsonResponse({
                    'success': True,
                    'response': ai_response
                })
            else:
                logger.warning("Groq API返回格式异常")
                raise ValueError("API返回格式异常")
                
        except Exception as e:
            logger.error(f"Groq API调用失败: {e}")
            # 如果API调用失败，使用本地回复
            local_response = get_local_response(user_message)
            return JsonResponse({
                'success': True,
                'response': local_response
            })
            
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'error': f'JSON解析失败: {str(e)}'
        }, status=400)
    except Exception as e:
        logger.error(f"AI聊天接口异常: {e}")
        return JsonResponse({
            'success': False,
            'error': f'请求处理失败: {str(e)}'
        }, status=500)

def get_local_response(user_message):
    """
    获取本地回复（作为备用）
    
    Args:
        user_message (str): 用户消息
        
    Returns:
        str: 本地回复内容
    """
    message = user_message.lower()
    
    # 系统监控相关
    if '监控' in message or '告警' in message:
        return '我可以帮您监控系统状态！当前监控功能包括：CPU、内存、磁盘、网络性能监控。您可以在数据采集页面设置阈值，当数据超过阈值时会自动告警。'
    
    # 数据采集相关
    if '采集' in message or '数据' in message:
        return '数据采集功能可以帮助您实时监控服务器性能。您可以：1. 选择要监控的服务器 2. 设置性能阈值 3. 开始数据采集 4. 查看实时数据和分析报告。'
    
    # 阈值设置相关
    if '阈值' in message or '设置' in message:
        return '阈值设置可以帮您监控系统性能：CPU使用率阈值、内存使用率阈值、磁盘使用率阈值、网络速率阈值。当性能指标超过阈值时会自动告警。'
    
    # 大屏监控相关
    if '大屏' in message or 'dashboard' in message:
        return '大屏监控页面可以实时显示系统性能数据，包括CPU、内存、磁盘、网络使用率的圆形进度图。您可以点击侧边栏的"大屏监控"进入。'
    
    # 数据中台相关
    if '中台' in message or '数据中台' in message:
        return '数据中台页面提供了系统性能数据的综合展示，包括各种性能指标的可视化图表和分析报告。'
    
    # 性能分析相关
    if '分析' in message or '性能' in message:
        return '系统提供了多种性能分析功能：CPU性能分析、内存性能分析、磁盘性能分析、网络性能分析。您可以在侧边栏找到相应的分析页面。'
    
    # 帮助相关
    if '帮助' in message or '怎么' in message or '如何' in message:
        return '我是您的AI小助手！我可以帮您：1. 解答系统监控相关问题 2. 指导数据采集操作 3. 解释各种功能用法 4. 提供技术支持。'
    
    # 问候相关
    if '你好' in message or 'hi' in message or 'hello' in message:
        return '您好！我是您的AI小助手 🤖 很高兴为您服务！我可以帮您解答系统监控、数据采集、性能分析等相关问题。'
    
    # 默认回复
    return '我理解您的问题，但可能需要更多信息。您可以询问关于系统监控、数据采集、性能分析等方面的问题，我会尽力帮助您！' 