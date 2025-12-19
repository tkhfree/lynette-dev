# GeoNetworking 车联网示例

## 概述

本示例展示了如何使用 Lynette PNE 语言在多个 P4 可编程交换机上实现完整的 GeoNetworking 协议，用于车联网（V2X - Vehicle-to-Everything）通信。实现基于 **ETSI EN 302 636** 标准（欧洲电信标准化协会的 GeoNetworking 规范）。

## 什么是 GeoNetworking？

GeoNetworking 是一种专为车联网设计的网络层协议，其核心特点是：

- **地理位置路由**：基于车辆和RSU的地理位置进行路由决策
- **无需基础设施**：支持车辆间直接通信（V2V）
- **地理区域广播**：向特定地理区域内的所有节点广播消息
- **移动性支持**：天然适应车辆高速移动的场景
- **安全关键**：用于传输紧急制动、碰撞预警等安全相关消息

## 应用场景

### 典型 V2X 应用

1. **紧急制动警告（Emergency Brake Warning）**
   - 车辆紧急制动时向后方车辆广播警告
   - 防止追尾事故

2. **交叉路口碰撞预警（Intersection Collision Warning）**
   - 在路口预警潜在的碰撞风险
   - 提高路口安全性

3. **紧急车辆优先（Emergency Vehicle Priority）**
   - 救护车、消防车接近时提前通知
   - 协助其他车辆让行

4. **道路危险警告（Road Hazard Warning）**
   - 事故、施工、路面结冰等危险通知
   - 向相关区域广播

5. **协作感知（Cooperative Awareness）**
   - 车辆周期性广播位置和状态
   - 增强态势感知能力

## 架构设计

### 网络拓扑

本示例模拟一个城市十字路口场景，包含 5 个 RSU（路边单元）：

```
                    [rsu-north]
                   (北侧RSU)
                        |
                   Vehicle-1
                        |
    [rsu-west] ---  [rsu-center]  --- [rsu-east]
   (西侧RSU)         (中心RSU)         (东侧RSU)
  Emergency-V            |            Vehicle-2
                         |
                   [rsu-south]
                   (南侧RSU)
                        |
                   Vehicle-3
```

### 地理坐标系统

以北京市中心某路口为例（可根据实际需求修改）：

| RSU | 纬度 | 经度 | 位置描述 |
|-----|------|------|---------|
| rsu-north | 39.9075°N | 116.3972°E | 路口北侧 200米 |
| rsu-south | 39.9055°N | 116.3972°E | 路口南侧 200米 |
| rsu-east | 39.9065°N | 116.3992°E | 路口东侧 200米 |
| rsu-west | 39.9065°N | 116.3952°E | 路口西侧 200米 |
| rsu-center | 39.9065°N | 116.3972°E | 路口中心 |

## GeoNetworking 核心组件

基于 ETSI EN 302 636 标准，实现了以下核心组件：

### 1. **GeoParser** - 数据包解析器
   - 解析 GeoNetworking 各种头部类型
   - 支持 Beacon、GBC、GUC 等消息类型
   - 提取地理位置信息

### 2. **LocationTable** - 位置表
   - 维护邻居节点的位置信息
   - 从 Beacon 和 CAM 消息更新
   - 支持位置查询和老化机制

### 3. **GeoAreaCheck** - 地理区域检查
   - 判断节点是否在目标地理区域内
   - 支持圆形、矩形、椭圆等区域类型
   - 计算节点到区域中心的距离

### 4. **GreedyForwarding** - 贪婪转发算法
   - 选择最接近目标位置的邻居转发
   - 实现地理位置路由核心算法
   - 处理转发失败和路由空洞

### 5. **SequenceNumberCheck** - 序列号检查
   - 防止数据包重复接收和转发
   - 维护已接收消息的序列号缓存
   - 环路检测和防止

### 6. **GeoStatistics** - 统计模块
   - 统计各类消息数量
   - 监控转发性能
   - 区域命中率统计

## GeoNetworking 协议头部

### 基本头部（Basic Header）

```
+------------------+
| Version (4 bits) |    协议版本
| NextHdr (4 bits) |    下一个头部类型
+------------------+
| Reserved (8)     |
| Lifetime (8)     |    数据包生存时间
| RemainingHL (8)  |    剩余跳数限制
+------------------+
```

### 公共头部（Common Header）

```
+------------------+
| NextHdr (4)      |
| Reserved (4)     |
| HT (4)           |    头部类型（Beacon/GBC/GUC等）
| HST (4)          |    头部子类型
+------------------+
| TrafficClass (8) |    流量类别
| Flags (8)        |    标志位
| PayloadLen (16)  |    载荷长度
| MaxHopLimit (8)  |    最大跳数
| Reserved (8)     |
+------------------+
```

### GeoBroadcast 头部（GBC）

```
+------------------------+
| Sequence Number (16)   |    序列号
| Reserved (16)          |
+------------------------+
| Source Long Position Vector:
|   - GN Address (64)    |    源节点地址
|   - Timestamp (32)     |    时间戳
|   - Latitude (32)      |    纬度
|   - Longitude (32)     |    经度
|   - Speed (16)         |    速度
|   - Heading (16)       |    航向
+------------------------+
| Destination Area:
|   - Latitude (32)      |    目标区域中心纬度
|   - Longitude (32)     |    目标区域中心经度
|   - DistanceA (16)     |    半长轴
|   - DistanceB (16)     |    半短轴
|   - Angle (16)         |    角度
+------------------------+
```

## 转发流程

### GeoBroadcast (GBC) 转发流程

