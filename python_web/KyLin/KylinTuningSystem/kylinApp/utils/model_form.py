from django import forms
from kylinApp.models import UserModels,MonitoringServerInformation,DataBaseInformationManagement,ServerManagement


class UserModelForm(forms.ModelForm):
    class Meta:
        model = UserModels
        fields ="__all__"

    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        return pwd


class BaseModel(forms.ModelForm):
    pass


class JianKongFuWuQi(BaseModel):
    """监控服务器信息管理"""
    class Meta:
        model = MonitoringServerInformation
        fields = "__all__"
        widgets = {
            "remarks":forms.Textarea
        }


class JianKongShuJuKu(BaseModel):
    """监控数据库信息管理"""
    class Meta:
        model = DataBaseInformationManagement
        fields = "__all__"
        widgets = {
            "remarks": forms.Textarea
        }



class FuWuXinXi(BaseModel):
    """服务信息管理"""
    class Meta:
        model = ServerManagement
        fields = "__all__"