# Lynette Agent 开发方案

## 1. 概述

本文档描述如何将Lynette编译器的功能封装为Agent，使大模型能够通过自然语言调用Lynette的各种编译、生成和部署功能。

### 1.1 目标

- 将Lynette的核心功能封装为可被大模型调用的工具集
- 支持自然语言交互，用户可以用自然语言描述需求
- 提供RESTful API接口，便于集成到各种AI平台
- 支持异步任务执行和状态查询
- 提供详细的错误信息和执行日志

### 1.2 核心能力

1. **PNE文件编译**：将PNE源代码编译为P4代码
2. **代码生成**：生成节点级别的P4程序
3. **配置管理**：管理服务配置、拓扑配置和路径配置
4. **代码验证**：使用p4test验证生成的P4代码
5. **部署管理**：部署P4代码和表项到网络设备
6. **语法检查**：检查PNE文件语法正确性
7. **代码分析**：分析PNE代码结构（服务、应用、模块）

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    AI Agent Layer                        │
│  (自然语言理解、意图识别、参数提取、结果格式化)          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  API Gateway Layer                       │
│  (REST API、WebSocket、认证授权、限流)                   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                Service Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Compile  │  │ Deploy   │  │ Analyze  │              │
│  │ Service  │  │ Service  │  │ Service  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Lynette Core Library                        │
│  (parser_tree, collect, generate, aggregate, output)    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

#### 2.2.1 Agent层 (`lynette_agent/`)

- **`nlp_processor.py`**: 自然语言处理，将用户输入转换为结构化请求
- **`intent_classifier.py`**: 意图分类，识别用户想要执行的操作
- **`parameter_extractor.py`**: 参数提取，从自然语言中提取必要参数
- **`response_formatter.py`**: 响应格式化，将执行结果转换为自然语言描述

#### 2.2.2 API层 (`lynette_api/`)

- **`app.py`**: FastAPI应用主文件
- **`routes/`**: API路由定义
  - `compile.py`: 编译相关接口
  - `deploy.py`: 部署相关接口
  - `analyze.py`: 分析相关接口
  - `config.py`: 配置管理接口
- **`models/`**: 数据模型定义（Pydantic）
- **`middleware/`**: 中间件（认证、日志等）

#### 2.2.3 Service层 (`lynette_service/`)

- **`compile_service.py`**: 编译服务封装
- **`deploy_service.py`**: 部署服务封装
- **`analyze_service.py`**: 代码分析服务
- **`config_service.py`**: 配置管理服务
- **`task_manager.py`**: 异步任务管理

## 3. API接口设计

### 3.1 RESTful API规范

#### 3.1.1 基础URL

```
http://localhost:8000/api/v1
```

#### 3.1.2 认证方式

使用API Key认证，在请求头中携带：

```
Authorization: Bearer <api_key>
```

### 3.2 核心接口

#### 3.2.1 编译接口

**POST `/compile`**

编译PNE文件为P4代码。

**请求体**:
```json
{
  "mode": "debug|service",
  "input_file": "path/to/main.pne",  // debug模式必需
  "config_file": "path/to/service.json",  // service模式必需
  "output_dir": "path/to/output",
  "target": "v1model|tna",
  "options": {
    "p4_only": false,
    "check": false,
    "clean": true
  }
}
```

**响应**:
```json
{
  "task_id": "uuid",
  "status": "pending|running|completed|failed",
  "message": "编译任务已创建",
  "output_dir": "path/to/output"
}
```

**GET `/compile/{task_id}/status`**

查询编译任务状态。

**响应**:
```json
{
  "task_id": "uuid",
  "status": "completed",
  "progress": 100,
  "result": {
    "output_dir": "path/to/output",
    "generated_files": ["node1.p4", "node2.p4"],
    "entry_files": ["node1_entry.json", "node2_entry.json"],
    "log_file": "path/to/log.txt"
  },
  "error": null
}
```

#### 3.2.2 部署接口

**POST `/deploy`**

部署P4代码到网络设备。

**请求体**:
```json
{
  "task_id": "compile_task_id",  // 可选，如果提供则使用编译结果
  "output_dir": "path/to/output",  // 如果未提供task_id则必需
  "deploy_type": "code|entry|both",
  "nodes": ["node1", "node2"],  // 可选，如果未提供则部署所有节点
  "options": {
    "port": 13345,
    "timeout": 30
  }
}
```

