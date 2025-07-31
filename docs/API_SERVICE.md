# LangGraph + Mem0 Agent OpenAI-Compatible API Service

这个项目将原有的LangGraph + Mem0智能Agent重构为一个OpenAI兼容的FastAPI服务，允许任何支持OpenAI API的客户端与智能Agent进行交互。

## 🚀 新特性

- 🔌 **OpenAI兼容API**: 完全兼容OpenAI Chat Completions API格式
- 🌊 **流式响应**: 支持流式和非流式响应模式
- 🧠 **记忆管理**: 提供专门的记忆管理API端点
- 💬 **聊天内命令**: 支持在聊天中直接使用`/memories`、`/stats`等命令
- 💝 **情感陪伴**: 5种不同风格的情感陪伴AI人格（温暖朋友、温柔治愈、活泼伙伴、智慧导师、贴心家人）
- 👥 **多用户支持**: 基于用户ID的记忆隔离
- 📊 **监控端点**: 健康检查、服务信息和统计数据
- 🔄 **异步处理**: 基于FastAPI的高性能异步处理
- 📚 **自动文档**: 自动生成的API文档和交互式测试界面

## 📋 API端点概览

### 核心聊天端点
- `POST /v1/chat/completions` - OpenAI兼容的聊天完成端点

### 记忆管理端点

- `GET /v1/memory/stats/{user_id}` - 获取用户记忆统计 (对应原始Agent的`/stats`命令)
- `POST /v1/memory/maintenance/{user_id}` - 运行记忆维护 (对应原始Agent的`/maintenance`命令)
- `GET /v1/memory/memories/{user_id}` - 列出用户记忆 (对应原始Agent的`/memories`命令)
- `DELETE /v1/memory/clear/{user_id}` - 清除用户记忆 (谨慎使用)

### 服务端点
- `GET /health` - 健康检查
- `GET /info` - 服务信息
- `GET /docs` - API文档 (Swagger UI)
- `GET /redoc` - API文档 (ReDoc)

## 🛠️ 快速开始

### 1. 安装依赖

```bash
# 安装API服务依赖
pip install -r requirements-api.txt
```

### 2. 配置环境

确保你的`.env`文件包含必要的配置：

```env
# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=mem0_agent

# AWS配置
AWS_DEFAULT_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# 可选：Tavily搜索API
TAVILY_API_KEY=your-tavily-key
```

### 3. 启动服务

```bash
# 使用启动脚本（推荐）
./start-api-service.sh

# 或者直接使用uvicorn
uvicorn openai_compatible_service:app --host 0.0.0.0 --port 8000

# 开发模式（自动重载）
./start-api-service.sh --reload
```

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 服务信息
curl http://localhost:8000/info

# 访问API文档
open http://localhost:8000/docs
```

## 💬 使用示例

### 使用OpenAI Python客户端

```python
from openai import OpenAI

# 初始化客户端
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy-key"  # 我们的服务不需要真实的API密钥
)

# 发送聊天请求
response = client.chat.completions.create(
    model="langgraph-mem0-agent",
    messages=[
        {"role": "user", "content": "你好！我叫张三，我很喜欢踢足球。"}
    ],
    user="user_123"  # 用户ID用于记忆管理
)

print(response.choices[0].message.content)

# 💬 使用聊天内命令
command_response = client.chat.completions.create(
    model="langgraph-mem0-agent",
    messages=[
        {"role": "user", "content": "/memories"}  # 直接在聊天中使用命令
    ],
    user="user_123"
)

print(command_response.choices[0].message.content)

