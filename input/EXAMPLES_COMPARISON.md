# Lynette PNE 示例对比文档

本文档对比了两个基于 Lynette PNE 语言实现的网络协议示例：**NDN（命名数据网络）**和 **GeoNetworking（地理位置路由）**，展示了如何在 P4 可编程交换机上实现不同的创新网络架构。

---

## 📊 概览对比

| 维度 | NDN 示例 | GeoNetworking 示例 |
|------|----------|-------------------|
| **应用领域** | 内容分发、边缘计算 | 车联网（V2X）、智能交通 |
| **核心思想** | 以内容名字为中心 | 以地理位置为中心 |
| **标准依据** | NFD Developer's Guide | ETSI EN 302 636 |
| **交换机数量** | 3 个（内容网络） | 5 个（路口RSU） |
| **拓扑类型** | 三角形拓扑 | 星型拓扑 |
| **路由方式** | 基于名字前缀匹配 | 基于地理位置贪婪转发 |
| **典型延迟要求** | < 100ms（普通内容） | < 50ms（紧急消息） |

---

## 🏗️ 架构对比

### NDN 架构

```
应用层: 内容请求/响应
   ↓
网络层: Interest/Data 包处理
   ↓
核心组件:
   ├─ Content Store (CS)      - 内容缓存
   ├─ PIT                     - 待处理兴趣表
   └─ FIB                     - 转发信息库
```

### GeoNetworking 架构

```
应用层: CAM/DENM/SPAT
   ↓
传输层: BTP
   ↓
网络层: GeoNetworking
   ↓
核心组件:
   ├─ LocationTable           - 位置表
   ├─ GeoAreaCheck           - 区域检查
   └─ GreedyForwarding       - 贪婪转发
```

---

## 🔄 转发流程对比

### NDN Interest 转发流程

```
1. 接收 Interest
   ↓
2. CS 查找（缓存命中？）
   ├─ 命中 → 返回 Data
   └─ 未命中 ↓
3. PIT 查找（已有相同请求？）
   ├─ 已有 → 聚合 Interest
   └─ 没有 ↓
4. FIB 查找
   ↓
5. 转发到下一跳
   ↓
6. 记录到 PIT
```

### GeoNetworking GeoBroadcast 转发流程

```
1. 接收 GBC 消息
   ↓
2. 检查剩余跳数
   ↓
3. 序列号检查（防重复）
   ↓
4. 更新位置表
   ↓
5. 地理区域检查
   ├─ 在区域内 → 广播
   └─ 不在区域内 ↓
6. 贪婪转发（选最近邻居）
   ↓
7. 转发数据包
```

---

## 📦 数据包格式对比

### NDN Interest 包

```
+------------------+
| Ethernet Header  | 14 bytes
+------------------+
| NDN Interest     |
|  - Type: 0x05    | 1 byte
|  - Name          | 变长（这里简化为32字节）
|  - Nonce         | 4 bytes
|  - Lifetime      | 4 bytes
+------------------+
```

### GeoNetworking GBC 包

```
+------------------+
| Ethernet Header  | 14 bytes
+------------------+
| Basic Header     | 5 bytes
+------------------+
| Common Header    | 8 bytes
+------------------+
| GBC Extended     |
|  - SeqNum        | 2 bytes
|  - Src Position  | 24 bytes（位置向量）
|  - Target Area   | 16 bytes（目标区域）
+------------------+
```

---

## 🎯 核心数据结构对比

### NDN

| 数据结构 | 容量 | 作用 | 键 | 值 |
|----------|------|------|-----|-----|
| **Content Store** | 256 | 缓存 Data 包 | Name Hash | Data |
| **PIT** | 1024 | 跟踪 Interest | Name Hash | Incoming Face |
| **FIB** | 512 | 路由决策 | Name Prefix | Next Hop |

### GeoNetworking

| 数据结构 | 容量 | 作用 | 键 | 值 |
|----------|------|------|-----|-----|
| **LocationTable** | 256 | 邻居位置 | GN Address | (Lat, Lon, Time) |
| **Sequence Cache** | 512 | 防重复 | (Src Addr, SeqNum) | Received Flag |
| **Neighbor Table** | 32 | 邻居映射 | Port | (Lat, Lon) |

