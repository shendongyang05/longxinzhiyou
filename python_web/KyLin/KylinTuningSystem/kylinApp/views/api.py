#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KyLin系统优化API视图
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

# 配置日志
logger = logging.getLogger(__name__)

# 用于SSE客户端的导入
try:
    from sseclient import SSEClient
except ImportError:
    print("警告: sseclient-py 未安装，无法使用流式对话")
    SSEClient = None

# Django相关导入
from ..models import *
from django.views import View
from django.http import Http404
from ..model.SocketServer import select_client
from ..model.DBSence import dbSceneRecognition
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.http.response import HttpResponse, JsonResponse
from ..utils import encrypt
from kylinApp.util import dict_to_custom_str, get_info_to_ai
from ..utils.background_tasks import task_manager
from ..config import DOUBAO_API_URL, DOUBAO_API_KEY, ARK_API_URL, ARK_API_KEY

# ========= 配置区 =========
BOT_ID = "7525399030261284916"
ACCESS_TOKEN = "pat_H9dxbfanHsWDv6Fw7hofhfkwe2Sdy6YVuJBnrLSxIY0lAC7DZjPklsQypLsXn5Su"
BASE_URL = "https://api.coze.cn"
# =========================

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 直接在api.py中实现AI相关函数
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
        print("接收AI回答: ", end="", flush=True)
        for event in client.events():
            if event.event == "conversation.message.delta":
                data = json.loads(event.data)
                content = data.get("content", "")
                print(content, end="", flush=True)
                full_result += content
        print()  # 换行
        return full_result
    else:
        print("接收AI回答: ", end="", flush=True)
        for event in client.events():
            if event.event == "conversation.message.delta":
                data = json.loads(event.data)
                print(data.get("content", ""), end="", flush=True)
        print()  # 换行
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
    print(f"API响应: {data}")  # 调试信息
    
    if data.get("code") != 0:
        raise RuntimeError(data)
    
    # 检查是否是异步响应（现在直接使用流式调用，不需要这个检查）
    # if "data" in data and data["data"].get("status") == "in_progress":
    #     print("检测到异步响应，开始轮询等待结果...")
    #     return _wait_for_async_result(conversation_id, user_id, query)
    
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
        print("使用流式调用获取异步结果...")
        return chat_stream(conversation_id, user_id, query, capture_result=True)
    except Exception as e:
        print(f"流式调用失败: {e}")
        # 如果流式调用失败，尝试创建新会话
        try:
            print("尝试创建新会话...")
            new_user_id = str(uuid.uuid4())
            new_conversation_id = create_conversation(new_user_id)
            return chat_sync(new_conversation_id, new_user_id, query)
        except Exception as e2:
            print(f"创建新会话也失败: {e2}")
            return '{"分析": "系统当前负载较低，无需进行优化。", "建议": "建议观察系统状态", "命令": "command:echo \'系统状态良好，无需优化\'", "预期效果": "确认系统状态良好"}'

# 直接在api.py中实现AI优化推理函数
def direct_ai_optimize_infer():
    """使用简化的工作流调用实现AI优化推理"""
    try:
        print("开始AI推理流程...")
        
        # 获取系统数据
        system_data = get_info_to_ai()
        print("系统数据获取成功")
            
        # 构造查询 - 明确要求分析系统数据并给出优化建议
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

        print("生成用户ID...")
        user_id = str(uuid.uuid4())
        print(f"用户ID: {user_id}")
        
        try:
            print("创建会话...")
            conversation_id = create_conversation(user_id)
            print(f"会话ID: {conversation_id}")
            
            print("开始调用工作流...")
            print(f"使用的Bot ID: {BOT_ID}")
            print(f"查询内容: {query}")
            # 直接使用流式调用获取工作流结果
            result = chat_stream(conversation_id, user_id, query, capture_result=True)
            print(f"工作流返回结果长度: {len(result) if result else 0}")
            
            # 如果结果为空，返回默认值
            if not result or len(result) < 50:
                print("返回默认回答")
                return json.dumps({
                    "分析": "系统当前负载偏高，但尚可接受。",
                    "建议": "建议暂不进行自动优化，观察负载趋势。",
                    "命令": "command:echo '系统状态良好，无需优化'",
                    "预期效果": "系统负载稳定，无需干预"
                }, ensure_ascii=False)
            
            return result
                
        except Exception as e:
            print(f"API调用失败: {e}")
            traceback.print_exc()
            return json.dumps({
                "分析": "系统当前负载偏高，但尚可接受。",
                "建议": "建议暂不进行自动优化，观察负载趋势。",
                "命令": "command:echo '系统状态良好，无需优化'",
                "预期效果": "系统负载稳定，无需干预"
            }, ensure_ascii=False)
            
    except Exception as e:
        print(f"AI推理全局异常: {e}")
        traceback.print_exc()
        return json.dumps({
            "分析": "系统当前负载偏高，但尚可接受。",
            "建议": "建议暂不进行自动优化，观察负载趋势。",
            "命令": "command:echo '系统状态良好，无需优化'",
            "预期效果": "系统负载稳定，无需干预"
        }, ensure_ascii=False)

# 使用直接实现的AI优化推理函数
ai_optimize_infer = direct_ai_optimize_infer

# 策略包接口（场景化）
STRATEGY_PACKS = {
        "db_speedup": [
            "command:添加数据库缓存",
            "command:优化文件系统",
            "command:重启MySQL服务",
            "command:查看磁盘使用情况"
        ],
        "io_optimize": [
            "command:清理系统缓存",
            "command:查看磁盘使用情况",
            "command:查看活跃连接数",
            "command:查看运行进程"
        ],
        "security_harden": [
            "command:查看防火墙",
            "command:开启防火墙",
            "command:启用SYN Cookie",
            "command:关闭NTP同步服务器",
            "command:查看当前登录用户"
        ],
        "memory_release": [
            "command:清理系统缓存",
            "command:查看内存使用情况",
            "command:查看运行进程"
        ],
        "service_restart": [
            "command:重启Nginx服务",
            "command:重启MySQL服务",
            "command:重启Docker服务"
        ],
        "network_optimize": [
            "command:检测网络连接状态",
            "command:查看端口占用情况",
            "command:终止占用端口的进程",
            "command:查看活跃连接数"
        ],
        "system_health_check": [
            "command:查看系统负载",
            "command:查看CPU信息",
            "command:查看内核日志",
            "command:检查系统内核日志",
            "command:导出当前系统状态"
        ],
        "resource_release": [
            "command:清理系统缓存",
            "command:查看内存使用情况",
            "command:查看磁盘使用情况",
            "command:查看运行进程"
        ],
        "server_reboot": [
            "command:重启服务器"
        ]}
