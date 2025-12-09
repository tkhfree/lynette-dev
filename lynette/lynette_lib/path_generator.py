"""path_generator.py - 自动路径生成器

功能说明：
    根据 service.json 和 topology.json 自动生成 path.json
    减少人工配置，提高编译效率
    
主要功能：
    1. 从 topology.json 构建网络图
    2. 根据 service.json 中的起点和终点计算最短路径
    3. 提取路径上的端口号
    4. 自动分配 IP 地址和表资源
    5. 生成完整的 path.json
"""

import json
import os
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional


class NetworkGraph:
    """网络拓扑图类，用于路径查找"""
    
    def __init__(self):
        """初始化网络图结构"""
        self.graph = defaultdict(dict)  # {src_device: {dst_device: port}}
        self.devices = set()
        
    def add_link(self, src_device: str, dst_device: str, src_port: str):
        """添加链路到图中
        
        Args:
            src_device: 源设备名称
            dst_device: 目标设备名称  
            src_port: 源设备的出端口
        """
        self.graph[src_device][dst_device] = src_port
        self.devices.add(src_device)
        self.devices.add(dst_device)
    
    def find_shortest_path(self, start: str, end: str) -> Optional[List[str]]:
        """使用 BFS 查找最短路径
        
        Args:
            start: 起点设备名称
            end: 终点设备名称
            
        Returns:
            路径节点列表，如果不存在路径则返回 None
        """
        if start not in self.devices or end not in self.devices:
            return None
            
        if start == end:
            return [start]
        
        # BFS 搜索
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            # 检查当前节点的所有邻居
            for neighbor in self.graph[current]:
                if neighbor == end:
                    return path + [neighbor]
                    
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None  # 没有找到路径
    
    def get_port(self, src: str, dst: str) -> Optional[str]:
        """获取从源设备到目标设备的端口号
        
        Args:
            src: 源设备名称
            dst: 目标设备名称
            
        Returns:
            端口号字符串，如果链路不存在则返回 None
        """
        return self.graph[src].get(dst)


