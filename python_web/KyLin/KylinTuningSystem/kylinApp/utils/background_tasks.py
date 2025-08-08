import threading
import time
import json
import logging
from datetime import datetime
from django.utils import timezone
from ..models import CPUPerformanceMetrics, MemoryPerformanceMetrics, DiskPerformanceMetrics, NetworkPerformanceMetrics
from ..model.SocketServer import select_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('collection_tasks.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """后台任务管理器"""
    
    def __init__(self):
        self.tasks = {}  # 存储正在运行的任务
        self.lock = threading.Lock()
        self.max_retries = 3  # 最大重试次数
        self.retry_interval = 5  # 重试间隔（秒）
    
    def start_collection_task(self, task_id, ip, port, interval=30):
        """启动采集任务"""
        with self.lock:
            if task_id in self.tasks:
                logger.warning(f"任务已存在: {task_id}")
                return False, "任务已存在"
            
            # 创建任务线程
            task_thread = threading.Thread(
                target=self._collection_worker,
                args=(task_id, ip, port, interval),
                daemon=True
            )
            
            self.tasks[task_id] = {
                'thread': task_thread,
                'running': True,
                'ip': ip,
                'port': port,
                'interval': interval,
                'start_time': timezone.now(),
                'error_count': 0,  # 错误计数
                'last_success': None,  # 最后一次成功时间
                'status': 'starting'  # 任务状态
            }
            
            logger.info(f"启动采集任务: {task_id}, IP: {ip}, Port: {port}, Interval: {interval}s")
            task_thread.start()
            return True, "任务启动成功"
    
    def stop_collection_task(self, task_id):
        """停止采集任务"""
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False, "任务不存在"
            
            logger.info(f"停止采集任务: {task_id}")
            
            # 立即设置停止标志
            self.tasks[task_id]['running'] = False
            self.tasks[task_id]['status'] = 'stopping'
            
            # 等待线程真正停止
            thread = self.tasks[task_id]['thread']
            if thread.is_alive():
                logger.info(f"等待任务线程停止: {task_id}")
                
                # 多次尝试停止，每次等待较短时间
                for attempt in range(3):
                    thread.join(timeout=5)  # 每次等待5秒
                    if not thread.is_alive():
                        logger.info(f"任务线程已停止: {task_id}")
                        break
                    else:
                        logger.warning(f"任务线程仍在运行，尝试 {attempt + 1}/3: {task_id}")
                
                if thread.is_alive():
                    logger.warning(f"任务线程未能及时停止，强制标记为停止: {task_id}")
            
            # 确保状态更新为stopped
            self.tasks[task_id]['status'] = 'stopped'
            self.tasks[task_id]['running'] = False
            logger.info(f"任务已停止: {task_id}")
            return True, "任务停止成功"
    
    def cleanup_task(self, task_id):
        """清理已停止的任务"""
        with self.lock:
            if task_id in self.tasks and self.tasks[task_id]['status'] == 'stopped':
                del self.tasks[task_id]
                logger.info(f"清理任务: {task_id}")
    
    def cleanup_stopped_tasks(self):
        """清理所有已停止的任务"""
        with self.lock:
            stopped_tasks = []
            for task_id, task_info in self.tasks.items():
                if task_info['status'] == 'stopped':
                    stopped_tasks.append(task_id)
            
            for task_id in stopped_tasks:
                del self.tasks[task_id]
                logger.info(f"自动清理已停止任务: {task_id}")
            
            if stopped_tasks:
                logger.info(f"共清理了 {len(stopped_tasks)} 个已停止的任务")
    
    def force_stop_all_tasks(self):
        """强制停止所有任务"""
        with self.lock:
            logger.warning("执行强制停止所有任务操作")
            stopped_count = 0
            
            for task_id, task_info in list(self.tasks.items()):
                try:
                    # 设置停止标志
                    task_info['running'] = False
                    task_info['status'] = 'force_stopped'
                    
                    # 强制终止线程
                    thread = task_info.get('thread')
                    if thread and thread.is_alive():
                        logger.warning(f"强制停止任务线程: {task_id}")
                        # 注意：Python中无法强制杀死线程，只能设置标志让线程自己退出
                        # 这里我们设置较短的超时时间
                        thread.join(timeout=2)
                        if thread.is_alive():
                            logger.error(f"任务线程无法停止: {task_id}")
                    
                    stopped_count += 1
                    logger.info(f"强制停止任务: {task_id}")
                    
                except Exception as e:
                    logger.error(f"强制停止任务 {task_id} 时出错: {e}")
            
            # 清空所有任务
            self.tasks.clear()
            logger.warning(f"已强制停止并清理 {stopped_count} 个任务")
            
            return stopped_count
    
    def get_task_status(self, task_id):
        """获取任务状态"""
        with self.lock:
            if task_id not in self.tasks:
                return None
            task_info = self.tasks[task_id].copy()
            # 移除不可序列化的线程对象
            task_info.pop('thread', None)
            # 转换时间对象为字符串
            task_info['start_time'] = task_info['start_time'].strftime('%Y-%m-%d %H:%M:%S')
            if task_info['last_success']:
                task_info['last_success'] = task_info['last_success'].strftime('%Y-%m-%d %H:%M:%S')
            return task_info
    
    def get_all_tasks(self):
        """获取所有任务"""
        with self.lock:
            return list(self.tasks.keys())
    
    def _collection_worker(self, task_id, ip, port, interval):
        """采集工作线程"""
        consecutive_errors = 0  # 连续错误计数
        logger.info(f"开始后台数据采集任务: {task_id}, IP: {ip}, 端口: {port}, 间隔: {interval}秒")
        
        while True:
            # 检查任务是否应该停止
            with self.lock:
                if task_id not in self.tasks:
                    logger.info(f"任务已删除: {task_id}")
                    break
                
                task_info = self.tasks[task_id]
                if not task_info['running']:
                    logger.info(f"任务停止信号: {task_id}")
                    break
                
                # 更新状态为运行中
                task_info['status'] = 'running'
            
            try:
                logger.info(f"开始采集数据: {task_id}, IP: {ip}, 端口: {port}")
                
                # 采集CPU数据
                cpu_data = self._get_info_with_retry('cpu', ip, port)
                if cpu_data and 'state' in cpu_data and cpu_data['state'] == 'ok':
                    logger.info(f"CPU数据采集成功: {cpu_data}")
                    # 验证数据是否为真实数据
                    if 'info' in cpu_data and cpu_data['info']:
                        cpu_info = cpu_data['info']
                        logger.info(f"CPU详细信息: 用户时间={cpu_info.get('cpu_user_time')}, 系统时间={cpu_info.get('cpu_system_time')}, 使用率={cpu_info.get('cpu_percent')}%")
                else:
                    logger.warning(f"CPU数据采集失败: {cpu_data}")
                
                # 采集内存数据
                mem_data = self._get_info_with_retry('memory', ip, port)
                if mem_data and 'state' in mem_data and mem_data['state'] == 'ok':
                    logger.info(f"内存数据采集成功: {mem_data}")
                    # 验证数据是否为真实数据
                    if 'info' in mem_data and mem_data['info']:
                        mem_info = mem_data['info']
                        logger.info(f"内存详细信息: 总量={mem_info.get('mem_total')}, 已用={mem_info.get('mem_used')}, 使用率={mem_info.get('mem_percent')}%")
                else:
                    logger.warning(f"内存数据采集失败: {mem_data}")
                
                # 采集磁盘数据
                disk_data = self._get_info_with_retry('disk', ip, port)
                if disk_data and 'state' in disk_data and disk_data['state'] == 'ok':
                    logger.info(f"磁盘数据采集成功: {disk_data}")
                    # 验证数据是否为真实数据
                    if 'info' in disk_data and disk_data['info']:
                        disk_info = disk_data['info']
                        logger.info(f"磁盘详细信息: 总量={disk_info.get('disk_total')}, 已用={disk_info.get('disk_used')}, 使用率={disk_info.get('disk_percent')}%")
                else:
                    logger.warning(f"磁盘数据采集失败: {disk_data}")
                
                # 采集网络数据
                net_data = self._get_info_with_retry('network', ip, port)
                if net_data and 'state' in net_data and net_data['state'] == 'ok':
                    logger.info(f"网络数据采集成功: {net_data}")
                    # 验证数据是否为真实数据
                    if 'info' in net_data and net_data['info']:
                        net_info = net_data['info']
                        logger.info(f"网络详细信息: 发送={net_info.get('net_bytes_sent')}, 接收={net_info.get('net_bytes_recv')}")
                else:
                    logger.warning(f"网络数据采集失败: {net_data}")
                
                # 更新任务状态
                with self.lock:
                    if task_id in self.tasks:
                        self.tasks[task_id]['last_success'] = timezone.now()
                        self.tasks[task_id]['error_count'] = 0
                
                consecutive_errors = 0  # 重置连续错误计数
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"采集任务 {task_id} 出错 ({consecutive_errors}/{self.max_retries}): {e}")
                
                with self.lock:
                    if task_id in self.tasks:
                        self.tasks[task_id]['error_count'] = consecutive_errors
                        self.tasks[task_id]['status'] = 'error'
                
                if consecutive_errors >= self.max_retries:
                    logger.error(f"任务 {task_id} 连续错误次数过多，暂停采集")
                    time.sleep(self.retry_interval * 2)  # 较长的等待时间
                    consecutive_errors = 0  # 重置计数，给予新的机会
                else:
                    time.sleep(self.retry_interval)  # 短暂等待后重试
                continue
            
            # 等待下次采集前再次检查停止信号
            for i in range(interval):
                time.sleep(1)
                with self.lock:
                    if task_id not in self.tasks:
                        logger.info(f"任务在等待期间被删除: {task_id}")
                        return
                    
                    if not self.tasks[task_id]['running']:
                        logger.info(f"任务在等待期间收到停止信号: {task_id}")
                        return
            
            # 最后一次检查停止信号
            with self.lock:
                if task_id not in self.tasks:
                    logger.info(f"任务在循环结束后被删除: {task_id}")
                    return
                
                if not self.tasks[task_id]['running']:
                    logger.info(f"任务在循环结束后收到停止信号: {task_id}")
                    return
    
    def _get_info_with_retry(self, info_type, ip, port, max_retries=3):
        """带重试机制的数据获取"""
        for attempt in range(max_retries):
            try:
                logger.info(f"正在获取{info_type}数据，IP: {ip}, 端口: {port}")
                result = select_client.get_info(ip, port, info_type)
                logger.info(f"成功获取{info_type}数据: {result}")
                return result
            except Exception as e:
                logger.error(f"获取{info_type}数据失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:  # 最后一次尝试
                    raise
                logger.warning(f"等待{self.retry_interval}秒后重试...")
                time.sleep(self.retry_interval)
    
    # 注意：数据保存由 select_client.get_info() 自动处理
    # 这些函数已不再需要，因为 select_client.get_info() 会自动调用 set_info() 保存数据

# 全局任务管理器实例
task_manager = BackgroundTaskManager()