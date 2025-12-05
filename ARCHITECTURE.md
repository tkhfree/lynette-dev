# Lynette 项目架构分析文档

## 1. 项目概述

Lynette 是一个面向网络拓扑的特定领域语言（PNE - Programmable Network Element）编译器，用于将基于整个网络拓扑的PNE程序编译生成面向单个设备的P4程序。与P4语言基于单个设备编程不同，PNE语言支持基于整个网络拓扑进行编程。

## 2. 核心架构设计

### 2.1 整体架构

Lynette采用经典的编译器前端-后端架构，主要包含以下阶段：

```
PNE源代码 → 语法解析 → AST构建 → 语义收集 → 代码生成 → 代码聚合 → P4输出
```

### 2.2 模块划分

#### 2.2.1 语法解析层 (`lynette_lib/grammar/`)

**职责**：定义PNE语言的EBNF语法规则，使用Lark库进行词法和语法分析。

**核心文件**：
- `grammar.py` - 主语法定义，包含PNE语言的核心语法规则
- `grammar_define.py` - 类型和常量定义语法
- `grammar_header.py` - 头部定义语法
- `grammar_parser.py` - 解析器定义语法

**关键语法元素**：
- `include` - 文件包含机制（支持系统文件和用户文件）
- `service` - 服务定义
- `application` - 应用定义
- `module` - 模块定义（可复用组件）
- `control` - 控制流代码块
- `parser` - 解析器定义

#### 2.2.2 解析树构建层 (`parser_tree.py`)

**职责**：将PNE源代码解析为抽象语法树（AST），处理文件包含和依赖关系。

**核心功能**：
- 使用Lark解析器将PNE代码转换为语法树
- 处理`#include`指令，递归解析依赖文件
- 支持系统域（`include_sys_domain`）和用户域（`include_user_domain`）
- 处理字符串替换（`"` → `>-<`）以支持domain文件解析

**依赖关系**：
- 依赖：`lynette_lib.grammar.grammar`
- 被依赖：`collect.py`

#### 2.2.3 语义收集层 (`collect.py`)

**职责**：从AST中提取语义信息，构建中间表示（IR）。

**核心功能**：
- 收集服务（Service）定义
- 收集应用（Application）定义
- 收集模块（Module）定义
- 解析指令序列（赋值、调用、条件、原语等）
- 构建数据结构（tuple、set、map、register等）

**数据结构**：
- `LYNETTE_SERVICE` - 服务结构
- `LYNETTE_APP` - 应用结构
- `LYNETTE_MODULE` - 模块结构
- `LYNETTE_INS` - 指令结构
- `LYNETTE_BLOCK` - 代码块结构

**依赖关系**：
- 依赖：`parser_tree.py`, `data_structure.py`
- 被依赖：`generate.py`

#### 2.2.4 代码生成层 (`generate.py`)

**职责**：将中间表示转换为P4代码片段。

**核心功能**：
- 变量生成和命名空间管理
- 指令展开（赋值、调用、条件、循环等）
- 表（Table）生成和优化
- 动作（Action）生成
- 模块调用展开
- 条件语句优化（单表优化）

**关键优化**：
- **单表优化**：将符合条件的if/switch语句转换为单个P4表，提高性能
- **代码片段化**：将应用代码切分为多个片段（fragment），便于后续聚合

**依赖关系**：
- 依赖：`collect.py`, `data_structure.py`, `grammar_define.py`
- 被依赖：`aggregate.py`

#### 2.2.5 代码聚合层 (`aggregate.py`)

**职责**：根据网络拓扑将代码片段聚合到各个网络节点。

**核心功能**：
- 读取拓扑信息（`topology.json`）和路径信息（`path.json`）
- 将服务代码片段分配到网络节点
- 资源约束检查（表数量限制）
- 生成节点级别的Parser
- 生成节点级别的Header定义
- 生成节点级别的Deparser
- 生成表项（Entry）配置

**关键算法**：
- **片段分配算法**：根据服务路径和节点资源约束，将代码片段分配到节点
- **Parser树构建**：根据节点使用的协议头，构建最小化的Parser树

**依赖关系**：
- 依赖：`generate.py`, `data_structure.py`, `grammar_define.py`, `grammar_header.py`, `grammar_parser.py`
- 被依赖：`output.py`

#### 2.2.6 代码输出层 (`output.py`)

**职责**：将聚合后的代码片段组合成完整的P4程序。

**核心功能**：
- 组合Header定义
- 组合Parser定义
- 组合Control（Ingress）定义
- 组合Deparser定义
- 生成主程序结构（Package）
- 生成表项JSON文件
- 支持v1model和TNA两种架构

**依赖关系**：
- 依赖：`aggregate.py`
- 被依赖：`__main__.py`

#### 2.2.7 数据结构层 (`data_structure.py`)

**职责**：定义编译器内部使用的数据结构。

**核心数据结构**：
- `LYNETTE_SERVICE` - 服务
- `LYNETTE_APP` - 应用
- `LYNETTE_MODULE` - 模块
- `LYNETTE_INS` - 指令
- `LYNETTE_BLOCK` - 代码块
- `LYNETTE_CONDITION` - 条件
- `LYNETTE_MAP/SET` - 映射/集合
- `LYNETTE_FRAG_RELATION` - 片段关系
- `LYNETTE_PARSER_NODE` - 解析器节点

#### 2.2.8 主程序入口 (`__main__.py`)

**职责**：协调各个模块，执行完整的编译流程。

**核心类**：`LynetteRunner`

