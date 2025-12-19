# IPv6 网络示例

## 概述

本示例展示如何使用 Lynette PNE 在 P4 交换机上实现 IPv6 网络。基于 **RFC 8200** 标准。

## IPv6 核心特性

### 1. **128位地址空间**
- 地址数量：2^128 ≈ 3.4 × 10^38
- 支持地址层次化分配
- 无需 NAT

### 2. **邻居发现协议（NDP）**
- 替代 ARP
- 使用 ICMPv6 消息
- 支持无状态地址配置（SLAAC）

### 3. **简化的头部**
- 固定40字节基本头部
- 扩展头部链式结构
- 取消头部校验和

### 4. **组播替代广播**
- 没有广播地址
- 使用组播实现类似功能
- 减少网络流量

## 设备要求

### 终端设备

**IPv6 配置**
```bash
# Linux
sudo ip -6 addr add 2001:db8:100::10/64 dev eth0
sudo ip -6 route add default via 2001:db8:100::1

# Windows
netsh interface ipv6 add address "Ethernet" 2001:db8:100::10/64
netsh interface ipv6 add route ::/0 "Ethernet" 2001:db8:100::1
```

**协议栈**
```
┌─────────────────────────────────┐
│  应用层 (HTTP/2, QUIC)          │
├─────────────────────────────────┤
│  传输层 (TCP, UDP)              │
├─────────────────────────────────┤
│  网络层 (IPv6, ICMPv6, NDP)     │
├─────────────────────────────────┤
│  数据链路层 (Ethernet)           │
└─────────────────────────────────┘
```

### P4 交换机

**编译和部署**
```bash
# 编译
make compile

# 部署
simple_switch_grpc --device-id 1 \
    -i 1@veth1 -i 2@veth2 \
    output/ipv6_example/ipv6-core.json
```

## IPv6 地址类型

| 类型 | 前缀 | 说明 |
|------|------|------|
| **全局单播** | 2000::/3 | 互联网可路由 |
| **唯一本地** | FC00::/7 | 类似私有地址 |
| **链路本地** | FE80::/10 | 本地链路通信 |
| **组播** | FF00::/8 | 组播地址 |
| **环回** | ::1/128 | 本地环回 |

## 测试

```bash
# Ping6 测试
ping6 2001:db8:100::10

# Traceroute6
traceroute6 2001:db8:100::10

# 查看邻居缓存
ip -6 neigh show
```

## 参考文档

- RFC 8200: IPv6 Specification
- RFC 4861: Neighbor Discovery
- RFC 4862: IPv6 Stateless Address Autoconfiguration

## 许可证

本示例遵循开源许可证。