class PathGenerator:
    """路径配置生成器"""
    
    def __init__(self, service_json_path: str, topology_json_path: str):
        """初始化生成器
        
        Args:
            service_json_path: service.json 文件路径
            topology_json_path: topology.json 文件路径
        """
        self.service_json_path = service_json_path
        self.topology_json_path = topology_json_path
        self.network_graph = NetworkGraph()
        self.device_info = {}
        
    def load_topology(self) -> Dict:
        """加载拓扑配置
        
        Returns:
            拓扑配置字典
        """
        with open(self.topology_json_path, 'r', encoding='utf-8') as f:
            topology = json.load(f)
        
        # 构建网络图
        for link in topology.get('links', []):
            src_device = link['src']['device']
            dst_device = link['dst']['device']
            src_port = link['src']['port']
            
            # 提取端口号（处理 "[s1-eth2](2)" 格式）
            port_num = self._extract_port_number(src_port)
            
            self.network_graph.add_link(src_device, dst_device, port_num)
        
        # 保存设备信息
        self.device_info = topology.get('deviceStaticInfo', {})
        
        return topology
    
    def load_service(self) -> Dict:
        """加载服务配置
        
        Returns:
            服务配置字典
        """
        with open(self.service_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _extract_port_number(self, port_str: str) -> str:
        """从端口字符串中提取端口号
        
        支持格式：
        - "[s1-eth2](2)" -> "2"
        - "2" -> "2"
        - "12" -> "12"
        
        Args:
            port_str: 端口字符串
            
        Returns:
            提取的端口号
        """
        import re
        
        # 尝试匹配 "(数字)" 格式
        match = re.search(r'\((\d+)\)', port_str)
        if match:
            return match.group(1)
        
        # 直接返回（假设是纯数字）
        return str(port_str).strip()
    
    def _generate_ip_address(self, device_name: str, base_ip: str = "192.168.0") -> str:
        """为设备生成 IP 地址
        
        Args:
            device_name: 设备名称（如 s1, s2）
            base_ip: IP 地址前缀
            
        Returns:
            生成的 IP 地址
        """
        # 从设备名中提取数字
        import re
        match = re.search(r'\d+', device_name)
        if match:
            device_num = match.group(0)
            return f"{base_ip}.{device_num}"
        
        # 默认 IP
        return f"{base_ip}.100"
    
    def _get_table_count(self, device_name: str) -> int:
        """获取设备的表数量限制
        
        根据设备型号推断或使用默认值
        
        Args:
            device_name: 设备名称
            
        Returns:
            表数量限制
        """
        # 可以根据 deviceStaticInfo 中的型号推断
        device_info = self.device_info.get(device_name, {})
        device_model = device_info.get('设备型号', '')
        
        # 根据设备型号设置不同的表数量
        if 'A1000' in device_model:
            return 8  # 较小型号
        elif 'B1000' in device_model:
            return 12  # 较大型号
        else:
            return 6  # 默认值
    
    def generate_path_for_service(self, service_name: str, service_hosts: List[Dict]) -> Dict:
        """为单个服务生成路径配置
        
        Args:
            service_name: 服务名称
            service_hosts: 服务的主机列表
            
        Returns:
            该服务的路径配置字典
        """
        if len(service_hosts) < 2:
            print(f"⚠️  Service '{service_name}' has less than 2 hosts, using first host only")
            start_device = service_hosts[0]['device_uuid']
            return {
                start_device: {
                    "next": {},
                    "tables": self._get_table_count(start_device),
                    "ip": self._generate_ip_address(start_device)
                }
            }
        
        # 获取起点和终点
        start_device = service_hosts[0]['device_uuid']
        end_device = service_hosts[-1]['device_uuid']
        
        # 查找路径
        path = self.network_graph.find_shortest_path(start_device, end_device)
        
        if not path:
            print(f"❌ No path found from {start_device} to {end_device}")
            return {}
        
        print(f"✅ Found path for '{service_name}': {' -> '.join(path)}")
        
        # 构建路径配置
        path_config = {}
        
        for i, node in enumerate(path):
            node_config = {
                "tables": self._get_table_count(node),
                "ip": self._generate_ip_address(node)
            }
            
            # 设置下一跳
            if i < len(path) - 1:
                next_node = path[i + 1]
                port = self.network_graph.get_port(node, next_node)
                
                if port:
                    node_config["next"] = {next_node: int(port)}
                else:
                    print(f"⚠️  No port found from {node} to {next_node}, using default")
                    node_config["next"] = {next_node: 1}
            else:
                # 最后一个节点没有下一跳
                node_config["next"] = {}
            
            path_config[node] = node_config
        
        return path_config
    
    def generate(self, output_path: str = "path/path.json") -> Dict:
        """生成完整的 path.json 配置
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            生成的路径配置字典
        """
        print("🔄 Loading topology...")
        self.load_topology()
        
        print("🔄 Loading service configuration...")
        service_config = self.load_service()
        
        print("🔄 Generating path configurations...\n")
        
        path_json = {}
        
        # 遍历所有用户和服务
        for user, user_config in service_config.items():
            services = user_config.get('services', [])
            
            for service in services:
                service_name = service.get('service_name')
                service_hosts = service.get('service_hosts', [])
                
                if not service_name:
                    continue
                
                print(f"📍 Processing service: {service_name}")
                
                # 生成路径配置
                path_config = self.generate_path_for_service(service_name, service_hosts)
                
                if path_config:
                    path_json[service_name] = path_config
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(path_json, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ Path configuration generated: {output_path}")
        
        return path_json


def generate_path_json(service_json_path: str, 
                       topology_json_path: str, 
                       output_path: str = "path/path.json") -> Dict:
    """便捷函数：生成 path.json
    
    Args:
        service_json_path: service.json 文件路径
        topology_json_path: topology.json 文件路径
        output_path: 输出文件路径
        
    Returns:
        生成的路径配置字典
    """
    generator = PathGenerator(service_json_path, topology_json_path)
    return generator.generate(output_path)


if __name__ == '__main__':
    """测试代码"""
    import sys
    
    # 默认路径
    service_json = "service.json"
    topology_json = "topology.json"
    output = "path/path.json"
    
    # 解析命令行参数
    if len(sys.argv) >= 3:
        service_json = sys.argv[1]
        topology_json = sys.argv[2]
    if len(sys.argv) >= 4:
        output = sys.argv[3]
    
    print("=" * 60)
    print("Path Generator - 自动路径配置生成器")
    print("=" * 60)
    print(f"Service Config: {service_json}")
    print(f"Topology Config: {topology_json}")
    print(f"Output: {output}")
    print("=" * 60)
    print()
    
    try:
        result = generate_path_json(service_json, topology_json, output)
        print("\n" + "=" * 60)
        print("✅ Generation completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