# 流式响应
stream = client.chat.completions.create(
    model="langgraph-mem0-agent",
    messages=[
        {"role": "user", "content": "/stats"}  # 命令也支持流式响应
    ],
    user="user_123",
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

### 💬 聊天内命令 (新功能!)

用户可以在聊天中直接输入命令，就像原始Agent一样：

```python
# 可用的聊天内命令
commands = [
    "/help",           # 显示帮助信息
    "/stats",          # 显示记忆统计 (对应原始Agent的/stats)
    "/memories",       # 显示所有记忆 (对应原始Agent的/memories)
    "/memories core",  # 显示核心记忆
    "/memories long",  # 显示长期记忆
    "/memories short", # 显示短期记忆
    "/memories working", # 显示工作记忆
    "/maintenance"     # 运行记忆维护 (对应原始Agent的/maintenance)
]

# 示例：混合对话
messages = [
    {"role": "user", "content": "你好！我叫李四，我是程序员。"},
    {"role": "assistant", "content": "你好李四！很高兴认识一位程序员..."},
    {"role": "user", "content": "/memories"},  # 使用命令查看记忆
    {"role": "assistant", "content": "📚 All memories for user_123:\n  1. [core] 用户叫李四，是程序员..."},
    {"role": "user", "content": "谢谢！请继续我们的对话。"}
]
```

### 使用curl

```bash
# 基本聊天请求
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "langgraph-mem0-agent",
    "messages": [
      {"role": "user", "content": "你好！我是李四，我喜欢编程。"}
    ],
    "user": "user_456",
    "temperature": 0.7,
    "max_tokens": 1000
  }'

# 💬 使用聊天内命令
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "langgraph-mem0-agent",
    "messages": [
      {"role": "user", "content": "/memories core"}
    ],
    "user": "user_456"
  }'

# 流式命令请求
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "langgraph-mem0-agent",
    "messages": [
      {"role": "user", "content": "/stats"}
    ],
    "user": "user_456",
    "stream": true
  }'
```

### 记忆管理

```bash
# 获取用户记忆统计 (对应 /stats 命令)
curl "http://localhost:8000/v1/memory/stats/user_123"

# 运行记忆维护 (对应 /maintenance 命令)
curl -X POST "http://localhost:8000/v1/memory/maintenance/user_123"

# 列出所有记忆 (对应 /memories 命令)
curl "http://localhost:8000/v1/memory/memories/user_123?memory_type=all&limit=10"

# 列出特定类型记忆
curl "http://localhost:8000/v1/memory/memories/user_123?memory_type=core&limit=5"

# 清除特定类型的记忆
curl -X DELETE "http://localhost:8000/v1/memory/clear/user_123?memory_type=working"
```

#### 记忆类型说明

- **`all`** - 所有记忆
- **`core`** - 核心身份和基本特征
- **`long`** - 长期偏好和重要事实  
- **`short`** - 近期重要信息
- **`working`** - 临时工作记忆

#### 记忆管理API响应示例

**记忆统计响应:**
```json
{
  "user_id": "user_123",
  "total_memories": 15,
  "by_type": {
    "core": 2,
    "long_term": 8,
    "short_term": 4,
    "working": 1
  },
  "average_importance": 6.8,
  "memory_health": {
    "status": "healthy",
    "avg_importance": 6.8,
    "highly_accessed": 3
  }
}
```

**记忆列表响应:**
```json
{
  "user_id": "user_123",
  "memory_type_filter": "all",
  "total_found": 15,
  "showing": 10,
  "memories": [
    {
      "id": "mem_001",
      "content": "用户喜欢踢足球，是一名软件工程师",
      "type": "core",
      "importance": 8.5,
      "metadata": {
        "memory_type": "core",
        "importance_level": 8.5
      }
    }
  ]
}
```

## 💝 情感陪伴配置 (新功能!)

服务支持5种不同的情感陪伴风格，每种风格都有独特的人格特征和对话方式：

### 🎭 可用风格

| 风格 | 名称 | 特点 | 适用场景 |
|------|------|------|----------|
| `warm_friend` | 温暖朋友 | 温暖贴心，像最好的朋友 | 日常陪伴、情感支持 |
| `gentle_healing` | 温柔治愈 | 温柔包容，具有治愈力量 | 心理疏导、情绪治愈 |
| `cheerful_companion` | 活泼伙伴 | 乐观开朗，充满正能量 | 提振情绪、增加活力 |
| `wise_mentor` | 智慧导师 | 深度智慧，人生指导 | 人生指导、深度思考 |
| `caring_sibling` | 贴心家人 | 像家人一样关爱 | 家庭式关怀、生活陪伴 |

### 🔧 配置方法

```bash
# 1. 查看所有可用风格
python configure_emotional_style.py --list

# 2. 预览特定风格
python configure_emotional_style.py --preview gentle_healing

# 3. 设置风格
python configure_emotional_style.py --set gentle_healing

# 4. 重启服务应用新风格
./start-api-service.sh

# 5. 交互式配置（推荐）
python configure_emotional_style.py --interactive
```

### 💬 风格效果对比

**温暖朋友风格**：
```
用户：我今天心情不好
AI：听到你心情不好，我很关心你呢。作为你的朋友，我想陪伴你度过这个难过的时刻。能告诉我发生什么事了吗？我会认真倾听的。
```

**温柔治愈风格**：
```
用户：我今天心情不好  
AI：亲爱的，我能感受到你内心的不安。就像夜空中的星星，即使被乌云遮挡，它们依然在那里闪闪发光。你的内心也有这样的光芒，让我陪你一起找到它好吗？
```

**活泼伙伴风格**：
```
用户：我今天心情不好
AI：哎呀，我的小伙伴心情不美丽了！🌈 没关系没关系，坏心情就像天气一样，总会过去的！来来来，告诉我发生什么事了，我们一起想办法让你重新开心起来！
```

### 🎯 环境变量配置

也可以通过环境变量直接设置：

```bash
# 在 .env 文件中添加
EMOTIONAL_COMPANION_STYLE=gentle_healing

# 或者临时设置
export EMOTIONAL_COMPANION_STYLE=warm_friend
```

### 🧪 测试情感陪伴效果

```bash
# 测试当前风格效果
python test_emotional_styles.py --test

# 查看所有风格特征对比
python test_emotional_styles.py --table

# 显示配置指南
python test_emotional_styles.py --guide

# 运行完整演示
python test_emotional_styles.py --all
```

### 💡 使用建议

- **温暖朋友**: 适合日常聊天，提供友善的陪伴
- **温柔治愈**: 适合用户情绪低落时，提供心灵慰藉  
- **活泼伙伴**: 适合需要正能量时，带来欢乐和活力
- **智慧导师**: 适合人生困惑时，提供深度指导
- **贴心家人**: 适合需要关怀时，给予家人般的温暖

### 服务器配置

```bash
# 自定义主机和端口
./start-api-service.sh --host 127.0.0.1 --port 8080

# 启用开发模式
./start-api-service.sh --reload

# 多进程模式
./start-api-service.sh --workers 4
```

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `POSTGRES_HOST` | PostgreSQL主机 | `localhost` |
| `POSTGRES_PORT` | PostgreSQL端口 | `5432` |
| `POSTGRES_USER` | 数据库用户名 | `postgres` |
| `POSTGRES_PASSWORD` | 数据库密码 | `` |
| `POSTGRES_DB` | 数据库名称 | `mem0_agent` |
| `AWS_DEFAULT_REGION` | AWS区域 | `us-west-2` |
| `TAVILY_API_KEY` | Tavily搜索API密钥 | 可选 |

## 📊 API响应格式

### 聊天完成响应

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "langgraph-mem0-agent",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "你好张三！很高兴认识一位足球爱好者..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 25,
    "total_tokens": 37
  }
}
```

### 记忆统计响应

```json
{
  "user_id": "user_123",
  "total_memories": 15,
  "by_type": {
    "core": 2,
    "long_term": 8,
    "short_term": 4,
    "working": 1
  },
  "average_importance": 6.8,
  "memory_health": {
    "status": "healthy",
    "avg_importance": 6.8,
    "highly_accessed": 3,
    "scored_memories": 12,
    "unscored_memories": 3
  }
}
```

## 🔌 客户端集成

### 支持的客户端

- **OpenAI Python客户端**: `pip install openai`
- **LangChain**: 使用`ChatOpenAI`并设置`base_url`
- **任何HTTP客户端**: requests, httpx, axios等
- **curl**: 命令行测试

### LangChain集成示例

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy-key",
    model="langgraph-mem0-agent"
)

response = llm.invoke("你好，我是新用户")
print(response.content)
```

