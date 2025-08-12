from django.db import models

# Create your models here.


class UserModels(models.Model):
    """用户表"""
    username = models.CharField(verbose_name="用户名", max_length=50)
    password = models.CharField(verbose_name="密码", max_length=64)  # 更新为64位以支持MD5

    class Meta:
        db_table = 'users'


class MonitoringServerInformation(models.Model):
    """监控服务器信息管理"""
    ip = models.CharField(verbose_name="ip地址", max_length=32)
    port = models.IntegerField(verbose_name="端口")
    server_category = models.CharField(verbose_name="服务类型", max_length=32, blank=True, default="")
    remarks = models.CharField(verbose_name="备注", max_length=128, blank=True, default="")

    class Meta:
        db_table = "serveInfo"


class DataBaseInformationManagement(models.Model):
    """监控数据库信息管理"""
    ip = models.CharField(verbose_name="ip地址", max_length=32)
    port = models.IntegerField(verbose_name="端口")
    database = models.CharField(verbose_name="数据库", max_length=32)
    type = models.CharField(verbose_name="类型", max_length=32)
    user = models.CharField(verbose_name="用户名", max_length=32)
    password = models.CharField(verbose_name="密码", max_length=64)
    code = models.CharField(verbose_name="编码", max_length=32)
    remarks = models.CharField(verbose_name="备注", max_length=128, blank=True, null=True)
    

    class Meta:
        db_table = "DbServeInfo"


class ServerManagement(models.Model):
    """服务信息管理"""
    ip = models.CharField(verbose_name="ip地址", max_length=32)
    port = models.IntegerField(verbose_name="端口")
    server_category = models.CharField(verbose_name="服务类型", max_length=32)
    remarks = models.CharField(verbose_name="备注", max_length=128)

    class Meta:
        db_table = "fuwuxingxiguanli"


class CPUPerformanceMetrics(models.Model):
    # 采集CPU性能指标
    type = models.CharField(max_length=64)
    ipaddress = models.CharField(max_length=64)
    userTime = models.CharField(max_length=64)
    SystemTime = models.CharField(max_length=64)
    waitIO = models.CharField(max_length=64)
    Idle = models.CharField(max_length=64)

    count = models.IntegerField(default=0)
    percent = models.DecimalField(max_digits=5, decimal_places=2,default=0.00)

    currentTime = models.DateTimeField()

    class Meta:
        db_table = "cpuInfo"


class MemoryPerformanceMetrics(models.Model):
    # 采集内存性能指标
    type = models.CharField(max_length=64)
    ipaddress = models.CharField(max_length=64)
    total = models.CharField(max_length=64)
    used = models.CharField(max_length=64)
    free = models.CharField(max_length=64)
    buffers = models.CharField(max_length=64)
    cache = models.CharField(max_length=64)
    swap = models.CharField(max_length=64)

    percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    currentTime = models.DateTimeField()

    class Meta:
        db_table = "memoryInfo"


class DiskPerformanceMetrics(models.Model):
    # 采集磁盘性能指标
    type = models.CharField(max_length=64)
    ipaddress = models.CharField(max_length=64)

    total = models.CharField(max_length=64, default="")
    used = models.CharField(max_length=64, default="")
    free = models.CharField(max_length=64, default="")
    percent = models.DecimalField(max_digits=5,decimal_places=2, default=0.00)

    readCount = models.CharField(max_length=64)
    writeCount = models.CharField(max_length=64)
    readBytes = models.CharField(max_length=64)
    writeBytes = models.CharField(max_length=64)
    readTime = models.CharField(max_length=64)
    writeTime = models.CharField(max_length=64)
    currentTime = models.DateTimeField()

    class Meta:
        db_table = "DfInfo"


class NetworkPerformanceMetrics(models.Model):
    # 采集网络性能指标
    type = models.CharField(max_length=64)
    ipaddress = models.CharField(max_length=64)

    sent = models.CharField(max_length=64,default="")
    recv = models.CharField(max_length=64,default="")


    packetSent = models.CharField(max_length=64)
    packetRecv = models.CharField(max_length=64)
    currentTime = models.DateTimeField()

    class Meta:
        db_table = "networkInfo"


class AdditionalInformation(models.Model):
    # 其他信息
    type = models.CharField(max_length=64)
    os_info = models.CharField(max_length=64)
    os_version = models.CharField(max_length=64)
    os_release = models.CharField(max_length=64)
    cpu_model = models.CharField(max_length=64)
    os_processor_name = models.CharField(max_length=64)
    os_processor_architecture = models.CharField(max_length=64)
    os_name = models.CharField(max_length=64)

    class Meta:
        db_table = "otherInfo"


class LogRecord(models.Model):
    """日志记录模型"""
    LOG_TYPE_CHOICES = (
        ('system', '系统日志'),
        ('application', '应用日志'),
        ('security', '安全日志'),
        ('performance', '性能日志'),
        ('other', '其他'),
    )
    
    STATUS_CHOICES = (
        ('success', '成功'),
        ('pending', '处理中'),
        ('error', '失败'),
    )
    
    title = models.CharField(verbose_name="日志标题", max_length=255)
    description = models.TextField(verbose_name="日志描述", blank=True, null=True)
    type = models.CharField(verbose_name="日志类型", max_length=50, choices=LOG_TYPE_CHOICES, default='system')
    # 原始文件名（用于下载展示）
    original_name = models.CharField(verbose_name="原始文件名", max_length=255, blank=True, null=True)
    # 文件二进制内容（把日志本体存到数据库）
    file_blob = models.BinaryField(verbose_name="文件内容", null=True, blank=True)
    # 为兼容旧数据，路径改为可为空
    file_path = models.CharField(verbose_name="文件路径", max_length=255, blank=True, null=True)
    size = models.IntegerField(verbose_name="文件大小", default=0)
    status = models.CharField(verbose_name="状态", max_length=20, choices=STATUS_CHOICES, default='success')
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    
    class Meta:
        db_table = "log_records"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