**响应**:
```json
{
  "task_id": "uuid",
  "status": "pending",
  "message": "部署任务已创建"
}
```

#### 3.2.3 分析接口

**POST `/analyze`**

分析PNE代码结构。

**请求体**:
```json
{
  "input_file": "path/to/main.pne",
  "analysis_type": "syntax|structure|dependencies"
}
```

**响应**:
```json
{
  "syntax_valid": true,
  "services": [
    {
      "name": "service1",
      "applications": ["app1", "app2"]
    }
  ],
  "applications": [
    {
      "name": "app1",
      "variables": ["var1", "var2"],
      "instructions_count": 10
    }
  ],
  "modules": [
    {
      "name": "module1",
      "functions": ["func1"],
      "tables": ["table1"]
    }
  ],
  "dependencies": {
    "includes": ["file1.pne", "file2.pne"],
    "modules": ["module1"]
  }
}
```

#### 3.2.4 自然语言接口

**POST `/nlp/execute`**

通过自然语言执行操作。

**请求体**:
```json
{
  "query": "编译input/Alice_main.pne文件，输出到output目录",
  "context": {
    "previous_tasks": ["task_id1"],
    "user_preferences": {
      "target": "v1model",
      "auto_deploy": false
    }
  }
}
```

**响应**:
```json
{
  "intent": "compile",
  "parameters": {
    "mode": "debug",
    "input_file": "input/Alice_main.pne",
    "output_dir": "output",
    "target": "v1model"
  },
  "task_id": "uuid",
  "status": "pending",
  "message": "已理解您的请求，正在编译PNE文件..."
}
```

**POST `/nlp/chat`**

对话式交互接口。

**请求体**:
```json
{
  "message": "帮我编译Alice_main.pne，然后部署到所有节点",
  "session_id": "session_uuid",
  "history": [
    {
      "role": "user",
      "content": "之前的消息"
    },
    {
      "role": "assistant",
      "content": "之前的回复"
    }
  ]
}
```

**响应**:
```json
{
  "response": "好的，我将为您编译Alice_main.pne文件，编译完成后会自动部署到所有节点。编译任务ID: xxx",
  "actions": [
    {
      "type": "compile",
      "task_id": "uuid1"
    },
    {
      "type": "deploy",
      "task_id": "uuid2",
      "depends_on": "uuid1"
    }
  ],
  "session_id": "session_uuid"
}
```

### 3.3 工具函数定义（Function Calling）

为了支持大模型的Function Calling机制，定义以下工具函数：

#### 3.3.1 compile_pne

```json
{
  "name": "compile_pne",
  "description": "编译PNE文件为P4代码。支持debug模式（单文件编译）和service模式（完整服务编译）。",
  "parameters": {
    "type": "object",
    "properties": {
      "mode": {
        "type": "string",
        "enum": ["debug", "service"],
        "description": "编译模式：debug模式用于快速测试单个文件，service模式用于完整服务编译"
      },
      "input_file": {
        "type": "string",
        "description": "PNE主文件路径（debug模式必需）"
      },
      "config_file": {
        "type": "string",
        "description": "服务配置文件路径（service模式必需）"
      },
      "output_dir": {
        "type": "string",
        "description": "输出目录路径，默认为./pne_out"
      },
      "target": {
        "type": "string",
        "enum": ["v1model", "tna"],
        "description": "目标P4架构，v1model用于软件交换机，tna用于硬件交换机"
      },
      "p4_only": {
        "type": "boolean",
        "description": "是否只生成P4文件，不进行后续聚合和输出"
      },
      "check": {
        "type": "boolean",
        "description": "是否使用p4test验证生成的P4代码"
      }
    },
    "required": ["mode"]
  }
}
```

#### 3.3.2 deploy_p4

```json
{
  "name": "deploy_p4",
  "description": "部署P4代码或表项到网络设备。可以部署代码、表项或两者。",
  "parameters": {
    "type": "object",
    "properties": {
      "output_dir": {
        "type": "string",
        "description": "包含P4文件的输出目录"
      },
      "deploy_type": {
        "type": "string",
        "enum": ["code", "entry", "both"],
        "description": "部署类型：code表示部署P4代码，entry表示部署表项，both表示两者都部署"
      },
      "nodes": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "要部署的节点列表，如果未提供则部署所有节点"
      },
      "port": {
        "type": "integer",
        "description": "目标设备端口，默认为13345"
      }
    },
    "required": ["output_dir", "deploy_type"]
  }
}
```