# 策略包接口
@csrf_exempt
def apply_strategy(request):
    data = json.loads(request.body.decode("utf8"))
    ip = data.get("ip")
    port = int(data.get("port"))
    strategy = data.get("strategy")
    commands = STRATEGY_PACKS.get(strategy, [])
    results = []
    for cmd in commands:
        result = select_client.send_command(cmd, ip, port)
        results.append({ "command": cmd, "result": result })
    return JsonResponse({ "message": "success", "results": results }, status=200)
def create_data(dbmodel, data):
    try:
        # 处理服务信息管理的字段映射
        if dbmodel.__name__ == 'ServerManagement':
            # 映射前端字段名到模型字段名
            if 'severCategory' in data:
                data['server_category'] = data.pop('severCategory')
            if 'remark' in data:
                data['remarks'] = data.pop('remark')

        # 处理监控服务器信息管理的字段映射
        elif dbmodel.__name__ == 'MonitoringServerInformation':
            # 字段映射：前端字段名 -> 模型字段名
            if 'serviceType' in data:
                data['server_category'] = data.pop('serviceType')
            if 'severCategory' in data:
                data['server_category'] = data.pop('severCategory')
            
            # 移除不属于模型的字段
            allowed_fields = ['ip', 'port', 'server_category', 'remarks']
            filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
            data = filtered_data

            # 验证必填字段
            if not data.get('ip'):
                raise ValueError("IP地址不能为空")
            if not data.get('port'):
                raise ValueError("端口不能为空")

            # 确保端口是整数
            if 'port' in data:
                try:
                    data['port'] = int(data['port'])
                    if data['port'] < 1 or data['port'] > 65535:
                        raise ValueError("端口号必须在1-65535之间")
                except (ValueError, TypeError):
                    raise ValueError("端口号必须是有效的数字")

            # 确保服务类型和备注字段存在
            if 'server_category' not in data or data['server_category'] is None:
                data['server_category'] = ""
            if 'remarks' not in data or data['remarks'] is None:
                data['remarks'] = ""

        print(f"Creating {dbmodel.__name__} with data: {data}")
        dbmodel.objects.create(**data)
        print(f"Successfully created {dbmodel.__name__}")
    except Exception as e:
        print(f"Error creating {dbmodel.__name__}: {e}")
        print(f"Data: {data}")
        raise e


def select_data(dbmodel, data):
    condition = data
    query = dbmodel.objects.filter(**condition)
    return query


def select_all_data(dbmodel):
    query = dbmodel.objects.all()
    return query


def update_data(dbmodel, data):
    try:
        # 检查数据类型，如果已经是字典则直接使用，否则解析JSON
        if isinstance(data["old"], str):
            old = json.loads(data["old"])
        else:
            old = data["old"]

        if isinstance(data["new"], str):
            new = json.loads(data["new"])
        else:
            new = data["new"]

        print(f"原始更新数据 - 旧数据: {old}")
        print(f"原始更新数据 - 新数据: {new}")

        # 处理服务信息管理的字段映射
        if dbmodel.__name__ == 'ServerManagement':
            # 映射前端字段名到模型字段名
            for data_dict in [old, new]:
                if 'severCategory' in data_dict:
                    data_dict['server_category'] = data_dict.pop('severCategory')
                if 'remark' in data_dict:
                    data_dict['remarks'] = data_dict.pop('remark')

        # 处理监控服务器信息管理的字段映射
        elif dbmodel.__name__ == 'MonitoringServerInformation':
            # 字段映射：前端字段名 -> 模型字段名
            for data_dict in [old, new]:
                if 'serviceType' in data_dict:
                    data_dict['server_category'] = data_dict.pop('serviceType')
                if 'severCategory' in data_dict:
                    data_dict['server_category'] = data_dict.pop('severCategory')
            
            # 移除不属于模型的字段
            allowed_fields = ['ip', 'port', 'server_category', 'remarks']
            for data_dict in [old, new]:
                filtered_data = {k: v for k, v in data_dict.items() if k in allowed_fields}
                data_dict.clear()
                data_dict.update(filtered_data)

                # 验证必填字段
                if not data_dict.get('ip'):
                    raise ValueError("IP地址不能为空")
                if not data_dict.get('port'):
                    raise ValueError("端口不能为空")

                # 确保端口是整数
                if 'port' in data_dict:
                    try:
                        data_dict['port'] = int(data_dict['port'])
                        if data_dict['port'] < 1 or data_dict['port'] > 65535:
                            raise ValueError("端口号必须在1-65535之间")
                    except (ValueError, TypeError):
                        raise ValueError("端口号必须是有效的数字")

                # 确保备注字段存在
                if 'remarks' not in data_dict or data_dict['remarks'] is None:
                    data_dict['remarks'] = ""

        print(f"处理后更新数据 - 旧数据: {old}")
        print(f"处理后更新数据 - 新数据: {new}")
    except Exception as e:
        print(f"数据处理错误: {e}")
        raise e

    try:
        # 处理remarks字段的空字符串和None值匹配，并排除密码字段
        old_without_password = {k: v for k, v in old.items() if k != "password"}

        print(f"查询条件: {old_without_password}")

        if "remarks" in old_without_password and old_without_password["remarks"] == "":
            # 如果旧数据中remarks是空字符串，则查询时排除remarks字段或使用None
            old_without_remarks = {k: v for k, v in old_without_password.items() if k != "remarks"}
            query = dbmodel.objects.filter(**old_without_remarks)
            # 进一步过滤remarks为None或空字符串的记录
            query = query.filter(remarks__isnull=True) | query.filter(remarks="")
        else:
            query = dbmodel.objects.filter(**old_without_password)

        print(f"查询结果数量: {query.count()}")

        if query.exists():
            # 更新时也排除密码字段，除非新数据中的密码不是******
            new_without_password = {k: v for k, v in new.items() if k != "password" or v != "******"}
            print(f"更新数据: {new_without_password}")
            result = query.update(**new_without_password)
            print(f"更新结果: {result} 条记录被更新")
        else:
            print("未找到匹配的记录")
            # 尝试更宽松的查询（只用IP和端口）
            if 'ip' in old and 'port' in old:
                fallback_query = dbmodel.objects.filter(ip=old['ip'], port=old['port'])
                print(f"备用查询结果数量: {fallback_query.count()}")
                if fallback_query.exists():
                    new_without_password = {k: v for k, v in new.items() if k != "password" or v != "******"}
                    result = fallback_query.update(**new_without_password)
                    print(f"备用更新结果: {result} 条记录被更新")
                else:
                    print("备用查询也未找到匹配的记录")
    except Exception as e:
        print(f"更新操作错误: {e}")
        raise e


def back_del_message(query):
    if query:
        query.delete()
        return "删除成功"
    return "无效IP地址"