---

## 🚀 典型应用场景对比

### NDN 应用场景

1. **内容检索**
   - Consumer 从 Producer 获取命名内容
   - 利用 CS 缓存加速重复请求
   - 示例：视频流、文件分发

2. **内容缓存**
   - 网络内缓存热点内容
   - 减少回源请求
   - 示例：CDN 加速

3. **Interest 聚合**
   - 多个相同请求合并
   - 减少网络负载
   - 示例：大规模内容订阅

### GeoNetworking 应用场景

1. **紧急制动警告**
   - 车辆紧急制动时向后方广播
   - 向特定地理区域（半径200m）发送
   - 延迟要求：< 50ms

2. **紧急车辆优先**
   - 救护车接近时提前通知
   - 高优先级消息处理
   - 广播到行驶路径区域

3. **协作感知**
   - 车辆周期性广播位置（10Hz）
   - RSU 维护位置表
   - 实现邻居发现

4. **事故通知**
   - 向事故区域广播警告
   - 基于区域的选择性转发
   - 只有相关 RSU 参与转发

---

## 💡 关键技术对比

### NDN 关键技术

#### 1. **名字路由**
```python
# 基于名字前缀的最长匹配
/ndn/edu/ucla/video/lecture1
         ↓ (匹配)
FIB: /ndn/edu/ucla → port 2
```

#### 2. **有状态转发**
```python
# PIT 记录 Interest 状态
Interest: /video/lecture1 → 记录 incoming_face
Data: /video/lecture1 → 查 PIT，沿原路返回
```

#### 3. **内容缓存**
```python
# 网络内缓存
第一次: Consumer → Network → Producer
第二次: Consumer → Network (CS命中) ✓
```

### GeoNetworking 关键技术

#### 1. **地理位置路由**
```python
# 基于地理坐标的转发
目标位置: (39.9065°N, 116.3972°E)
邻居1距离: 150m
邻居2距离: 80m ← 选择（最近）
```

#### 2. **区域广播**
```python
# 向特定地理区域广播
if node_in_circle(center, radius):
    broadcast_to_all_neighbors()
else:
    greedy_forward_to_closest()
```

#### 3. **移动性支持**
```python
# 位置表动态更新
Beacon/CAM 消息 → 更新邻居位置
支持高速移动节点（车辆）
```

---

## 📈 性能参数对比

### NDN

| 参数 | 值 | 说明 |
|------|-----|------|
| Interest Lifetime | 4000 ms | Interest 有效期 |
| CS Size | 256 entries | 缓存容量 |
| PIT Size | 1024 entries | 待处理请求数 |
| 内容获取延迟 | < 100 ms | 普通内容 |
| CS 命中率目标 | > 50% | 热点内容 |

### GeoNetworking

| 参数 | 值 | 说明 |
|------|-----|------|
| Beacon Interval | 1000 ms | RSU 位置广播 |
| CAM Frequency | 10 Hz | 车辆状态广播 |
| Max Hop Limit | 10 | 最大跳数 |
| 紧急消息延迟 | < 50 ms | 安全关键 |
| 消息成功率 | > 95% | 安全消息 |

---

## 🔧 实现特点对比

### NDN 实现特点

✅ **优势**
- 天然支持多播和内容分发
- 网络内缓存提升性能
- Interest 聚合减少流量
- 安全性内置于架构

⚠️ **挑战**
- 需要大容量表项（FIB、PIT、CS）
- 名字设计需要规划
- 与现有 IP 网络集成

### GeoNetworking 实现特点

✅ **优势**
- 天然适应移动场景
- 无需基础设施支持
- 地理区域广播高效
- 实时性好

⚠️ **挑战**
- 需要精确位置信息（GPS）
- 路由空洞问题
- 高速移动下的位置更新

---

## 📂 文件结构对比

### NDN 示例文件

```
input/NDN_example/
├── include/
│   ├── ndn_headers.pne          # NDN 协议头部
│   └── standard_headers.pne     # 以太网头部
├── ndn_forwarding.pne           # 转发逻辑（220行）
├── topology.json                # 3交换机拓扑
├── service.json                 # NDN服务配置
├── README.md                    # 文档（287行）
├── Makefile                     # 构建脚本
└── quick_start.sh               # 快速启动
```

