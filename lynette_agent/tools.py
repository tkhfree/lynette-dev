"""
Lynette Agent工具函数定义
用于Function Calling机制
"""

def get_tools_definition():
    """获取所有工具函数的定义，用于OpenAI Function Calling"""
    return [
        {
            "type": "function",
            "function": {
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
        },
        {
            "type": "function",
            "function": {
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
        },
        {
            "type": "function",
            "function": {
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
        },
        {
            "type": "function",
            "function": {
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
        },
        {
            "type": "function",
            "function": {
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
        }
    ]














