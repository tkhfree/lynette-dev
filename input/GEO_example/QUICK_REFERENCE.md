# GeoNetworking 快速参考手册

## 🚗 什么是 GeoNetworking？

GeoNetworking 是专为**车联网（V2X）**设计的网络层协议，核心特点是基于**地理位置**进行路由和通信。

### 核心概念

- **地理位置路由**：不依赖传统地址，使用地理坐标（纬度、经度）
- **区域通信**：向特定地理区域内的所有节点广播消息
- **移动性支持**：天然适应车辆高速移动场景
- **自组织**：无需固定基础设施，支持 V2V（车到车）直接通信

---

## 📋 消息类型速查

| 消息类型 | 全称 | 用途 | 频率 | 优先级 |
|---------|------|------|------|--------|
| **CAM** | Cooperative Awareness Message | 周期性广播车辆状态 | 10 Hz | 普通 |
| **DENM** | Decentralized Environmental Notification | 事件驱动的危险警告 | 事件触发 | 高/最高 |
| **SPAT** | Signal Phase and Timing | 交通信号灯信息 | 10 Hz | 普通 |
| **Beacon** | Location Beacon | RSU位置信息广播 | 1 Hz | 普通 |

---

## 🎯 GeoNetworking 头部类型

| 类型代码 | 名称 | 说明 |
|---------|------|------|
| `0x1` | **Beacon** | 单跳位置广播 |
| `0x2` | **GeoUnicast (GUC)** | 地理单播，发送到特定位置的节点 |
| `0x3` | **GeoAnycast** | 地理任播，发送到区域内任一节点 |
| `0x4` | **GeoBroadcast (GBC)** | 地理广播，发送到区域内所有节点 |
| `0x5` | **TSB** | 拓扑范围广播，单跳或多跳 |

---

## 🗺️ 地理区域类型

### 1. 圆形区域 (Circle)
```
中心点: (latitude, longitude)
半径: radius (米)
用途: 事故区域、路口区域
```

### 2. 矩形区域 (Rectangle)
```
中心点: (latitude, longitude)
宽度: width (米)
长度: length (米)
角度: angle (度)
用途: 道路段、车道
```

### 3. 椭圆区域 (Ellipse)
```
中心点: (latitude, longitude)
半长轴: distanceA (米)
半短轴: distanceB (米)
角度: angle (度)
用途: 高速公路段
```

---

## 🔄 转发算法速查

### 贪婪转发 (Greedy Forwarding)

```
for each neighbor:
    distance = calculate_distance(neighbor_pos, target_pos)
    
选择 distance 最小的邻居转发
```

**优点**：简单高效  
**缺点**：可能遇到路由空洞

### 区域内广播

```
if my_position in target_area:
    broadcast_to_all_neighbors()
else:
    greedy_forward_to_closest()
```

---

## 📊 核心数据结构

### LocationTable（位置表）

```
结构: GN_Address → (Latitude, Longitude, Timestamp)
容量: 256 条目
更新: 从 Beacon、CAM 消息
用途: 邻居发现、转发决策
```

### Sequence Number Cache

```
结构: (Source_Addr, SeqNum) → Received_Flag
容量: 512 条目
用途: 防止重复接收、环路检测
```

### Neighbor Table

```
结构: Port → (Latitude, Longitude)
配置: 静态配置或动态学习
用途: 端口到位置的映射
```

---

## 💻 常用命令

### 编译

```bash
cd input/GEO_example
make compile
```

### 查看拓扑

```bash
make topology
```

### 查看转发流程

```bash
make flow
```

### 查看应用场景

```bash
make use-cases
```

### 查看架构

```bash
make arch
```

### 清理

```bash
make clean
```

---

## 🎬 典型场景

### 场景 1: 紧急制动警告

```
触发: 车辆紧急制动
消息: DENM
类型: GeoBroadcast
区域: 圆形，半径 200m
延迟: < 50ms
```

**流程**：
1. Vehicle-1 紧急制动 → 生成 DENM
2. DENM 向后方 200米 区域广播
3. RSU 转发到区域内所有节点
4. 后方车辆收到警告，减速避让

### 场景 2: 救护车接近

```
触发: 紧急车辆接近
消息: DENM (高优先级)
类型: GeoBroadcast
区域: 矩形，沿行驶方向 400m
延迟: < 50ms
```

**流程**：
1. Emergency Vehicle 广播高优先级 DENM
2. 消息沿行驶路径转发
3. 前方车辆收到，准备让行
4. 交通信号灯协调，优先通行

### 场景 3: 协作感知

```
触发: 周期性（100ms）
消息: CAM
类型: TSB（拓扑范围广播）
内容: 位置、速度、航向
```

**作用**：
- 邻居发现
- 碰撞风险评估
- 盲区预警
- 变道辅助

---

## 🔢 关键参数

### 时间参数