```
1. 接收 GBC 消息
   ↓
2. 检查剩余跳数（RHL > 0？）
   ↓
3. 序列号检查（是否重复？）
   ↓
4. 更新位置表（记录源节点位置）
   ↓
5. 地理区域检查
   ├─ 在区域内 → 广播到所有邻居（除入端口）
   └─ 不在区域内 ↓
6. 贪婪转发
   ├─ 查找位置表
   ├─ 计算邻居到目标的距离
   └─ 选择最近的邻居转发
   ↓
7. 减少 RHL，更新头部
   ↓
8. 转发数据包
```

### Beacon 处理流程

```
1. 接收 Beacon 消息
   ↓
2. 提取位置信息
   ↓
3. 更新位置表
   ├─ 新节点 → 添加条目
   └─ 已知节点 → 更新位置和时间戳
   ↓
4. 不转发（Beacon 仅单跳）
```

### GeoUnicast (GUC) 转发流程

```
1. 接收 GUC 消息
   ↓
2. 检查目标地址
   ├─ 是本节点 → 上传到应用层
   └─ 不是本节点 ↓
3. 查找位置表中的目标位置
   ↓
4. 贪婪转发到最近邻居
   ↓
5. 更新并转发
```

## 设备和协议栈要求

### 车载终端设备要求（OBU - On-Board Unit）

#### 硬件要求

| 组件 | 最低要求 | 推荐配置 | 说明 |
|------|---------|---------|------|
| **处理器** | ARM Cortex-A53 双核 | ARM Cortex-A72 四核 | 实时处理 CAM/DENM |
| **内存** | 1 GB RAM | 4 GB RAM | 用于位置表和消息缓存 |
| **存储** | 8 GB eMMC | 32 GB SSD | 存储地图和应用 |
| **V2X 通信模块** | ITS-G5 (802.11p) 单天线 | ITS-G5 双天线 MIMO | 5.9 GHz V2X 通信 |
| **GNSS 模块** | GPS L1 | GPS L1+L5 / 北斗 / Galileo | 位置精度 < 5m |
| **CAN 接口** | CAN 2.0B | CAN-FD | 连接车辆总线 |
| **电源** | 12V 车载电源 | 12V/24V 宽电压 | 车辆供电 |
| **工作温度** | -20°C ~ 70°C | -40°C ~ 85°C | 车载环境 |

#### 软件要求

**操作系统**
- Linux 实时内核（PREEMPT_RT patch）
- 或嵌入式 Linux（Yocto, Buildroot）
- 或 Android Automotive OS

**完整协议栈**
```
┌─────────────────────────────────────┐
│  应用层 (Facilities Layer)           │
│  - CAM 生成器 (周期性 10Hz)          │
│  - DENM 触发器 (事件驱动)            │
│  - SPAT/MAP 处理器                   │
│  - 驾驶员告警接口                    │
├─────────────────────────────────────┤
│  传输层                              │
│  - BTP (Basic Transport Protocol)   │
│    • BTP-A: 交互式通信               │
│    • BTP-B: 非交互式通信             │
│  - 端口复用 (2001-2009)              │
├─────────────────────────────────────┤
│  网络层                              │
│  - GeoNetworking 协议栈              │
│    • Basic Header 处理               │
│    • Common Header 处理              │
│    • Location Table 管理             │
│    • 转发决策引擎                    │
│    • 序列号管理                      │
├─────────────────────────────────────┤
│  接入层                              │
│  - IEEE 802.11p (ITS-G5) MAC        │
│  - DCC (Decentralized Congestion Control) │
│  - 信道管理 (CCH/SCH)                │
├─────────────────────────────────────┤
│  物理层                              │
│  - 5.9 GHz 射频前端                  │
│  - 天线 (全向/定向)                  │
└─────────────────────────────────────┘
```

**依赖软件包**
```bash
# 安装 GeoNetworking 协议栈 (基于 Vanetza)
sudo apt-get install build-essential cmake libboost-all-dev \
    libcrypto++-dev libgeographic-dev

# 安装 Vanetza (开源 GeoNetworking 实现)
git clone https://github.com/riebl/vanetza.git
cd vanetza
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make
sudo make install

# 安装 GPS 工具
sudo apt-get install gpsd gpsd-clients
```

**OBU 配置示例**
```bash
# /etc/vanetza/obu.conf
[station]
type = passenger_car
station_id = 12345
country_code = 156  # 中国

[positioning]
device = /dev/ttyUSB0
gnss_type = gps+beidou
update_rate = 10  # Hz

[communication]
interface = wlan0
mac_address = auto
channel = 178  # ITS-G5 CCH
tx_power = 20  # dBm

[geonetworking]
location_table_size = 256
sequence_cache_size = 512
max_hop_limit = 10

[cam]
generation_interval = 100  # ms
min_interval = 100  # ms
max_interval = 1000  # ms
```

**CAM 生成示例**
```python
#!/usr/bin/env python3
import time
import gpsd
from vanetza import GeoNetworking, CAM

# 连接 GPS
gpsd.connect()

# 创建 GeoNetworking 实例
gn = GeoNetworking(interface="wlan0")

while True:
    # 获取当前位置
    packet = gpsd.get_current()
    
    # 生成 CAM 消息
    cam = CAM()
    cam.station_id = 12345
    cam.latitude = packet.lat
    cam.longitude = packet.lon
    cam.speed = packet.speed
    cam.heading = packet.track
    cam.timestamp = int(time.time() * 1000)
    
    # 发送 CAM (TSB)
    gn.send_tsb(cam.encode(), hop_limit=1)
    
    time.sleep(0.1)  # 10 Hz
```

