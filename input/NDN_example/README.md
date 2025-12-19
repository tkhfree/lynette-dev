# NDN 网络示例 - 基于 NFD 规范的 P4 实现

## 概述

本示例展示了如何使用 Lynette PNE 语言在三个 P4 可编程交换机上实现一个完整的命名数据网络（Named Data Networking, NDN）。实现基于《NFD Developer's Guide》规范，包含了 NDN 转发平面的核心组件。

## 架构设计

### 拓扑结构

```
          Consumer1
              |
              | port 3
         [ndn-switch1] ----------- port 1 ----------- [ndn-switch2]
          (Arizona)      |                                  |
              |          |                                  | port 2
              | port 2   |                                  |
         Producer2       |                             [ndn-switch3]
                         |                              (UCLA)
                         |                                  |
                         +---------- port 2 ----------------+
                                                            | port 3
                                                            |
                                                       Producer1
```

### NDN 核心组件实现

根据 NFD Developer's Guide，本示例实现了以下核心组件：

#### 1. **Content Store (CS)** - 内容缓存
- **功能**: 缓存经过的 Data 包，加速内容检索
- **容量**: 每个交换机 256 条目
- **替换策略**: 简化的 FIFO（可扩展为 LRU）
- **位置**: `ndn_forwarding.pne` 的 `ContentStore` 模块

#### 2. **Pending Interest Table (PIT)** - 待处理兴趣表
- **功能**: 
  - 跟踪待处理的 Interest 包
  - 实现 Interest 聚合
  - 环路检测（基于 nonce）
  - 为返回的 Data 包提供转发路径
- **容量**: 每个交换机 1024 条目
- **位置**: `ndn_forwarding.pne` 的 `PendingInterestTable` 模块

#### 3. **Forwarding Information Base (FIB)** - 转发信息库
- **功能**: 
  - 基于名字前缀的路由决策
  - 支持最长前缀匹配
  - 配置 Interest 的转发路径
- **容量**: 每个交换机 512 条目
- **位置**: `ndn_forwarding.pne` 的 `ForwardingInformationBase` 模块

#### 4. **NDN Parser** - 数据包解析器
- **功能**: 
  - 识别 NDN Interest 和 Data 包
  - 提取名字并计算哈希
  - 设置处理元数据
- **位置**: `ndn_forwarding.pne` 的 `NDNParser` 模块

#### 5. **Statistics** - 统计模块
- **功能**: 
  - 统计 Interest/Data 包数量
  - 记录 CS 命中率
  - 记录 PIT 命中率
- **位置**: `ndn_forwarding.pne` 的 `NDNStatistics` 模块

## NDN 转发流程

### Interest 包处理流程

根据 NFD Developer's Guide 第 4 章描述的转发管道：

```
1. 接收 Interest
   ↓
2. CS 查找
   ├─ 命中 → 返回缓存的 Data
   └─ 未命中 ↓
3. PIT 查找
   ├─ 已存在 → Interest 聚合（检查 nonce）
   └─ 不存在 ↓
4. FIB 查找
   ↓
5. 转发到下一跳
   ↓
6. 记录到 PIT
```

### Data 包处理流程

```
1. 接收 Data
   ↓
2. PIT 查找
   ├─ 命中 → 按 PIT 记录的 face 转发
   │         ↓
   │      3. 缓存到 CS
   │         ↓
   │      4. 清除 PIT 条目
   └─ 未命中 → 丢弃（未请求的 Data）
```

## 文件说明

### 核心文件

- **`ndn_forwarding.pne`**: 主要的 NDN 转发逻辑实现
  - 实现了 CS、PIT、FIB 等核心数据结构
  - 定义了 `NDNRouter` 应用程序

- **`include/ndn_headers.pne`**: NDN 协议头部定义
  - Interest 包头部结构
  - Data 包头部结构
  - NDN 元数据定义
  - 基于 NDN Packet Format Specification (NDN-TLV)

- **`include/standard_headers.pne`**: 标准网络头部
  - 以太网头部
  - IPv4/UDP 头部（用于 NDN over UDP）