#### 3.3.3 analyze_pne

```json
{
  "name": "analyze_pne",
  "description": "分析PNE代码结构，包括语法检查、服务/应用/模块提取、依赖关系分析等。",
  "parameters": {
    "type": "object",
    "properties": {
      "input_file": {
        "type": "string",
        "description": "要分析的PNE文件路径"
      },
      "analysis_type": {
        "type": "string",
        "enum": ["syntax", "structure", "dependencies", "all"],
        "description": "分析类型：syntax仅检查语法，structure提取代码结构，dependencies分析依赖关系，all执行全部分析"
      }
    },
    "required": ["input_file"]
  }
}
```

#### 3.3.4 check_compile_status

```json
{
  "name": "check_compile_status",
  "description": "查询编译任务的状态和结果。",
  "parameters": {
    "type": "object",
    "properties": {
      "task_id": {
        "type": "string",
        "description": "编译任务ID"
      }
    },
    "required": ["task_id"]
  }
}
```

#### 3.3.5 validate_p4

```json
{
  "name": "validate_p4",
  "description": "使用p4test验证P4代码的正确性。",
  "parameters": {
    "type": "object",
    "properties": {
      "p4_file": {
        "type": "string",
        "description": "要验证的P4文件路径"
      },
      "target": {
        "type": "string",
        "enum": ["v1model", "tna"],
        "description": "目标架构"
      }
    },
    "required": ["p4_file"]
  }
}
```

## 4. 实现细节

### 4.1 自然语言处理

#### 4.1.1 意图识别

使用关键词匹配和规则引擎识别用户意图：

```python
INTENT_PATTERNS = {
    "compile": [
        "编译", "生成", "转换", "compile", "generate", "convert",
        "把...编译成", "将...转换为"
    ],
    "deploy": [
        "部署", "发送", "上传", "deploy", "send", "upload",
        "部署到", "发送到"
    ],
    "analyze": [
        "分析", "检查", "查看", "analyze", "check", "view",
        "分析代码", "检查语法"
    ],
    "validate": [
        "验证", "校验", "validate", "verify"
    ]
}
```

#### 4.1.2 参数提取

使用正则表达式和命名实体识别提取参数：

```python
PARAMETER_PATTERNS = {
    "file_path": r"([\w/\\]+\.pne)",
    "output_dir": r"(?:输出到|输出目录|output)[:：]?\s*([\w/\\]+)",
    "target": r"(?:目标|架构|target)[:：]?\s*(v1model|tna)",
    "node": r"(?:节点|node)[:：]?\s*(\w+)"
}
```

### 4.2 异步任务管理

使用Celery或类似框架管理长时间运行的编译任务：

```python
from celery import Celery

app = Celery('lynette_agent')

@app.task
def compile_task(mode, input_file=None, config_file=None, output_dir=None, **options):
    """异步编译任务"""
    runner = LynetteRunner(...)
    try:
        runner.run(...)
        return {
            "status": "completed",
            "output_dir": output_dir,
            "files": get_generated_files(output_dir)
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
```

### 4.3 错误处理

统一的错误处理机制：

```python
class LynetteAgentError(Exception):
    """Agent基础异常类"""
    pass

class CompileError(LynetteAgentError):
    """编译错误"""
    pass

class DeployError(LynetteAgentError):
    """部署错误"""
    pass

class ValidationError(LynetteAgentError):
    """验证错误"""
    pass
```

### 4.4 日志记录

使用结构化日志记录所有操作：

```python
import logging
import json

logger = logging.getLogger('lynette_agent')

def log_operation(operation, parameters, result):
    logger.info(json.dumps({
        "operation": operation,
        "parameters": parameters,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }))
```

## 5. 使用示例

### 5.1 命令行使用

```bash
# 启动Agent服务
python -m lynette_agent.server --host 0.0.0.0 --port 8000

# 使用curl调用API
curl -X POST http://localhost:8000/api/v1/nlp/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "query": "编译input/Alice_main.pne文件，输出到output目录"
  }'
```

### 5.2 Python SDK使用