**DENM 触发示例**
```python
#!/usr/bin/env python3
from vanetza import GeoNetworking, DENM

gn = GeoNetworking(interface="wlan0")

def emergency_brake_detected():
    """紧急制动时触发"""
    denm = DENM()
    denm.cause_code = DENM.CAUSE_EMERGENCY_BRAKE
    denm.sub_cause = DENM.SUB_EMERGENCY_BRAKE_LIGHT
    denm.latitude = get_current_latitude()
    denm.longitude = get_current_longitude()
    
    # 向后方 200米 区域广播
    gn.send_gbc(
        payload=denm.encode(),
        area_type=GeoNetworking.CIRCLE,
        center_lat=denm.latitude,
        center_lon=denm.longitude,
        radius=200,  # 米
        hop_limit=10
    )
    
    print("Emergency brake DENM sent!")

# 监听 CAN 总线的制动信号
import can
bus = can.interface.Bus(channel='can0', bustype='socketcan')

for msg in bus:
    if msg.arbitration_id == 0x123:  # 制动信号
        if msg.data[0] > 0x80:  # 紧急制动阈值
            emergency_brake_detected()
```

#### 车辆集成要求

**CAN 总线集成**
```python
# 需要读取的车辆信息
- 车速 (CAN ID: 0x1XX)
- 转向角 (CAN ID: 0x2XX)
- 制动状态 (CAN ID: 0x3XX)
- 档位信息 (CAN ID: 0x4XX)
- 灯光状态 (CAN ID: 0x5XX)
```

**HMI 界面要求**
- 显示接收到的 DENM 警告
- 显示周边车辆位置（基于 CAM）
- 紧急情况声音告警
- 触摸屏或按钮交互

#### OBU 移动性要求（关键特性）

**✅ 必须支持高速移动**

GeoNetworking 专为车辆移动场景设计，OBU 必须满足以下移动性要求：

**1. 移动速度支持**

| 场景 | 速度范围 | OBU 要求 | 通信性能 |
|------|---------|---------|---------|
| **城市道路** | 0-60 km/h | 标准 OBU | 稳定通信 |
| **城市快速路** | 60-80 km/h | 标准 OBU | 稳定通信 |
| **高速公路** | 80-120 km/h | 高性能 OBU | 需要快速切换 |
| **极限场景** | 120-200 km/h | 高端 OBU + 高级天线 | 切换频繁 |

**2. 位置更新频率配置**

```python
# OBU 移动性配置
class MobilityConfig:
    # 基于速度的自适应配置
    @staticmethod
    def get_config(speed_kmh):
        if speed_kmh < 30:  # 低速（城市拥堵）
            return {
                'cam_interval': 500,      # ms (2 Hz)
                'gnss_update': 5,         # Hz
                'tx_power': 20,           # dBm
                'handover_threshold': -85 # dBm
            }
        elif speed_kmh < 80:  # 中速（城市正常）
            return {
                'cam_interval': 100,      # ms (10 Hz)
                'gnss_update': 10,        # Hz
                'tx_power': 23,           # dBm
                'handover_threshold': -80 # dBm
            }
        else:  # 高速（高速公路）
            return {
                'cam_interval': 100,      # ms (10 Hz)
                'gnss_update': 20,        # Hz (更快定位)
                'tx_power': 23,           # dBm
                'handover_threshold': -75 # dBm (提前切换)
            }

# 应用示例
speed = get_vehicle_speed()  # 从 CAN 获取
config = MobilityConfig.get_config(speed)
update_cam_interval(config['cam_interval'])
```

**3. 快速 RSU 切换（Handover）**

```python
#!/usr/bin/env python3
"""
OBU 移动性管理 - RSU 切换
"""
class RSUHandoverManager:
    def __init__(self):
        self.current_rsu = None
        self.rssi_threshold = -80  # dBm
        self.neighbor_rsus = {}
        
    def monitor_signal_strength(self):
        """监控信号强度，决定是否切换"""
        while True:
            # 获取当前 RSU 信号强度
            current_rssi = get_rssi(self.current_rsu)
            
            if current_rssi < self.rssi_threshold:
                print(f"⚠ Weak signal from {self.current_rsu}: {current_rssi} dBm")
                
                # 扫描邻居 RSU
                best_rsu = self.find_best_neighbor()
                
                if best_rsu and best_rsu != self.current_rsu:
                    self.handover(best_rsu)
            
            time.sleep(0.1)  # 100ms 检查一次
    
    def find_best_neighbor(self):
        """查找信号最强的邻居 RSU"""
        neighbor_scan = scan_nearby_rsus()
        
        best_rsu = None
        best_rssi = -100
        
        for rsu_id, rssi in neighbor_scan.items():
            if rssi > best_rssi:
                best_rssi = rssi
                best_rsu = rsu_id
        
        return best_rsu if best_rssi > self.rssi_threshold else None
    
    def handover(self, new_rsu):
        """执行 RSU 切换"""
        print(f"🔄 Handover: {self.current_rsu} → {new_rsu}")
        
        # 1. 与新 RSU 建立连接
        connect_to_rsu(new_rsu)
        
        # 2. 发送 Beacon 通知新 RSU
        send_beacon(new_rsu)
        
        # 3. 断开旧 RSU
        if self.current_rsu:
            disconnect_from_rsu(self.current_rsu)
        
        self.current_rsu = new_rsu
        print(f"✓ Connected to {new_rsu}")

# 启动移动性管理
manager = RSUHandoverManager()
manager.monitor_signal_strength()
```

**4. 位置预测（提升转发性能）**