### 配置文件

- **`topology.json`**: 网络拓扑配置
  - 定义 3 个 P4 交换机
  - 配置交换机之间的链路
  - 描述主机连接

- **`service.json`**: NDN 服务配置
  - FIB 路由表配置
  - 端口映射
  - 转发策略参数
  - 测试场景定义

## 设备和协议栈要求

### 终端设备要求（Consumer）

#### 硬件要求

| 组件 | 最低要求 | 推荐配置 | 说明 |
|------|---------|---------|------|
| **处理器** | ARM Cortex-A7 / x86 双核 | ARM Cortex-A53 四核 / x86 四核 | 用于 Interest 生成和 Data 处理 |
| **内存** | 512 MB RAM | 2 GB RAM | 用于应用缓存和包处理 |
| **存储** | 4 GB eMMC/SD | 16 GB SSD | 存储应用和本地缓存 |
| **网络接口** | 1x 100Mbps 以太网 | 1x 1Gbps 以太网 | 连接到 NDN 网络 |
| **可选** | Wi-Fi (802.11n) | Wi-Fi 6 (802.11ax) | 无线接入 |

#### 软件要求

**操作系统**
- Linux 发行版（Ubuntu 20.04+, Debian 11+, Raspberry Pi OS）
- 或 macOS 10.15+
- 或 Windows 10/11（使用 WSL2）

**必需软件栈**
```
┌─────────────────────────────────────┐
│  应用层                              │
│  - NDN应用程序 (ndnping, ndnputchunks, etc.) │
├─────────────────────────────────────┤
│  NDN协议栈                           │
│  - ndn-cxx (C++ 库)                 │
│  - NDN Forwarding Daemon (NFD)      │
│    或 Mini-NDN (测试用)              │
├─────────────────────────────────────┤
│  传输层                              │
│  - TCP/UDP (用于 NDN over TCP/UDP)  │
│  - 或直接使用以太网 (NDN over Ethernet) │
├─────────────────────────────────────┤
│  网络层                              │
│  - 本地 NDN 转发表                   │
│  - Face 管理                         │
├─────────────────────────────────────┤
│  链路层                              │
│  - Ethernet / Wi-Fi 驱动             │
└─────────────────────────────────────┘
```

**依赖包**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential libssl-dev libsqlite3-dev \
    libboost-all-dev libpcap-dev pkg-config

# 安装 ndn-cxx
git clone https://github.com/named-data/ndn-cxx.git
cd ndn-cxx
./waf configure
./waf
sudo ./waf install

# 安装 NFD (可选，用于本地转发)
git clone https://github.com/named-data/NFD.git
cd NFD
./waf configure
./waf
sudo ./waf install
```

**配置示例**
```bash
# Consumer 配置文件 (~/.ndn/client.conf)
transport=tcp://ndn-switch1:6363
```

#### 协议栈配置

**Face 配置**
```bash
# 创建到 NDN 交换机的 Face
nfdc face create tcp4://192.168.1.1:6363

# 添加路由
nfdc route add /ndn/edu/ucla tcp4://192.168.1.1:6363
```

**Interest 发送示例**
```bash
# 使用 ndnping 测试
ndnping /ndn/edu/ucla

# 使用 ndncatchunks 获取文件
ndncatchunks /ndn/edu/ucla/video/lecture1
```

#### Consumer 本地缓存配置（重要）

**是否需要本地缓存？** ✅ **强烈推荐配置本地缓存**

Consumer 端配置本地缓存可以显著提升性能：

**1. NFD 本地缓存配置**

Consumer 可以运行轻量级 NFD 实例作为本地缓存代理：

```bash
# 安装并启动 NFD
nfd-start

# 配置 NFD 缓存大小
nfdc cs config capacity 1000  # 缓存 1000 个 Data 包

# 查看缓存状态
nfdc cs info
```

**2. Consumer 缓存配置文件**
```bash
# ~/.ndn/nfd.conf
general {
  user ndn
  group ndn
}

# Content Store 配置
tables {
  cs_max_packets 1000      # 最大缓存包数
  cs_policy lru            # 缓存替换策略：LRU
  cs_unsolicited_policy drop-all
}

