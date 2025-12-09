# Path.json 自动生成器使用指南

## 📌 概述

Path.json 自动生成器可以根据 `service.json` 和 `topology.json` 自动生成准确的 `path.json` 配置，无需手动编辑，大幅减少人工介入。

## 🎯 核心功能

### 1. **自动路径查找**
- 使用 BFS 算法查找最短路径
- 支持任意网络拓扑
- 自动处理多跳路由

### 2. **端口号提取**
- 自动从 topology.json 提取端口信息
- 支持多种端口格式：`"[s1-eth2](2)"` → `2`

### 3. **IP 地址生成**
- 自动为每个节点分配 IP 地址
- 基于节点名称生成（如 s1 → 192.168.0.1）

### 4. **表资源管理**
- 根据设备型号自动设置表数量限制
- 支持不同型号的差异化配置

## 📋 使用方法

### 方式一：独立命令行工具

```bash
# 基本用法
python3 generate_path.py input/service.json input/topology.json

# 指定输出路径
python3 generate_path.py input/service.json input/topology.json custom/path.json
```

### 方式二：集成到编译流程（自动）

在 Debug 模式下，如果检测到 `topology.json` 存在，会自动调用生成器：

```bash
# Debug 模式编译
python3 -m lynette --debug-main Alice_main.pne

# 编译器会自动：
# 1. 检测 topology.json
# 2. 生成 service.json
# 3. 自动生成 path.json（而不是模板）
# 4. 无需手动编辑即可继续编译
```

### 方式三：在代码中使用

```python
from lynette_lib.path_generator import generate_path_json

# 生成 path.json
result = generate_path_json(
    service_json_path="input/service.json",
    topology_json_path="input/topology.json",
    output_path="path/path.json"
)

print(f"Generated paths for {len(result)} services")
```

## 📂 输入文件格式

### service.json

```json
{
    "Alice": {
        "services": [
            {
                "service_name": "Alice_geo",
                "service_domain": "geo",
                "service_hosts": [
                    {
                        "device_uuid": "s1",
                        "ports": {"h1": 21}
                    },
                    {
                        "device_uuid": "s4",
                        "ports": {"h2": 22}
                    }
                ],
                "applications": ["Router"]
            }
        ]
    }
}
```

**关键字段：**
- `service_name`: 服务名称（必需）
- `service_hosts`: 服务涉及的设备列表（必需）
  - 第一个设备：起点
  - 最后一个设备：终点
  - 系统会自动计算中间路径

### topology.json

```json
{
    "devices": ["s1", "s2", "s3", "s4"],
    "links": [
        {
            "src": {
                "device": "s1",
                "port": "[s1-eth2](2)"
            },
            "dst": {
                "device": "s2",
                "port": "1"
            },
            "bandwidth": 9999999
        }
    ],
    "deviceStaticInfo": {
        "s1": {
            "设备型号": "PINE-A1000-T32X8A",
            "设备形态": "1U机架设备"
        }
    }
}
```

**关键字段：**
- `devices`: 设备列表
- `links`: 设备间的链路（用于路径查找）
- `deviceStaticInfo`: 设备详细信息（用于推断资源限制）

## 📤 输出文件格式

生成的 `path.json`：

```json
{
    "Alice_geo": {
        "s1": {
            "next": {"s2": 2},
            "tables": 8,
            "ip": "192.168.0.1"
        },
        "s2": {
            "next": {"s4": 2},
            "tables": 12,
            "ip": "192.168.0.2"
        },
        "s4": {
            "next": {},
            "tables": 8,
            "ip": "192.168.0.4"
        }
    }
}
```

## 🔧 高级配置

### 自定义 IP 地址前缀

编辑 `path_generator.py`，修改 `_generate_ip_address` 方法：

```python
def _generate_ip_address(self, device_name: str, base_ip: str = "10.0.0") -> str:
    # 修改 base_ip 为你的网络前缀
    ...
```

### 自定义表数量规则

编辑 `path_generator.py`，修改 `_get_table_count` 方法：