```python
class LocationPredictor:
    """基于速度和航向预测未来位置"""
    
    @staticmethod
    def predict(current_lat, current_lon, speed_ms, heading_deg, time_delta_s):
        """
        预测 time_delta_s 秒后的位置
        
        Args:
            current_lat: 当前纬度
            current_lon: 当前经度
            speed_ms: 速度 (米/秒)
            heading_deg: 航向角 (度, 0=北, 90=东)
            time_delta_s: 预测时间 (秒)
        """
        import math
        
        # 移动距离
        distance = speed_ms * time_delta_s
        
        # 转换为弧度
        heading_rad = math.radians(heading_deg)
        
        # 地球半径
        R = 6371000  # 米
        
        # 计算位移
        delta_lat = (distance * math.cos(heading_rad)) / R
        delta_lon = (distance * math.sin(heading_rad)) / (R * math.cos(math.radians(current_lat)))
        
        # 预测位置
        future_lat = current_lat + math.degrees(delta_lat)
        future_lon = current_lon + math.degrees(delta_lon)
        
        return future_lat, future_lon

# 使用示例
current_lat = 39.9065
current_lon = 116.3972
speed_kmh = 60
speed_ms = speed_kmh / 3.6  # 转换为 m/s
heading = 90  # 向东

# 预测 5 秒后位置
future_lat, future_lon = LocationPredictor.predict(
    current_lat, current_lon, speed_ms, heading, 5
)
print(f"Current: {current_lat}, {current_lon}")
print(f"Future (5s): {future_lat}, {future_lon}")
```

**5. 移动性测试场景**

```bash
#!/bin/bash
# OBU 移动性测试脚本

echo "=== GeoNetworking 移动性测试 ==="

# 场景 1: 低速移动（30 km/h）
echo "\n[测试 1] 低速城市道路"
./simulate_obu.sh --speed 30 --route urban --duration 300

# 场景 2: 中速移动（60 km/h）
echo "\n[测试 2] 城市快速路"
./simulate_obu.sh --speed 60 --route highway --duration 300

# 场景 3: 高速移动（120 km/h）
echo "\n[测试 3] 高速公路"
./simulate_obu.sh --speed 120 --route expressway --duration 300

# 场景 4: RSU 切换
echo "\n[测试 4] RSU 切换性能"
./test_handover.sh --rsus "rsu1,rsu2,rsu3" --speed 80

# 评估指标
echo "\n=== 性能指标 ==="
echo "- 切换次数: $(count_handovers)"
echo "- 切换延迟: $(avg_handover_delay) ms"
echo "- 数据包丢失率: $(packet_loss_rate)%"
echo "- 平均通信延迟: $(avg_latency) ms"
```

---

---

### 无线通信基站要求（ITS-G5 基站/RSU）

**✅ GeoNetworking 必须部署无线通信基站**

与传统网络不同，车联网的 GeoNetworking 场景必须部署专用的 ITS-G5 无线通信基站（即 RSU），原因如下：

#### 为什么必须使用专用 V2X 基站？

**1. 不能使用传统 Wi-Fi/4G/5G 的原因**

| 对比项 | ITS-G5 (专用) | Wi-Fi | 4G/5G |
|--------|--------------|-------|-------|
| **延迟** | < 10 ms | 50-100 ms | 50-200 ms |
| **可靠性** | > 95% @ 120km/h | 差（高速下） | 中等 |
| **覆盖范围** | 300-500m | 100m | 好，但延迟高 |
| **专用频段** | 5.9 GHz (专用) | 2.4/5 GHz (共享) | 授权频段 |
| **安全关键** | ✅ 支持 | ❌ 不支持 | ⚠ 需额外设计 |
| **地理路由** | ✅ 原生支持 | ❌ 不支持 | ❌ 不支持 |

**2. ITS-G5 基站（RSU）的关键特性**

```
专用 V2X 通信特性:

┌─────────────────────────────────────┐
│  低延迟通信 (< 10 ms)               │  ← 安全关键
├─────────────────────────────────────┤
│  高速移动支持 (250+ km/h)           │  ← 移动性
├─────────────────────────────────────┤
│  广播/多播优化                      │  ← 高效分发
├─────────────────────────────────────┤
│  地理位置感知                       │  ← GeoNetworking
├─────────────────────────────────────┤
│  免授权接入 (无需鉴权)              │  ← 快速连接
├─────────────────────────────────────┤
│  优先级队列 (紧急消息优先)          │  ← QoS 保证
└─────────────────────────────────────┘
```

**3. RSU 部署密度要求**

```
城市路口场景:

     RSU-N (北)
        |
      300m
        |
  RSU-W—+—RSU-C—RSU-E
      300m 中心 300m
        |
      300m
        |
     RSU-S (南)

部署密度要求:
- 路口: 1 个中心 RSU + 4 个方向 RSU
- 道路: 每 300-500m 一个 RSU
- 隧道: 每 200m 一个 RSU (信号衰减大)
- 高速公路: 每 500m-1km 一个 RSU
```

**4. RSU 覆盖计算**

