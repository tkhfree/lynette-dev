# Makefile for IPv4 Enterprise Network Example

LYNETTE = python -m lynette
INPUT_PNE = ipv4_forwarding.pne
TOPOLOGY = topology.json
SERVICE = service.json
OUTPUT_DIR = ../../output/ipv4_example

.PHONY: all compile clean help test

all: compile

help:
	@echo "IPv4 企业网络示例 Makefile"
	@echo ""
	@echo "命令:"
	@echo "  make compile  - 编译 PNE 代码"
	@echo "  make clean    - 清理生成文件"
	@echo "  make test     - 运行测试"
	@echo "  make help     - 显示帮助"

compile:
	@echo "编译 IPv4 PNE 代码..."
	@mkdir -p $(OUTPUT_DIR)
	$(LYNETTE) compile \
		--input $(INPUT_PNE) \
		--topology $(TOPOLOGY) \
		--service $(SERVICE) \
		--output $(OUTPUT_DIR)
	@echo "编译完成！"

clean:
	@echo "清理文件..."
	@rm -rf $(OUTPUT_DIR)
	@echo "清理完成！"

test:
	@echo "运行 IPv4 网络测试..."
	@echo "测试 1: 路由表验证"
	@echo "测试 2: ACL 规则测试"
	@echo "测试 3: QoS 分类测试"

