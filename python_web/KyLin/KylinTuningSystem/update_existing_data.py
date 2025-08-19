#!/usr/bin/env python
"""
更新现有服务器数据的脚本
为现有的服务器记录添加服务类型字段
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'KylinTuningSystem.settings')
django.setup()

from kylinApp.models import MonitoringServerInformation

def update_server_categories():
    """根据端口号为现有服务器记录添加服务类型"""
    
    # 端口到服务类型的映射
    port_to_service = {
        22: 'SSH',
        80: 'Nginx',
        443: 'Nginx',
        222: 'SSH',
        3306: 'MySQL',
        5432: 'PostgreSQL',
        6379: 'Redis',
        7788: '监控代理',
        8080: 'Tomcat',
        9200: 'Elasticsearch',
        5672: 'RabbitMQ',
        9092: 'Kafka',
        21: 'FTP',
        23: 'Telnet',
        53: 'DNS',
        1521: 'Oracle',
        5236: '达梦数据库',
        9090: 'Prometheus',
        3000: 'Grafana',
        2375: 'Docker',
        8443: 'Kubernetes',
        11211: 'Memcached',
        9000: 'MinIO',
        8080: 'Jenkins',  # 注意：8080可能对应多种服务
    }
    
    print("开始更新服务器服务类型...")
    
    # 获取所有没有服务类型的记录
    servers = MonitoringServerInformation.objects.filter(
        server_category__in=['', None]
    )
    
    updated_count = 0
    
    for server in servers:
        if server.port in port_to_service:
            old_category = server.server_category
            server.server_category = port_to_service[server.port]
            server.save()
            
            print(f"更新服务器 {server.ip}:{server.port} "
                  f"服务类型: '{old_category}' -> '{server.server_category}'")
            updated_count += 1
        else:
            # 对于未知端口，设置为"其他"
            server.server_category = '其他'
            server.save()
            print(f"设置服务器 {server.ip}:{server.port} 服务类型为: '其他'")
            updated_count += 1
    
    print(f"\n更新完成！共更新了 {updated_count} 条记录。")
    
    # 显示所有记录
    print("\n当前所有服务器记录:")
    all_servers = MonitoringServerInformation.objects.all().order_by('ip', 'port')
    for server in all_servers:
        print(f"IP: {server.ip}, 端口: {server.port}, "
              f"服务类型: {server.server_category}, 备注: {server.remarks}")

def create_sample_data():
    """如果没有数据，创建一些示例数据"""
    
    if MonitoringServerInformation.objects.count() == 0:
        print("没有找到现有数据，创建示例数据...")
        
        sample_servers = [
            {'ip': '192.168.46.50', 'port': 7788, 'server_category': '监控代理', 'remarks': '主监控服务器'},
            {'ip': '192.168.46.57', 'port': 22, 'server_category': 'SSH', 'remarks': '远程管理服务器'},
            {'ip': '192.168.1.100', 'port': 80, 'server_category': 'Nginx', 'remarks': 'Web前端服务器'},
        ]
        
        for server_data in sample_servers:
            server = MonitoringServerInformation.objects.create(**server_data)
            print(f"创建服务器记录: {server.ip}:{server.port} ({server.server_category})")
        
        print(f"创建了 {len(sample_servers)} 条示例记录。")
    else:
        print(f"找到 {MonitoringServerInformation.objects.count()} 条现有记录。")

if __name__ == '__main__':
    try:
        # 首先检查是否有数据，如果没有则创建示例数据
        create_sample_data()
        
        # 更新现有数据的服务类型
        update_server_categories()
        
    except Exception as e:
        print(f"执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