```python
class RSUCoverageCalculator:
    """计算 RSU 覆盖范围和部署方案"""
    
    @staticmethod
    def calculate_coverage_area(tx_power_dbm, frequency_ghz=5.9):
        """
        计算 RSU 覆盖范围
        
        使用自由空间路径损耗模型:
        PL(d) = 20*log10(d) + 20*log10(f) + 32.45
        """
        import math
        
        # 接收灵敏度 (OBU)
        rx_sensitivity = -85  # dBm
        
        # 路径损耗
        max_path_loss = tx_power_dbm - rx_sensitivity
        
        # 计算距离 (km)
        distance_km = 10 ** ((max_path_loss - 32.45 - 20*math.log10(frequency_ghz*1000)) / 20)
        
        # 转换为米
        distance_m = distance_km * 1000
        
        # 考虑障碍物和衰减 (城市环境 70% 折损)
        effective_range = distance_m * 0.7
        
        return effective_range
    
    @staticmethod
    def plan_deployment(road_length_m, rsu_power_dbm=33):
        """
        规划 RSU 部署方案
        """
        coverage_range = RSUCoverageCalculator.calculate_coverage_area(rsu_power_dbm)
        
        # 考虑 20% 重叠覆盖
        rsu_spacing = coverage_range * 0.8
        
        num_rsus = int(math.ceil(road_length_m / rsu_spacing))
        
        return {
            'coverage_range': coverage_range,
            'rsu_spacing': rsu_spacing,
            'num_rsus': num_rsus,
            'total_cost_estimate': num_rsus * 50000  # 假设每个 RSU 5万元
        }

# 使用示例
# 5 公里道路需要多少个 RSU？
plan = RSUCoverageCalculator.plan_deployment(5000, tx_power_dbm=33)
print(f"覆盖范围: {plan['coverage_range']:.0f} 米")
print(f"RSU 间距: {plan['rsu_spacing']:.0f} 米")
print(f"需要 RSU 数量: {plan['num_rsus']} 个")
print(f"预估成本: {plan['total_cost_estimate']:,} 元")
```

**5. RSU 部署最佳实践**

```bash
# RSU 选址清单

□ 位置要求:
  □ 安装高度: 5-7 米（路灯杆高度）
  □ 视距: 无明显遮挡
  □ 覆盖范围: 至少 300 米半径
  
□ 供电要求:
  □ 220V 市电接入
  □ UPS 备用电源（至少 4 小时）
  □ 防雷保护
  
□ 网络回程:
  □ 光纤接入（推荐）
  □ 或 4G/5G 无线回程
  □ 带宽: 至少 10 Mbps
  
□ 环境要求:
  □ 防护等级: IP65 或更高
  □ 工作温度: -40°C ~ 75°C
  □ 防盗措施: 锁定机柜

□ GPS 要求:
  □ 天线位置: 顶部，天空视野良好
  □ 精度: RTK 级别 (< 10cm)
  □ 授时: 支持 PPS 输出
```

**6. RSU 与 P4 交换机集成**

```
RSU 系统架构:

┌─────────────────────────────────────┐
│  天线阵列 (ITS-G5)                  │
│  • 4-8 根天线                       │
│  • 360° 覆盖                        │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│  RF 前端                            │
│  • 5.9 GHz 收发                     │
│  • 功率放大 (33 dBm)                │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│  MAC 层 (IEEE 802.11p)              │
│  • CSMA/CA                          │
│  • EDCA 优先级队列                  │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│  P4 交换芯片 (GeoNetworking)        │  ← 本项目的核心
│  • 位置表管理                       │
│  • 地理转发                         │
│  • 序列号检查                       │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│  控制平面 (Linux)                   │
│  • SPAT/MAP 生成                    │
│  • 配置管理                         │
│  • 与交通中心通信                   │
└─────────────────────────────────────┘
```

---

### 路边单元设备要求（RSU - Roadside Unit）

#### 硬件要求

| 组件 | 最低要求 | 推荐配置 | 说明 |
|------|---------|---------|------|
| **处理器** | x86 四核 / ARM Cortex-A72 | x86 八核 / ARM 服务器级 | 处理大量 V2X 消息 |
| **内存** | 4 GB RAM | 16 GB RAM | 大容量位置表 |
| **存储** | 32 GB SSD | 128 GB SSD | 日志和统计数据 |
| **V2X 通信模块** | ITS-G5 四天线 MIMO | ITS-G5 八天线阵列 | 360° 覆盖 |
| **GNSS 模块** | GPS L1+L5 (RTK) | GPS+北斗+Galileo 多频 RTK | 位置精度 < 10cm |
| **回程网络** | 100M 以太网 | 1Gbps 以太网/4G/5G | 连接交通控制中心 |
| **P4 交换芯片** | Barefoot Tofino | Barefoot Tofino 2 | 硬件加速转发 |
| **电源** | 220V AC | 220V AC + UPS | 市电供电 |
| **防护等级** | IP65 | IP67 | 室外环境 |
| **工作温度** | -20°C ~ 60°C | -40°C ~ 75°C | 全天候运行 |

#### 软件要求

**操作系统**
- Linux Server（Ubuntu Server 20.04+, CentOS 8+）
- 实时性优化

**完整协议栈**
```
┌─────────────────────────────────────┐
│  管理平面                            │
│  - 配置管理                          │
│  - 日志和监控                        │
│  - 与交通控制中心通信                │
├─────────────────────────────────────┤
│  控制平面                            │
│  - P4Runtime API                     │
│  - 位置表管理                        │
│  - 路由策略配置                      │
├─────────────────────────────────────┤
│  应用层                              │
│  - SPAT 生成器 (信号灯信息)          │
│  - MAP 广播器 (地图信息)             │
│  - 事件检测器 (事故、拥堵)           │
│  - 统计收集器                        │
├─────────────────────────────────────┤
│  传输层                              │
│  - BTP-B (非交互式)                  │
│  - 端口管理                          │
├─────────────────────────────────────┤
│  网络层 (数据平面)                   │
│  - P4 程序化 GeoNetworking           │
│    • 硬件加速的位置表查找            │
│    • 硬件加速的区域判断              │
│    • 线速贪婪转发                    │
│    • 硬件序列号检查                  │
├─────────────────────────────────────┤
│  接入层                              │
│  - IEEE 802.11p MAC                  │
│  - 多天线 MIMO                       │
│  - DCC 拥塞控制                      │
├─────────────────────────────────────┤
│  物理层                              │
│  - 5.9 GHz 高功率射频                │
│  - 多天线阵列                        │
└─────────────────────────────────────┘
```

