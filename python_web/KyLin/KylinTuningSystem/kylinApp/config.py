# 配置文件
import os

# ARK API配置 (替代豆包API)
ARK_API_URL = "https://ark.cn-beijing.volces.com/api/v3/bots/chat/completions"
ARK_API_KEY = os.getenv('ARK_API_KEY', 'cf031d9f-ebdb-4bd0-bde2-e57444a86d31')  # 从环境变量获取，如果没有则使用默认值

# 豆包API配置 (已废弃，保留用于兼容性)
DOUBAO_API_URL = "https://api.doubao.com/v1/chat/completions"
DOUBAO_API_KEY = os.getenv('DOUBAO_API_KEY', 'your_doubao_api_key_here')  # 从环境变量获取，如果没有则使用默认值

# 其他API配置
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# 系统配置
DEBUG = True
LOG_LEVEL = 'INFO' 