### GeoNetworking 示例文件

```
input/GEO_example/
├── include/
│   └── geo_headers.pne          # GeoNetworking 头部
├── geo_forwarding.pne           # 转发逻辑（320行）
├── topology.json                # 5 RSU 拓扑
├── service.json                 # V2X 服务配置
├── README.md                    # 文档（500+行）
├── Makefile                     # 构建脚本
└── quick_start.sh               # 快速启动
```

---

## 🎓 学习路径建议

### 从 NDN 开始

适合人群：
- 对内容分发网络感兴趣
- 研究命名数据网络
- 关注边缘计算和缓存

学习顺序：
1. 理解 Interest/Data 交换模型
2. 学习 FIB、PIT、CS 的作用
3. 掌握名字路由和转发
4. 实验内容缓存效果

### 从 GeoNetworking 开始

适合人群：
- 对车联网、智能交通感兴趣
- 研究移动自组织网络
- 关注位置服务

学习顺序：
1. 理解地理位置路由原理
2. 学习 GeoBroadcast 机制
3. 掌握贪婪转发算法
4. 实验 V2X 应用场景

---

## 🔬 扩展方向对比

### NDN 扩展

1. **完整的 TLV 编解码**
   - 实现标准 NDN Packet Format
   - 支持可变长度名字

2. **高级转发策略**
   - 自适应 SRTT 转发（ASF）
   - 多路径转发

3. **安全机制**
   - 签名验证
   - 信任模型

4. **与应用集成**
   - NDN-RTC（实时通信）
   - 文件同步

### GeoNetworking 扩展

1. **复杂区域判断**
   - 精确的几何计算
   - 椭圆、多边形区域

2. **高级转发算法**
   - CBF（竞争转发）
   - Store-Carry-Forward

3. **位置预测**
   - 基于速度和航向
   - 提高转发准确性

4. **完整协议栈**
   - BTP 传输层
   - CAM/DENM 完整实现

---

## 🛠️ 使用方式对比

### NDN 编译和运行

```bash
cd input/NDN_example

# 编译
make compile

# 查看架构
make flow

# 部署
make deploy
```

### GeoNetworking 编译和运行

```bash
cd input/GEO_example

# 编译
make compile

# 查看拓扑
make topology

# 查看用例
make use-cases

# 部署
make deploy
```

---

## 📚 标准和参考

### NDN 参考文档

- NFD Developer's Guide
- NDN Packet Format Specification
- NDN Protocol Design Principles
- ndn-cxx Library Documentation

### GeoNetworking 参考文档

- ETSI EN 302 636-1: Requirements
- ETSI EN 302 636-3: Network Architecture
- ETSI EN 302 636-4-1: Media-Independent Functionality
- ETSI EN 302 637-2: CAM Specification
- ETSI EN 302 637-3: DENM Specification

---

## 🎯 总结

### NDN 适合场景

✓ 内容分发和边缘缓存  
✓ 大规模内容订阅  
✓ 多播和组播通信  
✓ 对延迟不极端敏感的应用  

### GeoNetworking 适合场景

✓ 车联网和智能交通  
✓ 移动自组织网络  
✓ 基于位置的服务  
✓ 低延迟安全关键应用  

### 共同特点

- 都是创新的网络层协议
- 都可在 P4 交换机上实现
- 都使用 Lynette PNE 语言描述
- 都有完整的示例和文档

---

## 🚀 快速开始

### 先尝试 NDN（相对简单）

```bash
cd input/NDN_example
bash quick_start.sh all
```

### 再尝试 GeoNetworking（稍复杂）

```bash
cd input/GEO_example
bash quick_start.sh all
```

---

## 📞 获取帮助

两个示例都提供了详细的文档和帮助命令：

```bash
# NDN 帮助
cd input/NDN_example
make help

# GeoNetworking 帮助
cd input/GEO_example
make help
```

---

## ⭐ 贡献

欢迎改进和扩展这两个示例！可以：

- 实现更完整的协议特性
- 添加新的测试场景
- 优化转发算法
- 改进文档和注释

---

**享受探索创新网络协议的乐趣！** 🎉

