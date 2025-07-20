##1、修改为国内镜像
pip install some-package -i https://pypi.tuna.tsinghua.edu.cn/simple
##2、创建虚拟环境
python3 -m venv myenv
##3、激活虚拟环境
python3 -m venv myenv
安装Django：pip install django -i https://mirrors.aliyun.com/pypi/simple/
##4、进入KylinTuningSystem目录下，下载依赖
pip install -r .\requirements.txt
##5、运行项目
Python manage.py runserver

注意：Python版本大于3.12
需要安装：pip install setuptools
提示如果没有数据库依赖：pip install mysqlclient -i https://mirrors.aliyun.com/pypi/simple/
