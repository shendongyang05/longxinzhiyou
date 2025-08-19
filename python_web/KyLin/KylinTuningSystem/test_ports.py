#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试端口功能的脚本
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'KylinTuningSystem.settings')
django.setup()

from kylinApp.models import MonitoringServerInformation

def test_ports():
    """测试端口功能"""
    
    print("🔍 测试端口功能")
    print("=" * 50)
    
    # 1. 检查监控服务器信息
    print("1. 检查监控服务器信息:")
    servers = MonitoringServerInformation.objects.all()
    if servers.exists():
        for server in servers:
            print(f"   - IP地址: {server.ip}")
            print(f"   - 端口: {server.port}")
            print(f"   - 服务类型: {server.server_category}")
            print(f"   - 备注: {server.remarks}")
            print()
    else:
        print("   ❌ 数据库中没有监控服务器信息")
        print("   需要先添加服务器信息")
    
    # 2. 检查数据库连接
    print("2. 检查数据库连接:")
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("   ✅ 数据库连接正常")
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
    
    # 3. 建议的解决方案
    print("\n3. 建议的解决方案:")
    print("   a) 检查数据库中的服务器信息")
    print("   b) 确保服务器可以访问")
    print("   c) 检查网络连接")
    print("   d) 验证端口是否开放")
    
    print("\n" + "=" * 50)
    print("📝 总结:")
    print("端口查询不到的原因可能是:")
    print("1. 数据库中没有服务器信息")
    print("2. 服务器无法访问")
    print("3. 端口被防火墙阻止")
    print("4. 网络配置问题")

if __name__ == "__main__":
    test_ports() 