def zeng_shan_gai_cha_one_tool(tp, number_range, db_model, data):
    try:
        # 模块一
        if tp == "create":
            create_data(db_model, data)
            return HttpResponse("新建成功", status=200)
        elif tp == "del":
            query = select_data(db_model, data=data)
            return HttpResponse(back_del_message(query), status=200)
        elif tp == "select":
            query = select_data(db_model, data=data)
            data_dicts = constrain_the_page(number_range, query)
            return JsonResponse(data_dicts, status=200)
        elif tp == "update":
            update_data(db_model, data)
            return HttpResponse("更新成功", status=200)
    except Exception as e:
        logger.error(f"Error in zeng_shan_gai_cha_one_tool: {e}")
        return JsonResponse({
            "error": str(e),
            "message": "操作失败"
        }, status=500)


def cha_two_tool(name, dbmodel, data, tp=""):
    try:
        if name == "get_ipadress":
            logger.info("开始获取IP地址列表")
            try:
                query = select_all_data(dbmodel)
                logger.info(f"查询到 {len(query)} 条服务器记录")
                
                # 修改：返回备注而不是IP地址，但保留IP作为值
                ip_remarks = {}
                for item in query:
                    # 使用备注作为显示文本，IP作为值
                    display_text = item.remarks if hasattr(item, 'remarks') and item.remarks else item.ip
                    ip_remarks[display_text] = item.ip
                    logger.info(f"服务器: {display_text} -> {item.ip}")
                
                logger.info(f"返回IP地址数据: {ip_remarks}")
                return JsonResponse(ip_remarks, status=200)
            except Exception as e:
                logger.error(f"获取IP地址列表失败: {e}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    "error": f"获取IP地址列表失败: {str(e)}"
                }, status=500)
        elif name == "start_caiji":
            host = data["ip"]
            port = int(data["port"])
            try:
                data = select_client.get_info(host, port, tp)
                return JsonResponse(data, status=200)
            except Exception as e:
                logger.error(f"采集数据失败: {e}")
                return JsonResponse({
                    "error": f"采集数据失败: {str(e)}"
                }, status=500)
        elif name == "get_port":
            try:
                # 数据已经在return_data_model_two中解析过了
                logger.info(f"get_port 接收到的数据: {data}")
                
                ip = data.get("ip")
                if not ip:
                    logger.error("IP参数为空")
                    return JsonResponse({
                        "error": "IP参数不能为空"
                    }, status=400)
                
                logger.info(f"查询IP: {ip} 的端口信息")
                
                # 查询指定IP的端口信息 - 使用正确的字段名 'ip'
                query = select_data(dbmodel, {"ip": ip})
                logger.info(f"查询结果数量: {query.count()}")
                
                if not query:
                    logger.error(f"未找到IP {ip} 的端口信息")
                    return JsonResponse({
                        "error": f"未找到IP {ip} 的端口信息"
                    }, status=404)
                
                # 返回端口列表
                ports = [item.port for item in query if hasattr(item, 'port')]
                port_dict = {}
                for i, port in enumerate(ports):
                    port_dict[f"port_{i}"] = port
                
                logger.info(f"为IP {ip} 找到端口: {port_dict}")
                return JsonResponse(port_dict, status=200)
            except Exception as e:
                logger.error(f"获取端口信息失败: {e}")
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    "error": f"获取端口信息失败: {str(e)}"
                }, status=500)
        else:
            return JsonResponse({
                "error": f"未知的操作类型: {name}"
            }, status=400)
    except Exception as e:
        logger.error(f"cha_two_tool函数异常: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "error": f"服务器内部错误: {str(e)}"
        }, status=500)


# 约束页面
def constrain_the_page(number_range, filtered_records):
    # 约束取值范围数据最长长度
    page_content_number = 50
    start_index, end_index = map(int, number_range.split("-"))
    start_index -= 1
    max_len = len(filtered_records)
    # 是50的几倍
    all_numb, a_mod = divmod(max_len, page_content_number)
    max_numb, m_mod = divmod(start_index, page_content_number)

    if all_numb >= max_numb:
        filtered_records = filtered_records[start_index:end_index]
    elif all_numb < max_numb:
        start_index = all_numb * page_content_number
        filtered_records = filtered_records[start_index:]

    data_dicts = {"all_data": [], "max_len": max_len, "all_numb": all_numb, "a_mod": a_mod, "page": page_content_number,
                  "range": number_range}
    for record in filtered_records:
        data_dict = model_to_dict(record)
        if "password" in data_dict:
            data_dict["password"] = "******"
        # 处理remarks字段的None值
        if "remarks" in data_dict and data_dict["remarks"] is None:
            data_dict["remarks"] = ""
        data_dicts["all_data"].append(data_dict)
    return data_dicts


@csrf_exempt
def return_data_model_one(request, name, tp, number_range):
    """
    :param request:
    :param name: 决定用那张数据表进行查询，前端必须返回model_form里面数据表对应的名字
    :param tp: 决定增删还是改查
    :param number_range
    :return:
    """
    # print(name, tp, number_range)
    data = json.loads(request.body.decode("utf8"))
    # print(data)
    if name == "JianKongFuWuQi":
        return zeng_shan_gai_cha_one_tool(tp, number_range, MonitoringServerInformation, data)
    elif name == "JianKongShuJuKu":
        return zeng_shan_gai_cha_one_tool(tp, number_range, DataBaseInformationManagement, data)
    elif name == "FuWuXinXi":
        return zeng_shan_gai_cha_one_tool(tp, number_range, ServerManagement, data)
    return JsonResponse({"state": "no"}, status=500)


@csrf_exempt
def return_data_model_two(request, tp, name):
    " ip地址"
    data = ""
    if name != "get_ipadress":
        try:
            data = json.loads(request.body.decode("utf8"))
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return JsonResponse({
                "error": "请求数据格式错误"
            }, status=400)
    return cha_two_tool(name, MonitoringServerInformation, data, tp)


