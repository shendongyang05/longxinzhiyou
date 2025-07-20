#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新增命令的脚本
"""

import json
import socket

def test_command(command, host="127.0.0.1", port=7788):
    """测试单个命令"""
    print(f"\n=== 测试命令: {command} ===")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            
            # 构建命令数据
            command_data = {'command': command}
            data = json.dumps(command_data)
            
            print(f"发送数据: {data}")
            client_socket.sendall(data.encode('utf-8'))
            
            # 接收响应
            recv_info = ""
            leng = 0
            while True:
                recv_data = client_socket.recv(1024).decode('utf-8')
                if leng == 0:
                    try:
                        len_data = int(recv_data)
                    except ValueError:
                        print(f"无法解析长度: {recv_data}")
                        break
                recv_info = recv_info + recv_data
                if isinstance(recv_data, int):
                    leng = leng + len(str(recv_data))
                else:
                    leng = leng + len(recv_data)
                if leng >= len_data:
                    break
            
            # 移除长度前缀
            if recv_info and recv_info[0].isdigit():
                # 找到第一个非数字字符的位置
                i = 0
                while i < len(recv_info) and recv_info[i].isdigit():
                    i += 1
                recv_info = recv_info[i:]
            
            print(f"接收到的响应: {repr(recv_info)}")
            return recv_info
            
    except Exception as e:
        print(f"错误: {e}")
        return None

def main():
    """主测试函数"""
    # 测试新增的命令
    new_commands = [
        "command:查看当前登录用户",
        "command:清理系统缓存", 
        "command:查看磁盘使用情况",
        "command:重启Nginx服务",
        "command:检查系统内核日志",
        "command:查看系统负载",
        "command:查看内存使用情况",
        "command:查看CPU信息",
        "command:重启服务器",
        "command:重启MySQL服务",
        "command:检测网络连接状态",
        "command:查看端口占用情况",
        "command:终止占用端口的进程",
        "command:查看活跃连接数",
        "command:重启Docker服务",
        "command:查看内核日志",
        "command:检查CPU绑定情况",
        "command:查看运行进程",
        "command:导出当前系统状态"
    ]
    
    # 测试一些已知工作的命令作为对比
    working_commands = [
        "command:查看防火墙",
        "command:who",
        "get_info"
    ]
    
    print("=== 测试已知工作的命令 ===")
    for cmd in working_commands:
        test_command(cmd)
    
    print("\n=== 测试新增命令 ===")
    for cmd in new_commands:
        result = test_command(cmd)
        if result == "unknown command":
            print(f"❌ 命令 '{cmd}' 返回 unknown command")
        else:
            print(f"✅ 命令 '{cmd}' 工作正常")

if __name__ == "__main__":
    main() 