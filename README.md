# LangGraph + Mem0 AI Agent with AWS Bedrock & PostgreSQL

这个项目展示了如何构建一个具有智能记忆能力的AI Agent，使用LangGraph和Mem0，基于AWS Bedrock和PostgreSQL with pgvector。

## 🚀 特性

- 🧠 **长期记忆**: 使用Mem0 + PostgreSQL + pgvector进行持久化智能记忆
- 🤖 **AWS Bedrock LLM**: Claude-3.7-Sonnet对话AI
- 🔍 **AWS Bedrock嵌入**: Titan嵌入用于语义搜索
- 🌐 **网络搜索**: 集成Tavily搜索获取实时信息
- 💬 **对话AI**: 使用LangGraph构建复杂对话流程
- 👤 **用户特定记忆**: 为不同用户分离记忆上下文
- 🔄 **记忆检索**: 自动检索相关记忆进行个性化回答
- 📊 **记忆仪表板**: 可视化记忆类型分布和统计信息
- 🐳 **双环境支持**: 本地Docker开发 + Aurora Serverless生产

## 🏗️ 架构

```
用户输入 → 记忆搜索 (PostgreSQL+pgvector) → LLM处理 (AWS Bedrock) → 工具调用 (Tavily) → 响应 + 记忆存储
```

### 技术栈

- **LLM**: AWS Bedrock Claude-3.7-Sonnet
- **嵌入**: AWS Bedrock Titan Text Embeddings
- **向量数据库**: PostgreSQL with pgvector extension
- **记忆管理**: Mem0
- **工作流**: LangGraph
- **网络搜索**: Tavily
- **语言**: Python 3.8+

## 📋 前置条件

### 1. AWS账户和Bedrock访问
- AWS账户具有Bedrock访问权限
- 访问Claude-3.7-Sonnet和Titan嵌入模型
- AWS凭证 (Access Key ID, Secret Access Key)

### 2. 本地开发环境
- Python 3.8+
- Docker和Docker Compose
- Node.js 14+ (用于CDK CLI)

### 3. Aurora CDK部署准备
- **AWS CLI**: 已配置并具有管理员权限
- **CDK CLI**: 全局安装的AWS CDK命令行工具
- **VPC权限**: 创建VPC、子网、安全组的权限
- **RDS权限**: 创建Aurora集群和实例的权限
- **Secrets Manager权限**: 管理数据库凭证的权限

### 4. API密钥
- Tavily API密钥 (可选，用于网络搜索)

## 🛠️ 安装步骤

### 步骤1: 克隆和环境设置

```bash
# 1. 进入项目目录
cd lg-m0-psql

# 2. 安装Python依赖
pip install -r requirements.txt

# 3. 配置AWS凭证
aws configure
# 或设置环境变量:
# export AWS_ACCESS_KEY_ID=your-access-key
# export AWS_SECRET_ACCESS_KEY=your-secret-key
# export AWS_DEFAULT_REGION=us-west-2
```

### 步骤2: 选择部署模式

#### 🐳 **模式A: 本地开发 (推荐开始)**

```bash
# 1. 切换到本地环境
./switch-env.sh local

# 2. 启动PostgreSQL容器
./docker-postgres.sh start

# 3. 验证数据库连接
python setup_postgres.py

# 4. 运行Agent
./run-agent.sh
```

#### ☁️ **模式B: Aurora Serverless生产**

**CDK环境准备:**
```bash
# 1. 安装Node.js (如果未安装)
# macOS: brew install node
# Ubuntu: sudo apt install nodejs npm
# Windows: 下载并安装 https://nodejs.org/

# 2. 安装AWS CDK CLI (全局安装)
npm install -g aws-cdk

# 3. 验证CDK安装
cdk --version

# 4. 安装CDK Python依赖
pip install -r requirements-cdk.txt

# 5. 验证AWS权限
aws sts get-caller-identity
```

**Aurora基础设施部署:**
```bash
# 1. CDK Bootstrap (首次使用CDK时需要)
cdk bootstrap

# 2. 自动化部署Aurora Serverless v2
python deploy_infrastructure.py

# 3. 获取Aurora凭证并更新.env
python get_aurora_credentials.py

# 4. 切换到Aurora环境
./switch-env.sh aurora

# 5. 验证Aurora连接 (需要VPC访问)
python verify_aurora_setup.py

# 6. 运行Agent (需要VPC访问)
python langgraph_mem0_agent.py
```