```python
from lynette_agent import LynetteAgent

agent = LynetteAgent(api_key="your_api_key", base_url="http://localhost:8000")

# 自然语言调用
response = agent.chat("帮我编译Alice_main.pne文件")
print(response)

# 直接调用工具函数
task = agent.compile_pne(
    mode="debug",
    input_file="input/Alice_main.pne",
    output_dir="output",
    target="v1model"
)

# 查询任务状态
status = agent.check_compile_status(task["task_id"])
print(status)
```

### 5.3 与OpenAI集成

```python
import openai
from lynette_agent.tools import get_tools_definition

client = openai.OpenAI(api_key="your_openai_key")

# 定义工具
tools = get_tools_definition()

# 对话
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "编译input/Alice_main.pne文件"}
    ],
    tools=tools,
    tool_choice="auto"
)

# 处理工具调用
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        if tool_call.function.name == "compile_pne":
            # 调用Lynette Agent
            result = agent.execute_tool(tool_call.function.name, 
                                      json.loads(tool_call.function.arguments))
```

## 6. 部署方案

### 6.1 Docker部署

```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "lynette_agent.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lynette-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lynette-agent
  template:
    metadata:
      labels:
        app: lynette-agent
    spec:
      containers:
      - name: agent
        image: lynette-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: lynette-secrets
              key: api-key
```

## 7. 安全考虑

### 7.1 API认证

- 使用JWT Token进行API认证
- 支持API Key认证
- 实现请求限流（Rate Limiting）

### 7.2 输入验证

- 验证文件路径，防止路径遍历攻击
- 限制文件大小和类型
- 验证配置文件的JSON格式

### 7.3 资源限制

- 限制并发编译任务数量
- 设置任务超时时间
- 限制输出目录大小

## 8. 测试方案

### 8.1 单元测试

```python
def test_compile_debug_mode():
    agent = LynetteAgent()
    result = agent.compile_pne(
        mode="debug",
        input_file="test/Alice_main.pne",
        output_dir="test_output"
    )
    assert result["status"] == "pending"
    assert "task_id" in result
```

### 8.2 集成测试

```python
def test_full_workflow():
    # 1. 编译
    compile_result = agent.compile_pne(...)
    task_id = compile_result["task_id"]
    
    # 2. 等待完成
    status = wait_for_completion(agent, task_id)
    assert status["status"] == "completed"
    
    # 3. 部署
    deploy_result = agent.deploy_p4(
        output_dir=status["result"]["output_dir"],
        deploy_type="code"
    )
    assert deploy_result["status"] == "pending"
```

### 8.3 端到端测试

使用真实PNE文件进行完整流程测试。

## 9. 性能优化

### 9.1 缓存机制

- 缓存语法树解析结果
- 缓存编译结果（基于文件hash）
- 缓存分析结果

### 9.2 并发处理

- 使用异步任务队列处理长时间任务
- 支持并行编译多个服务
- 使用连接池管理数据库连接

### 9.3 资源管理

- 及时清理临时文件
- 限制内存使用
- 监控系统资源使用情况

## 10. 监控和日志

### 10.1 监控指标

- API请求数量和响应时间
- 编译任务成功率和平均耗时
- 系统资源使用情况
- 错误率和错误类型

### 10.2 日志收集

- 使用ELK Stack收集和分析日志
- 结构化日志格式
- 日志级别分级（DEBUG, INFO, WARNING, ERROR）

## 11. 未来扩展

### 11.1 功能扩展

- 支持代码补全和智能提示
- 支持代码重构建议
- 支持性能分析和优化建议
- 支持多语言接口（英文、中文等）

### 11.2 集成扩展

- 集成到IDE插件
- 支持CI/CD流水线
- 支持Web界面
- 支持移动端应用

## 12. 开发计划

### Phase 1: 基础功能（2周）

- [ ] 实现核心API接口
- [ ] 实现自然语言处理基础功能
- [ ] 实现异步任务管理
- [ ] 基础测试

### Phase 2: 高级功能（2周）

- [ ] 完善自然语言理解
- [ ] 实现Function Calling支持
- [ ] 实现错误处理和日志
- [ ] 性能优化

### Phase 3: 集成和部署（1周）

- [ ] Docker化
- [ ] 文档完善
- [ ] 部署脚本
- [ ] 用户手册

## 13. 参考文档

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Celery文档](https://docs.celeryproject.org/)
- [Lynette架构文档](ARCHITECTURE.md)
- [Lynette开发指南](DEVELOPMENT_GUIDE.md)
