# Face 配置
face_system {
  tcp {
    listen yes
    port 6363
    enable_v4 yes
    enable_v6 no
  }
  
  udp {
    listen yes
    port 6363
    enable_v4 yes
    enable_v6 no
    mcast no  # Consumer 不需要组播
  }
}
```

**3. 应用层缓存**

对于特定应用，可以实现应用层缓存：

```python
#!/usr/bin/env python3
from pyndn import Name, Face
from pyndn.security import KeyChain
import time
from collections import OrderedDict

class NDNConsumerWithCache:
    def __init__(self, cache_size=100):
        self.face = Face()
        self.cache = OrderedDict()  # LRU 缓存
        self.cache_size = cache_size
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_data(self, name_str):
        """获取数据，优先从缓存"""
        # 1. 检查本地缓存
        if name_str in self.cache:
            self.cache_hits += 1
            print(f"✓ Cache HIT: {name_str}")
            # LRU: 移到最后（最近使用）
            self.cache.move_to_end(name_str)
            return self.cache[name_str]
        
        # 2. 缓存未命中，发送 Interest
        self.cache_misses += 1
        print(f"✗ Cache MISS: {name_str}, sending Interest...")
        
        interest = Interest(Name(name_str))
        interest.setInterestLifetimeMilliseconds(4000)
        interest.setMustBeFresh(True)
        
        data_content = None
        
        def on_data(interest, data):
            nonlocal data_content
            data_content = data.getContent().toBytes()
            
            # 3. 存入缓存
            self.cache[name_str] = data_content
            
            # 4. 维护缓存大小（LRU 淘汰）
            if len(self.cache) > self.cache_size:
                evicted = self.cache.popitem(last=False)  # 淘汰最旧的
                print(f"Cache eviction: {evicted[0]}")
        
        def on_timeout(interest):
            print(f"Timeout: {interest.getName().toUri()}")
        
        self.face.expressInterest(interest, on_data, on_timeout)
        
        # 等待响应
        timeout = time.time() + 4
        while data_content is None and time.time() < timeout:
            self.face.processEvents()
            time.sleep(0.01)
        
        return data_content
    
    def get_cache_stats(self):
        """获取缓存统计"""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': f'{hit_rate:.2%}',
            'cache_size': len(self.cache)
        }

# 使用示例
consumer = NDNConsumerWithCache(cache_size=100)

# 第一次请求（缓存未命中）
data1 = consumer.get_data('/ndn/edu/ucla/video/segment1')

# 第二次请求相同内容（缓存命中）
data2 = consumer.get_data('/ndn/edu/ucla/video/segment1')

# 查看缓存统计
stats = consumer.get_cache_stats()
print(f"Cache statistics: {stats}")
```

**4. Consumer 缓存策略选择**

| 场景 | 推荐策略 | 缓存大小 | 说明 |
|------|---------|---------|------|
| **视频流播放** | LRU + 预取 | 500-1000 包 | 缓存最近播放的段 |
| **文件下载** | FIFO | 100-200 包 | 顺序访问，简单缓存 |
| **网页浏览** | LRU | 200-500 包 | 缓存常访问资源 |
| **实时数据** | 不缓存或极小 | 10-20 包 | 数据实时性要求高 |
| **IoT 传感器数据** | Time-based | 50-100 包 | 基于时间的缓存过期 |

**5. Consumer 缓存效果示例**

```bash
# 测试缓存效果
# 第一次请求（网络获取）
time ndncatchunks /ndn/edu/ucla/video/lecture1
# 输出：Downloaded in 2.5 seconds

