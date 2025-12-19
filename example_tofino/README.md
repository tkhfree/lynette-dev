# Tofino 交换机示例项目

这是一个完整的 PNE 示例项目，演示如何编译并部署到 Tofino 交换机。

## 📋 项目结构

```
example_tofino/
├── Example_main.pne          # 主 PNE 文件
├── service.json              # 服务配置
├── topology.json             # 网络拓扑配置
├── include/
│   └── standard_headers.pne  # 标准头部定义
├── path/
│   └── path.json            # 路径配置（自动生成）
└── README.md                 # 本文件
```

## 🎯 功能说明

本示例实现了一个简单的 IPv4 路由器，包含以下功能：

### 1. **IPv4 转发模块** (`IPv4Forwarding`)
- ✅ IPv4 LPM（最长前缀匹配）路由表
- ✅ TTL 递减和检查
- ✅ 路由查找和转发
- ✅ 无效数据包丢弃

### 2. **流量统计模块** (`TrafficCounter`)
- ✅ 数据包计数
- ✅ 字节计数
- ✅ 基于源 IP 的统计

### 3. **应用组合** (`SimpleRouter`)
- ✅ 先统计后转发
- ✅ 模块化设计

## 🚀 快速开始

### 方法一：使用自动路径生成（推荐）

```bash
# 1. 生成 path.json
cd example_tofino
python3 ../generate_path.py service.json topology.json path/path.json

# 2. 编译为 Tofino P4 代码
python3 -m lynette --config service.json --output-dir pne_out --target tna

# 3. 查看生成的 P4 文件
ls pne_out/
# 应该看到: tofino1.p4, tofino2.p4, tofino3.p4
```

### 方法二：使用 Debug 模式快速测试

```bash
cd example_tofino

# Debug 模式（自动生成配置）
python3 -m lynette --debug-main Example_main.pne --output-dir pne_out --target tna

# 查看生成的配置
cat service.json
cat path/path.json

# 正式编译
python3 -m lynette --config service.json --output-dir pne_out --target tna
```

## 📦 生成的文件

编译成功后，`pne_out/` 目录包含：

```
pne_out/
├── tofino1.p4           # Tofino1 交换机的 P4 程序
├── tofino2.p4           # Tofino2 交换机的 P4 程序
├── tofino3.p4           # Tofino3 交换机的 P4 程序
├── tofino1_entry.json   # Tofino1 的表项配置
├── tofino2_entry.json   # Tofino2 的表项配置
└── tofino3_entry.json   # Tofino3 的表项配置
```

## 🔧 部署到 Tofino 交换机

### 1. 编译 P4 程序

使用 Barefoot SDE (Software Development Environment):

```bash
# 设置 SDE 环境变量
export SDE=/path/to/bf-sde-9.x.x
export SDE_INSTALL=$SDE/install
export PATH=$SDE_INSTALL/bin:$PATH

# 编译 P4 程序
cd pne_out
bf-p4c tofino1.p4 \
    --target tofino \
    --arch tna \
    -o tofino1.out \
    --p4runtime-files tofino1.p4info.txt \
    --bf-rt-schema tofino1.bfrt.json

# 重复编译其他节点的 P4 程序
bf-p4c tofino2.p4 --target tofino --arch tna -o tofino2.out
bf-p4c tofino3.p4 --target tofino --arch tna -o tofino3.out
```

### 2. 部署到交换机

```bash
# 方法 A: 使用 run_switchd.sh（开发测试）
cd $SDE_INSTALL
./run_switchd.sh -p tofino1

# 方法 B: 使用 bfshell（生产环境）
bfshell
> ucli
bf-sde> pm
bf-sde.pm> port-add 1/0 100G NONE
bf-sde.pm> port-enb 1/0
bf-sde.pm> an-set 1/0 2
bf-sde.pm> show
```

### 3. 安装表项

使用 P4Runtime 或 bfrt_python:

```bash
# 使用 bfrt_python
cd $SDE_INSTALL
./run_bfshell.sh -b bfrt_python/tofino1_entry.py
```

## 🧪 测试

### 1. 生成测试数据包

