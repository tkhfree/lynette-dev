# IPv4 企业网络示例

## 概述

本示例展示了如何使用 Lynette PNE 语言在 P4 可编程交换机上实现完整的 IPv4 企业网络。基于 **RFC 791 (IPv4)** 和 **RFC 1812 (路由器要求)** 标准，实现了三层网络架构。

## 网络拓扑

```
                      [Core Router]
                      (10.0.0.1)
                       /       \
                   10G /         \ 10G
                      /           \
            [Dist-Switch1]    [Dist-Switch2]
            (192.168.1.1)     (192.168.2.1)
                   |                |
                1G |                | 1G
                   |                |
          [Access-Switch1]  [Access-Switch2]
                   |                |
              PC1, PC2           PC3, PC4
          (192.168.1.x)      (192.168.2.x)
```

## IPv4 核心功能

### 1. **IPv4Parser** - 数据包解析
- 解析以太网和 IPv4 头部
- 识别传输层协议（TCP/UDP/ICMP）
- TTL 检查和递减
- 版本验证

### 2. **IPv4RoutingTable** - 路由表
- 最长前缀匹配（LPM）
- 支持直连网络和静态路由
- 默认路由配置
- 下一跳解析

### 3. **ARPTable** - 地址解析
- ARP 缓存管理
- 自动学习 IP-MAC 映射
- 超时机制

### 4. **AccessControlList** - 访问控制
- 基于源/目标 IP 的过滤
- 协议和端口过滤
- 允许/拒绝规则

### 5. **QoSClassifier** - 服务质量
- DSCP 标记识别
- 队列优先级设置
- 流量分类

### 6. **IPv4Statistics** - 统计
- 按协议统计流量
- 字节和包计数
- 丢包统计

## 设备和协议栈要求

### 终端设备（PC/工作站）

#### 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **处理器** | 双核 2GHz | 四核 3GHz |
| **内存** | 4 GB | 8 GB |
| **网卡** | 1 Gbps | 1 Gbps |
| **存储** | 128 GB SSD | 256 GB SSD |

#### 软件要求

**操作系统**
- Windows 10/11
- Linux (Ubuntu 20.04+)
- macOS 10.15+

**网络配置**
```bash
# Linux 示例
# /etc/network/interfaces
auto eth0
iface eth0 inet static
    address 192.168.1.10
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 8.8.8.8 8.8.4.4

# Windows PowerShell
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.1.10 `
    -PrefixLength 24 -DefaultGateway 192.168.1.1
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" `
    -ServerAddresses 8.8.8.8,8.8.4.4
```

**协议栈**
```
┌─────────────────────────────┐
│  应用层 (HTTP, FTP, SSH)    │
├─────────────────────────────┤
│  传输层 (TCP, UDP)          │
├─────────────────────────────┤
│  网络层 (IPv4, ICMP, ARP)   │
├─────────────────────────────┤
│  数据链路层 (Ethernet)       │
├─────────────────────────────┤
│  物理层 (1000BASE-T)        │
└─────────────────────────────┘
```

### 服务器设备

#### 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **处理器** | 四核 3GHz | 八核 3.5GHz |
| **内存** | 16 GB | 64 GB |
| **网卡** | 1 Gbps | 10 Gbps |
| **存储** | 500 GB SSD | 2 TB NVMe |

#### 服务器配置示例

**Web 服务器**
```bash
# 安装 Nginx
sudo apt-get install nginx

# 配置静态 IP
# /etc/netplan/01-netcfg.yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses: [10.0.0.10/24]
      gateway4: 10.0.0.1
      nameservers:
        addresses: [8.8.8.8]

sudo netplan apply
```

**数据库服务器**
```bash
# 安装 MySQL
sudo apt-get install mysql-server

# 绑定到特定 IP
# /etc/mysql/mysql.conf.d/mysqld.cnf
bind-address = 10.0.0.11

# 防火墙规则（仅允许内网访问）
sudo ufw allow from 10.0.0.0/8 to any port 3306
sudo ufw enable
```

### P4 交换机设备

#### 核心路由器要求

**硬件规格**
- **型号**: Barefoot Tofino 2
- **端口**: 32 x 100GbE
- **转发能力**: 12.8 Tbps
- **路由表**: 100,000+ 条目
- **内存**: TCAM 4MB, SRAM 200MB

**软件要求**
```bash
# 编译 IPv4 P4 程序
p4c-tofino --target tofino2 \
    -o ipv4_router.json \
    ipv4_forwarding.p4

# 启动交换机
./run_switchd.sh -p ipv4_router
```

**路由配置**
```bash
# 配置路由表
p4runtime-sh <<EOF
table_add IPv4RoutingTable route_ipv4 \
    192.168.1.0/24 => 10.0.1.2 1
table_add IPv4RoutingTable route_ipv4 \
    192.168.2.0/24 => 10.0.1.6 2