### JavaScript/Node.js示例

```javascript
const OpenAI = require('openai');

const openai = new OpenAI({
  baseURL: 'http://localhost:8000/v1',
  apiKey: 'dummy-key'
});

async function chat() {
  const completion = await openai.chat.completions.create({
    messages: [
      { role: 'user', content: '你好！我是JavaScript开发者。' }
    ],
    model: 'langgraph-mem0-agent',
    user: 'js_user_001'
  });

  console.log(completion.choices[0].message.content);
}

chat();
```

## 🚀 生产部署

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements-api.txt .
RUN pip install -r requirements-api.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "openai_compatible_service:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 使用反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 环境变量管理

```bash
# 生产环境建议使用环境变量而不是.env文件
export POSTGRES_HOST=your-production-db-host
export AWS_ACCESS_KEY_ID=your-production-key
export AWS_SECRET_ACCESS_KEY=your-production-secret
```

## 🔍 监控和调试

### 日志配置

服务使用Python的logging模块，可以通过环境变量配置日志级别：

```bash
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### 健康检查

```bash
# 简单健康检查
curl http://localhost:8000/health

# 详细服务信息
curl http://localhost:8000/info
```

### 性能监控

```python
# 在生产环境中，可以添加性能监控
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## 🛠️ 开发和测试