**所需AWS权限:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds:*",
                "ec2:*",
                "secretsmanager:*",
                "cloudformation:*",
                "iam:*",
                "logs:*"
            ],
            "Resource": "*"
        }
    ]
}
```

## 📁 项目文件说明

### 🤖 核心应用文件

| 文件 | 用途 | 说明 |
|------|------|------|
| `langgraph_mem0_agent.py` | 主应用程序 | LangGraph + Mem0 Agent核心逻辑 |
| `memory_dashboard.py` | 记忆仪表板 | 可视化记忆类型分布和统计信息 |
| `requirements.txt` | Python依赖 | 运行时所需的Python包 |
| `.env` | 环境配置 | 数据库连接和API密钥配置 |

### 🐳 本地开发文件

| 文件 | 用途 | 说明 |
|------|------|------|
| `docker-compose.yml` | Docker配置 | PostgreSQL容器定义 |
| `init-scripts/01-init-pgvector.sql` | 数据库初始化 | 自动创建pgvector扩展和表 |
| `docker-postgres.sh` | Docker管理 | PostgreSQL容器管理脚本 |
| `.env.local` | 本地环境配置 | 本地Docker PostgreSQL配置 |

### ☁️ AWS基础设施文件

| 文件 | 用途 | 说明 |
|------|------|------|
| `infrastructure/aurora_stack.py` | CDK栈定义 | Aurora Serverless v2基础设施 |
| `app.py` | CDK应用入口 | CDK应用主文件 |
| `cdk.json` | CDK配置 | CDK项目配置 |
| `requirements-cdk.txt` | CDK依赖 | CDK部署所需Python包 |

### 🛠️ 管理脚本

| 脚本 | 功能 | 用法 |
|------|------|------|
| `switch-env.sh` | 环境切换 | `./switch-env.sh local\|aurora\|status` |
| `run-agent.sh` | 启动Agent | `./run-agent.sh` (带警告抑制) |
| `deploy_infrastructure.py` | 部署Aurora | `python deploy_infrastructure.py` |
| `get_aurora_credentials.py` | 获取凭证 | `python get_aurora_credentials.py` |
| `setup_postgres.py` | 数据库设置 | `python setup_postgres.py` |
| `verify_aurora_setup.py` | 验证Aurora | `python verify_aurora_setup.py` |

### 🛠️ Docker PostgreSQL管理

```bash
# 启动PostgreSQL
./docker-postgres.sh start

# 停止PostgreSQL
./docker-postgres.sh stop

# 查看状态
./docker-postgres.sh status

# 连接数据库shell
./docker-postgres.sh shell

# 查看日志
./docker-postgres.sh logs

# 重置数据库
./docker-postgres.sh reset

# 备份数据库
./docker-postgres.sh backup

# 恢复数据库
./docker-postgres.sh restore
```

## 📁 项目结构

```
lg-m0-psql/
├── README.md                    # 项目主要说明
├── requirements.txt             # 统一的Python依赖
├── .env                        # 环境配置文件
├── start-api-service.sh        # API服务启动脚本 (兼容性)
├── docker-postgres.sh          # Docker管理脚本 (兼容性)
│
├── src/                        # 源代码目录
│   ├── core/                   # 核心功能模块
│   │   ├── agent.py           # LangGraph Agent主程序
│   │   ├── memory_manager.py  # 记忆管理器
│   │   ├── emotional_prompts.py # 情感陪伴提示词
│   │   └── telemetry.py       # 遥测禁用
│   ├── api/                    # API服务模块
│   │   ├── service.py         # OpenAI兼容API服务
│   │   └── memory_endpoints.py # 记忆管理端点
│   └── utils/                  # 工具模块
│       └── database.py        # 数据库设置工具
│
├── scripts/                    # 脚本目录
│   ├── start-api-service.sh   # API服务启动脚本
│   ├── docker-postgres.sh     # Docker PostgreSQL管理
│   ├── memory-maintenance     # 记忆维护脚本
│   └── configure_emotional_style.py # 情感风格配置
│
├── tools/                      # 工具和CLI
│   ├── memory_dashboard.py    # 记忆仪表板
│   ├── memory_maintenance_cli.py # 记忆维护CLI
│   └── enhanced_agent.py      # 增强版Agent
│
├── tests/                      # 测试目录
│   └── (各种测试文件)
│
├── docs/                       # 文档目录
│   ├── API_SERVICE.md         # API服务文档
│   ├── MEMORY_*.md           # 记忆相关文档
│   └── (其他文档)
│
├── infrastructure/             # 基础设施代码
│   ├── app.py                # CDK应用入口
│   ├── aurora_stack.py       # Aurora CDK栈
│   └── (部署相关文件)
│
├── docker/                     # Docker配置
│   ├── docker-compose.yml    # Docker Compose配置
│   └── init-scripts/         # 数据库初始化脚本
│
└── examples/                   # 示例代码
    └── (示例文件)
```

## 🔧 配置选项

### AWS Bedrock模型配置

在 `langgraph_mem0_agent.py` 中可以更改模型:

```python
# LLM模型选项
"model": "us.anthropic.claude-3-7-sonnet-20250219-v1:0"  # 最新Claude 3.7 Sonnet
"model": "anthropic.claude-3-sonnet-20240229-v1:0"       # 标准Claude 3 Sonnet
"model": "anthropic.claude-3-opus-20240229-v1:0"         # 最强能力