```python
def _get_table_count(self, device_name: str) -> int:
    device_info = self.device_info.get(device_name, {})
    device_model = device_info.get('设备型号', '')
    
    # 添加自定义规则
    if 'CustomModel' in device_model:
        return 16
    # ...
```

## 📊 工作流程

```
┌─────────────────┐
│  service.json   │  提供服务配置和起点/终点
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│ topology.json   │  │ Path Generator   │
│                 │  │                  │
│ • 设备列表      │  │ 1. 构建网络图    │
│ • 链路信息      ├─→│ 2. BFS 路径查找  │
│ • 端口配置      │  │ 3. 提取端口号    │
│ • 设备型号      │  │ 4. 生成 IP       │
└─────────────────┘  │ 5. 设置表限制    │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   path.json     │
                     │                 │
                     │ 准确的路径配置  │
                     │ 无需手动编辑    │
                     └─────────────────┘
```

## ✅ 优势对比

| 特性 | 手动配置 | 自动生成 |
|------|---------|---------|
| **准确性** | ❌ 容易出错 | ✅ 自动计算，准确 |
| **效率** | ❌ 耗时，需要手动计算路径 | ✅ 秒级完成 |
| **维护性** | ❌ 拓扑变化需要重新配置 | ✅ 重新运行即可 |
| **可扩展性** | ❌ 节点多时难以管理 | ✅ 支持任意规模 |
| **端口配置** | ❌ 需要查找拓扑文件 | ✅ 自动提取 |
| **IP 分配** | ❌ 手动分配 | ✅ 自动生成 |

## 🎯 使用场景

### 场景 1：开发新项目

```bash
# 1. 准备拓扑
vim topology.json

# 2. 编写 PNE 代码
vim Alice_main.pne

# 3. Debug 编译（自动生成配置）
python3 -m lynette --debug-main Alice_main.pne

# 4. 无需编辑，直接编译
python3 -m lynette --config service.json
```

### 场景 2：拓扑变化

```bash
# 1. 更新拓扑
vim topology.json  # 添加/删除节点或链路

# 2. 重新生成路径
python3 generate_path.py service.json topology.json

# 3. 重新编译
python3 -m lynette --config service.json
```

### 场景 3：多服务部署

```bash
# service.json 包含多个服务
{
    "Alice": {"services": [...]},
    "Bob": {"services": [...]},
    "Charlie": {"services": [...]}
}

# 一次性生成所有服务的路径
python3 generate_path.py service.json topology.json

# 生成的 path.json 包含所有服务
{
    "Alice_geo": {...},
    "Bob_mf": {...},
    "Charlie_ip": {...}
}
```

## 🔍 故障排除

### 问题 1：找不到路径

```
❌ No path found from s1 to s4
```

**原因：** 拓扑中不存在从 s1 到 s4 的连通路径

**解决：** 
- 检查 topology.json 中的 links
- 确保起点和终点之间有连通的链路

### 问题 2：端口号错误

```
⚠️  No port found from s1 to s2, using default
```

**原因：** 链路定义中缺少端口信息

**解决：** 
- 检查 topology.json 中对应链路的 src.port 字段
- 确保端口格式正确

### 问题 3：KeyError

```
KeyError: 'Alice_geo'
```

**原因：** service.json 中的服务名与 path.json 中的不匹配

**解决：** 
- 重新运行生成器
- 确保 service.json 中的 service_name 字段正确

## 📝 最佳实践

1. **保持拓扑文件最新**
   - 每次网络变化后及时更新 topology.json
   - 运行生成器重新生成 path.json

2. **版本控制**
   - 将 topology.json 纳入版本控制
   - 可以选择性地忽略 path.json（因为可以自动生成）

3. **验证生成结果**
   - 生成后检查输出的路径是否符合预期
   - 验证端口号和 IP 地址

4. **备份配置**
   - 如果手动调整了 path.json，记得备份
   - 重新生成会覆盖现有文件

## 🚀 下一步

- 现在可以开始使用自动生成器了！
- 查看项目中的示例：`input/` 目录
- 参考主文档：`README.md` 和 `DEVELOPMENT_GUIDE.md`

## 📞 反馈

如果遇到问题或有改进建议，欢迎提出 Issue！