### 运行测试客户端

```bash
# 运行示例客户端
python example_client.py
```

### API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 开发模式

```bash
# 启用自动重载
./start-api-service.sh --reload

# 或者直接使用uvicorn
uvicorn openai_compatible_service:app --reload --log-level debug
```

## 🔒 安全考虑

### 生产环境安全

1. **API密钥验证**: 在生产环境中实现真实的API密钥验证
2. **CORS配置**: 限制允许的源域名
3. **速率限制**: 实现请求速率限制
4. **HTTPS**: 使用HTTPS加密传输
5. **输入验证**: 严格验证所有输入参数

### 示例安全中间件

```python
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.middleware("http")
async def validate_api_key(request: Request, call_next):
    if request.url.path.startswith("/v1/"):
        # 在生产环境中验证API密钥
        pass
    response = await call_next(request)
    return response
```

## 📈 性能优化

### 连接池配置

```python
# 在生产环境中配置数据库连接池
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

### 缓存策略

```python
# 添加内存缓存以提高性能
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_memories(user_id: str):
    # 缓存用户记忆查询结果
    pass
```

## 🆘 故障排除

### 常见问题

1. **服务启动失败**
   - 检查端口是否被占用
   - 验证环境变量配置
   - 确认数据库连接

2. **记忆功能异常**
   - 检查PostgreSQL连接
   - 验证pgvector扩展
   - 查看数据库日志

3. **AWS Bedrock错误**
   - 验证AWS凭证
   - 检查区域配置
   - 确认模型访问权限

### 调试命令

```bash
# 检查服务状态
curl http://localhost:8000/health

# 测试数据库连接
python -c "from openai_compatible_service import initialize_agent; import asyncio; asyncio.run(initialize_agent())"

# 查看详细日志
./start-api-service.sh --reload  # 开发模式有更详细的日志
```

## 📚 相关文档

- [原始Agent文档](./README.md)
- [记忆机制说明](./MEMORY_MECHANISM.md)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [OpenAI API文档](https://platform.openai.com/docs/api-reference)

## 🎯 下一步计划

- [ ] 添加用户认证和授权
- [ ] 实现请求速率限制
- [ ] 添加更多监控指标
- [ ] 支持更多OpenAI API端点
- [ ] 添加批量处理支持
- [ ] 实现WebSocket支持

---

**享受你的OpenAI兼容智能Agent API服务！** 🎉
