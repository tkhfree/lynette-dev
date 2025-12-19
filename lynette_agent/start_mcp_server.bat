@echo off
REM Lynette MCP服务器启动脚本 (Windows)

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

REM 设置PYTHONPATH
set PYTHONPATH=%PROJECT_DIR%;%PYTHONPATH%

REM 启动MCP服务器
python -m lynette_agent.mcp_server