@csrf_exempt
def return_data_model_three(request, name, start_time, end_time, number_range, ipvalue):

    start_time = datetime.strptime(start_time, '%Y-%m-%d')
    end_time = datetime.strptime(end_time, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    condition = {}
    if ipvalue != "no":
        condition.update({"ipaddress": ipvalue})
    if name == "cpuxinnengzhibiao":
        records = select_data(CPUPerformanceMetrics, condition)
    elif name == "neicunxinnengzhibiao":
        records = select_data(MemoryPerformanceMetrics, condition)
    elif name == "cipuanxinnengzhibiao":
        records = select_data(DiskPerformanceMetrics, condition)
    elif name == "wangluoxinnengzhibiao":
        records = select_data(NetworkPerformanceMetrics, condition)
    else:
        return JsonResponse({"error": "Invalid name parameter"}, status=400,)
    # 过滤时间范围
    filtered_records = []
    for record in records:
        # 使用 parse_date 将字符串转换为 date 对象
        current_date = datetime.fromisoformat(str(record.currentTime))
        # 移除时区信息以保持一致性
        if current_date.tzinfo is not None:
            current_date = current_date.replace(tzinfo=None)
        if current_date and start_time <= current_date <= end_time:
            filtered_records.append(record)

    data_dicts = constrain_the_page(number_range, filtered_records)
    # 输出过滤后的结果
    for record in data_dicts["all_data"]:
        record["currentTime"] = record["currentTime"].strftime('%Y-%m-%d %H:%M:%S')
    return JsonResponse(data_dicts)


@csrf_exempt
def return_data_model_four(request):
    data = {}
    cpu_data = select_all_data(CPUPerformanceMetrics)
    disk_data = select_all_data(DiskPerformanceMetrics)
    memory_data = select_all_data(MemoryPerformanceMetrics)
    network_data = select_all_data(NetworkPerformanceMetrics)
    os_data = select_all_data(AdditionalInformation)
    if cpu_data:
        cpu_percent = cpu_data.last().percent
        data.update({"cpu_percent": cpu_percent})
    if disk_data:
        disk_percent = disk_data.last().percent
        data.update({"disk_percent": disk_percent})
    if memory_data:
        memory_percent = memory_data.last().percent
        data.update({"memory_percent": memory_percent})
    if network_data:
        network_info = network_data.last()
        data.update({"network_data": {"sent": network_info.sent, "recv": network_info.recv}})
    if os_data:
        os_info = os_data.last()
        data.update({"os_data": {"os_name": os_info.os_name,
                                 "os_info": os_info.os_info,
                                 "os_version": os_info.os_version,
                                 "os_processor_architecture": os_info.os_processor_architecture,
                                 "os_processor_name": os_info.os_processor_name}})
    return JsonResponse(data, status=200)


@csrf_exempt
def return_cmd_four(request):
    # 在 api.py 顶部添加

    choice_cmd = {
        "1": "command:查看防火墙",
        "2": "command:开启防火墙",
        "3": "command:关闭防火墙",
        "4": "command:优化文件系统",
        "5": "command:关闭NTP同步服务器",
        "6": "command:查看NTP同步服务器",
        "7": "command:开启NTP同步服务器",
        "10": "command:启用SYN Cookie",
        "11": "command:备份数据库 aa",
        "12": "command:添加数据库缓存",
        "13": "command:查看时间同步",
        "14": "command:设置NTP",
        "15": "slove_su",
        "16": "slove_system_jam",
        # 新增常用指令
        "17": "command:查看当前登录用户",
        "18": "command:清理系统缓存",
        "19": "command:查看磁盘使用情况",
        "20": "command:重启Nginx服务",
        "21": "command:检查系统内核日志",
        "22": "command:查看系统负载",
        "23": "command:查看内存使用情况",
        "24": "command:查看CPU信息",
        "25": "command:重启服务器",
        "26": "command:重启MySQL服务",
        "27": "command:检测网络连接状态",
        "28": "command:查看端口占用情况",
        "29": "command:终止占用端口的进程",
        "30": "command:查看活跃连接数",
        "31": "command:重启Docker服务",
        "32": "command:查看内核日志",
        "33": "command:检查CPU绑定情况",
        "34": "command:查看运行进程",
        "35": "command:导出当前系统状态"
    }
    choice_empty_info = {
        "2": "The firewall is successfully enabled",
        "3": "The firewall was successfully shut down",
        "5": "The NTP synchronization server was successfully shut down",
        "7": "The NTP synchronization server is enabled",
        "11": "The backup database succeeded load /backupfile.sql",
        "12": "query cache size=600000",
        "23": "Nginx has been restarted",
        "25": "Server is rebooting...",
        "26": "MySQL has been restarted",
        "31": "Docker service restarted successfully"
    }

    data = json.loads(request.body.decode("utf8"))
    ip = data.get("ip")
    port = int(data.get("port"))
    defaultcmd = data.get("defaultCmdString")
    command = data.get("cmdString")
    
    # 添加调试信息
    print(f"API接收到的数据: {data}")
    print(f"IP: {ip}, Port: {port}")
    print(f"defaultcmd: {defaultcmd}, command: {command}")
    print(f"choice_cmd.get(defaultcmd): {choice_cmd.get(defaultcmd) if defaultcmd else 'None'}")
    
    # if command in ["15", "16"]:
    #     state_info = select_client.send_command(f"command:{command}", ip, port)
    if command != "0":
        # 自动补全前缀
        cmd_to_send = command if command.startswith("command:") else "command:" + command
        print(f"发送自定义命令: {cmd_to_send}")
        state_info = select_client.send_command(cmd_to_send, ip, port)
    else:
        actual_command = choice_cmd.get(defaultcmd)
        print(f"发送预设命令: {actual_command}")
        state_info = select_client.send_command(actual_command, ip, port)
    
    print(f"命令执行结果: {state_info}")
    
    if not state_info or state_info == '""':
        state_info = choice_empty_info.get(defaultcmd)
        print(f"使用默认响应: {state_info}")
    
    return HttpResponse(str(state_info), status=200)


# 实则模块6
@csrf_exempt
def return_data_five(request):
    data = json.loads(request.body.decode("utf8"))
    ip = data.get("ip")
    port = int(data.get("port"))
    command = data.get("command")
    if command == "get_flame_graph":
        select_client.send_command("get_flame_graph", ip, port)
    elif command == "get_new_io_data":
        info = select_client.send_command("command:get_biotop", ip, port)
        return HttpResponse(info, status=200)
    elif command == "get_io_stack":
        info = select_client.send_command("command:get_io_stack", ip, port)
        return HttpResponse(info, status=200)
    return JsonResponse({"state": "ok"}, status=200)


# 火焰图转成二进制
class NoCacheImageView(View):
    def get(self, request, *args, **kwargs):
        image_name = kwargs.get('image_name')
        image_path = os.path.join('kylinApp', 'static', 'img', f'{image_name}')  # 替换为你的图片路径
        if not os.path.exists(image_path):
            raise Http404("Image does not exist")
        with open(image_path, mode="rb") as f:
            return HttpResponse(f.read(), status=200)


# 实则模块5
@csrf_exempt
def return_data_six(request):
    data = json.loads(request.body.decode("utf8"))
    tp = data.get("type")
    ip = data.get("ip")
    port = data.get("port")
    if tp == "get_db":
        query = select_all_data(DataBaseInformationManagement)
        if query:
            data = {"database": [item.database for item in query]}
        return JsonResponse(data, status=200)
    elif tp == "get_db_info":
        condition = {
            "database": data.get("db")
        }
        query = select_data(DataBaseInformationManagement, condition)
        if query:
            data = {"info": {"dbtype": [], 'ip': [], "port": []}}
            for item in query:
                data["info"]["dbtype"].append(item.type)
                data["info"]["ip"].append(item.ip)
                data["info"]["port"].append(item.port)
        return JsonResponse(data, status=200)
    elif tp == "get_db_scene":
        condition = {
            "database": data.get("db")
        }
        query = select_data(DataBaseInformationManagement, condition)[0]
        values = dbSceneRecognition.return_data_main(query.ip, query.user, query.password,
                                                     query.database, query.port, query.code)
        return JsonResponse(values, status=200)
    elif tp == "ceph_info":
        data = select_client.get_info(ip, int(port), tp)
        return JsonResponse(data)
    return HttpResponse("请求错误", status=303)


@csrf_exempt
def userManager(request, tp):
    data = json.loads(request.body.decode('utf-8'))
    if tp == "select":
        user_name = data.get("userName", {})
        filter = {}
        if user_name:
            filter["username"] = user_name
        user_info = list(UserModels.objects.filter(**filter).values())
        for user in user_info:
            user["password"] = "********"
        return JsonResponse({"message": "success", "data": user_info}, status=200)
    elif tp == "create":
        user_name = data.get("username", "")
        password = data.get("password", "")
        encrypt_password = encrypt.encrypt_md5(password)
        if UserModels.objects.filter(username=user_name).exists():
            return JsonResponse({"message": "用户已存在"}, status=200)
        else:
            UserModels.objects.create(username=user_name, password=encrypt_password)
            return JsonResponse({"message": "success"}, status=200)
    elif tp == "delete":
        user_name = data.get("username", "")
        UserModels.objects.filter(username=user_name).delete()
        return JsonResponse({"message": "success"}, status=200)
    elif tp == "update":
        old_value = json.loads(data.get("old", {}))
        new_value = json.loads(data.get("new", {}))
        new_user_name = new_value.get("username", "")
        new_password = new_value.get("password", "")
        encrypt_password = encrypt.encrypt_md5(new_password)
        UserModels.objects.filter(username=new_user_name).update(password=encrypt_password)

        return JsonResponse({"message": "success"}, status=200)
    return HttpResponse("地址请求成功")

def realtime_update_pid_data(request):
    """更新进程数据 """
    try:
        ip = request.GET.get('ip')
        port = request.GET.get('port')
        
        # 参数验证
        if not ip or not port:
            return JsonResponse({
                "message": "error",
                "error": "IP和端口参数不能为空"
            }, status=400)
        
        # 验证端口是否为有效数字
        try:
            port_int = int(port)
            if port_int <= 0 or port_int > 65535:
                return JsonResponse({
                    "message": "error", 
                    "error": "端口号必须在1-65535范围内"
                }, status=400)
        except ValueError:
            return JsonResponse({
                "message": "error",
                "error": "端口号必须是有效的数字"
            }, status=400)
        
        data = select_client.send_command("get_top", ip, port_int)
        json_data = json.loads(data)
        # 将字典转换为列表，以便筛选和排序
        data_list = list(json_data.values())

        # 筛选出 %CPU 和 %MEM 不等于 0 的数据
        filtered_data = [item for item in data_list if float(item['%CPU']) > 0 or float(item['%MEM']) > 0.1]

        # 按 %CPU 降序排序
        sorted_by_cpu = sorted(filtered_data, key=lambda x: float(x['%CPU']), reverse=True)

        data = {}
        if len(sorted_by_cpu) > 10:
            for item in sorted_by_cpu[:10]:
                PID = item.pop("PID")
                data[PID] = item
        else:
            for item in sorted_by_cpu:
                PID = item.pop("PID")
                data[PID] = item
        return JsonResponse({
            "message": "success",
            "data": data
        }, status=200)
    except Exception as e:
        logger.error(f"realtime_update_pid_data error: {e}")
        return JsonResponse({
            "message": "error",
            "error": f"获取进程数据失败: {str(e)}"
        }, status=500)

@csrf_exempt
def pid_info(request):
    ip = request.POST.get("ip")
    port = request.POST.get("port")
    tp = request.POST.get("tp")
    changeCpuId = request.POST.get("changeCpuId")
    currPid = request.POST.get("currPid")
    if tp == "GETPIDINFO":
        data = select_client.send_command("get_ps",ip, int(port))
        json_data = json.loads(data)
        json_data["CPUCount"] = [hex(i) for i in set(json_data["CPU核心"])]
        json_data["CPU核心"] = [hex(i) for i in json_data["CPU核心"]]
        return JsonResponse({
            "message": "success",
            "data": json_data
        }, status=200)
    elif tp == "CHANGECPUID":
        data = select_client.send_command("set_cpu_affinity", ip,int(port), changeCpuId, currPid)
        return JsonResponse({"message": "success"}, status=200)

@csrf_exempt
def ai_optimize_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    try:
        print("准备调用AI推理")
        result = direct_ai_optimize_infer()
        print("AI推理结果：", result)
        
        # 解析AI返回的策略方案
        strategies = []
        try:
            # 尝试直接解析为JSON
            try:
                parsed_result = json.loads(result)
                if isinstance(parsed_result, list):
                    strategies = parsed_result
                elif isinstance(parsed_result, dict):
                    strategies = [parsed_result]
            except Exception:
                # 如果不是有效JSON，尝试提取JSON部分
                json_match = re.search(r'\{[\s\S]*\}', result)
                if json_match:
                    possible_json = json_match.group(0)
                    try:
                        parsed_result = json.loads(possible_json)
                        if isinstance(parsed_result, dict):
                            strategies = [parsed_result]
                    except:
                        pass
                
                # 如果无法解析，作为普通文本处理
                if not strategies:
                    strategies = [{"策略": result, "可执行的指令": "请手动执行相关优化操作"}]
        except Exception as e:
            print(f"AI策略解析异常: {e}")
            strategies = [{"策略": result, "可执行的指令": "请手动执行相关优化操作"}]
        
        # 转换数据格式以匹配前端期望
        formatted_strategies = []
        for i, strategy in enumerate(strategies):
            if isinstance(strategy, dict):
                # 检查是否已经是前端期望的格式
                if any(key.startswith('调优方案') for key in strategy.keys()):
                    formatted_strategies.append(strategy)
                else:
                    # 转换为前端期望的格式
                    formatted_strategy = {
                        f"调优方案{i+1}": {
                            "策略": strategy.get("分析", "") + "\n" + strategy.get("建议", ""),
                            "可执行的指令": strategy.get("命令", strategy.get("可执行的指令", ""))
                        }
                    }
                    formatted_strategies.append(formatted_strategy)
            else:
                # 如果不是字典，创建默认格式
                formatted_strategies.append({
                    f"调优方案{i+1}": {
                        "策略": str(strategy),
                        "可执行的指令": "请手动执行相关优化操作"
                    }
                })
        
        return JsonResponse({
            'success': True,
            'strategies': formatted_strategies,
            'raw_result': result
        })
    except Exception as e:
        import traceback
        print("AI推理异常：", e)
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'result': f'AI推理失败: {str(e)}'
        }, status=500)

