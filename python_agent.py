import psutil
import re
import socket, os
import select
import json
import time
import platform
import subprocess
import logging
import threading
import multiprocessing
from lxml import etree

# from lxml.parser import result

# from lxml.parser import result

# 设置日志记录
logging.basicConfig(level=logging.INFO)


# 通用的字节转换函数
def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {s: 1 << (i + 1) * 10 for i, s in enumerate(symbols)}
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return f'{value:.1f}{s}'
    return f"{n}B"


# 获取主机名
hostname = socket.gethostname()


# 生成火焰图的函数
def generate_flame_graph(output_file='perf.svg'):
    try:
        # 记录perf数据
        perf_record_cmd = ['sudo', 'perf', 'record', '-e', 'cycles:u', '-a', '-g', '--', 'sleep', '60']
        result = subprocess.run(perf_record_cmd, check=True)

        # 生成折叠后的调用栈
        perf_script_cmd = ['sudo', 'perf', 'script', '-i', 'perf.data']
        if os.path.exists('perf.data'):
            with open('perf.unfold', 'w') as f:
                subprocess.run(perf_script_cmd, stdout=f, check=True)
        else:
            return

        # 生成SVG图
        flamegraph_cmd = (
            "sudo perf script | "
            "/root/os_manage/FlameGraphChart/FlameGraph/stackcollapse-perf.pl | "
            "/root/os_manage/FlameGraphChart/FlameGraph/flamegraph.pl > "
            f"{output_file}"
        )
        subprocess.run(flamegraph_cmd, shell=True, check=True)

        # 返回生成的文件路径
        return output_file
    except Exception as e:
        print(e)


# 获取CPU信息
def get_cpu_info():
    try:
        cpu_times = psutil.cpu_times(percpu=False)
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_model = platform.processor()
        user_time = time.strftime('%H:%M:%S', time.gmtime(cpu_times.user))
        system_time = time.strftime('%H:%M:%S', time.gmtime(cpu_times.system))
        idle_time = time.strftime('%H:%M:%S', time.gmtime(cpu_times.idle))
        wait_time = time.strftime('%H:%M:%S', time.gmtime(cpu_times.iowait))
        return dict(cpu_count=cpu_count, cpu_percent=cpu_percent, cpu_user_time=user_time, cpu_system_time=system_time,
                    cpu_idle_time=idle_time, cpu_wait_time=wait_time, cpu_model=cpu_model)
    except Exception as e:
        print(e)


# 获取内存信息
def get_memory_info():
    try:
        virtual_mem = psutil.virtual_memory()
        mem_total = bytes2human(virtual_mem.total)
        mem_used = bytes2human(virtual_mem.used)
        mem_free = bytes2human(virtual_mem.free)
        mem_percent = virtual_mem.percent
        mem_buffers = bytes2human(virtual_mem.buffers)
        mem_cache = bytes2human(virtual_mem.cached)
        swap_info = psutil.swap_memory()
        swap_total = bytes2human(swap_info.total)
        swap_used = bytes2human(swap_info.used)
        swap_free = bytes2human(swap_info.free)
        swap_percent = swap_info.percent
        return dict(mem_total=mem_total, mem_used=mem_used, mem_free=mem_free, mem_percent=mem_percent,
                    mem_buffers=mem_buffers, mem_cache=mem_cache, mem_swap_total=swap_total, mem_swap_used=swap_used,
                    mem_swap_free=swap_free, mem_swap_percent=swap_percent)
    except Exception as e:
        print(e)


# 获取磁盘信息
def get_disk_info():
    try:
        disk_usage = psutil.disk_usage('/')
        disk_total = bytes2human(disk_usage.total)
        disk_used = bytes2human(disk_usage.used)
        disk_free = bytes2human(disk_usage.free)
        disk_percent = disk_usage.percent
        disk_io = psutil.disk_io_counters()
        disk_read = bytes2human(disk_io.read_bytes)
        disk_write = bytes2human(disk_io.write_bytes)
        return dict(disk_total=disk_total, disk_used=disk_used, disk_free=disk_free, disk_percent=disk_percent,
                    disk_read=disk_read, disk_write=disk_write)
    except Exception as e:
        print(e)


# 获取网络信息
def get_net_info():
    try:
        net_io = psutil.net_io_counters(pernic=False)
        net_bytes_sent = bytes2human(net_io.bytes_sent)
        net_bytes_recv = bytes2human(net_io.bytes_recv)
        net_packets_recv = bytes2human(net_io.packets_recv)
        net_packets_sent = bytes2human(net_io.packets_sent)
        return dict(net_bytes_sent=net_bytes_sent, net_bytes_recv=net_bytes_recv,
                    net_packets_recv=net_packets_recv, net_packets_sent=net_packets_sent)
    except Exception as e:
        print(e)


