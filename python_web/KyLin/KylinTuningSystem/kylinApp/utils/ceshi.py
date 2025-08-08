import psutil
import time

def get_cpu_usage():
    # 获取 CPU 使用情况
    cpu_times = psutil.cpu_times(percpu=False)  # 获取所有 CPU 的总时间
    return {
        "Busy User": cpu_times.user,      # 用户时间
        "Busy System": cpu_times.system,   # 系统时间
        "Idle": cpu_times.idle,           # 空闲时间
        "Busy Iowait": getattr(cpu_times, 'iowait', 0),  # 等待 I/O 时间，如果不存在则为 0
        "Busy IRQs": getattr(cpu_times, 'interrupt', 0),  # 中断时间，如果不存在则为 0
        "Busy Other": getattr(cpu_times, 'nice', 0) + getattr(cpu_times, 'softirq', 0)  # 如果不存在则为 0
    }

while True:
    cpu_usage = get_cpu_usage()
    print(cpu_usage)
    time.sleep(1)  # 每秒更新一次