@csrf_exempt
def execute_ai_strategy(request):
    """执行AI策略命令"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    try:
        data = json.loads(request.body.decode("utf8"))
        print(f"接收到的数据: {data}")  # 添加调试信息
        
        ip = data.get("ip")
        port = data.get("port")
        strategy = data.get("strategy")
        
        print(f"解析的参数 - IP: {ip}, Port: {port}, Strategy: {strategy}")  # 添加调试信息
        
        if not ip or not port or not strategy:
            error_msg = f"缺少必要参数 - IP: {ip}, Port: {port}, Strategy: {strategy}"
            print(error_msg)  # 添加调试信息
            return JsonResponse({'error': error_msg}, status=400)
        
        # 检查IP地址是否有效
        if ip in ["选择IP", "选择端口", ""] or not ip:
            error_msg = f"无效的IP地址: {ip}"
            print(error_msg)  # 添加调试信息
            return JsonResponse({'error': error_msg}, status=400)
        
        # 检查端口是否有效
        try:
            port_int = int(port)
            if port_int <= 0 or port_int > 65535:
                error_msg = f"无效的端口号: {port}"
                print(error_msg)  # 添加调试信息
                return JsonResponse({'error': error_msg}, status=400)
        except (ValueError, TypeError):
            error_msg = f"端口号格式错误: {port}"
            print(error_msg)  # 添加调试信息
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
            elif "command" in strategy:
                command = strategy["command"]
        
        print(f"提取的命令: {command}")  # 添加调试信息
        
        if not command:
            error_msg = "策略中没有找到可执行的命令"
            print(error_msg)  # 添加调试信息
            return JsonResponse({'error': error_msg}, status=400)
        
        # 执行命令
        try:
            print(f"准备执行命令: {command} 在 {ip}:{port_int}")  # 添加调试信息
            result = select_client.send_command(command, ip, port_int)
            print(f"命令执行结果: {result}")  # 添加调试信息
            return JsonResponse({
                'success': True,
                'result': result,
                'command': command
            })
        except Exception as e:
            error_msg = f'命令执行失败: {str(e)}'
            print(error_msg)  # 添加调试信息
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'command': command
            })
            
    except json.JSONDecodeError as e:
        error_msg = f'JSON解析失败: {str(e)}'
        print(error_msg)  # 添加调试信息
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=400)
    except Exception as e:
        error_msg = f'请求处理失败: {str(e)}'
        print(error_msg)  # 添加调试信息
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=500)

@csrf_exempt
def background_collection_api(request):
    """后台采集任务管理接口"""
    try:
        # 记录请求信息
        logger.info(f"收到后台采集任务请求: {request.method}")
        
        if request.method != 'POST':
            logger.warning(f"不支持的请求方法: {request.method}")
            return JsonResponse({
                "success": False,
                "message": f"不支持的请求方法: {request.method}"
            }, status=405)
        
        # 解析请求数据
        try:
            data = json.loads(request.body.decode("utf8"))
            logger.info(f"请求数据: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return JsonResponse({
                "success": False,
                "message": f"JSON解析失败: {str(e)}"
            }, status=400)
        
        action = data.get("action")
        logger.info(f"执行操作: {action}")
        
        if action == "start":
            # 启动后台采集任务
            ip = data.get("ip")
            port = int(data.get("port"))
            interval = int(data.get("interval", 30))
            task_id = f"{ip}_{port}_{int(time.time())}"
            
            success, message = task_manager.start_collection_task(task_id, ip, port, interval)
            
            return JsonResponse({
                "success": success,
                "message": message,
                "task_id": task_id if success else None
            })
            
        elif action == "stop":
            # 停止后台采集任务
            task_id = data.get("task_id")
            logger.info(f"尝试停止任务: {task_id}")
            
            if not task_id:
                logger.warning("停止任务请求缺少任务ID")
                return JsonResponse({
                    "success": False,
                    "message": "缺少任务ID"
                }, status=400)
            
            try:
                success, message = task_manager.stop_collection_task(task_id)
                logger.info(f"停止任务结果: success={success}, message={message}")
                
                return JsonResponse({
                    "success": success,
                    "message": message
                })
            except Exception as e:
                logger.error(f"停止任务时发生异常: {e}")
                return JsonResponse({
                    "success": False,
                    "message": f"停止任务时发生异常: {str(e)}"
                }, status=500)
            
        elif action == "status":
            # 获取任务状态
            task_id = data.get("task_id")
            if task_id:
                # 先清理已停止的任务
                task_manager.cleanup_stopped_tasks()
                
                status = task_manager.get_task_status(task_id)
                if status is None:
                    return JsonResponse({
                        "success": False,
                        "message": "任务不存在"
                    }, status=404)
                return JsonResponse({
                    "success": True,
                    "status": status
                })
            else:
                # 返回所有任务
                tasks = task_manager.get_all_tasks()
                return JsonResponse({
                    "success": True,
                    "tasks": tasks
                })
        
        elif action == "cleanup":
            # 清理已停止的任务
            task_id = data.get("task_id")
            if task_id:
                task_manager.cleanup_task(task_id)
                return JsonResponse({
                    "success": True,
                    "message": "任务已清理"
                })
            else:
                # 清理所有已停止的任务
                task_manager.cleanup_stopped_tasks()
                return JsonResponse({
                    "success": True,
                    "message": "所有已停止任务已清理"
                })
        
        elif action == "force_stop_all":
            # 强制停止所有任务
            logger.warning("执行操作: force_stop_all")
            try:
                stopped_count = task_manager.force_stop_all_tasks()
                return JsonResponse({
                    "success": True,
                    "message": f"已强制停止并清理 {stopped_count} 个任务"
                })
            except Exception as e:
                logger.error(f"强制停止所有任务失败: {e}")
                return JsonResponse({
                    "success": False,
                    "message": f"强制停止失败: {str(e)}"
                }, status=500)
        elif action == "test_connection":
            # 测试探针连接
            ip = data.get("ip")
            port = data.get("port")
            if not ip or not port:
                return JsonResponse({
                    "success": False,
                    "message": "缺少IP或端口参数"
                }, status=400)
            
            try:
                # 测试CPU数据获取
                cpu_data = select_client.get_info(ip, int(port), 'cpu')
                return JsonResponse({
                    "success": True,
                    "message": "探针连接成功",
                    "data": cpu_data
                })
            except Exception as e:
                logger.error(f"探针连接测试失败: {e}")
                return JsonResponse({
                    "success": False,
                    "message": f"探针连接失败: {str(e)}"
                }, status=500)
        
        else:
            return JsonResponse({
                "success": False,
                "message": "无效的操作"
            }, status=400)
            
    except json.JSONDecodeError as e:
        return JsonResponse({
            "success": False,
            "message": f"JSON解析失败: {str(e)}"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"请求处理失败: {str(e)}"
        }, status=500)

@csrf_exempt
def get_latest_data_api(request):
    """获取最新采集数据接口"""
    try:
        data = json.loads(request.body.decode("utf8"))
        ip = data.get("ip")
        port = int(data.get("port"))
        
        logger.info(f"获取最新数据请求: IP={ip}, Port={port}")
        
        # 获取最新的CPU数据
        latest_cpu = CPUPerformanceMetrics.objects.filter(
            ipaddress=ip
        ).order_by('-currentTime').first()
        
        # 获取最新的内存数据
        latest_memory = MemoryPerformanceMetrics.objects.filter(
            ipaddress=ip
        ).order_by('-currentTime').first()
        
        # 获取最新的磁盘数据
        latest_disk = DiskPerformanceMetrics.objects.filter(
            ipaddress=ip
        ).order_by('-currentTime').first()
        
        # 获取最新的网络数据
        latest_network = NetworkPerformanceMetrics.objects.filter(
            ipaddress=ip
        ).order_by('-currentTime').first()
        
        # 检查是否有任何数据
        has_data = any([latest_cpu, latest_memory, latest_disk, latest_network])
        
        if not has_data:
            logger.warning(f"IP {ip} 没有找到任何性能数据")
            return JsonResponse({
                "success": True,
                "data": {
                    "cpu": {"message": f"IP {ip} 暂无CPU数据，请先采集数据"},
                    "memory": {"message": f"IP {ip} 暂无内存数据，请先采集数据"},
                    "disk": {"message": f"IP {ip} 暂无磁盘数据，请先采集数据"},
                    "network": {"message": f"IP {ip} 暂无网络数据，请先采集数据"}
                },
                "message": f"IP {ip} 暂无数据，请先通过其他页面采集数据"
            })
        
        # 转换数据格式
        def convert_cpu_data(cpu_obj):
            if not cpu_obj:
                return {"message": f"IP {ip} 暂无CPU数据"}
            return {
                'cpu_percent': float(cpu_obj.percent),
                'cpu_count': cpu_obj.count,
                'cpu_user_time': cpu_obj.userTime,
                'cpu_system_time': cpu_obj.SystemTime,
                'cpu_idle_time': cpu_obj.Idle,
                'cpu_wait_time': cpu_obj.waitIO,
                'host': ip,
                'time': cpu_obj.currentTime.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        def convert_memory_data(mem_obj):
            if not mem_obj:
                return {"message": f"IP {ip} 暂无内存数据"}
            return {
                'mem_percent': float(mem_obj.percent),
                'mem_total': mem_obj.total,
                'mem_used': mem_obj.used,
                'mem_free': mem_obj.free,
                'mem_buffers': mem_obj.buffers,
                'mem_cached': mem_obj.cache,
                'swap_used': mem_obj.swap,
                'swap_total': mem_obj.swap,  # 简化处理
                'time': mem_obj.currentTime.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        def convert_disk_data(disk_obj):
            if not disk_obj:
                return {"message": f"IP {ip} 暂无磁盘数据"}
            return {
                'disk_percent': float(disk_obj.percent),
                'disk_total': disk_obj.total,
                'disk_used': disk_obj.used,
                'disk_free': disk_obj.free,
                'disk_read': disk_obj.readBytes,
                'disk_write': disk_obj.writeBytes,
                'time': disk_obj.currentTime.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        def convert_network_data(net_obj):
            if not net_obj:
                return {"message": f"IP {ip} 暂无网络数据"}
            return {
                'net_bytes_sent': net_obj.sent,
                'net_bytes_recv': net_obj.recv,
                'net_packets_sent': net_obj.packetSent,
                'net_packets_recv': net_obj.packetRecv,
                'host': ip,
                'time': net_obj.currentTime.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        response_data = {
            "cpu": convert_cpu_data(latest_cpu),
            "memory": convert_memory_data(latest_memory),
            "disk": convert_disk_data(latest_disk),
            "network": convert_network_data(latest_network)
        }
        
        logger.info(f"返回数据: CPU={'有数据' if latest_cpu else '无数据'}, "
                   f"内存={'有数据' if latest_memory else '无数据'}, "
                   f"磁盘={'有数据' if latest_disk else '无数据'}, "
                   f"网络={'有数据' if latest_network else '无数据'}")
        
        return JsonResponse({
            "success": True,
            "data": response_data
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        return JsonResponse({
            "success": False,
            "message": f"JSON解析失败: {str(e)}"
        }, status=400)
    except Exception as e:
        logger.error(f"获取最新数据失败: {e}")
        return JsonResponse({
            "success": False,
            "message": f"获取数据失败: {str(e)}"
        }, status=500)

@csrf_exempt
def get_latest_data(request):
    """获取最新采集数据接口（简化版，不需要IP参数）"""
    try:
        # 获取最新的CPU数据
        latest_cpu = CPUPerformanceMetrics.objects.all().order_by('-currentTime').first()
        logger.info(f"CPU数据查询结果: {'找到' if latest_cpu else '未找到'}")
        
        # 获取最新的内存数据
        latest_memory = MemoryPerformanceMetrics.objects.all().order_by('-currentTime').first()
        logger.info(f"内存数据查询结果: {'找到' if latest_memory else '未找到'}")
        
        # 获取最新的磁盘数据
        latest_disk = DiskPerformanceMetrics.objects.all().order_by('-currentTime').first()
        logger.info(f"磁盘数据查询结果: {'找到' if latest_disk else '未找到'}")
        
        # 获取最新的网络数据
        latest_network = NetworkPerformanceMetrics.objects.all().order_by('-currentTime').first()
        logger.info(f"网络数据查询结果: {'找到' if latest_network else '未找到'}")
        
        # 准备返回数据
        response_data = {
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "network_usage": 0
        }
        
        # 更新CPU使用率
        if latest_cpu:
            response_data["cpu_usage"] = float(latest_cpu.percent)
            logger.info(f"CPU使用率: {response_data['cpu_usage']}%")
        
        # 更新内存使用率
        if latest_memory:
            response_data["memory_usage"] = float(latest_memory.percent)
            logger.info(f"内存使用率: {response_data['memory_usage']}%")
        
        # 更新磁盘使用率
        if latest_disk:
            response_data["disk_usage"] = float(latest_disk.percent)
            logger.info(f"磁盘使用率: {response_data['disk_usage']}%")
        
        # 更新网络性能（基于网络流量计算）
        if latest_network:
            try:
                # 计算网络使用率（基于发送和接收的字节数）
                sent_bytes = float(latest_network.sent) if latest_network.sent else 0
                recv_bytes = float(latest_network.recv) if latest_network.recv else 0
                total_bytes = sent_bytes + recv_bytes
                
                # 将字节数转换为0-1之间的使用率（假设1GB为满负荷）
                network_usage = min(1.0, total_bytes / (1024 * 1024 * 1024))
                response_data["network_usage"] = network_usage
                logger.info(f"网络使用率: {network_usage:.2%}")
            except (ValueError, TypeError) as e:
                logger.warning(f"网络数据转换失败: {e}")
                response_data["network_usage"] = 0.0
        
        return JsonResponse({
            "success": True,
            "data": response_data
        })
        
    except Exception as e:
        logger.error(f"获取最新数据失败: {str(e)}")
        return JsonResponse({
            "success": False,
            "message": f"获取数据失败: {str(e)}"
        }, status=500)

@csrf_exempt
def save_collected_data_api(request):
    """保存采集数据接口"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body.decode("utf8"))
        logger.info(f"收到保存数据请求: {data}")

        # 获取数据类型和IP地址 - 支持多种字段名
        data_type = data.get('type', 'unknown')
        ip_address = data.get('host', data.get('ip', data.get('ipaddress', '')))

        # 如果没有IP地址，尝试从info字段中获取
        if not ip_address and 'info' in data:
            info = data['info']
            if isinstance(info, dict):
                ip_address = info.get('host', info.get('ip', info.get('ipaddress', '')))

        if not ip_address:
            logger.warning(f"缺少IP地址信息，数据: {data}")
            return JsonResponse({
                'success': False,
                'message': '缺少IP地址信息'
            }, status=400)

        # 提取实际的数据内容
        actual_data = data
        if 'info' in data and isinstance(data['info'], dict):
            actual_data = data['info']

        logger.info(f"处理数据: IP={ip_address}, 类型={data_type}, 数据={actual_data}")

        # 根据数据类型保存到对应的表
        if 'cpu' in data_type.lower() or 'cpu_percent' in actual_data:
            # 保存CPU数据
            cpu_data = CPUPerformanceMetrics(
                type='cpu',
                ipaddress=ip_address,
                percent=actual_data.get('cpu_percent', 0),
                count=actual_data.get('cpu_count', 0),
                userTime=actual_data.get('cpu_user', actual_data.get('cpu_user_time', 0)),
                SystemTime=actual_data.get('cpu_system', actual_data.get('cpu_system_time', 0)),
                Idle=actual_data.get('cpu_idle', actual_data.get('cpu_idle_time', 0)),
                waitIO=actual_data.get('cpu_iowait', actual_data.get('cpu_wait_time', 0)),
                currentTime=timezone.now()
            )
            cpu_data.save()
            logger.info(f"保存CPU数据成功: {cpu_data.id}")

        elif 'memory' in data_type.lower() or 'mem_percent' in actual_data:
            # 保存内存数据
            memory_data = MemoryPerformanceMetrics(
                type='memory',
                ipaddress=ip_address,
                percent=actual_data.get('mem_percent', 0),
                total=actual_data.get('mem_total', ''),
                used=actual_data.get('mem_used', ''),
                free=actual_data.get('mem_free', ''),
                buffers=actual_data.get('mem_buffers', ''),
                cache=actual_data.get('mem_cached', ''),
                swap=actual_data.get('swap_used', ''),
                currentTime=timezone.now()
            )
            memory_data.save()
            logger.info(f"保存内存数据成功: {memory_data.id}")

        elif 'disk' in data_type.lower() or 'disk_usage' in actual_data:
            # 保存磁盘数据
            disk_data = DiskPerformanceMetrics(
                type='disk',
                ipaddress=ip_address,
                total=actual_data.get('disk_total', ''),
                used=actual_data.get('disk_used', ''),
                free=actual_data.get('disk_free', ''),
                percent=actual_data.get('disk_percent', 0),
                readCount=actual_data.get('disk_read_count', 0),
                writeCount=actual_data.get('disk_write_count', 0),
                readBytes=actual_data.get('disk_read_bytes', 0),
                writeBytes=actual_data.get('disk_write_bytes', 0),
                currentTime=timezone.now()
            )
            disk_data.save()
            logger.info(f"保存磁盘数据成功: {disk_data.id}")

        elif 'network' in data_type.lower() or 'net_bytes_sent' in actual_data:
            # 保存网络数据
            network_data = NetworkPerformanceMetrics(
                type='network',
                ipaddress=ip_address,
                sent=actual_data.get('net_bytes_sent', ''),
                recv=actual_data.get('net_bytes_recv', ''),
                packetSent=actual_data.get('net_packets_sent', ''),
                packetRecv=actual_data.get('net_packets_recv', ''),
                currentTime=timezone.now()
            )
            network_data.save()
            logger.info(f"保存网络数据成功: {network_data.id}")
        else:
            # 通用数据保存，尝试自动识别
            # 如果包含CPU相关字段，保存为CPU数据
            if any(key in actual_data for key in ['cpu_percent', 'cpu_user', 'cpu_system']):
                cpu_data = CPUPerformanceMetrics(
                    type='cpu',
                    ipaddress=ip_address,
                    percent=actual_data.get('cpu_percent', 0),
                    count=actual_data.get('cpu_count', 0),
                    userTime=actual_data.get('cpu_user', 0),
                    SystemTime=actual_data.get('cpu_system', 0),
                    Idle=actual_data.get('cpu_idle', 0),
                    waitIO=actual_data.get('cpu_iowait', 0),
                    currentTime=timezone.now()
                )
                cpu_data.save()
                logger.info(f"自动识别并保存CPU数据成功: {cpu_data.id}")
            else:
                logger.warning(f"无法识别数据类型，跳过保存: {actual_data}")

        return JsonResponse({
            'success': True,
            'message': '数据保存成功'
        })

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        return JsonResponse({
            'success': False,
            'message': f'JSON解析失败: {str(e)}'
        }, status=400)
    except Exception as e:
        logger.error(f"保存采集数据失败: {e}")
        return JsonResponse({
            'success': False,
            'message': f'数据保存失败: {str(e)}'
        }, status=500)

