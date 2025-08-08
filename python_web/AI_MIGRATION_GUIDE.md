# AI功能迁移指南：从火山引擎到扣子平台

## 概述

本项目已成功将AI功能从火山引擎迁移到扣子平台。本文档详细说明了迁移的内容和使用方法。

## 迁移内容

### 1. 主要文件变更

#### `python_web/ark_example.py`
- **变更前**: 使用火山引擎的`Ark`客户端
- **变更后**: 使用扣子平台的HTTP API调用
- **主要改动**:
  - 移除了`volcenginesdkarkruntime`依赖
  - 添加了`requests`、`json`、`uuid`等标准库
  - 实现了会话管理和API调用逻辑

#### `python_web/coze_ai_client.py` (新增)
- 创建了完整的扣子平台AI客户端类
- 支持同步和流式对话
- 提供了系统优化分析功能
- 包含错误处理和重试机制

#### `python_web/ai_config.py` (新增)
- 集中管理AI配置
- 支持多AI提供商切换
- 便于维护和更新

### 2. 依赖变更

#### 新增依赖
```bash
sseclient-py==1.8.0  # 用于流式对话（可选）
```

#### 移除依赖
```bash
volcenginesdkarkruntime  # 火山引擎SDK
```

### 3. 配置文件

#### 扣子平台配置
```python
COZE_CONFIG = {
    "BOT_ID": "7525399030261284916",
    "ACCESS_TOKEN": "pat_NxNtvGypqTp4auEF7tbh2HmiTSLC62ZKjODQrhzCAXTZUATHgS3dipfkOSbA10VQ",
    "BASE_URL": "https://api.coze.cn"
}
```

## 使用方法

### 1. 基本使用

```python
from ark_example import ai_optimize_infer

# 调用AI优化分析
result = ai_optimize_infer()
print(result)
```

### 2. 使用客户端类

```python
from coze_ai_client import create_default_client

# 创建客户端
client = create_default_client()

# 系统优化分析
system_data = {
    "cpu_percent": 85.5,
    "mem_percent": 78.2,
    "disk_percent": 65.1
}
result = client.system_optimize(system_data)
```

### 3. 流式对话

```python
from coze_ai_client import create_default_client

client = create_default_client()
user_id = str(uuid.uuid4())
conversation_id = client.create_conversation(user_id)

# 流式对话
client.chat_stream(conversation_id, user_id, "你好，请介绍一下自己")
```

## API接口保持不变

### Web API
- `ai_optimize_api`: AI优化分析接口
- `execute_ai_strategy`: 执行AI策略接口

这些接口的调用方式和返回格式保持不变，确保前端无需修改。

## 测试

### 1. 运行测试脚本

```bash
cd python_web
python test_coze_ai.py
```

### 2. 测试客户端

```bash
cd python_web
python coze_ai_client.py
```

### 3. 测试主功能

```bash
cd python_web
python ark_example.py
```

## 错误处理

### 常见错误及解决方案

1. **网络连接失败**
   - 检查网络连接
   - 验证API地址是否正确

2. **认证失败**
   - 检查`ACCESS_TOKEN`是否正确
   - 确认`BOT_ID`是否有效

3. **会话创建失败**
   - 检查API权限
   - 验证请求格式

## 性能对比

### 火山引擎 vs 扣子平台

| 特性 | 火山引擎 | 扣子平台 |
|------|----------|----------|
| 响应速度 | 中等 | 快速 |
| 稳定性 | 高 | 高 |
| 成本 | 按量计费 | 按量计费 |
| 功能丰富度 | 高 | 高 |
| 中文支持 | 优秀 | 优秀 |

## 回滚方案

如果需要回滚到火山引擎，可以：

1. 修改`ai_config.py`中的`AI_PROVIDER`为`"volcengine"`
2. 恢复`ark_example.py`中的火山引擎代码
3. 重新安装`volcenginesdkarkruntime`依赖

## 注意事项

1. **API密钥安全**: 请妥善保管扣子平台的访问令牌
2. **网络要求**: 确保服务器能够访问`api.coze.cn`
3. **错误监控**: 建议添加日志记录来监控AI调用状态
4. **成本控制**: 注意API调用次数，避免超出预算

## 技术支持

如遇到问题，请检查：

1. 网络连接状态
2. API配置是否正确
3. 依赖包是否已安装
4. 日志输出中的错误信息

## 更新日志

- **2024-01-XX**: 完成从火山引擎到扣子平台的迁移
- **2024-01-XX**: 添加了完整的错误处理机制
- **2024-01-XX**: 创建了配置管理系统 