EOF
```

#### 分布层交换机要求

**硬件规格**
- **型号**: Barefoot Tofino
- **端口**: 48 x 10GbE + 4 x 100GbE
- **转发能力**: 6.4 Tbps
- **路由表**: 10,000 条目
- **VLAN**: 4096

#### 接入层交换机要求

**硬件规格**
- **端口**: 24 x 1GbE
- **转发能力**: 48 Gbps
- **PoE**: IEEE 802.3at (30W/端口)
- **简化路由**: 仅默认网关

## 网络配置

### IP 地址规划

| 网段 | 用途 | VLAN | 主机数 |
|------|------|------|--------|
| 10.0.0.0/24 | 管理和服务器 | 1 | 254 |
| 10.0.1.0/30 | 核心-分布互连 | 10-11 | 2 |
| 192.168.1.0/24 | 楼层1用户 | 100 | 254 |
| 192.168.2.0/24 | 楼层2用户 | 200 | 254 |

### 路由表配置

**核心路由器**
```
目标网络          掩码             下一跳        接口    度量
192.168.1.0    255.255.255.0    10.0.1.2      eth1     10
192.168.2.0    255.255.255.0    10.0.1.6      eth2     10
0.0.0.0        0.0.0.0          Internet-GW   eth0     1
```

**分布层交换机1**
```
目标网络          掩码             下一跳        接口    度量
0.0.0.0        0.0.0.0          10.0.1.1      eth1     1
192.168.1.0    255.255.255.0    0.0.0.0       eth2     0 (直连)
```

### ACL 配置

```bash
# 允许用户访问 Web 服务器
acl 100 permit tcp any 10.0.0.10 eq 80
acl 100 permit tcp any 10.0.0.10 eq 443

# 禁止用户直接访问数据库
acl 200 deny tcp 192.168.0.0/16 10.0.0.11 eq 3306
acl 200 deny tcp 192.168.0.0/16 10.0.0.11 eq 5432

# 允许 ICMP (ping)
acl 300 permit icmp any any
```

### QoS 配置

```bash
# 标记 VoIP 流量为最高优先级
class-map voice
  match protocol sip
  match udp port 5060
  set dscp ef (46)
  set queue 3

# 标记视频流量
class-map video
  match protocol h323
  set dscp af41 (34)
  set queue 2

# 关键业务流量
class-map critical
  match tcp port 22 (SSH)
  match tcp port 3389 (RDP)
  set dscp af31 (26)
  set queue 1
```

## 使用方法

### 1. 编译 PNE 代码

```bash
cd input/IPv4_example

# 使用 Makefile
make compile

# 或直接使用 Lynette
python -m lynette compile \
    --input ipv4_forwarding.pne \
    --topology topology.json \
    --service service.json \
    --output ../../output/ipv4_example/
```

### 2. 部署到 P4 交换机

```bash
# 核心路由器
simple_switch_grpc --device-id 1 \
    -i 1@veth1 -i 2@veth2 -i 10@veth10 \
    output/ipv4_example/core-router.json

# 分布层交换机1
simple_switch_grpc --device-id 2 \
    -i 1@veth3 -i 2@veth4 \
    output/ipv4_example/dist-switch1.json
```

### 3. 测试网络连通性

```bash
# 测试 1: Ping 测试
ping -c 4 192.168.1.1  # Ping 网关
ping -c 4 10.0.0.10    # Ping Web 服务器

# 测试 2: Traceroute
traceroute 10.0.0.10

# 测试 3: HTTP 访问
curl http://10.0.0.10

# 测试 4: 带宽测试
iperf3 -c 10.0.0.10 -t 30
```

## 应用场景

### 场景 1: Web 访问

```
PC1 (192.168.1.10) 访问 Web 服务器 (10.0.0.10)

1. PC1 发送 HTTP 请求
2. Access-Switch1 转发到网关 (192.168.1.1)
3. Dist-Switch1 查路由表，转发到 Core-Router
4. Core-Router 查 ACL，允许 TCP 80
5. Core-Router 转发到 Server1
6. Server1 响应，数据包原路返回
```

### 场景 2: VLAN 间通信

```
PC1 (VLAN 100) → PC3 (VLAN 200)

1. PC1 → Dist-Switch1 (VLAN 100 网关)
2. Dist-Switch1 → Core-Router (三层路由)
3. Core-Router → Dist-Switch2
4. Dist-Switch2 → PC3 (VLAN 200)
```

### 场景 3: 互联网访问

```
PC1 → 互联网

1. PC1 查路由，使用默认网关 192.168.1.1
2. 多跳路由到 Core-Router
3. Core-Router NAT 转换: 192.168.1.10 → 公网 IP
4. 转发到互联网网关
```

## 性能指标

| 指标 | 值 |
|------|-----|
| **路由查找延迟** | < 1 μs (硬件) |
| **包转发速率** | > 100 Mpps |
| **吞吐量** | 10-100 Gbps |
| **路由表容量** | 100K 条目 |
| **ARP 表容量** | 10K 条目 |
| **并发连接数** | > 1M |

## 扩展方向

1. **动态路由协议**
   - OSPF 实现
   - BGP 实现
   - RIP 支持

2. **高级功能**
   - NAT/PAT
   - DHCP 服务器
   - 负载均衡
   - 防火墙规则

3. **IPv4/IPv6 双栈**
   - 同时支持 IPv4 和 IPv6
   - 隧道技术（6to4, DS-Lite）

4. **SDN 集成**
   - OpenFlow 支持
   - 集中式控制器
   - 动态流表下发

## 参考文档

- RFC 791: Internet Protocol
- RFC 826: ARP
- RFC 1812: Requirements for IP Version 4 Routers
- RFC 2474: DSCP
- RFC 3031: MPLS

## 许可证

本示例遵循开源许可证。

