"""
URL configuration for KylinTuningSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
    # 所有的url和对应关系都写在里面
"""
from django.contrib import admin
from django.urls import path
from kylinApp.views import view,user,api

urlpatterns = [
    # 配置管理
    # path('admin/', admin.site.urls),
    path("", view.yonghuguanli),
    # 用户管理
    path("index/usermanager", view.yonghuguanli),
    path('index/', view.index),
    path('index/jiankongshujukuxinxiguanli', view.jiankongshujukuxinxiguanli),
    path('index/fuwuxinxiguanli', view.fuwuxinxiguanli),
    # 数据采集
    path('index/caijicpuxinnengzhibiao', view.caijicpuxinnengzhibiao),
    path('index/caijineicunxinnengzhibiao', view.caijineicunxinnengzhibiao),
    path('index/caijicipanxinnengzhibiao', view.caijicipanxinnengzhibiao),
    path('index/caijiwangluoxinnengzhibiao', view.caijiwangluoxinnengzhibiao),
    path('index/caijiqitaxinxi', view.caijiqitaxinxi),
    path('index/yijiancaiji', view.yijiancaiji),
    # 分析采集数据
    path('index/cpuxinnengzhibiaofenxi', view.cpuxinnengzhibiaofenxi),
    path('index/neicunxinnengzhibiaofenxi', view.leicunxinnengzhibiaofenxi),
    path('index/cipanxinnengzhibiaofenxi', view.cipanxinnengzhibiaofenxi),
    path('index/wangluoxinnengzhibiaofenxi', view.wangluoxinnengzhibiaofenxi),
    path('index/ziyuanliantiao', view.ziyuanliantiao),
    path('index/ziyuanliantiaofenxi', view.ziyuanliantiaofenxi),
    path('index/tiaoyouqianhouduibi', view.tiaoyouqianhouduibi),
    path('index/shujuzhongtai', view.shujuzhongtai),
    path('index/datadashboard', view.datadashboard),
    path('index/test_threshold', view.test_threshold),
    path('index/global_monitor_test', view.global_monitor_test),
    path('index/alert_test', view.alert_test),
    path('index/test_polling', view.test_polling),
    path('index/debug_polling', view.debug_polling),

    path('api/doubao_chat/', api.doubao_chat),
    path('index/test_doubao', view.test_doubao),

    # 调优可视化
    path('index/zhanshiguanjianshuju', view.zhanshiguanjianshuju),
    path('index/shezhitiaoyoucelue', view.shezhitiaoyoucelue),
    # 场景实别
    path('index/shujukuchangjingshibie', view.shujukuchangjingshibie),
    path('index/fenbushicunchushibie', view.fenbushicunchushibie),
    # 数据统计分析
    path('index/iozhanshujutonglifenxi', view.iozhanshujutonglifenxi),
    path('index/cpushujutongjifenxi', view.cpushujutongjifenxi),
    path('index/cephshujutongjifenxi', view.cephshujutongji),
    # 亲和性调整
    path('index/qinhexintiaozheng', view.qinhexingtiaozheng),
    # api
    path("api/<str:name>/<str:tp>/<str:number_range>/oneModel", api.return_data_model_one),
    path("api/<str:tp>/<str:name>/twoModel", api.return_data_model_two),
    path("api/<str:name>/<str:start_time>/<str:end_time>/<str:number_range>/<str:ipvalue>/threeModel", api.return_data_model_three),
    path("api/fourModel", api.return_data_model_four),
    path("api/cmd/fourModel", api.return_cmd_four),
    path("api/return_cmd_four/", api.return_cmd_four),
    path("api/fiveModel", api.return_data_five),
    path("api/sixModel", api.return_data_six),
    path("api/userManager/<str:tp>", api.userManager),
    path("api/realtimeUpdatePidData", api.realtime_update_pid_data),
    path("api/pidInfo", api.pid_info),
    # 策略包接口
    path("api/strategy/apply", api.apply_strategy),

    # 火焰图
    path('no_cache_image/<str:image_name>/',api.NoCacheImageView.as_view(), name='no_cache_image'),

    # AI一键调优接口
    path('api/ai_optimize/', api.ai_optimize_api),
    # 执行AI策略接口
    path('api/execute_ai_strategy/', api.execute_ai_strategy),
    
    # 后台采集任务管理接口
    path('api/background_collection/', api.background_collection_api),
    # 获取最新采集数据接口
    path('api/get_latest_data/', api.get_latest_data_api),
    # 获取最新采集数据接口（简化版）
    path('api/get_latest_data_simple/', api.get_latest_data),
    # 保存采集数据接口
    path('api/save_collected_data/', api.save_collected_data_api),

    # 用户登录
    path('login/', user.login_index),
    # 提供用户账号信息
    path('api/user_info', user.get_user_info),
    # 退出
    path("logout/", user.log_out)
]
