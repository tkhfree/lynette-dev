# Lynette - 面向网络拓扑的PNE语言编译器

Lynette是一个面向网络拓扑的特定领域语言（PNE - Programmable Network Element）编译器，用于将基于整个网络拓扑的PNE程序编译生成面向单个设备的P4程序。与P4语言基于单个设备编程不同，PNE语言支持基于整个网络拓扑进行编程。

## 目录

- [安装指南](#安装指南)
- [PNE语言语法规则](#pne语言语法规则)
  - [文件包含机制](#文件包含机制)
  - [顶层结构](#顶层结构)
  - [服务定义](#服务定义)
  - [应用定义](#应用定义)
  - [模块定义](#模块定义)
  - [Parser和Control](#parser和control)
  - [数据类型](#数据类型)
  - [指令类型](#指令类型)
  - [表定义](#表定义)
  - [控制流](#控制流)
  - [表达式和运算符](#表达式和运算符)

## 安装指南

推荐使用`virtualenv`和`virtualenvwrapper`创建虚拟环境。
```sh
sudo python3 -m pip install virtualenv virtualenvwrapper

sudo find / -name virtualenvwrapper.sh

sed -i '$a\
export WORKON_HOME=$HOME/.virtualenvs\
export PROJECT_HOME=$HOME/PY_project\
export VIRTUALENVWRAPPER_SCRIPT=/usr/bin/virtualenvwrapper.sh\
source /usr/bin/virtualenvwrapper.sh' .bashrc
```

创建虚拟环境

```sh
# 创建
mkvirtualenv lynette
# 列出所有的虚拟环境，两种方法
workon
lsvirtualenv
# 进入
workon lynette
# 退出
deactivate
# 删除虚拟环境
rmvirtualenv lynette

```

以开发者模式安装lynette
```sh
python3 setup.py develop
python3 -m pip show lynette
python3 -m lynette -h
```

## PNE语言语法规则

PNE（Programmable Network Element）语言是一个面向网络拓扑的特定领域语言，其语法设计参考了P4语言，但提供了更高级的抽象，支持基于整个网络拓扑进行编程。本节详细说明PNE语言的语法规则。

### 文件包含机制

PNE支持多种文件包含方式，用于代码复用和模块化：

#### 系统文件包含
```pne
#include <path/to/file.pne>
#include <domain.domain>
```
- 使用尖括号 `<>` 包含系统库文件
- 支持路径分隔符 `/`
- `.domain` 文件用于批量包含多个文件

#### 用户文件包含
```pne
#include ">-<path/to/file.pne>-<"
#include ">-<path/to/domain.domain>-<"
```
- 使用特殊标记 `>-<` 包含用户自定义文件
- 避免与字符串字面量冲突

### 顶层结构

PNE程序的基本结构：
```pne
#include <header.pne>
using Parser;

// 服务、应用、模块定义
service[ServiceName] { ... }
application AppName { ... }
module ModuleName() { ... }
```

### 服务定义

服务定义了应用的调用链，描述数据包在网络中的处理流程：

```pne
service[ServiceName] {
    app1 -> app2 -> app3
}
```

- `service[ServiceName]`: 定义服务名称
- `app1 -> app2`: 使用箭头 `->` 表示应用调用顺序
- 对应P4中多个control块的组合调用

### 应用定义

应用是网络功能的逻辑单元：

```pne
application AppName using Parser {
    Module1.apply();
    Module2.apply();
}
```

- `application AppName`: 定义应用名称
- `using Parser`: 可选，指定使用的解析器
- 应用体包含模块调用和其他指令

### 模块定义

模块是可复用的网络功能组件：

```pne
module ModuleName(param1 bit<32> default_value) using Parser {
    parser {
        hdr.ethernet;
        hdr.ipv4;
    }
    control {
        // 控制逻辑
    }
}
```

- **模块参数**: 支持参数化设计，格式 `paramName DATA_TYPE defaultValue`
- **Parser声明**: 声明需要解析的头部字段
- **Control块**: 包含控制平面逻辑

### Parser和Control

#### Parser定义
```pne
parser {
    hdr.ethernet;
    hdr.ipv4;
}
```
- 简化了P4 parser的复杂状态机定义
- 只需声明需要解析的头部字段
- 对应P4 parser中的extract操作

#### Control定义
```pne
control {
    if (hdr.ipv4.isValid()) {
        ipv4_table.apply();
    }
}
```
- 包含控制平面的逻辑
- 对应P4的control块
- 可以包含表操作、条件判断、数据包处理等

### 数据类型

PNE支持以下数据类型：

#### 基本类型
- **位类型**: `bit<W>` - 固定宽度的位字段，如 `bit<32>`, `bit<48>`
- **类型别名**: 通过 `typedef` 定义，如 `typedef bit<48> mac_addr_t;`
- **常量**: 通过 `const` 定义，如 `const bit<16> ETHERTYPE_IPV4 = 0x0800;`

#### 复合类型
- **头部**: `header HeaderName { ... }` - 定义数据包头部结构
- **结构体**: `struct StructName { ... }` - 定义复合数据结构
- **元组**: `tuple TupleName { field1, field2, ... }` - 用于多值返回

#### 数据访问
```pne
hdr.ethernet.dmac        // 字段访问
hdr.ipv4.srcAddr[0]      // 数组访问
_standard_metadata.egress_spec  // 系统元数据
192.168.1.1              // IPv4地址
2001:db8::1             // IPv6地址
0x0800                   // 十六进制数
```

### 指令类型

PNE支持多种指令类型：

#### 赋值指令
```pne
hdr.ipv4.ttl = 64;
(pkt.out_port, pkt.out_port2) = (1, 2);  // 多值赋值
```

#### 表/模块调用
```pne
ipv4_table.apply();
Forwarding.apply();
```

#### 算术运算
```pne
hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
counter = counter + 1;
```
注意：P4不支持运行时除法，所以只支持 `+` 和 `-` 运算。

#### 原语操作
```pne
drop();                    // 丢弃数据包
sendToCPU();              // 发送到控制平面
addHeader(hdr.new_header); // 添加头部
removeHeader(hdr.old_header); // 移除头部
updateChecksum(hdr.ipv4); // 更新校验和
nop();                    // 空操作
return();                 // 提前返回
```

### 表定义

PNE支持两种表类型：

#### 映射表（Map）
对应P4的table，用于查找和匹配：

```pne
map<bit<32>, bit<9>>[1024] ipv4_table {
    (192.168.1.1, 1);
    (192.168.1.2, 2);
};
```

- `map<keyType, valueType>[size]`: 定义表类型和大小
- `{ ... }`: 可选的初始表项
- 支持复合键：`map<tuple<bit<32>, bit<16>>, bit<9>>`

#### 集合（Set）
对应P4的set，用于成员关系检查：

```pne
set<bit<32>> ipv4_set {
    (192.168.1.1);
    (192.168.1.2);
};
```

#### 寄存器（Register）
用于存储状态信息：

```pne
static bit<32> counter[1024];
static bit<64> timestamp;
```

### 控制流

#### 条件语句
```pne
if (hdr.ipv4.isValid()) {
    ipv4_table.apply();
} else if (hdr.ipv6.isValid()) {
    ipv6_table.apply();
} else {
    drop();
}
```

#### Switch语句
```pne
switch(hdr.eth_type.value) {
    0x0800: ipv4_handler.apply();
    0x86DD: ipv6_handler.apply();
    default: drop();
}
```

#### 循环语句
```pne
// For循环
for (bit<8> i = 0; i < 10; i = i + 1) {
    // 循环体
}

// While循环
while (condition) {
    // 循环体
}
```
**注意**: P4对循环有严格限制，循环次数必须在编译时确定。

#### 断言
```pne
assert(hdr.ipv4.isValid());
```

### 表达式和运算符

#### 算术运算符
- `+`: 加法
- `-`: 减法
- `*`: 乘法（如果目标架构支持）
- `/`: 除法（如果目标架构支持）
- `%`: 取模（如果目标架构支持）

#### 比较运算符
- `==`: 等于
- `!=`: 不等于
- `>`: 大于
- `>=`: 大于等于
- `<`: 小于
- `<=`: 小于等于

#### 逻辑运算符
- `&&`: 逻辑与
- `||`: 逻辑或
- `!`: 逻辑非

#### 位运算符
- `&`: 位与
- `|`: 位或
- `^`: 位异或
- `~`: 位取反
- `<<`: 左移
- `>>`: 右移

#### 成员检查
```pne
if (hdr.ipv4.dstAddr in ipv4_table) {
    // 键在表中
}
```

#### 有效性检查
```pne
if (hdr.ipv4.isValid()) {
    // 头部有效
}
```

### 函数定义

定义可复用的代码块：

```pne
func ProcessPacket() {
    if (hdr.ipv4.isValid()) {
        ipv4_table.apply();
    }
}
```

**注意**: 当前版本支持函数定义，参数支持将在未来版本中扩展。

### 注释

PNE支持两种注释方式：

```pne
// 单行注释

/* 
   多行注释
   可以包含多行内容
*/
```

### 完整示例

```pne
#include <header.pne>
#include <define.pne>

using Parser;

module Forwarding() {
    parser {
        hdr.ethernet;
        hdr.ipv4;
    }
    
    control {
        // 定义转发表
        map<bit<32>, bit<9>>[1024] ipv4_table {
            (192.168.1.1, 1);
            (192.168.1.2, 2);
        };
        
        // 转发逻辑
        if (hdr.ipv4.isValid()) {
            if (hdr.ipv4.dstAddr in ipv4_table) {
                pkt.out_port = ipv4_table[hdr.ipv4.dstAddr];
            } else {
                drop();
            }
        } else {
            drop();
        }
    }
}

application Router using Parser {
    Forwarding.apply();
}
```

## 语法规则更新日志

### 最新更新（2024）

1. **增强的表达式支持**
   - 添加了完整的表达式语法，支持算术、位运算、括号等
   - 支持运算符优先级（乘除优先于加减）

2. **循环语句支持**
   - 添加了 `for` 循环语法
   - 添加了 `while` 循环语法
   - 注意：P4对循环有严格限制，循环次数必须在编译时确定

3. **逻辑运算符**
   - 添加了逻辑与 `&&` 和逻辑或 `||` 运算符
   - 支持复杂的条件组合

4. **位运算符**
   - 添加了位与 `&`、位或 `|`、位异或 `^`
   - 添加了位取反 `~`、左移 `<<`、右移 `>>`

5. **函数参数支持**
   - 扩展了函数定义语法，支持参数列表
   - 为未来版本的功能扩展做准备

6. **详细注释**
   - 为所有语法规则添加了详细的中文注释
   - 说明了每个规则的作用和对应的P4特性
   - 提供了使用示例和注意事项

## 相关文档

- [架构文档](ARCHITECTURE.md) - 详细的系统架构说明
- [科学设计文档](SCIENTIFIC_DESIGN_DOCUMENT.md) - 项目设计文档
- [Agent开发方案](AGENT_DEVELOPMENT_PLAN.md) - Agent功能说明