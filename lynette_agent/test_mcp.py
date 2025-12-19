"""
MCP服务器测试脚本
用于测试MCP服务器的功能
"""

import asyncio
import json
from lynette_agent.mcp_server import MCPServer


async def test_mcp_server():
    """测试MCP服务器"""
    server = MCPServer()
    
    # 测试initialize
    print("测试 initialize...")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    response = await server.handle_request(init_request)
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print()
    
    # 测试tools/list
    print("测试 tools/list...")
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    response = await server.handle_request(tools_request)
    print(f"可用工具数量: {len(response['result']['tools'])}")
    for tool in response['result']['tools']:
        print(f"  - {tool['name']}: {tool['description']}")
    print()
    
    # 测试tools/call - compile_pne
    print("测试 tools/call - compile_pne...")
    compile_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "compile_pne",
            "arguments": {
                "mode": "debug",
                "input_file": "input/Alice_main.pne",
                "output_dir": "test_output",
                "target": "v1model"
            }
        }
    }
    response = await server.handle_request(compile_request)
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print()
    
    # 测试resources/list
    print("测试 resources/list...")
    resources_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "resources/list",
        "params": {}
    }
    response = await server.handle_request(resources_request)
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print()
    
    # 测试prompts/list
    print("测试 prompts/list...")
    prompts_request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "prompts/list",
        "params": {}
    }
    response = await server.handle_request(prompts_request)
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print()
    
    print("所有测试完成！")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())