# 第二次请求（缓存命中）
time ndncatchunks /ndn/edu/ucla/video/lecture1
# 输出：Downloaded in 0.1 seconds (25x 加速！)
```

**缓存收益分析**
- **减少网络延迟**: 本地缓存访问 < 1ms，网络访问 10-100ms
- **降低网络负载**: 缓存命中率 50% 可减少一半网络流量
- **提升用户体验**: 热点内容快速响应
- **减轻服务器压力**: Producer 负载显著降低

---

### 服务端设备要求（Producer）

#### 硬件要求

| 组件 | 最低要求 | 推荐配置 | 说明 |
|------|---------|---------|------|
| **处理器** | x86 四核 / ARM Cortex-A53 | x86 八核 / ARM Cortex-A72 | 处理大量 Interest 请求 |
| **内存** | 2 GB RAM | 8 GB RAM | 缓存热点内容 |
| **存储** | 100 GB HDD | 500 GB SSD | 存储内容数据 |
| **网络接口** | 1x 1Gbps 以太网 | 2x 10Gbps 以太网 | 高带宽内容分发 |

#### 软件要求

**操作系统**
- Linux 服务器版（Ubuntu Server 20.04+, CentOS 8+, Debian 11+）

**完整协议栈**
```
┌─────────────────────────────────────┐
│  内容服务层                          │
│  - 内容管理系统                      │
│  - 访问控制                          │
│  - 内容签名服务                      │
├─────────────────────────────────────┤
│  应用层                              │
│  - ndnputfile (发布内容)             │
│  - ndnpingserver (测试服务)          │
│  - ndn-svs (状态同步)                │
├─────────────────────────────────────┤
│  NDN协议栈                           │
│  - ndn-cxx 库                        │
│  - NFD (本地转发守护进程)            │
├─────────────────────────────────────┤
│  传输层                              │
│  - TCP/UDP Tunnel                    │
│  - Ethernet Face                     │
├─────────────────────────────────────┤
│  链路层                              │
│  - Ethernet 接口                     │
└─────────────────────────────────────┘
```

**Producer 配置**
```bash
# 启动 NFD
nfd-start

# 配置前缀注册
nfdc strategy set /ndn/edu/arizona /localhost/nfd/strategy/multicast
nfdc cs config capacity 10000

# 发布内容
ndnputchunks /ndn/edu/arizona/data/sensor1 < data.bin
```

#### Producer 缓存服务配置（关键）

**是否需要缓存服务？** ✅ **必须配置，这是 Producer 的核心功能**

Producer 需要配置完善的缓存服务来高效分发内容：

**1. NFD 大容量缓存配置**

```bash
# /etc/ndn/nfd.conf - Producer 配置
tables {
  # 大容量 Content Store
  cs_max_packets 100000        # 缓存 10 万个 Data 包
  cs_policy lru                # LRU 替换策略
  
  # 接受未请求的 Data（用于内容预发布）
  cs_unsolicited_policy admit-all
  
  # PIT 配置
  pit_lifetime_max 60000       # PIT 条目最长保留 60 秒
}

# 策略配置
strategy_choice {
  /ndn/edu/arizona /localhost/nfd/strategy/multicast/%FD%03
}
```

**2. 内容仓库服务（Repo）**

Producer 应该运行 NDN 内容仓库服务来持久化存储内容：

```bash
# 安装 ndn-repo-ng
git clone https://github.com/named-data/repo-ng.git
cd repo-ng
./waf configure --with-tests
./waf
sudo ./waf install

# 启动 Repo
ndn-repo-ng /etc/ndn/repo.conf &
```

**Repo 配置文件**
```json
{
  "repo_config": {
    "repo_capacity": 10000000,  // 10GB
    "data_path": "/var/ndn/repo",
    "tcp_bulk_insert": {
      "host": "localhost",
      "port": 7376,
      "enable": true
    }
  },
  "validator": {
    "trust_anchor": {
      "type": "file",
      "file_name": "/etc/ndn/keys/trust.cert"
    }
  }
}
```

**3. 内容发布和缓存脚本**

```python
#!/usr/bin/env python3
"""
NDN Producer with Content Repository
实现内容发布、缓存管理、热点识别
"""
from pyndn import Name, Data, Face
from pyndn.security import KeyChain
from pyndn.util import Blob
import os
import time
from collections import Counter
import threading

