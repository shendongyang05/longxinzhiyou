from django.shortcuts import render


# Create your views here.

"""模块一"""


def index(request):
    # 初始化页面 监控服务器信息管理

    return render(request, "main/JianKongXinXiFuWuGuanLi.html")


def jiankongshujukuxinxiguanli(request):
    # 监控数据库信息管理
    return render(request, "main/JianKongShuJuKuXinXiGuanLi.html")


def fuwuxinxiguanli(request):
    # 服务信息管理

    return render(request, "main/FuWuXinXiGuanLi.html")


"""模块二"""


def caijicpuxinnengzhibiao(request):
    # 采集CPU性能指标

    return render(request, "main/CaiJiCPUXinNengZhiBiao.html")


def caijineicunxinnengzhibiao(request):
    # 采集内存性能指标

    return render(request, "main/CaiJiNeiCunXinNengZhiBiao.html")


def caijicipanxinnengzhibiao(request):
    # 采集磁盘性能指标

    return render(request, "main/CaiJiCiPanXinNengZhiBiao.html")


def caijiwangluoxinnengzhibiao(request):
    # 采集网络性能指标

    return render(request, "main/CaiJiWangLuoXinNengZhiBiao.html")


def caijiqitaxinxi(request):
    # 采集其他信息

    return render(request, "main/CaiJiQiTaXinXi.html")

def yijiancaiji(request):

    return render(request, "main/Yijiancaiji.html")



"""模块三"""


def cpuxinnengzhibiaofenxi(request):
    # CPU性能指标分析

    return render(request, "main/CPUXinNengZhiBiaoFenXi.html")


def leicunxinnengzhibiaofenxi(request):
    # 内存性能指标分析

    return render(request, "main/NeiCunXinNengZhiBiaoFenXi.html")


def cipanxinnengzhibiaofenxi(request):
    # 磁盘性能指标分析

    return render(request, "main/CiPanXinNengZhiBiaoFenXi.html")


def wangluoxinnengzhibiaofenxi(request):
    # 网络性能指标分析

    return render(request, "main/WangLuoXinNengZhiBiaoFenXi.html")


"""模块四"""


def zhanshiguanjianshuju(request):
    # 展示关键数据

    return render(request, "main/ZhanShiGuanJianShuJu.html")


def shezhitiaoyoucelue(request):
    # 设置调优策略

    return render(request, "main/SheZhiTiaoYouCeLue.html")


"""模块五"""


def shujukuchangjingshibie(request):
    # 数据库场景识别

    return render(request, "main/ShuJuKuChangJingShiBie.html")

def fenbushicunchushibie(request):
    # 分布式存储 ceph 识别

    return render(request, "main/FenBuShiCunChuShiBie.html")


"""模块六"""


def iozhanshujutonglifenxi(request):
    # IO栈数据统计及分析

    return render(request, "main/IOZhanShuJuTongLiFenXi.html")


def cpushujutongjifenxi(request):
    # CPU数据统计及分析

    return render(request, "main/CPUShuJuTongJiFenXi.html")

def yonghuguanli(request):
    # 用户管理
    return render(request, "main/YongHuGanLi.html")

def ziyuanliantiao(request):
    # 资源链条
    return render(request, "main/ZiYuanLianTiao.html")

def ziyuanliantiaofenxi(request):
    # 资源链条分析
    return render(request, "main/ZiYuanLianTiaoFenXi.html")

def qinhexingtiaozheng(request):
    # 资源链条分析
    return render(request, "main/JingChengQianYi.html")
def cephshujutongji(request):
    # 资源链条分析
    return render(request, "main/CephShuJuTongJiJiFengXi.html")

def tiaoyouqianhouduibi(request):
    # 资源链条分析
    return render(request, "main/TiaoYouQianHouDuiBi.html")


def shujuzhongtai(request):
    # 数据中台
    return render(request, "main/ShuJuZhongTai.html")

def datadashboard(request):
    # 大屏监控
    return render(request, "main/DataDashboard.html")

def test_threshold(request):
    # 阈值监控测试
    return render(request, "main/test_threshold.html")

def global_monitor_test(request):
    # 全局监控测试
    return render(request, "main/global_monitor_test.html")

def test_doubao(request):
    # 豆包API测试
    return render(request, "main/test_doubao.html")


def alert_test(request):
    # 预警已读功能测试
    return render(request, "main/alert_test.html")





def test_polling(request):
    # 轮询停止功能测试
    return render(request, "main/test_polling.html")


def debug_polling(request):
    # 轮询调试页面
    return render(request, "main/debug_polling.html")


def rizhijilu(request):
    # 日志记录页面
    return render(request, "main/RiZhiJiLu.html")