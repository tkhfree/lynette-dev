#!/bin/bash
# Lynette MCP服务器启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# 设置PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# 启动MCP服务器
python -m lynette_agent.mcp_server

