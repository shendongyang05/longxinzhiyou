from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
"""redirect是一个快捷函数，用于生成重定向响应"""

class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """请求时触发"""
        # 不需要认证的路径列表
        exempt_paths = [
            "/login/",
            "/api/",  # 所有API接口都不需要认证
        ]

        # 检查是否是免认证路径
        for path in exempt_paths:
            if request.path_info.startswith(path):
                return

        """如果是登录页面或API接口不进行任何处理，请求将继续向下传递到视图函数"""
        if request.session.get("info"):
            return
        """检查用户会话中是否有info键，中用户登录成功后被设置用于标识用户已登录，如果有info，返回none，请求将继续向下传递到视图函数"""
        return redirect("/login/")
        """重定项到登录页面，如果用户既没有访问登录页面，也没有登录（没有info，）则返回一个重定向响应，将用户引导到登录页面"""

    def process_response(self, request, response):
        """返回时触发"""
        return response