# 获取操作系统信息
def get_os_info():
    try:
        os_name = platform.system()
        os_processor_name = platform.processor()
        os_processor_architecture = platform.architecture()
        os_info = platform.platform()
        os_version = platform.version()
        os_release = platform.release()
        return dict(os_info=os_info, os_version=os_version, os_release=os_release,
                    os_name=os_name, os_processor_name=os_processor_name,
                    os_processor_architecture=os_processor_architecture)
    except Exception as e:
        print(e)


def run_top():
    try:
        # 运行top命令
        result = subprocess.run(['top', '-n', '1', 'b'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                                text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"运行top出错: {e.stderr}")


def get_ps():
    try:
        # 运行ps命令
        result = subprocess.run(['ps', '-eo', 'psr=CPU核心,pid=进程号,cmd=启动命令'], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"运行ps出错: {e.stderr}")


# 运行biotop的函数
def run_biolatency():
    try:
        # 运行biotop命令，并将其输出写入到biotop_output.txt文件
        with open("/opt/biotop_output.txt", "w") as output_file:
            subprocess.run(['/usr/share/bcc/tools/biolatency', "-D", "-T", "3", "10"], stdout=output_file,
                           stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"运行biotop出错: {e.stderr}")


# 运行dd命令的函数
def run_dd():
    try:
        # 运行dd命令
        subprocess.run(['dd', 'if=/dev/vda', 'of=/dev/zero'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"运行dd出错: {e.stderr}")


# 汇集系统信息
def gather_monitor_data():
    return {
        'hostname': hostname,
        'os': get_os_info(),
        'cpu': get_cpu_info(),
        'memory': get_memory_info(),
        'disk': get_disk_info(),
        'network': get_net_info()
    }


# 分解长字符
def split_string_by_length(string, length):
    return [string[i:i + length] for i in range(0, len(string), length)]


def check_container_exists(container_name):
    try:
        result = subprocess.run(['docker', 'inspect', container_name],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        return True  # Container exists
    except subprocess.CalledProcessError:
        return False  # Container does not exist


# 处理客户端连接的函数
# def handle_client(client_socket):
#    try:
#        while True:
#            data = client_socket.recv(1024).decode('utf-8')
#            if not data:
#                break
#            command = json.loads(data)
#            if isinstance(command, dict) and 'command' in command:
#                response = handle_command(command['command'], command.get('cluster_ip'))
#                back_data = json.dumps(response)  # 提前做字符串格式转化
#                client_socket.send(str(len(back_data)).encode('utf-8'))
#                # print(len(back_data))
#                back_list = split_string_by_length(back_data,1024)
#                for sub_back in back_list:
#                    client_socket.send(sub_back.encode('utf-8'))
#            else:
#                response = {'error': 'Invalid command format'}
#                client_socket.send(json.dumps(response).encode('utf-8'))
#    except (ConnectionError, BrokenPipeError) as e:
#        logging.error(f"连接错误: {e}")
#    finally:
#        client_socket.close()
def handle_client(client_socket):
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            command = json.loads(data)
            if isinstance(command, dict) and 'command' in command:
                # 从 command 中提取 pid
                cmd = command['command']
                pid = command.get('pid')  # 提取 pid
                cpu_id = command.get('cpu_id')
                cluster_ip = command.get('cluster_ip')

                # 将 pid 传递给 handle_command 函数
                response = handle_command(cmd, cluster_ip, pid, cpu_id)

                # 返回响应
                back_data = json.dumps(response)
                client_socket.send(str(len(back_data)).encode('utf-8'))
                back_list = split_string_by_length(back_data, 1024)
                for sub_back in back_list:
                    client_socket.send(sub_back.encode('utf-8'))
            else:
                response = {'error': 'Invalid command format'}
                client_socket.send(json.dumps(response).encode('utf-8'))
    except (ConnectionError, BrokenPipeError) as e:
        logging.error(f"连接错误: {e}")
    finally:
        client_socket.close()


def get_process_cpu_affinity(pid):
    result = subprocess.run(["taskset", "-pc", str(pid)], capture_output=True, text=True)
    return result.stdout


def set_process_cpu_affinity(pid, cpu_id):
    result = subprocess.run(["taskset", "-pc", str(cpu_id), str(pid)], capture_output=True, text=True)
    return result.stdout


def check_and_fix_su_permissions():
    """检查并修复 /bin/su 文件的权限，返回检查和修复的结果"""
    su_path = '/bin/su'
    desired_permissions = '4755'

    # 检查权限
    def check_permissions():
        st = os.stat(su_path)
        permissions = oct(st.st_mode)[-4:]
        print(f"Current permissions of {su_path}: {permissions}")
        return permissions

    current_permissions = check_permissions()

    # 检查权限是否为 -rwsr-xr-x (04755)
    if current_permissions != '4755':
        print("Incorrect permissions detected. Attempting to fix...")

        # 修复权限
        def fix_permissions():
            try:
                subprocess.run(['sudo', 'chmod', desired_permissions, su_path], check=True)
                print(f"Permissions of {su_path} have been set to {desired_permissions}.")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to change permissions: {e}")
                return False

        fix_result = fix_permissions()
        new_permissions = check_permissions()  # 再次检查权限
        return {
            'initial_permissions': current_permissions,
            'fixed': fix_result,
            'final_permissions': new_permissions
        }
    else:
        print("Permissions are correct.")
        return {
            'initial_permissions': current_permissions,
            'fixed': False,
            'final_permissions': current_permissions
        }


# 运行Ceph命令并返回结果
def run_ceph_command(command, cluster_ip=None):
    # cmd = ['ceph', '-m', cluster_ip] + command if cluster_ip else ['ceph'] + command
    cmd = ['ssh', f'root@{cluster_ip}', 'docker', 'exec'] + command if cluster_ip else ['ceph'] + command
    print(cmd)
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"运行命令出错 {cmd}: {e.stderr}")
        return None


# , '--format', 'json' json.loads(mon_output)
def get_cluster_status(cluster_ip=None):
    status_output = run_ceph_command(['mon', 'ceph', 'status'], cluster_ip)
    return status_output if status_output else None


def get_osd_status(cluster_ip=None):
    osd_output = run_ceph_command(['mon', 'ceph', 'osd', 'tree'], cluster_ip)
    return osd_output if osd_output else None


def get_mon_status(cluster_ip=None):
    mon_output = run_ceph_command(['mon', 'ceph', '-s'], cluster_ip)
    return mon_output if mon_output else None


def Resolve_system_jam():
    try:
        result = subprocess.run(['sudo', 'yum', '-y', 'reinstall', 'kylin-activation'], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(e)
        return None


def Solve_auditd_hight_memory():
    try:
        result = subprocess.run(['sudo', 'systemctl', 'restart', 'auditd'], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(e)
        return None


# 处理输入命令并返回结果
def handle_command(command, cluster_ip=None, pid=None, cpu_id=None):
    print(f"进入handle_command，收到命令: {repr(command)}")
    print(f"命令类型: {type(command)}")
    print(f"命令长度: {len(command) if command else 0}")
    print(f"命令去除空格后: {repr(command.strip()) if command else 'None'}")
    try:
        # 指令映射表，支持直接输入完整命令
        COMMAND_MAP = {
            'command:sudo firewall-cmd --state': [['sudo', 'firewall-cmd', '--state'], ['sudo', 'systemctl', 'status', 'firewalld']],
            'command:sudo systemctl start firewalld': [['sudo', 'systemctl', 'start', 'firewalld']],
            'command:sudo systemctl stop firewalld': [['sudo', 'systemctl', 'stop', 'firewalld']],
            'command:sudo tune2fs -o journal_data_writeback /dev/sda1 && sudo mount -o remount /dev/sda1': [
                ['sudo', 'tune2fs', '-o', 'journal_data_writeback', '/dev/sda1'],
                ['sudo', 'mount', '-o', 'remount', '/dev/sda1']
            ],
            'command:sudo systemctl stop ntpd': [['sudo', 'systemctl', 'stop', 'ntpd'], ['sudo', 'systemctl', 'stop', 'chronyd']],
            'command:timedatectl status': [['timedatectl', 'status'], ['ntpq', '-p']],
            'command:sudo systemctl start ntpd': [['sudo', 'systemctl', 'start', 'ntpd'], ['sudo', 'systemctl', 'start', 'chronyd']],
            'command:sudo sysctl -w net.ipv4.tcp_syncookies=1': [['sudo', 'sysctl', '-w', 'net.ipv4.tcp_syncookies=1']],
            'command:mysqldump -u root -p yourpassword aa > aa_backup.sql': [['mysqldump', '-u', 'root', '-pyourpassword', 'aa']],
            'command:mysql -e "SET GLOBAL query_cache_size = 1048576;"': [['mysql', '-e', 'SET GLOBAL query_cache_size = 1048576;']],
            'command:timedatectl': [['timedatectl']],
            'command:sudo timedatectl set-ntp true': [['sudo', 'timedatectl', 'set-ntp', 'true'], ['sudo', 'systemctl', 'restart', 'ntpd']],
            'command:who': [['who'], ['w']],
            'command:sudo sync && sudo sysctl -w vm.drop_caches=3': [['sudo', 'sync'], ['sudo', 'sysctl', '-w', 'vm.drop_caches=3']],
            'command:df -h': [['df', '-h']],
            'command:sudo systemctl restart nginx': [['sudo', 'systemctl', 'restart', 'nginx']],
            'command:dmesg': [['dmesg']],
            'command:uptime': [['uptime'], ['top']],
            'command:free -h': [['free', '-h'], ['top']],
            'command:lscpu': [['lscpu'], ['cat', '/proc/cpuinfo']],
            'command:sudo reboot': [['sudo', 'reboot']],
            'command:sudo systemctl restart mysqld': [['sudo', 'systemctl', 'restart', 'mysqld'], ['mysql']],
            'command:ping 127.0.0.1': [['ping', '127.0.0.1']],
            'command:curl -I http://127.0.0.1': [['curl', '-I', 'http://127.0.0.1']],
            'command:sudo lsof -i :80': [['sudo', 'lsof', '-i', ':80'], ['sudo', 'netstat', '-tulnp']],
            'command:sudo kill -9 $(lsof -t -i:80)': [['sudo', 'kill', '-9', '$(lsof -t -i:80)']],
            'command:netstat -an': [['netstat', '-an']],
            'command:sudo systemctl restart docker': [['sudo', 'systemctl', 'restart', 'docker']],
            'command:journalctl -k': [['journalctl', '-k']],
            'command:ps -eo pid,psr,comm': [['ps', '-eo', 'pid,psr,comm']],
            'command:ps aux': [['ps', 'aux']],
            'command:top -b -n 1 > system_status.txt && dmesg > dmesg.log && free -h > memory.log': [
                ['top', '-b', '-n', '1'],
                ['dmesg'],
                ['free', '-h']
            ],
        }
        cmd_key = command.strip()
        if not cmd_key.startswith("command:"):
            cmd_key = "command:" + cmd_key
        cmd_key = cmd_key.strip()
        print(f"收到的cmd_key: [{cmd_key}], 长度: {len(cmd_key)}")
        for k in COMMAND_MAP.keys():
            print(f"可匹配key: [{k}], 长度: {len(k)}")
        # 匹配时也strip key
        match_key = None
        for k in COMMAND_MAP.keys():
            if cmd_key == k.strip():
                match_key = k
                break
        if match_key:
            output = ''
            for cmd in COMMAND_MAP[match_key]:
                try:
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    output += result.stdout + '\n'
                except Exception as e:
                    output += f'执行{cmd}出错: {e}\n'
            return output
        # 自定义函数分支
        elif cmd_key == 'command:slove_su' or cmd_key == 'slove_su':
            return check_and_fix_su_permissions()
        elif cmd_key == 'command:slove_system_jam' or cmd_key == 'slove_system_jam':
            subprocess.run(['sync'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            subprocess.run(['bash', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return "已尝试释放缓存，建议检查高负载进程"
        elif command.strip() == 'get_info':
            data = {
                "os_information": gather_monitor_data()
            }
            return data
        elif command.strip() == 'slove_su':
            data = check_and_fix_su_permissions()
            return data
        elif command.strip() == 'slove_system_jam':
            data = '优化银河麒麟V10 SP3 系统卡顿未响应'
            Resolve_system_jam()
            return data
        elif command.strip() == 'slove_auditd':
            data = '解决银河麒麟V10 SP3 审计工具 auditd 引发的内存占用过高'
            solve_auditd_hight_memory()
            return data
        elif command.strip() == 'get_cpuhe':
            data = get_process_cpu_affinity(pid)
            return data
        elif command.strip() == 'set_cpu_affinity' and pid is not None:
            # 示例：将进程迁移到指定的 CPU 核心上
            # 假设目标 CPU 核编号为 0
            data = set_process_cpu_affinity(pid, cpu_id)
            return data
        elif command.strip() == 'get_ps':
            input_string = get_ps()
            # 创建一个空字典，用于存储每一行的数据
            data = {
                'CPU核心': [],
                '进程号': [],
                '启动命令': []
            }

            # 分割字符串为多行
            lines = input_string.strip().split('\n')[1:]  # 跳过第一行标题
            # 遍历每一行数据
            for line in lines:
                # 去除行首的空白字符
                line = line.lstrip()
                # 分割行数据
                parts = line.split(maxsplit=2)
                if len(parts) == 3:
                    cpu_core, pid, command = parts
                    # 将数据存储到字典中
                    data['CPU核心'].append(int(cpu_core))
                    data['进程号'].append(int(pid))
                    data['启动命令'].append(command)

            return data
        elif command.strip() == 'get_top':
            input_string = run_top()
            # 初始化存储数据的字典
            process_data = {}

            # 使用正则表达式匹配进程信息的行
            pattern = re.compile(
                r'^\s*(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+K?)\s+(\d+K?)\s+(\d+K?)\s+(\S+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\S+)\s+(.+)$')

            # 逐行解析 top 输出
            for line in input_string.splitlines():
                match = pattern.match(line)
                if match:
                    pid = match.group(1)
                    process_data[pid] = {
                        "PID": pid,
                        "USER": match.group(2),
                        "PR": match.group(3),
                        "NI": match.group(4),
                        "VIRT": match.group(5),
                        "RES": match.group(6),
                        "SHR": match.group(7),
                        "S": match.group(8),
                        "%CPU": match.group(9),
                        "%MEM": match.group(10),
                        "TIME+": match.group(11),
                        "COMMAND": match.group(12)
                    }

            return process_data
        elif command.startswith('command:get_biotop'):
            new_multiprocess1 = multiprocessing.Process(target=run_biolatency())
            new_multiprocess2 = multiprocessing.Process(target=run_dd)
            new_multiprocess1.start()
            new_multiprocess2.start()
            time.sleep(30)
            with open('/opt/biotop_output.txt', 'r') as f:
                data = f.read()
            return data
        elif command.strip() == 'get_flame_graph':
            flame_graph_path = generate_flame_graph()
            with open(flame_graph_path, 'r') as f:
                data = f.read()
            return data
        # elif command.startswith('command:ls '):
        #     directory = command.split(' ', 1)[1]
        #     result = subprocess.run(['ls', directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        #     return result.stdout
        elif command.strip() == 'command:查看防火墙':
            result = subprocess.run(['systemctl', 'status', 'firewalld'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout
        elif command.strip() == 'command:get_io_stack':
            # 定义 docker run 命令及其参数

            docker_command = [
                "docker", "run", "-itd", "--name", "ebpf", "--privileged",
                "-v", "/lib/modules:/lib/modules:rw",
                "-v", "/sys:/sys",
                "-v", "/root:/root",
                "-v", "/usr/src:/usr/src",
                "-v", "/etc/localtime:/etc/localtime:rw",
                "-v", "/usr/src/kernels/:/usr/src/kernels/",
                '--restart=always',
                "--pid=host",
                "ebpf:v1", "python3", "wudipaima.py"
            ]
            # 使用 subprocess.run 执行 docker run 命令
            try:
                subprocess.run(docker_command)

                print(f"Please wait 30s ,Container started successfully")
                with open('/root/io_stats.txt', 'r') as f:
                    data = f.read()
                result = subprocess.run(['docker', 'exec', '-it', 'ebpf', 'cat', '/root/io_stats.json'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                # 将 result.stdout 转换为 JSON 格式并返回
                return data
                # time.sleep(30)
                # with open('/root/io_stats.txt','r') as f:
                # print(f.read())
                # data = f.read()

            except subprocess.CalledProcessError as e:
                print(f"Error occurred while starting the container", e)
        elif command.strip() == 'command:开启防火墙':
            result = subprocess.run(['sudo', 'systemctl', 'start', 'firewalld'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout
        elif command.strip() == 'command:关闭防火墙':
            result = subprocess.run(['sudo', 'systemctl', 'stop', 'firewalld'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout
        elif command.strip() == 'command:关闭NTP同步服务器':
            result = subprocess.run(['sudo', 'systemctl', 'stop', 'ntpd'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout
        elif command.strip() == 'command:查看NTP同步服务器':
            result = subprocess.run(['sudo', 'systemctl', 'status', 'ntpd'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout
        elif command.strip() == 'command:开启NTP同步服务器':
            result = subprocess.run(['sudo', 'systemctl', 'start', 'ntpd'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout
        elif command.strip() == 'command:优化文件系统':
            result = subprocess.run(['sudo', 'tune2fs', '-o', 'journal_data_writeback', '/dev/sda1'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout

        elif command.strip() == 'command:查看时间同步':
            result = subprocess.run(['chronyc', 'sources', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True)
            return result.stdout
        elif command.startswith('command:设置NTP'):
            subprocess.run(["sed", "-i", "'3a server ntp1.aliyun.com iburst'", "/etc/chrony.conf"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            subprocess.run(['systemctl', 'restart', 'chronyd'])
            return "设置成功"
        elif command.strip() == 'command:启用SYN Cookie':
            result = subprocess.run(['sudo', 'sysctl', '-w', 'net.ipv4.tcp_syncookies=1'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout
        elif command.startswith('command:备份数据库'):
            db_name = command.split(' ', 1)[1]
            result = subprocess.run(['sudo', 'pg_dump', db_name, '>', f'/backup/{db_name}.sql'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout
        elif command.strip() == 'command:添加数据库缓存':
            resize_commands = [
                'sudo', 'sed', '-i',
                '-e', '/^lower_case_table_names=/c\\lower_case_table_names = 0',
                '-e', '/^innodb_buffer_pool_size=/c\\innodb_buffer_pool_size = 4G',
                '-e', '/^innodb_log_buffer_size=/c\\innodb_log_buffer_size = 64M',
                '-e', '/^innodb_log_file_size=/c\\innodb_log_file_size = 256M',
                '-e', '/^innodb_log_files_in_group=/c\\innodb_log_files_in_group = 2',
                '-e', '/^query_cache_type=/c\\query_cache_type = 1',
                '-e', '/^query_cache_size=/c\\query_cache_size = 600000',
                # 如果以下行不存在，则在文件末尾添加它们
                '-e', '$a\\lower_case_table_names = 0',
                '-e', '$a\\innodb_buffer_pool_size = 4G',
                '-e', '$a\\innodb_log_buffer_size = 64M',
                '-e', '$a\\innodb_log_file_size = 256M',
                '-e', '$a\\innodb_log_files_in_group = 2',
                '-e', '$a\\query_cache_type = 1',
                '-e', '$a\\query_cache_size = 600000',
                '/etc/my.cnf'
            ]
            subprocess.run(resize_commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return "数据库缓存已添加"
        # 新增指令
        elif command.strip() == 'command:查看当前登录用户':
            print("执行查看当前登录用户命令")
            result = subprocess.run(['who'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print("who命令输出:", result.stdout)
            return result.stdout

        elif command.strip() == 'command:清理系统缓存':
            subprocess.run(['sync'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            subprocess.run(['bash', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)
            return "系统缓存已清理"

        elif command.strip() == 'command:查看磁盘使用情况':
            result = subprocess.run(['df', '-h'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout

        elif command.strip() == 'command:重启Nginx服务':
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'nginx'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout or "Nginx 服务已重启"

        elif command.strip() == 'command:检查系统内核日志':
            result = subprocess.run(['dmesg', '|', 'tail'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    shell=True)
            return result.stdout

        elif command.strip() == 'command:查看系统负载':
            result = subprocess.run(['uptime'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout

        elif command.strip() == 'command:查看内存使用情况':
            result = subprocess.run(['free', '-h'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout

        elif command.strip() == 'command:查看CPU信息':
            result = subprocess.run(['lscpu'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout

        elif command.strip() == 'command:重启服务器':
            result = subprocess.run(['sudo', 'reboot'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return "服务器重启命令已发送"

        elif command.strip() == 'command:重启MySQL服务':
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'mysqld'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout or "MySQL 服务已重启"

        elif command.strip() == 'command:检测网络连接状态':
            result = subprocess.run(['ping', '-c', '4', 'baidu.com'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True)
            return result.stdout

        elif command.strip() == 'command:查看端口占用情况':
            result = subprocess.run(['sudo', 'lsof', '-i', '-P', '-n'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True)
            return result.stdout

        elif command.strip() == 'command:终止占用端口的进程':
            result = subprocess.run(['sudo', 'fuser', '-k', '端口号/tcp'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout or "占用端口的进程已终止"

        elif command.strip() == 'command:查看活跃连接数':
            result = subprocess.run(['netstat', '-an'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout

        elif command.strip() == 'command:重启Docker服务':
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'docker'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout or "Docker 服务已重启"

        elif command.strip() == 'command:查看内核日志':
            result = subprocess.run(['journalctl', '-k', '--no-pager'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True)
            return result.stdout

        elif command.strip() == 'command:检查CPU绑定情况':
            result = subprocess.run(['ps', '-eo', 'pid,psr,comm'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True)
            return result.stdout

        elif command.strip() == 'command:查看运行进程':
            result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout

        elif command.strip() == 'command:导出当前系统状态':
            result = subprocess.run(['top', '-b', '-n', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            with open('/tmp/system_snapshot.txt', 'w') as f:
                f.write(result.stdout)
            return "系统状态已导出到 /tmp/system_snapshot.txt"
        else:
            # 支持自定义shell命令（仅开发/测试环境建议）
            if cmd_key.startswith('command:'):
                shell_cmd = cmd_key[len('command:'):].strip()
                print(f"执行自定义shell命令: {shell_cmd}")
                try:
                    result = subprocess.run(shell_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    return result.stdout + result.stderr
                except Exception as e:
                    return f'执行自定义命令出错: {e}'
            print(f"接收到的命令: {command}")
            print(f"收到命令: {repr(command)}")  # repr 能把不可见字符都打印出来
            print(f"命令不匹配，返回unknown command")
            return 'unknown command'
    except Exception as e:
        print(f"进入handle_command，收到命令: {repr(command)}")
        print(f"执行命令出错: {e}")
        logging.error(f"执行命令出错: {e}")
        return f"执行命令出错: {e}"


# 服务器主函数
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', 7788))
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8000000)
        # server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8000000)
        server_socket.listen(10)
        inputs = [server_socket]

        while True:
            try:
                readable, _, _ = select.select(inputs, [], [])
                for s in readable:
                    if s is server_socket:
                        new_socket, client_address = server_socket.accept()
                        logging.info(f"客户端连接: {client_address}")
                        client_thread = threading.Thread(target=handle_client, args=(new_socket,))
                        client_thread.start()
            except (ValueError, socket.error) as e:
                logging.error(f"select.select 错误: {e}")
                break


if __name__ == '__main__':
    main()

import socket, os, datetime, json
import time

#from ..ModuleTwo import cpu, disk, memory, network, other
import threading
# from kylinApp.utils import draw,write_data
import re


def recv_data(client_socket):
    # 分段接收数据
    recv_info = ""
    leng = 0
    while True:
        recv_data = client_socket.recv(1024).decode('utf-8')
        if leng == 0:
            len_data = int(recv_data)
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


# def set_network_info(data):
#     tp = "recieveNetWorkIfo"
#     ip = data.get("host")
#     sent = data.get("net_bytes_sent")
#     recv = data.get("net_bytes_recv")
#     packet_sent = data.get("net_packets_sent")
#     packet_recv = data.get("net_packets_recv")
#     current_t = data.get("time")
#     network.insert(tp, ip, sent, recv, packet_sent, packet_recv, current_t)
#
#
# def set_memory_info(data):
#     tp = "recievememoryInfo"
#     ip = data.get("host")
#     total = data.get("mem_total")
#     used = data.get("mem_used")
#     free = data.get("mem_free")
#     buffers = data.get("mem_buffers")
#     cache = data.get("mem_cache")
#     swap = data.get("mem_swap_used")
#     percent = data.get("mem_percent")
#     current_t = data.get("time")
#     memory.insert(tp, ip, total, used, free, buffers, cache, swap, percent, current_t)
#
#
# def set_disk_info(data):
#     tp = "recieveHDInfo"
#     ip = data.get("host")
#     total = data.get("disk_total")
#     used = data.get("disk_used")
#     free = data.get("disk_free")
#     percent = data.get("disk_percent")
#     read_count = data.get("disk_read")
#     write_count = data.get("disk_write")
#     r_bytes = data.get("disk_read")
#     w_bytes = data.get("disk_write")
#     r_time = data.get("time")
#     w_time = data.get("time")
#     current_t = data.get("time")
#     disk.insert(tp, ip, total, used, free, percent, read_count, write_count, r_bytes, w_bytes, r_time, w_time, current_t)
#
#
# def set_cpu_info(data):
#     tp = "recieveCPUInfo"
#     ip = data.get("host")
#     user_t = data.get("cpu_user_time")
#     system_t = data.get("cpu_system_time")
#     wait_io = data.get("cpu_wait_time")
#     idle = data.get("cpu_idle_time")
#     count = data.get("cpu_count")
#     percent = data.get("cpu_percent")
#     current_t = data.get("time")
#     cpu.insert(tp, ip, user_t, system_t,wait_io, idle, count, percent,current_t)
#
#
# def set_os_info(data):
#     tp = "recieveOsInfo"
#     os_info = data.get("os_info")
#     os_version = data.get("os_version")
#     os_release = data.get("os_release")
#     os_name = data.get("os_name")
#     os_processor_name = data.get("os_processor_name")
#     os_processor_architecture = data.get("os_processor_architecture")
#     cpu_model = data.get("os_processor_name")
#     other.insert(tp,os_info,os_version,os_release,os_name,os_processor_name,os_processor_architecture,cpu_model)


# def set_info(data, host, tp):
#     data = data[tp]
#     insert_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     data.update({"host": host})
#     data.update({"time": insert_time})
#
#     if tp == "cpu":
#         set_cpu_info(data)
#     elif tp == "memory":
#         set_memory_info(data)
#     elif tp == "network":
#         set_network_info(data)
#     elif tp == "os":
#         set_os_info(data)
#     else:
#         set_disk_info(data)


def category(data, tp):
    return data[tp]


# def get_info(host, port: int, tp):
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
#         client_socket.connect((host, port))
#         data = json.dumps({'command': 'get_info'})
#         client_socket.sendall(data.encode('utf-8'))
#
#         recv_info = recv_data(client_socket)
#         recv_info = remove_leading_numbers(recv_info)
#         recv_info = json.loads(recv_info)
#
#         if tp != "ceph_info":
#             recv_info = recv_info["os_information"]
#             set_info(recv_info, host, tp)
#             data_dict = {
#                 "info": category(recv_info, tp),
#                 "state": "ok"
#             }
#         else:
#             recv_info.pop("os_information")
#             data_dict = {
#                 "info": recv_info,
#                 "state": "ok"
#             }
#         return data_dict


# 发送远程执行命令
# def send_command(command_string, host, port: int):
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
#         client_socket.connect((host, port))
#         data = json.dumps({'command': command_string})
#         client_socket.sendall(data.encode('utf-8'))
#         if command_string == "get_flame_graph":
#             recv_info = recv_data(client_socket)
#             recv_info = remove_leading_numbers(recv_info)
#             recv_info = json.loads(recv_info)
#             with open("./kylinApp/static/img/perf.svg", mode="w") as f:
#                 f.write(recv_info)
#             return
#         recv_info = recv_data(client_socket)
#         recv_info = remove_leading_numbers(recv_info)
#         return recv_info.encode(errors="ignore").decode('unicode-escape', errors="ignore")


import socket
import json


def send_command(command_string, host, port, pid=None, cpu_id=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))

        # 构建要发送的数据，包括 command, pid 和 cpu_id
        data = {'command': command_string}
        if pid is not None:
            data['pid'] = pid
        if cpu_id is not None:
            data['cpu_id'] = cpu_id  # 添加 cpu_id

        data_json = json.dumps(data)

        client_socket.sendall(data_json.encode('utf-8'))

        if command_string == "get_flame_graph":
            recv_info = recv_data(client_socket)
            recv_info = remove_leading_numbers(recv_info)
            recv_info = json.loads(recv_info)
            with open("./kylinApp/static/img/perf.svg", mode="w") as f:
                f.write(recv_info)
            return

        recv_info = recv_data(client_socket)
        recv_info = remove_leading_numbers(recv_info)
        return recv_info.encode(errors="ignore").decode('unicode-escape', errors="ignore")

        recv_info = recv_data(client_socket)
        recv_info = remove_leading_numbers(recv_info)
        return recv_info.encode(errors="ignore").decode('unicode-escape', errors="ignore")


"""以下命令使用待定"""


# 发送Ceph集群命令的函数
def send_ceph_command(command, ceph_ip):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(('10.21.17.40' , 7788))
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

#print(send_command('set_cpu_affinity',"10.21.17.40",7788,326719,cpu_id=2))
#print(send_command('get_cpuhe',"10.21.17.40",7788,326719))
print(send_command('slove_auditd',"192.168.122.128",7788))

#导入必要的库
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
import gym
import matplotlib.pyplot as plt

#创建深度强化学习类
class simpleDRLScheduler:

#初始化simpleDRLScheduler类
    def __init__(self, state_dim, action_dim, hidden_dim, learning_rate, gamma, tau, device):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.tau = tau
        self.device = device
#构建Actor网络
    def build_actor(self):
        self.actor = nn.Sequential(
            nn.Linear(self.state_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, self.action_dim),
            nn.Tanh()
        )
#构建Critic网络
    def build_critic(self):
        self.critic = nn.Sequential(
            nn.Linear(self.state_dim, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, 1)
        )

#根据当前状态选择动作
    def select_action(self, state):
        state = torch.FloatTensor(state).to(self.device)
        action = self.actor(state)
        return action.detach().cpu().numpy()
#将经验储存在经验回放缓冲区
    def store_experience(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
#从经验回放缓冲区中采用并训练网络
    def train(self, batch_size):
        if len(self.memory) < batch_size:
            return
        batch = random.sample(self.memory, batch_size)
        state, action, reward, next_state, done = zip(*batch)
        state = torch.FloatTensor(np.array(state)).to(self.device)
        action = torch.FloatTensor(np.array(action)).to(self.device)
    def calculate_reward(self,machines,task,assigned_machine):
        cpu_utilization= assifned_machine.cpu_usage+tak.cpu_demand
        memory_utilization=assigned_machin.memory_usage+task.memory_demand
        load_balance_penalty= 0
        for machine in machines:
            if machin !=assined_machine:
                load_diff = abs(cpu_utilization-machine.cpu_usage )
                load_balance_penalty +=load_diff
        constraint_penaly = 0
        if cpu_utilization>1.0 or memory_utilization >1.0:
            constraint_penalty = -100
        reward= (cpu_utilization+memory_utilization)*0.5-load_balance_penalty*0.1+constraint_penalty
        return reward
    
    




