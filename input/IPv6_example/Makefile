# Makefile for IPv6 Example

LYNETTE = python -m lynette
INPUT_PNE = ipv6_forwarding.pne
TOPOLOGY = topology.json
SERVICE = service.json
OUTPUT_DIR = ../../output/ipv6_example

.PHONY: all compile clean help

all: compile

help:
	@echo "IPv6 示例 Makefile"
	@echo ""
	@echo "命令:"
	@echo "  make compile  - 编译"
	@echo "  make clean    - 清理"
	@echo "  make help     - 帮助"

compile:
	@echo "编译 IPv6 代码..."
	@mkdir -p $(OUTPUT_DIR)
	$(LYNETTE) compile \
		--input $(INPUT_PNE) \
		--topology $(TOPOLOGY) \
		--service $(SERVICE) \
		--output $(OUTPUT_DIR)
	@echo "编译完成！"

clean:
	@rm -rf $(OUTPUT_DIR)

