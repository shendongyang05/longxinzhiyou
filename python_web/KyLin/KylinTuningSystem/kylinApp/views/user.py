from django.shortcuts import render, redirect
from django.http.response import JsonResponse
from kylinApp.models import UserModels
from kylinApp.utils import model_form
from ..utils import encrypt
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def login_index(request):
    if request.method == "GET":
        return render(request, "user/login.html")

    form = model_form.UserModelForm(request.POST)

    if form.is_valid():
        # 表单验证正确（格式,类型）
        user = request.POST.get("username")
        pwd = request.POST.get("password")
        encrypt_pwd = encrypt.encrypt_md5(pwd)
        # 查询条件
        conditions = {
            "username": user,
            "password": pwd
        }
        info = UserModels.objects.filter(**conditions).first()
        if not info:
            error_message = "请检查账号密码"
            return render(request, "user/login.html", context={"message": error_message})

        # 成功
        request.session["info"] = {"user": user, "pad": pwd}
        request.session.set_expiry(60 * 60 * 24 * 7)
        return redirect("/index/usermanager")

    return render(request,"user/login.html")


def get_user_info(request):
    data = {"info": request.session.get("info").get("user")}
    return JsonResponse(data)


def log_out(request):
    request.session.clear()
    return redirect("/login")