```bash
# 使用 scapy 生成测试数据包
python3 << EOF
from scapy.all import *

# 创建 IPv4 数据包
pkt = Ether(dst="00:11:22:33:44:55", src="aa:bb:cc:dd:ee:ff") / \
      IP(src="10.0.0.1", dst="10.0.0.2", ttl=64) / \
      UDP(sport=12345, dport=80) / \
      Raw(load="Hello Tofino!")

# 保存为 pcap 文件
wrpcap("test_packet.pcap", pkt)
EOF
```

### 2. 发送测试数据包

```bash
# 方法 A: 使用 PTF (Packet Test Framework)
cd $SDE/pkgsrc/p4-examples/ptf-tests
./run-test.sh --test-dir tofino1 --arch tofino

# 方法 B: 使用 tcpreplay
sudo tcpreplay -i eth0 test_packet.pcap
```

### 3. 验证结果

```bash
# 在 bfshell 中查看统计信息
bf-sde> bfrt
bfrt> show
```

## 📊 网络拓扑

```
    [Host1] ─────┐
                 │
              [Tofino1] ───── [Tofino2] ───── [Tofino3]
                 │                               │
    [Host2] ─────┘                               └───── [Host4]
                                                 │
                                       [Host3] ──┘
```

## 🎓 关键概念

### PNE vs P4

| 特性 | PNE | P4 |
|------|-----|-----|
| **抽象层次** | 网络级 | 设备级 |
| **编程对象** | 整个网络拓扑 | 单个交换机 |
| **路径管理** | 自动计算和分配 | 手动配置 |
| **代码复用** | 模块化设计 | 需要复制粘贴 |

### 模块化设计

```pne
module IPv4Forwarding() {
    parser { ... }
    control { ... }
}

module TrafficCounter() {
    control { ... }
}

application SimpleRouter {
    TrafficCounter.apply();    // 可复用
    IPv4Forwarding.apply();    // 可复用
}
```

### 数据结构映射

| PNE | P4 (TNA) |
|-----|----------|
| `map<K,V>` | `table` + `action` |
| `set<K>` | `table` (只匹配) |
| `static T reg[N]` | `Register<T>(N)` |
| `tuple` | `struct` |

## 🔍 故障排除

### 问题 1: 编译失败

```bash
# 检查 PNE 语法
python3 -m lynette --debug-main Example_main.pne --p4

# 查看详细日志
cat log_out/log.txt
```

### 问题 2: 生成的 P4 代码有错误

```bash
# 使用 p4test 验证
p4test pne_out/tofino1.p4 --std p4-16

# 使用 bf-p4c 编译器检查
bf-p4c pne_out/tofino1.p4 --target tofino --arch tna
```

### 问题 3: Tofino 交换机加载失败

```bash
# 检查 SDE 版本
echo $SDE

# 查看交换机日志
tail -f /var/log/bf_switchd.log

# 检查端口状态
bf-sde.pm> show -a
```

## 📚 进一步学习

### 相关文档

- [PNE 语言参考](../README.md)
- [Lynette 架构文档](../ARCHITECTURE.md)
- [开发指南](../DEVELOPMENT_GUIDE.md)
- [路径生成器指南](../PATH_GENERATOR_GUIDE.md)

### Tofino 资源

- Intel Tofino Developer Documentation
- Barefoot SDE Guide
- TNA (Tofino Native Architecture) Specification
- P4 Language Specification (v1.2.0+)

## 💡 最佳实践

1. **开发流程**
   - 先使用 Debug 模式快速测试
   - 确认功能正确后使用 Service 模式
   - 部署前在模拟器中验证

2. **性能优化**
   - 合理设置表大小
   - 避免深层嵌套的条件判断
   - 使用寄存器而不是元数据存储状态

3. **调试技巧**
   - 使用 `assert()` 进行运行时检查
   - 添加计数器监控关键路径
   - 利用 Tofino Model 进行离线测试

## 🎉 成功！

如果一切顺利，你现在应该有一个运行在 Tofino 交换机上的 P4 程序了！

需要帮助？查看文档或提交 Issue。