class NDNProducerWithRepo:
    def __init__(self, prefix, repo_path):
        self.face = Face()
        self.keyChain = KeyChain()
        self.prefix = Name(prefix)
        self.repo_path = repo_path
        
        # 内容缓存（内存中的热数据）
        self.hot_cache = {}  # 热点内容快速缓存
        self.hot_cache_max = 1000
        
        # 访问统计（识别热点）
        self.access_counter = Counter()
        self.access_lock = threading.Lock()
        
        # 注册前缀
        self.face.registerPrefix(
            self.prefix,
            self.on_interest,
            self.on_register_failed
        )
        
        print(f"✓ Producer started, prefix: {self.prefix.toUri()}")
        print(f"✓ Repository: {self.repo_path}")
        
        # 启动统计线程
        self.stats_thread = threading.Thread(target=self.print_stats)
        self.stats_thread.daemon = True
        self.stats_thread.start()
    
    def on_interest(self, prefix, interest, face, interestFilterId, filter):
        """处理 Interest 请求"""
        name = interest.getName()
        name_str = name.toUri()
        
        # 记录访问
        with self.access_lock:
            self.access_counter[name_str] += 1
        
        # 1. 检查热点缓存（最快）
        if name_str in self.hot_cache:
            print(f"🔥 Hot cache HIT: {name_str}")
            data = self.hot_cache[name_str]
            face.putData(data)
            return
        
        # 2. 从 Repo 加载内容
        data = self.load_from_repo(name)
        
        if data:
            print(f"💾 Repo HIT: {name_str}")
            
            # 3. 更新热点缓存
            self.update_hot_cache(name_str, data)
            
            # 4. 发送 Data
            face.putData(data)
        else:
            print(f"❌ Not found: {name_str}")
            # 发送 Nack（可选）
    
    def load_from_repo(self, name):
        """从内容仓库加载数据"""
        # 将 Name 转换为文件路径
        file_path = self.name_to_filepath(name)
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 构造 Data 包
            data = Data(name)
            data.setContent(Blob(content))
            data.getMetaInfo().setFreshnessPeriod(10000)  # 10秒
            self.keyChain.sign(data)
            
            return data
        
        return None
    
    def update_hot_cache(self, name_str, data):
        """更新热点缓存（基于访问频率）"""
        access_count = self.access_counter[name_str]
        
        # 访问次数 > 5 认为是热点
        if access_count >= 5:
            if len(self.hot_cache) >= self.hot_cache_max:
                # 淘汰访问最少的
                min_name = min(
                    self.hot_cache.keys(),
                    key=lambda n: self.access_counter[n]
                )
                del self.hot_cache[min_name]
            
            self.hot_cache[name_str] = data
            print(f"🔥 Added to hot cache: {name_str} (访问 {access_count} 次)")
    
    def name_to_filepath(self, name):
        """将 NDN Name 转换为文件系统路径"""
        # /ndn/edu/arizona/video/segment1 
        # -> repo/ndn/edu/arizona/video/segment1.data
        components = [name.get(i).toEscapedString() for i in range(name.size())]
        rel_path = os.path.join(*components) + '.data'
        return os.path.join(self.repo_path, rel_path)
    
    def publish_content(self, name_str, content):
        """发布内容到仓库"""
        name = Name(name_str)
        file_path = self.name_to_filepath(name)
        
        # 创建目录
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入文件
        with open(file_path, 'wb') as f:
            if isinstance(content, str):
                f.write(content.encode())
            else:
                f.write(content)
        
        print(f"✓ Published: {name_str} -> {file_path}")
    
    def print_stats(self):
        """定期打印统计信息"""
        while True:
            time.sleep(30)  # 每 30 秒
            
            print("\n" + "="*60)
            print("📊 Producer Statistics (Last 30s)")
            print("="*60)
            
            # 前 10 热点内容
            top_10 = self.access_counter.most_common(10)
            if top_10:
                print("\n🔥 Top 10 Hot Contents:")
                for name, count in top_10:
                    print(f"  {count:4d}x  {name}")
            
            # 缓存统计
            print(f"\n💾 Cache Status:")
            print(f"  Hot cache size: {len(self.hot_cache)}/{self.hot_cache_max}")
            print(f"  Total unique content accessed: {len(self.access_counter)}")
            print("="*60 + "\n")
    
    def run(self):
        """运行事件循环"""
        while True:
            self.face.processEvents()
            time.sleep(0.01)

