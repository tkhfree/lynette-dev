# Lynette MCP服务使用指南

## 简介

Lynette MCP服务器实现了Model Context Protocol (MCP)，将Lynette编译器的功能暴露为MCP工具，使得AI助手（如Claude Desktop、Cursor等）可以通过MCP协议调用Lynette的编译、分析、部署等功能。

## MCP协议简介

Model Context Protocol (MCP) 是一个开放标准，用于将AI模型和代理与外部数据源和工具连接起来。它基于JSON-RPC 2.0协议，采用客户端-服务器架构。

## 安装和配置

### 1. 安装依赖

确保已安装所有必需的依赖：

```bash
pip install -r lynette_agent/requirements.txt
```

### 2. 配置MCP服务器

#### 在Claude Desktop中配置

编辑Claude Desktop的配置文件（macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`，Windows: `%APPDATA%\Claude\claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "lynette": {
      "command": "python",
      "args": [
        "-m",
        "lynette_agent.mcp_server"
      ],
      "env": {
        "PYTHONPATH": "/path/to/lynette-dev/lynette-dev"
      }
    }
  }
}
```

#### 在Cursor中配置

编辑Cursor的MCP配置文件（通常在用户配置目录下）：

```json
{
  "mcpServers": {
    "lynette": {
      "command": "python",
      "args": [
        "-m",
        "lynette_agent.mcp_server"
      ],
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

### 3. 测试MCP服务器

可以直接运行MCP服务器进行测试：

```bash
python -m lynette_agent.mcp_server
```

服务器将通过标准输入/输出与客户端通信。

## 可用的MCP工具

### 1. compile_pne

编译PNE文件为P4代码。

**参数：**
- `mode` (必需): 编译模式，`"debug"` 或 `"service"`
- `input_file` (可选): PNE主文件路径（debug模式必需）
- `config_file` (可选): 服务配置文件路径（service模式必需）
- `output_dir` (可选): 输出目录，默认为 `"./pne_out"`
- `target` (可选): 目标架构，`"v1model"` 或 `"tna"`，默认为 `"v1model"`
- `p4_only` (可选): 是否只生成P4文件，默认为 `false`
- `check` (可选): 是否使用p4test验证，默认为 `false`

**示例：**
```json
{
  "name": "compile_pne",
  "arguments": {
    "mode": "debug",
    "input_file": "input/Alice_main.pne",
    "output_dir": "output",
    "target": "v1model"
  }
}
```

### 2. deploy_p4

部署P4代码或表项到网络设备。

**参数：**
- `output_dir` (必需): 包含P4文件的输出目录
- `deploy_type` (必需): 部署类型，`"code"`、`"entry"` 或 `"both"`
- `nodes` (可选): 要部署的节点列表
- `port` (可选): 目标设备端口，默认为 `13345`

**示例：**
```json
{
  "name": "deploy_p4",
  "arguments": {
    "output_dir": "output",
    "deploy_type": "both",
    "nodes": ["s1", "s2"],
    "port": 13345
  }
}
```

### 3. analyze_pne

分析PNE代码结构。

**参数：**
- `input_file` (必需): 要分析的PNE文件路径
- `analysis_type` (可选): 分析类型，`"syntax"`、`"structure"`、`"dependencies"` 或 `"all"`，默认为 `"all"`

**示例：**
```json
{
  "name": "analyze_pne",
  "arguments": {
    "input_file": "input/Alice_main.pne",
    "analysis_type": "all"
  }
}
```

### 4. check_compile_status

查询编译任务的状态和结果。

**参数：**
- `task_id` (必需): 编译任务ID

**示例：**
```json
{
  "name": "check_compile_status",
  "arguments": {
    "task_id": "123e4567-e89b-12d3-a456-426614174000"
  }
}
```

### 5. validate_p4

使用p4test验证P4代码的正确性。

**参数：**
- `p4_file` (必需): 要验证的P4文件路径
- `target` (可选): 目标架构，`"v1model"` 或 `"tna"`，默认为 `"v1model"`

**示例：**
```json
{
  "name": "validate_p4",
  "arguments": {
    "p4_file": "output/s1.p4",
    "target": "v1model"
  }
}
```

## 可用的资源

### lynette://examples

访问Lynette项目中的示例PNE文件列表。

## 可用的提示模板

### compile_pne_template

编译PNE文件的提示模板。

**参数：**
- `input_file` (必需): 要编译的PNE文件路径
- `mode` (可选): 编译模式

### analyze_pne_template

分析PNE代码的提示模板。

**参数：**
- `input_file` (必需): 要分析的PNE文件路径

## 使用示例

### 在Claude Desktop中使用

1. 配置MCP服务器后，重启Claude Desktop
2. 在对话中，Claude可以自动调用Lynette工具
3. 例如，你可以说："请编译input/Alice_main.pne文件"
4. Claude会自动调用`compile_pne`工具

### 在Cursor中使用

1. 配置MCP服务器后，重启Cursor
2. 在AI对话中，可以直接使用自然语言调用工具
3. 例如："分析一下这个PNE文件的结构"

## 协议实现细节

### JSON-RPC 2.0消息格式

**请求格式：**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "compile_pne",
    "arguments": {
      "mode": "debug",
      "input_file": "input/Alice_main.pne"
    }
  }
}
```

**响应格式：**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"task_id\": \"...\", \"status\": \"pending\"}"
      }
    ]
  }
}
```

### 标准输入/输出通信

MCP服务器通过标准输入/输出与客户端通信：
- 从标准输入读取JSON-RPC请求
- 向标准输出写入JSON-RPC响应
- 每行一个JSON消息

## 故障排除

### 1. 服务器无法启动

- 检查Python路径是否正确
- 检查PYTHONPATH环境变量
- 确保所有依赖已安装

### 2. 工具调用失败

- 检查文件路径是否正确
- 检查Lynette包是否正确安装
- 查看错误消息中的详细信息

### 3. 连接问题

- 确保MCP服务器配置正确
- 检查客户端是否支持MCP协议
- 查看客户端日志

## 开发扩展

### 添加新工具

在`mcp_server.py`的`handle_tools_list`方法中添加新工具定义，在`handle_tools_call`方法中实现工具逻辑。

### 添加新资源

在`handle_resources_list`和`handle_resources_read`方法中添加新资源。

### 添加新提示模板

在`handle_prompts_list`和`handle_prompts_get`方法中添加新提示模板。

## 参考资源

- [MCP官方文档](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0规范](https://www.jsonrpc.org/specification)
- [Lynette项目文档](../README.md)

