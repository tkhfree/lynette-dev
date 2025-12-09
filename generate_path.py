#!/usr/bin/env python3
"""
generate_path.py - Path.json 自动生成工具

用法:
    python3 generate_path.py <service.json> <topology.json> [output_path]

示例:
    python3 generate_path.py input/service.json input/topology.json
    python3 generate_path.py input/service.json input/topology.json custom/path.json
"""

import sys
import os

# 添加 lynette 包到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lynette'))

from lynette_lib.path_generator import generate_path_json


def print_usage():
    """打印使用说明"""
    print("=" * 70)
    print("Path.json 自动生成工具")
    print("=" * 70)
    print("\n用法:")
    print("  python3 generate_path.py <service.json> <topology.json> [output_path]")
    print("\n参数:")
    print("  service.json   - 服务配置文件路径")
    print("  topology.json  - 网络拓扑文件路径")
    print("  output_path    - 输出文件路径 (可选，默认: path/path.json)")
    print("\n示例:")
    print("  python3 generate_path.py input/service.json input/topology.json")
    print("  python3 generate_path.py input/service.json input/topology.json input/path/path.json")
    print("=" * 70)


def main():
    """主函数"""
    # 检查参数
    if len(sys.argv) < 3:
        print("❌ 错误: 缺少必要参数\n")
        print_usage()
        sys.exit(1)
    
    service_json = sys.argv[1]
    topology_json = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) >= 4 else "path/path.json"
    
    # 检查文件是否存在
    if not os.path.exists(service_json):
        print(f"❌ 错误: 找不到文件 '{service_json}'")
        sys.exit(1)
    
    if not os.path.exists(topology_json):
        print(f"❌ 错误: 找不到文件 '{topology_json}'")
        sys.exit(1)
    
    # 打印配置
    print("=" * 70)
    print("Path.json 自动生成工具")
    print("=" * 70)
    print(f"📄 Service 配置: {service_json}")
    print(f"🌐 Topology 配置: {topology_json}")
    print(f"📤 输出文件: {output}")
    print("=" * 70)
    print()
    
    # 生成 path.json
    try:
        result = generate_path_json(service_json, topology_json, output)
        
        print("\n" + "=" * 70)
        print("✅ 生成成功！")
        print("=" * 70)
        print(f"\n生成了 {len(result)} 个服务的路径配置:")
        for service_name in result:
            nodes = list(result[service_name].keys())
            print(f"  • {service_name}: {' → '.join(nodes)}")
        
        print(f"\n✅ 配置已保存到: {output}")
        print("\n💡 提示: 现在可以运行编译器了:")
        print(f"   python3 -m lynette --config {service_json}")
        
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