# 使用示例
if __name__ == '__main__':
    producer = NDNProducerWithRepo(
        prefix='/ndn/edu/arizona',
        repo_path='/var/ndn/repo'
    )
    
    # 发布一些示例内容
    for i in range(100):
        producer.publish_content(
            f'/ndn/edu/arizona/video/segment{i}',
            f'Video segment {i} data...'.encode()
        )
    
    # 运行
    producer.run()
```

**4. Producer 分层缓存架构**

```
请求流程:

Interest →  [L1: 热点内存缓存]  ← 最快 (< 1ms)
               ↓ Miss
           [L2: NFD CS]         ← 快 (< 5ms)
               ↓ Miss
           [L3: Repo SSD]       ← 中等 (< 20ms)
               ↓ Miss
           [L4: 冷存储/HDD]     ← 慢 (< 100ms)
               ↓ Miss
           [生成或从源获取]      ← 最慢 (100ms+)
```

**5. Producer 缓存预热**

```bash
#!/bin/bash
# 内容预热脚本 - 在 Producer 启动时执行

echo "开始内容预热..."

# 1. 预热热点视频
for i in {1..100}; do
    ndnputchunks /ndn/edu/arizona/video/popular/segment$i < video_segment_$i.bin
done

# 2. 预热常访问的静态内容
ndnputfile /ndn/edu/arizona/static/index.html < index.html
ndnputfile /ndn/edu/arizona/static/style.css < style.css

# 3. 发送到 Repo
for name in $(cat hot_content_list.txt); do
    ndn-repo-ng-insert $name
done

echo "✓ 内容预热完成"
```

**6. Producer 缓存监控**

```bash
# 监控脚本
#!/bin/bash
watch -n 5 'echo "=== NFD CS Stats ===" && nfdc cs info && \
            echo "" && \
            echo "=== Top Processes ===" && \
            ps aux | grep nfd | head -5'
```

---

**内容发布脚本**
```python
#!/usr/bin/env python3
from pyndn import Name, Data, Face
from pyndn.security import KeyChain

face = Face()
keyChain = KeyChain()

def onInterest(prefix, interest, face, interestFilterId, filter):
    # 生成 Data 包
    data = Data(interest.getName())
    data.setContent("Hello from Producer!")
    keyChain.sign(data)
    face.putData(data)
    print(f"Replied to: {interest.getName().toUri()}")

# 注册前缀
face.registerPrefix("/ndn/edu/arizona", onInterest, 
                    lambda prefix: print(f"Prefix registered: {prefix.toUri()}"))

while True:
    face.processEvents()
```

---

### NDN 交换机（P4 交换机）要求

#### 硬件要求

**裸金属 P4 交换机**
- **推荐型号**: 
  - Barefoot Tofino (Intel)
  - Barefoot Tofino 2
  - Netronome Agilio SmartNIC
- **端口**: 至少 8x 1GbE 或 4x 10GbE
- **内存**: 
  - 包缓冲区: 12 MB+
  - 表内存: TCAM 2MB, SRAM 100MB+
- **处理能力**: > 1 Bpps (Billion packets per second)

**软件交换机（用于开发测试）**
- **BMv2 (Behavioral Model v2)**
  - 软件实现的 P4 交换机
  - 用于原型开发和测试
- **运行环境**: 
  - CPU: 4+ 核心
  - 内存: 4 GB+
  - 操作系统: Linux

#### 软件要求

**P4 运行时环境**
```
┌─────────────────────────────────────┐
│  控制平面                            │
│  - P4Runtime API                     │
│  - Table 配置管理                    │
├─────────────────────────────────────┤
│  数据平面                            │
│  - P4 编译后的程序                   │
│  - NDN 转发逻辑 (CS, PIT, FIB)      │
├─────────────────────────────────────┤
│  P4 运行时                           │
│  - simple_switch_grpc (BMv2)         │
│  - 或 Tofino SDE (硬件交换机)        │
├─────────────────────────────────────┤
│  驱动层                              │
│  - 网卡驱动                          │
└─────────────────────────────────────┘
```

**所需工具链**
```bash
# 安装 P4C 编译器
git clone https://github.com/p4lang/p4c.git
cd p4c
mkdir build && cd build
cmake ..
make && sudo make install

