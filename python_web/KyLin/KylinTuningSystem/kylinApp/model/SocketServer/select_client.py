import socket, os, datetime, json
import time

from ..ModuleTwo import cpu, disk, memory, network, other
import threading
# from kylinApp.utils import draw,write_data
import re


def match_leading_digits(text):
    """
    从字符串的开头开始匹配，直到遇到第一个非数字字符为止。

    :param text: 输入字符串
    :return: 匹配到的数字部分，如果没有匹配到则返回空字符串
    """
    match = re.match(r'^\d+', text)
    if match:
        return match.group(0)
    else:
        return ""

def recv_data(client_socket):
    # 分段接收数据
    recv_info = ""
    leng = 0
    while True:
        recv_data = client_socket.recv(1024).decode('utf-8')
        if leng == 0:
            # print(recv_data)
            try:
                len_data = int(recv_data)
            except ValueError:
                str_length = int(match_leading_digits(recv_data))
                len_data = str_length

        recv_info = recv_info + recv_data
        if isinstance(recv_data, int):
            leng = leng + len(str(recv_data))
        else:
            leng = leng + len(recv_data)
        if leng >= len_data:
            break
    return recv_info



def remove_leading_numbers(input_string):
    # 正则表达式模式：匹配开头的一个或多个数字
    pattern = r'^\d+'
    # 使用sub函数替换匹配到的部分为空字符串
    result = re.sub(pattern, '', input_string)
    return result


def set_network_info(data):
    tp = "recieveNetWorkIfo"
    ip = data.get("host")
    sent = data.get("net_bytes_sent")
    recv = data.get("net_bytes_recv")
    packet_sent = data.get("net_packets_sent")
    packet_recv = data.get("net_packets_recv")
    current_t = data.get("time")
    network.insert(tp, ip, sent, recv, packet_sent, packet_recv, current_t)


def set_memory_info(data):
    tp = "recievememoryInfo"
    ip = data.get("host")
    total = data.get("mem_total")
    used = data.get("mem_used")
    free = data.get("mem_free")
    buffers = data.get("mem_buffers")
    cache = data.get("mem_cache")
    swap = data.get("mem_swap_used")
    percent = data.get("mem_percent")
    current_t = data.get("time")
    memory.insert(tp, ip, total, used, free, buffers, cache, swap, percent, current_t)


def set_disk_info(data):
    tp = "recieveHDInfo"
    ip = data.get("host")
    total = data.get("disk_total")
    used = data.get("disk_used")
    free = data.get("disk_free")
    percent = data.get("disk_percent")
    read_count = data.get("disk_read")
    write_count = data.get("disk_write")
    r_bytes = data.get("disk_read")
    w_bytes = data.get("disk_write")
    r_time = data.get("time")
    w_time = data.get("time")
    current_t = data.get("time")
    disk.insert(tp, ip, total, used, free, percent, read_count, write_count, r_bytes, w_bytes, r_time, w_time, current_t)


def set_cpu_info(data):
    tp = "recieveCPUInfo"
    ip = data.get("host")
    user_t = data.get("cpu_user_time")
    system_t = data.get("cpu_system_time")
    wait_io = data.get("cpu_wait_time")
    idle = data.get("cpu_idle_time")
    count = data.get("cpu_count")
    percent = data.get("cpu_percent")
    current_t = data.get("time")
    cpu.insert(tp, ip, user_t, system_t,wait_io, idle, count, percent,current_t)


def set_os_info(data):
    tp = "recieveOsInfo"
    os_info = data.get("os_info")
    os_version = data.get("os_version")
    os_release = data.get("os_release")
    os_name = data.get("os_name")
    os_processor_name = data.get("os_processor_name")
    os_processor_architecture = data.get("os_processor_architecture")
    cpu_model = data.get("os_processor_name")
    other.insert(tp,os_info,os_version,os_release,os_name,os_processor_name,os_processor_architecture,cpu_model)


