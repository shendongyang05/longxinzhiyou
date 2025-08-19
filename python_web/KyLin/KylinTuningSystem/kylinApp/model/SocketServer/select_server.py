import select
import socket
import psutil

'''通用的字节转换函数'''
def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n
# 获取主机名
hostname = socket.gethostname()
'''获取CPU信息'''
def get_cpu_info():
    cpu_count = psutil.cpu_count()
    cpu_percent = psutil.cpu_percent(interval=2)
    return dict(cpu_count=cpu_count, cpu_percent=cpu_percent)

'''获取内存信息'''
def get_memory_info():
    virtual_mem = psutil.virtual_memory()
    mem_total = bytes2human(virtual_mem.total)
    mem_used = bytes2human(virtual_mem.total * virtual_mem.percent / 100)
    mem_free = bytes2human(virtual_mem.free)
    mem_percent = virtual_mem.percent
    return dict(mem_total=mem_total, mem_used=mem_used,mem_free=mem_free,mem_percent=mem_percent)

'''获取磁盘信息'''
def get_disk_info():
    disk_usage = psutil.disk_usage('/')
    disk_total = bytes2human(disk_usage.total)
    disk_used = bytes2human(disk_usage.used)
    disk_free = bytes2human(disk_usage.free)
    disk_percent = disk_usage.percent
    disk_io = psutil.disk_io_counters()
    disk_read = bytes2human(disk_io.read_bytes)
    disk_write = bytes2human(disk_io.write_bytes)
    return dict(disk_total=disk_total,disk_used=disk_used,disk_free=disk_free, disk_percent=disk_percent,disk_read=disk_read,disk_write=disk_write)

'''获取网络信息'''
def get_net_info():
    net_io = psutil.net_io_counters()
    net_sent = bytes2human(net_io.bytes_sent)
    net_recv = bytes2human(net_io.bytes_recv)
    return dict(net_sent=net_sent,net_recv=net_recv)

'''汇集系统信息'''
def gather_monitor_data():
    data = {}
    data.update(get_cpu_info())
    data.update(get_memory_info())
    data.update(get_disk_info())
    data.update(get_net_info())
    print(get_cpu_info())
    print(get_memory_info())
    print(get_disk_info())
    print(get_net_info())
    return data

def main():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind(('',3302))
    server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    server_socket.listen(10)
    inputs = [server_socket]
    while True:
        #调用select()函数，阻塞等待
        readable,writeable,exceptional = select.select(inputs,[],[])
        #数据抵达，循环
        for temp_socket in readable:
            if temp_socket == server_socket:
                new_sockect,client_address = server_socket.accept()
                print("一个新的客户端到来：%s" %str(client_address))
                inputs.append(new_sockect)
            else:
                data = temp_socket.recv(1024).decode('gb2312')
                if data == 'get_info':
                    data = gather_monitor_data()
                    temp_socket.send(str(data).encode('gb2312'))
                else:
                    inputs.remove(temp_socket)
                    temp_socket.close()
    server_socket.close()

if __name__ == '__main__':
    main()