# 安装 BMv2
git clone https://github.com/p4lang/behavioral-model.git
cd behavioral-model
./install_deps.sh
./autogen.sh
./configure
make && sudo make install

# 安装 P4Runtime
pip3 install p4runtime p4runtime-sh
```

**交换机配置**
```bash
# 启动 P4 交换机
simple_switch_grpc \
    --device-id 1 \
    -i 1@veth1 -i 2@veth2 -i 3@veth3 \
    --log-console \
    ndn-switch1.json

# 通过 P4Runtime 配置表项
echo "
table_add ContentStore add_cs_entry 0x12345678 => 1
table_add PendingInterestTable add_pit_entry 0x23456789 => 2
table_add ForwardingInformationBase fib_forward 0x34567890 => 3
" | simple_switch_CLI --thrift-port 9090
```

---

### 网络连接要求

#### Consumer ↔ NDN Switch

**物理连接**
- 以太网: Cat5e 及以上
- 带宽: 至少 100 Mbps，推荐 1 Gbps
- 延迟: < 10 ms

**协议配置**
```bash
# Consumer 端配置
# /etc/ndn/client.conf
transport=ether://[ndn-switch1-mac]
```

#### Producer ↔ NDN Switch

**物理连接**
- 以太网: Cat6 及以上
- 带宽: 1 Gbps - 10 Gbps
- 延迟: < 5 ms

**协议配置**
```bash
# Producer 端配置
# 注册到交换机的端口
nfdc face create ether://[ndn-switch1-mac]
nfdc route add /ndn/edu/arizona ether://[ndn-switch1-mac]
```

#### NDN Switch ↔ NDN Switch

**物理连接**
- 以太网: Cat6/Cat6a/光纤
- 带宽: 10 Gbps 或更高
- 延迟: < 1 ms（本地）, < 10 ms（广域）

---

### 部署拓扑示例

```
                Consumer1 (192.168.1.10)
                     | eth0
                     | 1 Gbps
                     |
            +--------+--------+
            | ndn-switch1     |
            | (P4 Switch)     |
            | 192.168.1.1     |
            +--------+--------+
                     | port1 (10 Gbps)
                     |
            +--------+--------+
            | ndn-switch2     |
            | (P4 Switch)     |
            | 192.168.1.2     |
            +--------+--------+
                     | port2 (10 Gbps)
                     |
            +--------+--------+
            | ndn-switch3     |
            | (P4 Switch)     |
            | 192.168.1.3     |
            +--------+--------+
                     | port3
                     | 1 Gbps
                     |
                Producer1 (192.168.1.20)
                  | eth0
```

---

### 性能基准

| 指标 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **Interest 处理速率** | 10k pps | 100k pps |
| **Data 处理速率** | 10k pps | 100k pps |
| **CS 命中延迟** | < 1 ms | < 100 μs |
| **端到端延迟** | < 100 ms | < 10 ms |
| **吞吐量** | 100 Mbps | 1 Gbps+ |

---

## 使用方法

### 1. 编译 PNE 代码

使用 Lynette 编译器将 PNE 代码编译为 P4 代码：

```bash
cd /path/to/lynette-dev
python -m lynette compile \
    --input input/NDN_example/ndn_forwarding.pne \
    --topology input/NDN_example/topology.json \
    --service input/NDN_example/service.json \
    --output output/ndn_example/
