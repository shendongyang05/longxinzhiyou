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
from django.shortcuts import redirect
from kylinApp.views import view, user, api
from kylinApp.views import ai_api
from kylinApp.views import swagger

urlpatterns = [
    # 默认页面重定向
    path('', lambda request: redirect('/index/dataMonitor')),
    path('index/', lambda request: redirect('/index/dataMonitor')),
    
    # 配置管理
    # path('admin/', admin.site.urls),
    # 用户管理
    path("index/user", view.yonghuguanli),
    path('index/server', view.index),
    path('index/middleware', view.fuwuxinxiguanli),
    # 数据采集
    path('index/cpuCollect', view.caijicpuxinnengzhibiao),
    path('index/memoryCollect', view.caijineicunxinnengzhibiao),
    path('index/diskCollect', view.caijicipanxinnengzhibiao),
    path('index/netCollect', view.caijiwangluoxinnengzhibiao),
    path('index/softHardCollect', view.caijiqitaxinxi),
    path('index/pollingCollect', view.yijiancaiji),
    # 分析采集数据
    path('index/cpuAnalysis', view.cpuxinnengzhibiaofenxi),
    path('index/memoryAnalysis', view.leicunxinnengzhibiaofenxi),
    path('index/diskAnalysis', view.cipanxinnengzhibiaofenxi),
    path('index/netAnalysis', view.wangluoxinnengzhibiaofenxi),
    path('index/resourceAnalysis', view.ziyuanliantiaofenxi),
    path('index/resourceAnalysis', view.tiaoyouqianhouduibi),
    path('index/dataDashboard', view.shujuzhongtai),
    path('index/dataMonitor', view.datadashboard),



    # 调优可视化
    # path('index/dataDashboard', view.zhanshiguanjianshuju),
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

    # AI一键调优接口 - 使用新的ai_api模块
    path('api/ai_optimize/', ai_api.ai_optimize_api),
    # 执行AI策略接口 - 使用新的ai_api模块
    path('api/execute_ai_strategy/', ai_api.execute_ai_strategy),
    
    # 后台采集任务管理接口
    path('api/background_collection/', api.background_collection_api),
    # 获取最新采集数据接口
    path('api/get_latest_data/', api.get_latest_data_api),
    # 获取最新采集数据接口（简化版）
    path('api/get_latest_data_simple/', api.get_latest_data),
    # 保存采集数据接口
    path('api/save_collection_data/', api.save_collected_data_api),

    # Swagger/OpenAPI 文档
    path('api/openapi.json', swagger.openapi_schema),
    path('api/docs/', swagger.swagger_ui),
    
    # 日志记录相关路由
    path('index/log', view.rizhijilu),
    path('api/upload_log/', api.upload_log),
    path('api/get_logs/', api.get_logs),
    path('api/view_log/<int:log_id>/', api.view_log),
    path('api/download_log/<int:log_id>/', api.download_log),
    path('api/delete_log/<int:log_id>/', api.delete_log),
    path('api/create_direct_log/', api.create_direct_log),

    # 用户登录
    path('login/', user.login_index),
    # 提供用户账号信息
    path('api/user_info', user.get_user_info),
    # 退出
    path("logout/", user.log_out)
]
