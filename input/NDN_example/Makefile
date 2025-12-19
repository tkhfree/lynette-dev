# Makefile for NDN Example
# 用于编译和部署 NDN 网络示例

# 配置
LYNETTE = python -m lynette
INPUT_PNE = ndn_forwarding.pne
TOPOLOGY = topology.json
SERVICE = service.json
OUTPUT_DIR = ../../output/ndn_example

# 颜色定义
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
NC = \033[0m # No Color

.PHONY: all compile clean help test deploy

all: compile

help:
	@echo "$(GREEN)NDN 示例 Makefile$(NC)"
	@echo ""
	@echo "可用命令:"
	@echo "  $(YELLOW)make compile$(NC)  - 编译 PNE 代码为 P4 代码"
	@echo "  $(YELLOW)make clean$(NC)    - 清理生成的文件"
	@echo "  $(YELLOW)make test$(NC)     - 运行测试"
	@echo "  $(YELLOW)make deploy$(NC)   - 部署到 P4 交换机"
	@echo "  $(YELLOW)make help$(NC)     - 显示此帮助信息"
	@echo ""
	@echo "配置:"
	@echo "  输入文件: $(INPUT_PNE)"
	@echo "  拓扑文件: $(TOPOLOGY)"
	@echo "  服务文件: $(SERVICE)"
	@echo "  输出目录: $(OUTPUT_DIR)"

compile:
	@echo "$(GREEN)开始编译 NDN PNE 代码...$(NC)"
	@mkdir -p $(OUTPUT_DIR)
	$(LYNETTE) compile \
		--input $(INPUT_PNE) \
		--topology $(TOPOLOGY) \
		--service $(SERVICE) \
		--output $(OUTPUT_DIR)
	@echo "$(GREEN)编译完成！P4 代码已生成到 $(OUTPUT_DIR)$(NC)"
	@echo ""
	@echo "生成的文件:"
	@ls -lh $(OUTPUT_DIR)/

clean:
	@echo "$(YELLOW)清理生成的文件...$(NC)"
	@rm -rf $(OUTPUT_DIR)
	@echo "$(GREEN)清理完成！$(NC)"

test:
	@echo "$(YELLOW)运行 NDN 测试场景...$(NC)"
	@echo "测试 1: 基本内容检索"
	@echo "  Consumer1 -> /ndn/edu/ucla/video/lecture1 -> Producer1"
	@echo ""
	@echo "测试 2: 内容缓存"
	@echo "  多次请求相同内容，验证 CS 功能"
	@echo ""
	@echo "测试 3: Interest 聚合"
	@echo "  同时发送相同 Interest，验证 PIT 聚合功能"
	@echo ""
	@echo "$(RED)注意: 需要先部署到实际环境或仿真器才能运行测试$(NC)"

deploy:
	@echo "$(YELLOW)部署 NDN 网络到 P4 交换机...$(NC)"
	@if [ ! -d "$(OUTPUT_DIR)" ]; then \
		echo "$(RED)错误: 请先运行 'make compile' 生成 P4 代码$(NC)"; \
		exit 1; \
	fi
	@echo ""
	@echo "$(GREEN)部署步骤:$(NC)"
	@echo "1. 启动 ndn-switch1:"
	@echo "   simple_switch_grpc -i 1@veth1 -i 2@veth2 -i 3@veth3 -i 4@veth4 $(OUTPUT_DIR)/ndn-switch1.p4.json"
	@echo ""
	@echo "2. 启动 ndn-switch2:"
	@echo "   simple_switch_grpc -i 1@veth5 -i 2@veth6 $(OUTPUT_DIR)/ndn-switch2.p4.json"
	@echo ""
	@echo "3. 启动 ndn-switch3:"
	@echo "   simple_switch_grpc -i 1@veth7 -i 2@veth8 -i 3@veth9 $(OUTPUT_DIR)/ndn-switch3.p4.json"
	@echo ""
	@echo "$(YELLOW)注意: 需要根据实际环境调整网络接口和端口配置$(NC)"

# 验证配置文件
validate:
	@echo "$(YELLOW)验证配置文件...$(NC)"
	@if [ ! -f "$(INPUT_PNE)" ]; then \
		echo "$(RED)错误: 找不到 $(INPUT_PNE)$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(TOPOLOGY)" ]; then \
		echo "$(RED)错误: 找不到 $(TOPOLOGY)$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "$(SERVICE)" ]; then \
		echo "$(RED)错误: 找不到 $(SERVICE)$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)配置文件验证通过！$(NC)"

# 显示拓扑信息
topology:
	@echo "$(GREEN)NDN 网络拓扑:$(NC)"
	@echo ""
	@echo "          Consumer1"
	@echo "              |"
	@echo "              | port 3"
	@echo "         [ndn-switch1] ----------- port 1 ----------- [ndn-switch2]"
	@echo "          (Arizona)      |                                  |"
	@echo "              |          |                                  | port 2"
	@echo "              | port 2   |                                  |"
	@echo "         Producer2       |                             [ndn-switch3]"
	@echo "                         |                              (UCLA)"
	@echo "                         |                                  |"
	@echo "                         +---------- port 2 ----------------+"
	@echo "                                                            | port 3"
	@echo "                                                            |"
	@echo "                                                       Producer1"

# 显示转发流程
flow:
	@echo "$(GREEN)NDN Interest 转发流程:$(NC)"
	@echo ""
	@echo "1. 接收 Interest"
	@echo "   ↓"
	@echo "2. CS 查找"
	@echo "   ├─ 命中 → 返回缓存的 Data"
	@echo "   └─ 未命中 ↓"
	@echo "3. PIT 查找"
	@echo "   ├─ 已存在 → Interest 聚合"
	@echo "   └─ 不存在 ↓"
	@echo "4. FIB 查找"
	@echo "   ↓"
	@echo "5. 转发到下一跳"
	@echo "   ↓"
	@echo "6. 记录到 PIT"
	@echo ""
	@echo "$(GREEN)NDN Data 转发流程:$(NC)"
	@echo ""
	@echo "1. 接收 Data"
	@echo "   ↓"
	@echo "2. PIT 查找"
	@echo "   ├─ 命中 → 按 PIT 转发"
	@echo "   │         ↓"
	@echo "   │      3. 缓存到 CS"
	@echo "   │         ↓"
	@echo "   │      4. 清除 PIT"
	@echo "   └─ 未命中 → 丢弃"