**RSU 配置示例**
```bash
# /etc/rsu/config.yaml
station:
  type: rsu
  station_id: 1001
  location:
    latitude: 39.9065
    longitude: 116.3972
    altitude: 55
  coverage_radius: 300  # 米

communication:
  interfaces:
    - name: wlan0
      type: its-g5
      channel: 178
      tx_power: 33  # dBm (2W)
    - name: wlan1
      type: its-g5
      channel: 180
      tx_power: 33
  
p4_switch:
  device_id: 1
  program: geo_forwarding.json
  ports:
    - id: 1
      neighbor: rsu-center
      neighbor_lat: 39.9065
      neighbor_lon: 116.3972
    - id: 2
      neighbor: rsu-east
      neighbor_lat: 39.9065
      neighbor_lon: 116.3992

geonetworking:
  location_table_size: 512
  sequence_cache_size: 1024
  beacon_interval: 1000  # ms
  neighbor_timeout: 5000  # ms

applications:
  spat:
    enabled: true
    interval: 100  # ms
    traffic_light_id: TL-001
  
  map:
    enabled: true
    interval: 1000  # ms
    map_file: /etc/rsu/intersection_map.geojson
```

**SPAT 广播示例**
```python
#!/usr/bin/env python3
from vanetza import GeoNetworking, SPAT
import signal_controller

gn = GeoNetworking(interface="wlan0")

def broadcast_spat():
    """广播交通信号灯状态"""
    # 从信号灯控制器获取状态
    signal_state = signal_controller.get_current_state()
    
    spat = SPAT()
    spat.intersection_id = 1001
    
    # 北向信号灯
    spat.add_signal_group(
        id=1,
        phase=signal_state.north.phase,  # GREEN/YELLOW/RED
        min_end_time=signal_state.north.min_end_time,
        max_end_time=signal_state.north.max_end_time
    )
    
    # 东向信号灯
    spat.add_signal_group(
        id=2,
        phase=signal_state.east.phase,
        min_end_time=signal_state.east.min_end_time,
        max_end_time=signal_state.east.max_end_time
    )
    
    # 向路口区域广播 SPAT
    gn.send_gbc(
        payload=spat.encode(),
        area_type=GeoNetworking.CIRCLE,
        center_lat=39.9065,
        center_lon=116.3972,
        radius=150,  # 米
        hop_limit=2
    )

# 10 Hz 广播
import schedule
schedule.every(0.1).seconds.do(broadcast_spat)

while True:
    schedule.run_pending()
```

**事件检测和 DENM 生成**
```python
#!/usr/bin/env python3
from vanetza import GeoNetworking, DENM
import accident_detector

gn = GeoNetworking(interface="wlan0")

def on_accident_detected(event):
    """检测到事故时生成 DENM"""
    denm = DENM()
    denm.station_id = 1001
    denm.cause_code = DENM.CAUSE_ACCIDENT
    denm.sub_cause = DENM.SUB_MULTI_VEHICLE_ACCIDENT
    denm.latitude = event.latitude
    denm.longitude = event.longitude
    denm.severity = DENM.SEVERITY_HIGH
    
    # 向事故区域广播
    gn.send_gbc(
        payload=denm.encode(),
        area_type=GeoNetworking.CIRCLE,
        center_lat=event.latitude,
        center_lon=event.longitude,
        radius=500,  # 米
        hop_limit=10,
        traffic_class=GeoNetworking.TC_HIGH_PRIORITY
    )
    
    print(f"Accident DENM broadcast: {event}")
    
    # 同时上报到交通控制中心
    report_to_control_center(event)

# 启动事故检测器
accident_detector.start(callback=on_accident_detected)
```

---

### P4 交换机（RSU 核心）要求

#### 硬件要求

**推荐型号**
- **Barefoot Tofino**: 6.4 Tbps, 4 Bpps
- **Barefoot Tofino 2**: 12.8 Tbps, 8 Bpps
- **Netronome Agilio CX SmartNIC**: 软硬件混合

**资源要求**
| 资源类型 | 最低要求 | 推荐配置 |
|---------|---------|---------|
| **TCAM** | 1 MB | 4 MB |
| **SRAM** | 50 MB | 200 MB |
| **端口数** | 8 x 1GbE | 32 x 10GbE |
| **包缓冲区** | 12 MB | 24 MB |
| **处理延迟** | < 1 μs | < 500 ns |

#### 软件要求

**P4 程序编译**
```bash
# 编译 GeoNetworking P4 程序
p4c-tofino \
    --target tofino \
    --arch tna \
    --p4runtime-files geo_forwarding.p4info.txt \
    -o geo_forwarding.json \
    geo_forwarding.p4

# 或使用 BMv2（开发测试）
p4c-bm2-ss \
    --p4runtime-files geo_forwarding.p4info.txt \
    -o geo_forwarding.json \
    geo_forwarding.p4
```

**运行时配置**
```bash
# 启动 Tofino 交换机（硬件）
./run_switchd.sh -p geo_forwarding

# 或启动 BMv2（软件）
simple_switch_grpc \
    --device-id 1 \
    --log-console \
    -i 1@veth1 -i 2@veth2 -i 3@veth3 -i 4@veth4 \
    geo_forwarding.json \
    -- --grpc-server-addr 0.0.0.0:50051

# 配置位置表
p4runtime-sh --grpc-addr localhost:50051 <<EOF
te = table_entry["LocationTable"](action="update_location")
te.match["gnAddress"] = 0x123456789ABCDEF0
te.action["latitude"] = 0x1E8B4567
te.action["longitude"] = 0x327B23C6
te.action["timestamp"] = 1234567890
te.insert()
EOF
```