def set_info(data, host, tp):
    data = data[tp]
    insert_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data.update({"host": host})
    data.update({"time": insert_time})

    if tp == "cpu":
        set_cpu_info(data)
    elif tp == "memory":
        set_memory_info(data)
    elif tp == "network":
        set_network_info(data)
    elif tp == "os":
        set_os_info(data)
    else:
        set_disk_info(data)


def category(data, tp):
    return data[tp]


def get_info(host, port: int, tp):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # 设置连接超时和读取超时
        client_socket.settimeout(10.0)  # 10秒超时
        client_socket.connect((host, port))
        data = json.dumps({'command': 'get_info',"cluster_ip": "10.21.17.25"})
        # data = json.dumps({'command': 'get_info'})]]
        client_socket.sendall(data.encode('utf-8'))
        recv_info = recv_data(client_socket)
        recv_info = remove_leading_numbers(recv_info)
        recv_info = json.loads(recv_info)

        if tp != "ceph_info":
            recv_info = recv_info["os_information"]
            set_info(recv_info, host, tp)
            data_dict = {
                "info": category(recv_info, tp),
                "state": "ok"
            }
        else:
            data_dict = {
                "info": recv_info,
                "state": "ok"
            }
        return data_dict


# 发送远程执行命令
def send_command(command_string, host, port: int, change_cpu=None, pid=None):
    print(f"select_client.send_command 被调用")
    print(f"参数: command_string={repr(command_string)}, host={host}, port={port}")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # 设置连接超时和读取超时
        client_socket.settimeout(10.0)  # 10秒超时
        client_socket.connect((host, port))
        command_data = {'command': command_string}
        if change_cpu and pid:
            command_data["pid"] = pid
            hex_string = change_cpu
            decimal_value = int(hex_string, 16)
            command_data["cpu_id"] = decimal_value
        data = json.dumps(command_data)
        print(f"发送的JSON数据: {data}")
        client_socket.sendall(data.encode('utf-8'))
        if command_string == "get_flame_graph":
            recv_info = recv_data(client_socket)
            recv_info = remove_leading_numbers(recv_info)
            recv_info = json.loads(recv_info)
            with open("./kylinApp/static/img/perf.svg", mode="w") as f:
                f.write(recv_info)
            return
        recv_info = recv_data(client_socket)
        recv_info = remove_leading_numbers(recv_info)
        print(f"接收到的原始响应: {repr(recv_info)}")
        if command_string == "get_ps":
            return recv_info
        else:
            processed_response = recv_info.encode(errors="ignore").decode('unicode-escape', errors="ignore")
            print(f"处理后的响应: {repr(processed_response)}")
            return processed_response


"""以下命令使用待定"""


# 发送Ceph集群命令的函数
def send_ceph_command(command, ceph_ip):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(('10.21.17.85' , 7788))
        data = json.dumps({'command': command, 'cluster_ip': ceph_ip})
        client_socket.sendall(data.encode('utf-8'))
        recv_info = ""
        leng = 0
        while True:
            recv_data = client_socket.recv(1024).decode('utf-8')
            if leng == 0:
                len_data = int(recv_data)
            recv_info = recv_info + recv_data
            if isinstance(recv_data,int):
                leng  = leng + len(str(recv_data))
            else:
                leng = leng + len(recv_data)
            if leng == len_data:
                break
            print(leng,len_data)
        print(recv_info)

# 创建线程的函数
def create_thread(target_function, args=()):
    thread = threading.Thread(target=target_function, args=args)
    thread.start()
    return thread

# 并行发送多个命令
# def parallel_commands(commands, ceph_ip="10.21.17.50"):
#     threads = []
#     for command in commands:
#         if ceph_ip:
#             thread = create_thread(send_ceph_command, (command, ceph_ip))
#         else:
#             thread = create_thread(send_command, (command,))
#         threads.append(thread)
#     # 等待所有线程完成
#     for thread in threads:
#         thread.join()


if __name__ == '__main__':
    # print(send_command("get_top", "10.21.17.40", 7788))
    pass