"""
Lynette MCP服务器
实现Model Context Protocol，将Lynette编译器功能暴露为MCP工具
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from lynette_agent.service import CompileService, AnalyzeService, DeployService


class MCPServer:
    """MCP服务器实现
    
    基于JSON-RPC 2.0协议，实现MCP标准接口
    """
    
    def __init__(self):
        """初始化MCP服务器"""
        self.compile_service = CompileService()
        self.analyze_service = AnalyzeService()
        self.deploy_service = DeployService()
        self.running = True
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求
        
        Args:
            request: JSON-RPC 2.0格式的请求
            
        Returns:
            JSON-RPC 2.0格式的响应
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list()
            elif method == "tools/call":
                result = await self.handle_tools_call(params)
            elif method == "resources/list":
                result = await self.handle_resources_list()
            elif method == "resources/read":
                result = await self.handle_resources_read(params)
            elif method == "prompts/list":
                result = await self.handle_prompts_list()
            elif method == "prompts/get":
                result = await self.handle_prompts_get(params)
            else:
                raise ValueError(f"未知的方法: {method}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理initialize请求"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "serverInfo": {
                "name": "lynette-mcp-server",
                "version": "0.1.0"
            }
        }
    
    async def handle_tools_list(self) -> Dict[str, Any]:
        """返回所有可用的工具列表"""
        return {
            "tools": [
                {
                    "name": "compile_pne",
                    "description": "编译PNE文件为P4代码。支持debug模式（单文件编译）和service模式（完整服务编译）。",
                    "inputSchema": {
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
                },
                {
                    "name": "deploy_p4",
                    "description": "部署P4代码或表项到网络设备。可以部署代码、表项或两者。",
                    "inputSchema": {
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
                                "items": {"type": "string"},
                                "description": "要部署的节点列表，如果未提供则部署所有节点"
                            },
                            "port": {
                                "type": "integer",
                                "description": "目标设备端口，默认为13345"
                            }
                        },
                        "required": ["output_dir", "deploy_type"]
                    }
                },
                {
                    "name": "analyze_pne",
                    "description": "分析PNE代码结构，包括语法检查、服务/应用/模块提取、依赖关系分析等。",
                    "inputSchema": {
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
                },
                {
                    "name": "check_compile_status",
                    "description": "查询编译任务的状态和结果。",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "编译任务ID"
                            }
                        },
                        "required": ["task_id"]
                    }
                },
                {
                    "name": "validate_p4",
                    "description": "使用p4test验证P4代码的正确性。",
                    "inputSchema": {
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
            ]
        }
    
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "compile_pne":
            result = self.compile_service.compile(
                mode=arguments.get("mode"),
                input_file=arguments.get("input_file"),
                config_file=arguments.get("config_file"),
                output_dir=arguments.get("output_dir", "./pne_out"),
                target=arguments.get("target", "v1model"),
                p4_only=arguments.get("p4_only", False),
                check=arguments.get("check", False)
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, ensure_ascii=False)
                    }
                ]
            }
        
        elif tool_name == "deploy_p4":
            result = self.deploy_service.deploy(
                output_dir=arguments.get("output_dir"),
                deploy_type=arguments.get("deploy_type"),
                nodes=arguments.get("nodes"),
                port=arguments.get("port", 13345)
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, ensure_ascii=False)
                    }
                ]
            }
        
        elif tool_name == "analyze_pne":
            result = self.analyze_service.analyze(
                input_file=arguments.get("input_file"),
                analysis_type=arguments.get("analysis_type", "all")
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, ensure_ascii=False)
                    }
                ]
            }
        
        elif tool_name == "check_compile_status":
            status = self.compile_service.get_task_status(
                task_id=arguments.get("task_id")
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(status, indent=2, ensure_ascii=False)
                    }
                ]
            }
        
        elif tool_name == "validate_p4":
            # 这里应该调用p4test进行验证
            # 为了简化，这里只返回一个占位结果
            p4_file = arguments.get("p4_file")
            target = arguments.get("target", "v1model")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"验证P4文件: {p4_file} (目标: {target})\n注意: 实际验证功能需要p4test工具"
                    }
                ]
            }
        
        else:
            raise ValueError(f"未知的工具: {tool_name}")
    
    async def handle_resources_list(self) -> Dict[str, Any]:
        """返回可用的资源列表"""
        return {
            "resources": [
                {
                    "uri": "lynette://examples",
                    "name": "Lynette示例文件",
                    "description": "访问Lynette项目中的示例PNE文件",
                    "mimeType": "text/plain"
                }
            ]
        }
    
    async def handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """读取资源内容"""
        uri = params.get("uri")
        
        if uri == "lynette://examples":
            # 返回示例文件列表
            examples_dir = os.path.join(parent_dir, "input")
            examples = []
            if os.path.exists(examples_dir):
                for file in os.listdir(examples_dir):
                    if file.endswith(".pne"):
                        examples.append(file)
            
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": "\n".join(examples) if examples else "未找到示例文件"
                    }
                ]
            }
        
        raise ValueError(f"未知的资源URI: {uri}")
    
    async def handle_prompts_list(self) -> Dict[str, Any]:
        """返回可用的提示模板列表"""
        return {
            "prompts": [
                {
                    "name": "compile_pne_template",
                    "description": "编译PNE文件的提示模板",
                    "arguments": [
                        {
                            "name": "input_file",
                            "description": "要编译的PNE文件路径",
                            "required": True
                        },
                        {
                            "name": "mode",
                            "description": "编译模式（debug或service）",
                            "required": False
                        }
                    ]
                },
                {
                    "name": "analyze_pne_template",
                    "description": "分析PNE代码的提示模板",
                    "arguments": [
                        {
                            "name": "input_file",
                            "description": "要分析的PNE文件路径",
                            "required": True
                        }
                    ]
                }
            ]
        }
    
    async def handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取提示模板内容"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if prompt_name == "compile_pne_template":
            input_file = arguments.get("input_file", "未指定")
            mode = arguments.get("mode", "debug")
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"请编译PNE文件: {input_file}，使用{mode}模式"
                        }
                    }
                ]
            }
        
        elif prompt_name == "analyze_pne_template":
            input_file = arguments.get("input_file", "未指定")
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"请分析PNE文件: {input_file}，包括语法检查、代码结构分析和依赖关系分析"
                        }
                    }
                ]
            }
        
        raise ValueError(f"未知的提示模板: {prompt_name}")
    
    async def run(self):
        """运行MCP服务器（标准输入/输出模式）"""
        while self.running:
            try:
                # 从标准输入读取请求
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # 解析JSON请求
                request = json.loads(line)
                
                # 处理请求
                response = await self.handle_request(request)
                
                # 发送响应到标准输出
                print(json.dumps(response, ensure_ascii=False))
                sys.stdout.flush()
            
            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"JSON解析错误: {str(e)}"
                    }
                }
                print(json.dumps(error_response, ensure_ascii=False))
                sys.stdout.flush()
            
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"内部错误: {str(e)}"
                    }
                }
                print(json.dumps(error_response, ensure_ascii=False))
                sys.stdout.flush()


async def main():
    """主函数"""
    server = MCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

