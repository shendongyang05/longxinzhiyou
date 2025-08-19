from hashlib import md5
from django.conf import settings


def encrypt_md5(encrypt_string: str):
    salt = settings.SECRET_KEY
    obj = md5(salt.encode("utf-8"))
    obj.update(encrypt_string.encode("utf-8"))
    return obj.hexdigest()