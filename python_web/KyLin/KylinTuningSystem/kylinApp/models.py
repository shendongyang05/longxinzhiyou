from django.db import models

# Create your models here.


class UserModels(models.Model):
    """用户表"""
    username = models.CharField(verbose_name="用户名", max_length=50)
    password = models.CharField(verbose_name="密码", max_length=50)

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