```
Beacon间隔:        1000 ms
CAM频率:          10 Hz (100 ms)
DENM保持时间:      根据事件（可达数分钟）
位置表老化:        5 秒
```

### 跳数参数

```
最大跳数(MHL):     10
默认跳数(RHL):     10
Beacon跳数:        1 (单跳)
```

### 延迟要求

```
紧急消息:         < 50 ms
安全消息:         < 100 ms
非安全消息:       < 500 ms
```

### 成功率要求

```
紧急消息:         > 99%
安全消息:         > 95%
非安全消息:       > 90%
```

---

## 🌐 坐标系统

### 纬度（Latitude）

```
范围: -90° 到 +90°
正值: 北纬
负值: 南纬
精度: 0.00001° ≈ 1米
```

### 经度（Longitude）

```
范围: -180° 到 +180°
正值: 东经
负值: 西经
精度: 0.00001° ≈ 1米（赤道附近）
```

### 示例坐标（北京市中心）

```
路口中心:   39.9065°N, 116.3972°E
北侧RSU:    39.9075°N, 116.3972°E  (向北 ~111米)
东侧RSU:    39.9065°N, 116.3992°E  (向东 ~200米)
```

---

## 🚦 协议栈层次

```
┌─────────────────────────────────┐
│  应用层 (Application)            │
│  CAM, DENM, SPAT, MAP           │
├─────────────────────────────────┤
│  传输层 (BTP)                    │
│  端口复用                        │
├─────────────────────────────────┤
│  网络层 (GeoNetworking)          │
│  • Basic Header                 │
│  • Common Header                │
│  • Extended Header              │
├─────────────────────────────────┤
│  接入层 (IEEE 802.11p / ITS-G5) │
├─────────────────────────────────┤
│  物理层 (5.9 GHz DSRC)          │
└─────────────────────────────────┘
```

---

## 🔧 调试技巧

### 1. 查看位置表

```bash
# 在 P4 运行时查询 LocationTable
simple_switch_CLI --thrift-port 9090
> table_dump LocationTable
```

### 2. 监控转发

```bash
# 抓包查看 GeoNetworking 消息
tcpdump -i veth1 -w geo.pcap ether proto 0x8947
```

### 3. 统计信息

```bash
# 查询统计寄存器
> register_read beacon_counter
> register_read gbc_counter
```

---

## 📐 距离计算公式

### 简化距离（本示例使用）

```python
lat_diff = abs(lat1 - lat2)
lon_diff = abs(lon1 - lon2)
distance ≈ (lat_diff + lon_diff) >> 16  # 简化
```

### 精确距离（Haversine 公式）

```python
R = 6371000  # 地球半径（米）
φ1 = lat1 * π / 180
φ2 = lat2 * π / 180
Δφ = (lat2 - lat1) * π / 180
Δλ = (lon2 - lon1) * π / 180

a = sin²(Δφ/2) + cos(φ1) * cos(φ2) * sin²(Δλ/2)
c = 2 * atan2(√a, √(1−a))
distance = R * c
```

---

## 🎓 学习资源

### 必读标准文档

1. **ETSI EN 302 636-4-1**: GeoNetworking 协议规范
2. **ETSI EN 302 637-2**: CAM 规范
3. **ETSI EN 302 637-3**: DENM 规范

### 推荐阅读顺序

1. 阅读 `README.md` 了解整体架构
2. 查看 `topology.json` 理解网络拓扑
3. 阅读 `geo_forwarding.pne` 学习实现
4. 运行 `make use-cases` 查看场景
5. 实验和修改代码

---

## ⚡ 快速调试清单

### 编译失败？

- [ ] 检查 Python 环境
- [ ] 确认 Lynette 模块存在
- [ ] 验证 JSON 配置文件格式

### 转发不工作？

- [ ] 检查邻居位置表配置
- [ ] 验证地理坐标正确性
- [ ] 确认端口映射正确

### 消息丢失？

- [ ] 检查剩余跳数（RHL）
- [ ] 验证序列号未重复
- [ ] 确认在目标区域内

---

## 💡 优化建议

### 性能优化

1. **位置表大小**：根据邻居数量调整
2. **序列号缓存**：平衡内存和重复检测
3. **区域判断**：使用更精确的算法

### 功能扩展

1. 实现 CBF（竞争转发）
2. 添加路由空洞恢复
3. 集成位置预测算法
4. 实现完整的 BTP 层

---

## 📞 获取帮助

```bash
# 命令行帮助
make help

# 快速启动脚本
bash quick_start.sh help

# 查看所有可用选项
bash quick_start.sh
```

---

## 🎯 下一步

1. ✅ 编译示例代码
2. ✅ 理解转发流程
3. ✅ 运行测试场景
4. 📝 修改配置参数
5. 🚀 添加新功能

**祝您学习愉快！** 🎉

