# Lynette 项目开发指南

## 目录

1. [环境设置](#环境设置)
2. [项目构建](#项目构建)
3. [开发规范](#开发规范)
4. [测试指南](#测试指南)
5. [调试技巧](#调试技巧)
6. [常见问题](#常见问题)

## 环境设置

### 1.1 系统要求

- **操作系统**：Linux / Windows / macOS
- **Python版本**：Python 3.8 或更高版本
- **依赖工具**：
  - `p4test`（用于P4代码验证，可选）

### 1.2 Python环境配置

#### 方法一：使用virtualenv（推荐）

```bash
# 安装virtualenv和virtualenvwrapper
sudo python3 -m pip install virtualenv virtualenvwrapper

# 查找virtualenvwrapper.sh位置
sudo find / -name virtualenvwrapper.sh

# 配置.bashrc（Linux）或.bash_profile（macOS）
# 添加以下内容：
export WORKON_HOME=$HOME/.virtualenvs
export PROJECT_HOME=$HOME/PY_project
export VIRTUALENVWRAPPER_SCRIPT=/usr/bin/virtualenvwrapper.sh
source /usr/bin/virtualenvwrapper.sh

# 重新加载配置
source ~/.bashrc  # 或 source ~/.bash_profile
```

#### 方法二：使用venv（Python 3.3+）

```bash
# 创建虚拟环境
python3 -m venv lynette-env

# 激活虚拟环境
# Linux/macOS:
source lynette-env/bin/activate
# Windows:
lynette-env\Scripts\activate
```

### 1.3 安装依赖

```bash
# 进入项目根目录
cd lynette-dev

# 以开发者模式安装lynette
python3 setup.py develop

# 或者直接安装依赖
pip install -r requirements.txt  # 如果存在requirements.txt
# 或手动安装
pip install lark setuptools pysnooper
```

### 1.4 验证安装

```bash
# 检查安装
python3 -m pip show lynette

# 测试命令行工具
python3 -m lynette -h
```

## 项目构建

### 2.1 项目结构

```
lynette-dev/
├── setup.py              # 安装配置
├── README.md             # 项目说明
├── ARCHITECTURE.md       # 架构文档
├── DEVELOPMENT_GUIDE.md  # 本文件
├── generat.py            # 生成脚本（示例）
├── input/                # 输入文件目录
│   ├── *.pne            # PNE源文件
│   ├── service.json      # 服务配置
│   ├── topology.json     # 拓扑配置
│   ├── path/            # 路径配置
│   └── include/         # 包含文件
└── lynette/              # 源代码目录
    ├── __main__.py       # 主程序
    ├── deploy.py         # 部署工具
    └── lynette_lib/      # 核心库
```

### 2.2 编译流程

#### 2.2.1 Debug模式（单文件编译）

```bash
# 编译单个PNE文件
python3 -m lynette --debug-main input/Alice_main.pne --output-dir input/pne_out

# 只生成P4文件（不进行服务编译）
python3 -m lynette --debug-main input/Alice_main.pne --p4 --output-dir input/pne_out
```

#### 2.2.2 Service模式（完整编译）

```bash
# 使用service.json进行完整编译
python3 -m lynette --config input/service.json --output-dir input/pne_out

# 编译并部署到后端
python3 -m lynette --config input/service.json --output-dir input/pne_out --deploy

# 生成并部署表项
python3 -m lynette --config input/service.json --output-dir input/pne_out --entry
```

### 2.3 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--config` | 服务配置文件路径 | `./service.json` |
| `--debug-main` | Debug模式主文件路径 | 无 |
| `--output-dir` | 输出目录 | `./pne_out/` |
| `--log-dir` | 日志目录 | `./log/` |
| `--p4` | 只编译P4文件 | False |
| `--deploy` | 部署到后端 | False |
| `--entry` | 部署表项 | False |
| `--check` | 使用p4test验证 | False |
| `--clean` | 清理旧文件 | True |
| `--target` | 目标架构（v1model/tna） | `v1model` |

### 2.4 输入文件格式

#### 2.4.1 service.json

```json
{
    "用户名称": {
        "services": [
            {
                "service_name": "服务名称",
                "service_domain": "域名称",
                "service_hosts": [
                    {
                        "device_uuid": "设备ID",
                        "ports": {"主机名": 端口号}
                    }
                ],
                "applications": ["应用名称"]
            }
        ]
    }
}
```

#### 2.4.2 topology.json

```json
{
    "devices": ["设备列表"],
    "links": [
        {
            "src": {"device": "源设备", "port": "源端口"},
            "dst": {"device": "目标设备", "port": "目标端口"},
            "bandwidth": 带宽
        }
    ],
    "deviceStaticInfo": {
        "设备ID": {
            "设备信息": "详细信息"
        }
    }
}
```

#### 2.4.3 path/path.json

```json
{
    "服务名称": {
        "节点1": {
            "next": {"节点2": 端口号},
            "tables": 表数量,
            "ip": "IP地址"
        }
    }
}
```

## 开发规范

### 3.1 代码风格

#### 3.1.1 Python代码规范

- 遵循PEP 8代码风格
- 使用4个空格缩进
- 行长度不超过120字符
- 函数和类需要文档字符串

#### 3.1.2 命名规范

- **模块名**：小写字母，单词间用下划线分隔（`parser_tree.py`）
- **类名**：大驼峰命名（`LynetteRunner`）
- **函数名**：小写字母，单词间用下划线分隔（`execute()`）
- **变量名**：小写字母，单词间用下划线分隔（`var_list`）
- **常量名**：全大写，单词间用下划线分隔（`SYS_DATA`）

#### 3.1.3 文件组织

```python
# 1. 标准库导入
import sys, os
import json

# 2. 第三方库导入
from lark import Lark, Tree

# 3. 本地库导入
from lynette_lib import data_structure
from lynette_lib.grammar.grammar import grammar

# 4. 常量定义
CONSTANT_VALUE = 100

# 5. 类定义
class MyClass:
    pass

# 6. 函数定义
def my_function():
    pass

# 7. 主程序
if __name__ == '__main__':
    main()
```

### 3.2 语法定义规范

#### 3.2.1 EBNF语法规则

- 使用Lark库的EBNF语法
- 规则名使用小写下划线命名
- 终端符号使用大写
- 添加适当的注释

```python
grammar = """
    # 注释：说明规则用途
    rule_name: sub_rule1 | sub_rule2
    
    TERMINAL: "literal" | REGEX
    
    %import common.INT
    %ignore WS
"""
```

#### 3.2.2 语法扩展

添加新语法时：
1. 在`grammar.py`中添加规则
2. 在`collect.py`中添加收集逻辑
3. 在`generate.py`中添加生成逻辑
4. 更新相关文档

### 3.3 错误处理

#### 3.3.1 错误类型

- **语法错误**：在`parser_tree.py`中捕获Lark解析错误
- **语义错误**：在`collect.py`中检查语义正确性
- **生成错误**：在`generate.py`中检查生成条件

#### 3.3.2 错误报告

```python
# 使用print输出错误信息
print("error-module_name-function_name error description")
print("variable_name:", variable_value)
exit()  # 严重错误时退出
```

### 3.4 日志记录

```python
# 在关键步骤记录日志
with open(path + "//log_out//log.txt", "a") as file:
    file.write('step_name...\n')
```

### 3.5 测试规范

#### 3.5.1 单元测试

- 为每个模块编写单元测试
- 测试文件命名：`test_模块名.py`
- 使用`unittest`或`pytest`框架

#### 3.5.2 集成测试

- 使用示例PNE文件进行端到端测试
- 验证生成的P4代码正确性

## 测试指南

### 4.1 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/

# 运行特定测试文件
python3 -m pytest tests/test_parser_tree.py

# 运行特定测试函数
python3 -m pytest tests/test_parser_tree.py::test_parse_file
```

### 4.2 测试示例文件

```bash
# 编译示例文件
python3 -m lynette --debug-main input/Alice_main.pne --output-dir input/pne_out

# 验证生成的P4代码
p4test input/pne_out/s1.p4 --toJSON input/pne_out/s1.json
```

### 4.3 验证输出

1. **检查P4文件语法**：使用`p4test`验证
2. **检查表项格式**：验证JSON格式正确性
3. **检查代码完整性**：确保所有必要的组件都已生成

## 调试技巧

### 5.1 使用pysnooper

项目已集成`pysnooper`，可以在函数上添加装饰器进行调试：

```python
import pysnooper

@pysnooper.snoop()
def my_function():
    # 函数代码
    pass
```

### 5.2 打印调试信息

```python
# 打印变量值
print("debug variable_name:", variable_value)

# 打印数据结构
print("debug data structure:", data_structure)
```

### 5.3 检查中间文件

编译过程中会在`component/`目录生成中间文件：
- `component/main/` - 预处理后的主文件
- `component/code/` - 节点代码片段
- `component/*_var.pne` - 变量定义
- `component/*_control.pne` - 控制流代码
- `component/*_table.pne` - 表定义
- `component/*_action.pne` - 动作定义
- `component/*_entry.pne` - 表项定义

### 5.4 日志文件

检查`input/log_out/log.txt`查看编译日志。

## 常见问题

### 6.1 编译错误

**问题**：语法解析失败
- **原因**：PNE文件语法错误
- **解决**：检查PNE文件语法，参考`grammar.py`中的语法规则

**问题**：找不到文件
- **原因**：文件路径错误或文件不存在
- **解决**：检查文件路径，确保使用正确的路径分隔符（Windows使用`//`）

### 6.2 生成错误

**问题**：变量未定义
- **原因**：变量在使用前未定义
- **解决**：检查变量定义顺序，确保在使用前定义

**问题**：表项格式错误
- **原因**：表项数据与表定义不匹配
- **解决**：检查表项的key和value数量是否与表定义一致

### 6.3 部署错误

**问题**：无法连接到后端
- **原因**：网络连接问题或后端服务未启动
- **解决**：检查网络连接和后端服务状态

**问题**：端口被占用
- **原因**：默认端口13345被占用
- **解决**：修改`deploy.py`中的端口号或关闭占用端口的程序

### 6.4 性能问题

**问题**：编译速度慢
- **原因**：大项目或复杂语法
- **解决**：
  - 优化PNE代码结构
  - 减少不必要的include
  - 考虑并行化编译过程

**问题**：内存占用高
- **原因**：大项目AST和IR占用内存
- **解决**：
  - 优化数据结构
  - 考虑流式处理
  - 增加系统内存

## 贡献指南

### 7.1 提交代码

1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 提交Pull Request

### 7.2 代码审查

- 确保代码符合规范
- 添加必要的注释和文档
- 通过所有测试
- 更新相关文档

### 7.3 文档更新

修改代码时，同步更新：
- 架构文档（如涉及架构变更）
- 开发指南（如涉及开发流程变更）
- README（如涉及使用方式变更）

## 参考资料

- [P4语言规范](https://p4.org/specs/)
- [Lark解析器文档](https://lark-parser.readthedocs.io/)
- [Python PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [项目README](README.md)
- [架构文档](ARCHITECTURE.md)

