# 龙芯智优软件

龙芯智优软件是一款针对国产操作系统智能调优的软件，帮助运维人员对银河麒麟操作系统进行可视化监控与调优。系统分为管理端应用和服务探针两部分，支持 MySQL 或达梦数据库，集成消息队列、Redis 缓存及 AI 大模型分析，支持 Docker 部署日志和监控组件。

## 快速开始

### 1. 使用国内镜像安装依赖

```bash
pip install some-package -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 创建并激活虚拟环境

```bash
python3 -m venv myenv
# 激活虚拟环境（Linux/macOS）
source myenv/bin/activate
# 或在 Windows
myenv\Scripts\activate
```

### 3. 安装 Django 及其他依赖

```bash
pip install django -i https://mirrors.aliyun.com/pypi/simple/
pip install -r requirements.txt
```

### 4. 运行项目

```bash
python manage.py runserver
```

## 注意事项

- **Python 版本需 ≥ 3.12**
- 如果缺少 setuptools，请执行：
  ```bash
  pip install setuptools
  ```
- 如需数据库依赖，请安装：
  ```bash
  pip install mysqlclient -i https://mirrors.aliyun.com/pypi/simple/
  ```