```

### 2. 查看生成的 P4 代码

编译完成后，将在输出目录生成三个交换机的 P4 代码：

```
output/ndn_example/
├── ndn-switch1.p4
├── ndn-switch1_entry.json
├── ndn-switch2.p4
├── ndn-switch2_entry.json
├── ndn-switch3.p4
└── ndn-switch3_entry.json
```

### 3. 部署到 P4 交换机

将生成的 P4 代码部署到实际的 P4 交换机或仿真环境（如 BMv2）：

```bash
# 示例：使用 BMv2 仿真器
simple_switch_grpc --device-id 1 \
    -i 1@veth1 -i 2@veth2 -i 3@veth3 -i 4@veth4 \
    output/ndn_example/ndn-switch1.p4.json
```

## NDN 数据包格式

### Interest 包结构（简化）

```
+------------------+
| Ethernet Header  | 14 bytes
|  - Dst MAC       |
|  - Src MAC       |
|  - Type: 0x8624  | (NDN EtherType)
+------------------+
| NDN Interest     |
|  - Type: 0x05    | 1 byte
|  - Length        | 1 byte
|  - Name          |
|    - Type: 0x07  | 1 byte
|    - Length      | 1 byte
|    - Prefix      | 32 bytes (简化)
|  - Nonce         | 4 bytes
|  - Lifetime      | 4 bytes
+------------------+
```

### Data 包结构（简化）

```
+------------------+
| Ethernet Header  | 14 bytes
+------------------+
| NDN Data         |
|  - Type: 0x06    | 1 byte
|  - Length        | 1 byte
|  - Name          | 34 bytes
|  - MetaInfo      | 2 bytes
|  - Content Type  | 2 bytes
|  - Freshness     | 4 bytes
|  - Content       | (变长)
+------------------+
```

## 测试场景

### 场景 1: 基本内容检索

Consumer1 向 Producer1 请求内容：

1. Consumer1 发送 Interest: `/ndn/edu/ucla/video/lecture1`
2. Interest 经过: ndn-switch1 → ndn-switch3
3. Producer1 响应 Data
4. Data 返回: ndn-switch3 → ndn-switch1 → Consumer1

### 场景 2: 内容缓存测试

多个 Consumer 请求相同内容：

1. 第一个 Interest 到达 ndn-switch2，未命中 CS
2. 转发到 Producer，Data 返回并缓存
3. 第二个 Interest 到达 ndn-switch2，CS 命中
4. 直接从缓存返回 Data，无需再次请求 Producer

### 场景 3: Interest 聚合

多个 Consumer 同时请求相同内容：

1. Interest-1 到达并记录到 PIT
2. Interest-2 到达，检测到 PIT 中已有相同请求
3. 聚合 Interest-2，不重复转发
4. Data 返回时，同时满足两个 Interest

## 性能参数

基于 NFD Developer's Guide 的建议：

- **PIT Lifetime**: 4000ms（Interest 生存时间）
- **CS Size**: 256 条目（可根据内存调整）
- **PIT Size**: 1024 条目
- **FIB Size**: 512 条目
- **Name Hash**: 32-bit hash（用于快速查表）

## 扩展方向

本示例是基础实现，可以扩展的方向：

1. **完整的 TLV 解析**: 当前使用简化的固定长度名字，可扩展为完整的 TLV 编解码
2. **多路径转发**: 实现 multicast 策略，向多个 face 转发 Interest
3. **自适应转发**: 实现 ASF（Adaptive SRTT-based Forwarding）策略
4. **完整的 CS 替换策略**: 实现 LRU 或其他高级缓存替换算法
5. **Nack 支持**: 实现 NDN Nack 机制处理拥塞
6. **NDNLP**: 实现链路层协议，支持分片和可靠传输
7. **安全机制**: 添加签名验证功能

## 参考资料

1. **NFD Developer's Guide**: `ndn-0021-10-nfd-developer-guide.pdf`
   - 第 2 章: Face System
   - 第 3 章: Tables (FIB, PIT, CS)
   - 第 4 章: Forwarding Pipelines
   - 第 5 章: Forwarding Strategies

2. **NDN Packet Format Specification**: http://named-data.net/doc/ndn-tlv/

3. **NFD Management Protocol**: https://redmine.named-data.net/projects/nfd/wiki/Management

## 作者与贡献

基于 NFD 团队的设计和规范实现。

## 许可证

本示例代码遵循与 NFD 相同的开源许可证。