**编译流程**：
1. 清理组件目录
2. 预处理（字符串替换）
3. 解析语法树（`parser_tree.execute`）
4. 收集语义信息（`collect.execute`）
5. 生成代码片段（`generate.execute`）
6. 聚合代码（`aggregate.execute`）
7. 输出P4文件（`output.execute`）

**支持模式**：
- Debug模式：直接编译单个`.pne`文件
- Service模式：基于`service.json`编译多个服务

## 3. 数据流分析

### 3.1 编译流程数据流

```
输入文件（.pne）
    ↓
[parser_tree] → forest (AST字典)
    ↓
[collect] → services, applications, modules (IR)
    ↓
[generate] → frag_relation_dict (代码片段字典)
    ↓
[aggregate] → 节点代码文件 (control, parser, header, deparser, entry)
    ↓
[output] → P4文件 (.p4) + Entry文件 (.json/.py)
```

### 3.2 关键数据结构流转

1. **AST (Abstract Syntax Tree)**
   - 格式：Lark Tree对象
   - 存储：`forest`字典，key为文件名，value为语法树

2. **IR (Intermediate Representation)**
   - 格式：自定义数据结构（`LYNETTE_*`类）
   - 存储：`services`, `applications`, `modules`字典

3. **代码片段 (Fragment)**
   - 格式：P4代码片段文件
   - 存储：`component/`目录下的临时文件
   - 包含：`*_var.pne`, `*_control.pne`, `*_action.pne`, `*_table.pne`, `*_entry.pne`

4. **节点代码**
   - 格式：P4代码片段
   - 存储：`component/code/`目录
   - 包含：`{node}_control`, `{node}_parser`, `{node}_header`, `{node}_deparser`, `{node}_entry`

5. **最终输出**
   - 格式：完整P4程序
   - 存储：`pne_out/`目录
   - 文件：`{node}.p4`, `{node}_entry.json`

## 4. 依赖关系图

```
__main__.py (LynetteRunner)
    ├── parser_tree.py
    │   └── grammar.py
    ├── collect.py
    │   ├── parser_tree.py
    │   └── data_structure.py
    ├── generate.py
    │   ├── collect.py
    │   ├── data_structure.py
    │   └── grammar_define.py
    ├── aggregate.py
    │   ├── generate.py
    │   ├── data_structure.py
    │   ├── grammar_define.py
    │   ├── grammar_header.py
    │   └── grammar_parser.py
    └── output.py
        └── aggregate.py
```

## 5. 关键设计模式

### 5.1 管道模式 (Pipeline Pattern)
编译过程采用管道模式，每个阶段处理上一阶段的输出，产生下一阶段的输入。

### 5.2 访问者模式 (Visitor Pattern)
`collect.py`中遍历AST树，根据不同节点类型执行不同的收集操作。

### 5.3 策略模式 (Strategy Pattern)
`generate.py`中根据指令类型选择不同的生成策略（单表优化 vs 大if展开）。

### 5.4 模板方法模式 (Template Method Pattern)
`__main__.py`中的`run()`方法定义了编译流程的模板，具体步骤由各模块实现。

## 6. 文件组织

```
lynette/
├── __main__.py          # 主程序入口
├── deploy.py            # 部署工具
├── component/           # 编译中间文件
│   ├── main/           # 预处理后的主文件
│   ├── code/           # 节点代码片段
│   ├── path/           # 路径信息
│   ├── topo/           # 拓扑信息
│   └── rest/           # REST API模板
└── lynette_lib/        # 核心库
    ├── parser_tree.py   # 解析树构建
    ├── collect.py       # 语义收集
    ├── generate.py     # 代码生成
    ├── aggregate.py    # 代码聚合
    ├── output.py       # 代码输出
    ├── data_structure.py # 数据结构
    ├── clean.py        # 清理工具
    └── grammar/        # 语法定义
        ├── grammar.py
        ├── grammar_define.py
        ├── grammar_header.py
        └── grammar_parser.py
```

## 7. 关键算法

### 7.1 片段分配算法
根据服务路径和节点资源约束，将代码片段分配到网络节点：
- 每个应用的head和tail片段必须分配到路径上的所有节点
- 中间片段根据节点资源约束进行分配
- 优先保证关键片段的分配

### 7.2 单表优化算法
将符合条件的if/switch语句转换为单个P4表：
- 检查条件类型（必须是check类型）
- 检查动作复杂度（必须是简单动作）
- 生成单个表，每个分支对应一个action

### 7.3 Parser树剪枝算法
根据节点使用的协议头，构建最小化的Parser树：
- 标记节点使用的协议头
- 从Parser树中移除不需要的节点
- 处理依赖关系，确保Parser树连通

## 8. 扩展点

### 8.1 语法扩展
在`lynette_lib/grammar/`目录下添加新的语法规则文件。

### 8.2 优化扩展
在`generate.py`中添加新的优化策略。

### 8.3 架构扩展
在`output.py`中添加对新P4架构的支持。

### 8.4 部署扩展
在`deploy.py`中添加新的部署后端支持。

## 9. 已知问题和限制

1. **字符串处理**：使用`>-<`替换`"`来处理domain文件，这是一个临时解决方案
2. **资源分配**：片段分配算法是启发式的，可能不是最优解
3. **Parser循环**：不支持Parser树中的循环结构
4. **错误处理**：错误处理机制较为简单，主要使用`exit()`

## 10. 性能考虑

1. **文件I/O**：大量使用文件I/O进行代码片段传递，可能影响性能
2. **内存使用**：AST和IR都保存在内存中，大项目可能占用较多内存
3. **并行化**：当前实现是单线程的，可以考虑并行化某些阶段
