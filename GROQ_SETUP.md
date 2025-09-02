# Groq API 配置说明

## 环境变量设置

为了使用Groq AI服务，请设置以下环境变量：

```bash
# Linux/macOS
export GROQ_API_KEY="your_groq_api_key"

# Windows
set GROQ_API_KEY=your_groq_api_key
```

## 启动项目

```bash
# 确保环境变量已设置后启动Django项目
python manage.py runserver
```

## 注意事项

- 请将 `your_groq_api_key` 替换为您的实际Groq API密钥
- 不要将真实的API密钥提交到代码仓库中
- 如果未设置环境变量，系统会使用本地回复模式
