from hashlib import md5
from django.conf import settings


def encrypt_md5(encrypt_string: str):
    # 使用纯MD5加密，不使用盐值，以匹配数据库中的密码格式
    obj = md5()
    obj.update(encrypt_string.encode("utf-8"))
    return obj.hexdigest()