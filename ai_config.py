#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI配置文件
"""

# ========= 扣子平台配置 =========
COZE_CONFIG = {
    "BOT_ID": "7525399030261284916",
    "ACCESS_TOKEN": "pat_g66hT0gq8592rgYgnGTW7l6T7bturLPbYpYbgsk1j7Zd7kFvPiMIc6Ha5VlHphFk",
    "BASE_URL": "https://api.coze.cn"
}

# ========= 火山引擎配置（已弃用） =========
VOLCENGINE_CONFIG = {
    "API_KEY": "cf031d9f-ebdb-4bd0-bde2-e57444a86d31",
    "MODEL": "bot-20250702164711-8jhhd"
}

# ========= Groq平台配置 =========
GROQ_CONFIG = {
    "API_KEY": "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",
    "BASE_URL": "https://api.groq.com/openai/v1/chat/completions",
    "MODEL": "meta-llama/llama-4-scout-17b-16e-instruct"
}

# ========= AI提供商选择 =========
# 设置为 "coze" 使用扣子平台，设置为 "volcengine" 使用火山引擎，设置为 "groq" 使用Groq平台
AI_PROVIDER = "groq"

def get_ai_config():
    """获取AI配置"""
    if AI_PROVIDER == "coze":
        return COZE_CONFIG
    elif AI_PROVIDER == "volcengine":
        return VOLCENGINE_CONFIG
    elif AI_PROVIDER == "groq":
        return GROQ_CONFIG
    else:
        raise ValueError(f"不支持的AI提供商: {AI_PROVIDER}")

def is_coze_enabled():
    """检查是否启用扣子平台"""
    return AI_PROVIDER == "coze"

def is_volcengine_enabled():
    """检查是否启用火山引擎"""
    return AI_PROVIDER == "volcengine"

def is_groq_enabled():
    """检查是否启用Groq平台"""
    return AI_PROVIDER == "groq" 