# 豆包API集成
@csrf_exempt
def doubao_chat(request):
    """
    豆包API聊天接口 (现在使用ARK API)
    """
    try:
        if request.method != 'POST':
            return JsonResponse({
                'success': False,
                'error': '只支持POST请求'
            }, status=405)
        
        data = json.loads(request.body.decode('utf-8'))
        user_message = data.get('message', '')
        system_context = data.get('system_context', '')
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': '缺少用户消息'
            }, status=400)
        
        # ARK API配置
        if ARK_API_KEY == 'pat_H9dxbfanHsWDv6Fw7hofhfkwe2Sdy6YVuJBnrLSxIY0lAC7DZjPklsQypLsXn5Su':
            return JsonResponse({
                'success': False,
                'error': '请先配置ARK API密钥'
            }, status=500)
        
        # 构建请求数据
        payload = {
            "model": "bot-20250702164711-8jhhd",  # ARK模型名称
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{system_context}\n\n用户消息：{user_message}"}
                    ]
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {ARK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 调用ARK API
        response = requests.post(ARK_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return JsonResponse({
                'success': True,
                'response': ai_response
            })
        else:
            logger.error(f"ARK API调用失败: {response.status_code} - {response.text}")
            return JsonResponse({
                'success': False,
                'error': f'ARK API调用失败: {response.status_code}'
            }, status=500)
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        return JsonResponse({
            'success': False,
            'error': f'JSON解析失败: {str(e)}'
        }, status=400)
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求失败: {e}")
        return JsonResponse({
            'success': False,
            'error': f'网络请求失败: {str(e)}'
        }, status=500)
    except Exception as e:
        logger.error(f"ARK API处理失败: {e}")
        return JsonResponse({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }, status=500)