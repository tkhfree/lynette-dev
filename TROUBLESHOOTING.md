# 问题排查指南

## ModuleNotFoundError: No module named 'lynette_lib'

### 问题描述

在新服务器上下载项目后，启动 agent 时遇到以下错误：

```
ModuleNotFoundError: No module named 'lynette_lib'
```

### 问题原因

1. **导入路径错误**：`lynette/__main__.py` 和其他文件中使用了 `from lynette_lib import ...`，但 `lynette_lib` 是 `lynette` 包下的子包，不是独立的顶级包。

2. **包未正确安装**：在新服务器上，如果没有以开发者模式安装 `lynette` 包，Python 无法找到正确的模块路径。

### 解决方案

#### 方案一：修复导入语句（已修复）

已将所有错误的导入语句从：
```python
from lynette_lib import ...
```

修改为：
```python
from lynette.lynette_lib import ...
```

**修复的文件：**
- `lynette/__main__.py`
- `lynette/lynette_lib/collect.py`
- `lynette/lynette_lib/generate.py`
- `lynette/lynette_lib/aggregate.py`
- `lynette/lynette_lib/parser_tree.py`

#### 方案二：正确安装 lynette 包（推荐）

在新服务器上，需要以开发者模式安装 `lynette` 包：

```bash
# 进入项目根目录
cd ~/lynette-dev

# 以开发者模式安装 lynette 包
python3 setup.py develop

# 验证安装
python3 -m pip show lynette
python3 -m lynette -h
```

#### 方案三：设置 PYTHONPATH（临时方案）

如果不想安装包，可以临时设置 PYTHONPATH：

```bash
export PYTHONPATH=~/lynette-dev:$PYTHONPATH
python3 -m lynette_agent.server
```

### 完整安装步骤

在新服务器上部署项目时，建议按以下步骤操作：

1. **克隆或下载项目**
   ```bash
   cd ~
   git clone <repository_url> lynette-dev
   # 或解压下载的压缩包
   ```

2. **安装依赖**
   ```bash
   cd ~/lynette-dev
   
   # 安装 lynette 包（开发者模式）
   python3 setup.py develop
   
   # 安装 agent 依赖
   pip3 install -r lynette_agent/requirements.txt
   ```

3. **验证安装**
   ```bash
   # 检查 lynette 包
   python3 -m pip show lynette
   python3 -m lynette -h
   
   # 检查 agent 依赖
   python3 -c "import fastapi; print('FastAPI installed')"
   ```

4. **启动服务**
   ```bash
   # 设置 API Key（可选）
   export LYNETTE_API_KEY=your_api_key
   
   # 启动服务
   python3 -m lynette_agent.server
   ```

### 常见问题

#### Q: 为什么需要 `python3 setup.py develop`？

A: `develop` 模式会在当前环境中安装包，但不会复制文件，而是创建链接。这样修改代码后无需重新安装即可生效。

#### Q: 可以使用 `pip install -e .` 吗？

A: 可以，`pip install -e .` 等同于 `python3 setup.py develop`，是更现代的方式。

#### Q: 如果仍然遇到导入错误怎么办？

A: 
1. 检查 Python 路径：`python3 -c "import sys; print(sys.path)"`
2. 检查包是否正确安装：`python3 -m pip show lynette`
3. 检查导入：`python3 -c "from lynette.lynette_lib import parser_tree; print('OK')"`

### 相关文件

- `setup.py` - 包安装配置
- `lynette/__main__.py` - 主入口文件（已修复导入）
- `lynette_agent/service.py` - Agent 服务层（使用正确的导入方式）