---

### 网络连接要求

#### OBU ↔ RSU（无线）

**物理层**
- **频段**: 5.9 GHz ITS-G5
- **信道**: 
  - CCH (Control Channel): 178 (5890 MHz)
  - SCH (Service Channel): 180, 182 (可配置)
- **带宽**: 10 MHz / 20 MHz
- **发射功率**: 
  - OBU: 最大 23 dBm (200 mW)
  - RSU: 最大 33 dBm (2 W)
- **通信范围**: 
  - OBU: ~300m
  - RSU: ~500m
- **延迟**: < 10 ms

**MAC 层**
- **协议**: IEEE 802.11p (EDCA)
- **接入方式**: CSMA/CA
- **优先级队列**: 4 个（AC_BK, AC_BE, AC_VI, AC_VO）
- **DCC**: 动态拥塞控制

#### RSU ↔ RSU（有线）

**物理连接**
- **介质**: 光纤或 Cat6A 以太网
- **带宽**: 10 Gbps 或更高
- **延迟**: < 1 ms
- **协议**: 以太网 (IEEE 802.3)

**配置示例**
```bash
# RSU 间连接配置
# rsu-north port1 ↔ rsu-center port1
ifconfig eth1 up
ethtool -s eth1 speed 10000 duplex full
```

#### RSU ↔ 交通控制中心（回程网络）

**连接方式**
- **有线**: 光纤 / 以太网
- **无线**: 4G LTE / 5G NR

**带宽要求**
- 最低: 10 Mbps
- 推荐: 100 Mbps

**功能**
- 远程配置和管理
- 日志上传
- 事件上报
- 地图和 SPAT 更新

---

### 部署拓扑示例

```
     OBU-1 (Vehicle-1)        OBU-2 (Vehicle-2)
         |  (无线)                |  (无线)
         |  ITS-G5                |  ITS-G5
         |                        |
    [RSU-North] ========== [RSU-Center] ========== [RSU-East]
    (P4 Switch)   10Gbps    (P4 Switch)   10Gbps   (P4 Switch)
         |                        |                      |
         | 100Mbps                | 100Mbps              | (无线)
         | (回程)                 | (回程)               | ITS-G5
         |                        |                      |
    交通控制中心            交通信号灯              OBU-3 (Vehicle-3)
```

---

### 性能基准

| 指标 | OBU 要求 | RSU 要求 |
|------|---------|---------|
| **CAM 生成速率** | 10 Hz | N/A |
| **DENM 响应延迟** | < 50 ms | < 10 ms |
| **位置更新频率** | 10 Hz | 1 Hz (Beacon) |
| **消息处理速率** | 1k pps | 10k pps |
| **转发延迟** | N/A | < 1 ms (硬件) |
| **通信范围** | 300m | 500m |
| **定位精度** | < 5m | < 10cm (RTK) |

---

### 测试和验证要求

#### OBU 测试

```bash
# 1. GPS 定位测试
gpspipe -w -n 10

# 2. V2X 通信测试
iwconfig wlan0
iwlist wlan0 scan

# 3. CAM 发送测试
vanetza-cam-sender --interface wlan0 --rate 10

# 4. DENM 接收测试
vanetza-denm-receiver --interface wlan0
```

#### RSU 测试

```bash
# 1. P4 交换机测试
simple_switch_CLI --thrift-port 9090
> show_tables
> table_dump LocationTable

# 2. 覆盖范围测试
iperf3 -s -p 5201  # RSU 端
# OBU 端移动并测试
iperf3 -c rsu-ip -p 5201 -t 10

# 3. 转发性能测试
# 使用 pktgen 生成测试流量
pktgen-dpdk -l 0-3 -n 4 -- -P -m "[1:2].0"
```

---

### 认证和合规要求

#### 硬件认证

- **无线电认证**: 
  - 欧洲: EN 302 571 (ITS-G5)
  - 美国: FCC Part 95 (DSRC)
  - 中国: SRRC 认证
- **车规级认证**: 
  - ISO 16750（电气要求）
  - ISO 20524（硬件要求）
- **环境认证**: 
  - IP 防护等级
  - EMC 电磁兼容

#### 软件合规

- **协议标准**: 
  - ETSI EN 302 636 (GeoNetworking)
  - ETSI EN 302 637-2 (CAM)
  - ETSI EN 302 637-3 (DENM)
- **安全标准**: 
  - IEEE 1609.2 (安全服务)
  - ETSI TS 102 940 (安全管理)

---

## 使用方法

### 1. 编译 PNE 代码

```bash
cd input/GEO_example

# 使用 Makefile
make compile

# 或直接使用 Lynette
python -m lynette compile \
    --input geo_forwarding.pne \
    --topology topology.json \
    --service service.json \
    --output ../../output/geo_example/
```

### 2. 查看拓扑和配置

```bash
# 查看拓扑结构
make topology

# 查看转发流程
make flow

# 查看用例
make use-cases
```

### 3. 部署到P4交换机

```bash
# 启动 RSU 节点（需要 BMv2 或真实 P4 交换机）

# RSU-North
simple_switch_grpc --device-id 1 \
    -i 1@veth1 -i 2@veth2 -i 3@veth3 \
    output/geo_example/rsu-north.p4.json

# RSU-Center
simple_switch_grpc --device-id 2 \
    -i 1@veth4 -i 2@veth5 -i 3@veth6 -i 4@veth7 \
    output/geo_example/rsu-center.p4.json

# ... 其他 RSU 类似
```

### 4. 测试场景

