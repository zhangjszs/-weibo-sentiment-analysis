# 上下文感知情感分析功能指南

## 功能介绍

上下文感知情感分析是一种高级情感分析技术，能够：

1. **上下文理解**：分析文本的语境和语义关联
2. **情感趋势分析**：识别情感变化趋势和突变
3. **网络用语处理**：支持网络用语、emoji表情和新兴词汇
4. **语义关联分析**：理解文本之间的语义关系

## 技术架构

### 核心组件

1. **ContextManager**：管理上下文信息，支持多会话
2. **ContextAnalyzer**：分析上下文，计算情感趋势和突变
3. **InternetSlangProcessor**：处理网络用语和emoji表情
4. **ContextualSentimentAnalyzer**：整合基础分析和上下文分析

### 工作流程

1. 文本预处理：去除多余空格，扩展网络用语缩写
2. 基础情感分析：使用SnowNLP进行初步分析
3. 上下文关联分析：分析情感趋势、语义关联和情感突变
4. 网络用语增强：处理网络用语和emoji表情
5. 结果融合：融合基础分析和上下文分析结果
6. 上下文更新：将当前分析结果加入上下文

## 使用方法

### 1. 基本使用

```python
from src.services.sentiment_service import SentimentService

# 基础情感分析
result = SentimentService.analyze("这部电影yyds，强烈推荐", mode="contextual")
print(result)
```

### 2. 上下文关联分析

```python
from src.services.contextual_sentiment import contextual_analyzer

# 清除之前的上下文
contextual_analyzer.clear_context("user123")

# 分析对话历史
conversation = [
    "今天是个好日子",
    "天气晴朗，心情不错",
    "但是突然下起了雨",
    "心情瞬间变差了"
]

for text in conversation:
    result = contextual_analyzer.analyze(text, context_id="user123")
    print(f"文本: {text}")
    print(f"得分: {result.score}")
    print(f"标签: {result.label}")
    print(f"情感: {result.emotion}")
    print(f"推理: {result.reasoning}")
    print("---")
```

### 3. 批量分析

```python
from src.services.sentiment_service import SentimentService

texts = [
    "这部电影真的很棒",
    "今天天气很差",
    "yyds！这个游戏太好玩了"
]

results = SentimentService.analyze_batch(texts, mode="contextual")
for text, result in zip(texts, results):
    print(f"文本: {text}")
    print(f"得分: {result['score']}")
    print(f"标签: {result['label']}")
    print("---")
```

## API 参考

### SentimentService.analyze()

**参数**：
- `text` (str): 待分析文本
- `mode` (str): 分析模式，使用 "contextual" 启用上下文感知分析

**返回值**：
- `dict`: 包含以下字段的字典：
  - `score`: 情感得分 (0-1)
  - `label`: 情感标签 (positive/neutral/negative)
  - `emotion`: 细粒度情感
  - `keywords`: 关键词列表
  - `reasoning`: 分析推理
  - `source`: 分析来源

### SentimentService.analyze_batch()

**参数**：
- `texts` (list): 文本列表
- `mode` (str): 分析模式，使用 "contextual" 启用上下文感知分析

**返回值**：
- `list`: 分析结果列表，每个元素与 `analyze()` 返回格式相同

### contextual_analyzer.analyze()

**参数**：
- `text` (str): 待分析文本
- `context_id` (str, optional): 上下文ID，用于关联上下文

**返回值**：
- `SentimentResult`: 情感分析结果对象

### contextual_analyzer.clear_context()

**参数**：
- `context_id` (str): 上下文ID

**功能**：清除指定上下文的历史记录

## 性能优化

1. **缓存机制**：使用内存缓存减少重复计算
2. **批量处理**：支持批量分析，提高处理效率
3. **上下文管理**：使用固定大小的队列管理上下文，避免内存占用过大
4. **异步处理**：支持异步分析，适合高并发场景

## 网络用语支持

当前支持的网络用语包括：

- 正向：yyds、绝绝子、666、nb、牛批、奥利给、种草、安利、真香、爱了
- 负向：破防、破防了、无语、醉了、吐了、服了、晕了、崩溃、绝望、难受

支持的emoji表情：

- 😄 😊 😃 😁 😆 😅 🤣 😂 😍 😘 👍 👌 ✌️ 🤞 🤟 🤘
- 😢 😭 😞 😔 😟 😕 🙁 ☹️ 😤 😠 😡 🤬
- 😰 😥 😓 😨 😱 🤢 🤮 😴 🤔 😐 😑

## 部署指南

### 依赖安装

```bash
# 安装基本依赖
pip install requests snownlp circuitbreaker pydantic python-dotenv

# 安装完整依赖（可选）
pip install -r requirements.txt
```

### 环境配置

在 `.env` 文件中配置：

```
# LLM配置（可选）
LLM_API_KEY=your_api_key
LLM_API_URL=https://api.deepseek.com/v1/chat/completions
LLM_MODEL=deepseek-chat

# Redis配置（可选，用于缓存）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

### 启动服务

```bash
# 启动主服务
python run.py

# 启动NLP服务
cd nlp_service
python -m app.main
```

## 监控和维护

### 性能监控

- 批量分析4条文本平均耗时：约0.009秒/条
- 支持每秒处理约100条文本

### 常见问题

1. **Redis连接失败**：服务会自动降级为内存缓存，不影响核心功能
2. **LLM API不可用**：服务会自动降级为SnowNLP，确保基本功能正常
3. **上下文过大**：系统会自动限制上下文大小，最多保留5条历史记录

### 日志管理

日志文件位于 `logs/` 目录，包含：
- 服务启动日志
- 分析错误日志
- 性能统计日志

## 示例应用

### 社交媒体情感分析

```python
from src.services.sentiment_service import SentimentService

# 分析社交媒体评论
comments = [
    "这部电影yyds，强烈推荐",
    "剧情有点无聊，不推荐",
    "演员表演很出色，666",
    "结局太感人了，哭了"
]

results = SentimentService.analyze_batch(comments, mode="contextual")

# 统计情感分布
positive = sum(1 for r in results if r['label'] == 'positive')
negative = sum(1 for r in results if r['label'] == 'negative')
neutral = sum(1 for r in results if r['label'] == 'neutral')

print(f"正面: {positive}, 中性: {neutral}, 负面: {negative}")
```

### 客服对话情感分析

```python
from src.services.contextual_sentiment import contextual_analyzer

# 分析客服对话
conversation = [
    "您好，我想咨询一下订单问题",
    "好的，请问您的订单号是多少？",
    "我的订单号是123456，已经等了3天了还没发货",
    "非常抱歉，我帮您查询一下"
]

# 清除之前的上下文
contextual_analyzer.clear_context("customer_123")

# 分析对话情感变化
for i, text in enumerate(conversation):
    result = contextual_analyzer.analyze(text, context_id="customer_123")
    print(f"对话 {i+1}: {text}")
    print(f"情感得分: {result.score:.4f}")
    print(f"情感标签: {result.label}")
    print(f"细粒度情感: {result.emotion}")
    print("---")
```

## 总结

上下文感知情感分析是一种强大的情感分析技术，能够：

- 理解文本的上下文语境
- 识别情感变化趋势
- 处理网络用语和emoji表情
- 提供更准确的情感分析结果

通过简单的API调用，您可以轻松集成这一功能到您的应用中，为用户提供更智能的情感分析服务。
