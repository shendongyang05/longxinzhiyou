import socket, os, datetime, json
import time

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



def set_info(data, host, tp):
    data = data[tp]
    insert_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data.update({"host": host})
    data.update({"time": insert_time})

    # if tp == "cpu":
    #     set_cpu_info(data)
    # elif tp == "memory":
    #     set_memory_info(data)
    # elif tp == "network":
    #     set_network_info(data)
    # elif tp == "os":
    #     set_os_info(data)
    # else:
    #     set_disk_info(data)


def category(data, tp):
    return data[tp]


def get_info(host, port: int, tp):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        data = json.dumps({'command': 'get_info'})
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
            recv_info.pop("os_information")
            data_dict = {
                "info": recv_info,
                "state": "ok"
            }
        return data_dict


# 发送远程执行命令
def send_command(command_string, host, port: int, change_cpu=None, pid=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        data = json.dumps({'command': command_string})
        if change_cpu and pid:
            data[""]
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
        if command_string == "get_ps":
            return recv_info
        else:
            return recv_info.encode(errors="ignore").decode('unicode-escape', errors="ignore")



"""以下命令使用待定"""


if __name__ == '__main__':
    # print(send_command("get_ps", "10.21.17.40", 7788))
    data = send_command("slove_su", "10.21.17.40", 7788)
    data = send_command("slove_system_jam", "10.21.17.40", 7788)
    print(data)
    pass

    # print(decimal_value)
    # with open("data.json", "w") as f:
    #     json.dump(data, f, indent=4)
    # print(data)
    # print(send_command("get_top", "10.21.17.40", 7788))