# 嵌入模型选项  
"model": "amazon.titan-embed-text-v1"     # 标准版
"model": "amazon.titan-embed-text-v2:0"   # 最新版本
```

### PostgreSQL配置

修改 `.env` 中的数据库设置:
```env
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432
POSTGRES_USER=your-username
POSTGRES_PASSWORD=your-password
POSTGRES_DB=your-database-name
```

### 记忆配置

自定义记忆行为:
```python
mem0 = Memory.from_config({
    "version": "v1.1",
    "llm": {
        "provider": "aws_bedrock",
        "config": {
            "model": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            "max_tokens": 1000,  # 调整响应长度
            "temperature": 0.7   # 调整创造性
        }
    }
})
```

### CDK配置

修改Aurora Serverless配置在 `infrastructure/aurora_stack.py`:
```python
# Aurora Serverless v2 容量配置
ServerlessV2ScalingConfiguration={
    "MinCapacity": 0.5,    # 最小容量 (ACU)
    "MaxCapacity": 16.0    # 最大容量 (ACU)
}

# 数据库参数组配置
parameters={
    "log_statement": "all",
    "log_min_duration_statement": "1000",  # 记录慢查询
    "max_connections": "100"
}
```

## 💡 使用示例

### 第一次对话
```
输入: 我最近很喜欢看足球比赛
AI: 太好了！足球是一项很精彩的运动...

输入: 我不喜欢坐飞机，更喜欢坐火车旅行
AI: 火车旅行确实很舒适，可以欣赏沿途风景...
```

### 后续会话 (记忆激活)
```
输入: 推荐一些旅游目的地
AI: 基于您之前提到的对足球的喜爱和偏好火车旅行，我推荐...
```

### 📊 记忆仪表板使用

**启动记忆仪表板**:
```bash
python memory_dashboard.py
```

**功能特性**:
- 📈 **记忆类型分布**: 可视化WORKING、SHORT_TERM、LONG_TERM、CORE记忆的数量分布
- 📊 **统计信息**: 显示总记忆数量、平均重要性、访问模式等关键指标
- 🔍 **记忆详情**: 查看具体记忆内容、元数据和分类信息
- 🎯 **用户筛选**: 支持按用户ID筛选查看特定用户的记忆数据
- 🔄 **实时更新**: 动态刷新显示最新的记忆状态

**示例输出**:
```
=== 记忆仪表板 ===
用户: default_user
总记忆数: 25

记忆类型分布:
├── WORKING: 5 (20%)
├── SHORT_TERM: 12 (48%)  
├── LONG_TERM: 6 (24%)
└── CORE: 2 (8%)

平均重要性: 5.8/10
最近访问: 2025-01-31 15:30:00
```

## 🚨 故障排除

### 常见问题

1. **AWS Bedrock访问被拒绝**
   - 确保AWS账户有Bedrock访问权限
   - 检查模型在您的区域是否可用
   - 验证AWS凭证

2. **PostgreSQL连接失败**
   - 检查PostgreSQL是否运行
   - 验证连接参数
   - 确保数据库存在

3. **pgvector扩展缺失**
   - 运行: `python setup_postgres.py`
   - 检查PostgreSQL版本兼容性
   - 验证向量维度匹配

4. **记忆操作失败**
   - 检查表权限
   - 验证向量维度匹配
   - 运行数据库设置脚本

5. **CDK部署失败**
   - 确保AWS CLI已配置且有足够权限
   - 检查CDK CLI版本: `cdk --version`
   - 运行CDK bootstrap: `cdk bootstrap`
   - 检查AWS账户限制和配额

6. **Aurora连接超时**
   - Aurora Serverless v2可能需要15-30秒启动
   - 检查VPC和安全组配置
   - 确保从正确的网络环境访问

### 调试模式

启用详细日志:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔒 安全考虑

- 安全存储AWS凭证 (生产环境使用IAM角色)
- 使用PostgreSQL连接池
- 实施适当的用户认证
- 加密记忆存储中的敏感数据
- 在AWS中使用VPC进行数据库访问

## 🚀 生产部署

### AWS基础设施
- 使用RDS PostgreSQL with pgvector
- 在ECS/EKS上部署，使用IAM角色
- 使用Application Load Balancer
- 启用CloudWatch监控

### 数据库优化
- 配置连接池
- 设置读取副本进行扩展
- 实施适当的索引策略
- 监控查询性能

## 📊 性能考虑

- **记忆搜索**: 使用适当索引的O(log n)
- **嵌入生成**: 每个请求约100ms
- **LLM响应**: 1-3秒，取决于模型
- **数据库操作**: 典型查询<50ms

## 📚 相关文档

- [MEMORY_MECHANISM.md](./MEMORY_MECHANISM.md) - 详细的记忆机制说明
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Aurora Serverless详细部署指南
- [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) - 项目结构说明
- [LangGraph文档](https://langchain-ai.github.io/langgraph/)
- [Mem0文档](https://docs.mem0.ai/)
- [AWS Bedrock文档](https://docs.aws.amazon.com/bedrock/)
- [pgvector文档](https://github.com/pgvector/pgvector)

## 🆘 支持

如果遇到问题:

1. 运行设置指南: `python verify_aurora_setup.py`
2. 检查故障排除部分
3. 查看AWS Bedrock和PostgreSQL日志
4. 确保满足所有前置条件

---

**开心编码! 🎉**