本示例包含 4 个典型测试场景：

#### 场景 1: 紧急制动警告

```
Vehicle-1 紧急制动 → 向周边 200米 广播 DENM
路径: Vehicle-1 → RSU-North → RSU-Center → 
      → RSU-East → Vehicle-2
      → RSU-South → Vehicle-3
```

#### 场景 2: 紧急车辆接近

```
Emergency-Vehicle 接近路口 → 广播高优先级警告
路径: Emergency-V → RSU-West → RSU-Center → 所有方向
```

#### 场景 3: 协作感知

```
所有车辆周期性（10Hz）广播 CAM
RSU 维护位置表，实现邻居发现
```

#### 场景 4: 事故通知

```
路口东北象限事故 → 向事故区域广播 DENM
只有 RSU-North, RSU-East, RSU-Center 参与转发
```

## 消息类型

### CAM (Cooperative Awareness Message)
- **用途**：周期性广播车辆状态
- **频率**：10 Hz
- **GeoNetworking类型**：TSB（拓扑范围广播）
- **内容**：位置、速度、加速度、航向等

### DENM (Decentralized Environmental Notification Message)
- **用途**：事件驱动的危险警告
- **触发**：紧急制动、事故、道路危险等
- **GeoNetworking类型**：GBC（地理广播）
- **优先级**：高

### SPAT (Signal Phase and Timing)
- **用途**：交通信号相位和时间
- **发送者**：RSU（路边单元）
- **GeoNetworking类型**：GBC
- **目标区域**：路口区域

## 性能参数

| 参数 | 值 | 说明 |
|------|-----|------|
| Beacon间隔 | 1000 ms | RSU间位置信息交换频率 |
| CAM频率 | 10 Hz | 车辆状态广播频率 |
| 位置表大小 | 256 条目 | 每个RSU可维护的邻居数 |
| 序列号缓存 | 512 条目 | 防重复的缓存大小 |
| 最大跳数 | 10 | 数据包最大转发跳数 |
| 包生存时间 | 60 秒 | 数据包有效期 |
| 紧急消息延迟 | < 50 ms | 端到端延迟要求 |
| 安全消息成功率 | > 95% | 可靠性要求 |

## 地理区域类型

### 圆形区域（Circle）
```json
{
    "type": "circle",
    "center": {"latitude": 39.9065, "longitude": 116.3972},
    "radius_meters": 150
}
```

### 矩形区域（Rectangle）
```json
{
    "type": "rectangle",
    "center": {"latitude": 39.9065, "longitude": 116.3972},
    "width_meters": 100,
    "length_meters": 200,
    "angle_degrees": 45
}
```

### 椭圆区域（Ellipse）
```json
{
    "type": "ellipse",
    "center": {"latitude": 39.9065, "longitude": 116.3972},
    "semi_major_axis": 200,
    "semi_minor_axis": 100,
    "angle_degrees": 90
}
```

## 文件说明

### 核心文件

- **`geo_forwarding.pne`**: GeoNetworking 转发逻辑主文件
  - 包含所有核心转发模块
  - 实现 GeoRouter 应用

- **`include/geo_headers.pne`**: GeoNetworking 协议头部定义
  - 基于 ETSI EN 302 636 标准
  - 完整的头部结构定义

### 配置文件

- **`topology.json`**: 网络拓扑配置
  - 5个RSU的星型拓扑
  - 包含地理坐标信息
  - 车辆连接配置

- **`service.json`**: GeoNetworking 服务配置
  - RSU位置参数
  - 邻居位置映射
  - 用例场景定义

### 文档和脚本

- **`README.md`**: 本文档
- **`Makefile`**: 编译构建脚本
- **`quick_start.sh`**: 快速启动脚本

## 扩展方向

1. **完整的区域判断算法**
   - 当前是简化的距离计算
   - 可实现精确的点在多边形内算法
   - 支持复杂地理区域

2. **高级转发策略**
   - Contention-Based Forwarding (CBF)
   - Store-Carry-Forward (SCF)
   - 路由空洞恢复机制

3. **位置预测**
   - 基于速度和航向预测未来位置
   - 提高转发决策准确性

4. **安全机制**
   - 消息签名验证
   - 位置可信度验证
   - 防止恶意节点攻击

5. **QoS 支持**
   - 基于优先级的队列管理
   - 紧急消息快速通道
   - 拥塞控制

6. **与其他协议集成**
   - IPv6 over GeoNetworking
   - BTP (Basic Transport Protocol)
   - 应用层协议（CAM、DENM编解码）

## 标准参考

1. **ETSI EN 302 636-1**: GeoNetworking Part 1 - Requirements
2. **ETSI EN 302 636-2**: GeoNetworking Part 2 - Scenarios  
3. **ETSI EN 302 636-3**: GeoNetworking Part 3 - Network Architecture
4. **ETSI EN 302 636-4-1**: GeoNetworking Part 4-1 - Media-Independent Functionality
5. **ETSI EN 302 636-5-1**: GeoNetworking Part 5-1 - Transport Protocols
6. **ETSI EN 302 637-2**: V2X Applications - CAM
7. **ETSI EN 302 637-3**: V2X Applications - DENM

## 相关技术

- **ITS-G5**: 欧洲 5.9 GHz V2X 通信标准
- **DSRC**: 美国专用短程通信
- **C-V2X**: 基于蜂窝网络的 V2X 通信
- **IEEE 1609**: 美国 WAVE 协议栈
- **ISO 21217**: 智能交通系统站点与站点通信

## 许可证

本示例代码遵循开源许可证，可用于学术研究和商业应用。

## 联系方式

如有问题或建议，请通过项目仓库提交 Issue。

