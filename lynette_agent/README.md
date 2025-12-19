# Lynette Agent 使用指南

## 简介

Lynette Agent将Lynette编译器的功能封装为AI Agent，支持通过自然语言调用编译、部署、分析等功能。

## 快速开始

### 1. 安装依赖

```bash
pip install -r lynette_agent/requirements.txt
```

### 2. 启动服务

```bash
# 设置API Key（可选）
export LYNETTE_API_KEY=9e3b500e76df4145a50e0d1690b91177.wS0L2NL1EhXY3rXv
your_api_key

# 启动服务
python -m lynette_agent.server
```

服务将在 `http://localhost:8000` 启动。

### 3. 使用API

#### 3.1 编译PNE文件

```bash
curl -X POST http://localhost:8000/api/v1/compile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "mode": "debug",
    "input_file": "input/Alice_main.pne",
    "output_dir": "output",
    "target": "v1model"
  }'
```

#### 3.2 查询编译状态

```bash
curl -X GET http://localhost:8000/api/v1/compile/{task_id}/status \
  -H "Authorization: Bearer your_api_key"
```

#### 3.3 自然语言调用

```bash
curl -X POST http://localhost:8000/api/v1/nlp/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "query": "编译input/Alice_main.pne文件，输出到output目录"
  }'
```

#### 3.4 对话式交互

```bash
curl -X POST http://localhost:8000/api/v1/nlp/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "message": "帮我编译Alice_main.pne文件"
  }'
```

## Python SDK使用

```python
from lynette_agent import LynetteAgent

# 初始化Agent
agent = LynetteAgent(
    api_key="your_api_key",
    base_url="http://localhost:8000"
)

# 自然语言调用
response = agent.chat("编译input/Alice_main.pne文件")
print(response)

# 直接调用工具函数
task = agent.compile_pne(
    mode="debug",
    input_file="input/Alice_main.pne",
    output_dir="output"
)

# 查询任务状态
status = agent.check_compile_status(task["task_id"])
print(status)
```

## 支持的意图

- **编译**: "编译xxx.pne文件"、"生成P4代码"
- **部署**: "部署到所有节点"、"发送代码到设备"
- **分析**: "分析代码结构"、"检查语法"
- **验证**: "验证P4代码"、"检查代码正确性"
- **查询状态**: "查询编译状态"、"查看任务进度"

## API文档

启动服务后，访问 `http://localhost:8000/docs` 查看完整的API文档。

## MCP服务支持

Lynette Agent还支持Model Context Protocol (MCP)，可以将Lynette功能暴露给支持MCP的AI客户端（如Claude Desktop、Cursor等）。

### 使用MCP服务

1. **配置MCP服务器**

   在支持MCP的客户端中配置（如Claude Desktop或Cursor）：
   
   ```json
   {
     "mcpServers": {
       "lynette": {
         "command": "python",
         "args": ["-m", "lynette_agent.mcp_server"],
         "env": {
           "PYTHONPATH": "/path/to/lynette-dev/lynette-dev"
         }
       }
     }
   }
   ```

2. **测试MCP服务器**

   ```bash
   python -m lynette_agent.test_mcp
   ```

3. **在AI客户端中使用**

   配置完成后，重启AI客户端，然后可以直接使用自然语言调用Lynette功能：
   - "请编译input/Alice_main.pne文件"
   - "分析一下这个PNE文件的结构"
   - "部署P4代码到所有节点"

详细使用说明请参考 [MCP_GUIDE.md](MCP_GUIDE.md)

## 注意事项

1. 确保Lynette包已正确安装
2. 确保输入文件路径正确
3. 编译任务为异步执行，需要轮询查询状态
4. API Key认证为简化实现，生产环境应使用更安全的认证方式
5. MCP服务通过标准输入/输出通信，适用于支持MCP协议的客户端














