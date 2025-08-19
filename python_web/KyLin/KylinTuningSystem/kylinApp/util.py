def dict_to_custom_str(data):
    return "; ".join([f"{k}={v}" for k, v in data.items()])

# 新增：AI推理用的数据获取函数
from kylinApp.models import CPUPerformanceMetrics, MemoryPerformanceMetrics, DiskPerformanceMetrics, NetworkPerformanceMetrics

def get_info_to_ai():
    # 获取最新一条CPU、内存、磁盘、网络数据
    cpu = CPUPerformanceMetrics.objects.last()
    mem = MemoryPerformanceMetrics.objects.last()
    disk = DiskPerformanceMetrics.objects.last()
    net = NetworkPerformanceMetrics.objects.last()
    data = {}
    if cpu:
        data.update({
            'cpu_type': cpu.type,
            'cpu_ip': cpu.ipaddress,
            'cpu_userTime': cpu.userTime,
            'cpu_SystemTime': cpu.SystemTime,
            'cpu_waitIO': cpu.waitIO,
            'cpu_Idle': cpu.Idle,
            'cpu_count': cpu.count,
            'cpu_percent': float(cpu.percent),
            'cpu_time': cpu.currentTime.strftime('%Y-%m-%d %H:%M:%S'),
        })
    if mem:
        data.update({
            'mem_type': mem.type,
            'mem_ip': mem.ipaddress,
            'mem_total': mem.total,
            'mem_used': mem.used,
            'mem_free': mem.free,
            'mem_buffers': mem.buffers,
            'mem_cache': mem.cache,
            'mem_swap': mem.swap,
            'mem_percent': float(mem.percent),
            'mem_time': mem.currentTime.strftime('%Y-%m-%d %H:%M:%S'),
        })
    if disk:
        data.update({
            'disk_type': disk.type,
            'disk_ip': disk.ipaddress,
            'disk_total': disk.total,
            'disk_used': disk.used,
            'disk_free': disk.free,
            'disk_percent': float(disk.percent),
            'disk_time': disk.currentTime.strftime('%Y-%m-%d %H:%M:%S'),
        })
    if net:
        data.update({
            'net_type': net.type,
            'net_ip': net.ipaddress,
            'net_sent': net.sent,
            'net_recv': net.recv,
            'net_packetSent': net.packetSent,
            'net_packetRecv': net.packetRecv,
            'net_time': net.currentTime.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return data 
