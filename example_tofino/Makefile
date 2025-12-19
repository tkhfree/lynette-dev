# Makefile for Tofino Example
# 使用 GNU Make 自动化编译和部署流程

# 配置变量
PNE_FILE = Example_main.pne
SERVICE_JSON = service.json
TOPOLOGY_JSON = topology.json
OUTPUT_DIR = pne_out
TARGET = tna

# Tofino SDE 路径（根据实际环境修改）
SDE ?= /opt/bf-sde-9.7.0
SDE_INSTALL = $(SDE)/install
BF_P4C = $(SDE_INSTALL)/bin/bf-p4c

# 编译器选项
LYNETTE = python3 -m lynette
PATH_GEN = python3 ../generate_path.py

# 默认目标
.PHONY: all
all: compile

# 生成 path.json
.PHONY: path
path:
	@echo "==> Generating path.json..."
	@mkdir -p path
	$(PATH_GEN) $(SERVICE_JSON) $(TOPOLOGY_JSON) path/path.json
	@echo "✅ path.json generated"

# 使用 Service 模式编译
.PHONY: compile
compile: path
	@echo "==> Compiling PNE to P4..."
	$(LYNETTE) --config $(SERVICE_JSON) --output-dir $(OUTPUT_DIR) --target $(TARGET)
	@echo "✅ P4 files generated in $(OUTPUT_DIR)/"

# 使用 Debug 模式快速测试
.PHONY: debug
debug:
	@echo "==> Debug mode compilation..."
	$(LYNETTE) --debug-main $(PNE_FILE) --output-dir $(OUTPUT_DIR) --target $(TARGET)
	@echo "✅ Debug compilation completed"

# 编译生成的 P4 文件为 Tofino 二进制
.PHONY: build-p4
build-p4: compile
	@echo "==> Compiling P4 files with bf-p4c..."
	@for p4file in $(OUTPUT_DIR)/*.p4; do \
		base=$$(basename $$p4file .p4); \
		echo "  Compiling $$p4file..."; \
		$(BF_P4C) $$p4file \
			--target tofino \
			--arch tna \
			-o $(OUTPUT_DIR)/$$base.out \
			--p4runtime-files $(OUTPUT_DIR)/$$base.p4info.txt \
			--bf-rt-schema $(OUTPUT_DIR)/$$base.bfrt.json || exit 1; \
	done
	@echo "✅ P4 compilation completed"

# 验证 P4 代码语法
.PHONY: check
check: compile
	@echo "==> Checking P4 syntax..."
	@for p4file in $(OUTPUT_DIR)/*.p4; do \
		echo "  Checking $$p4file..."; \
		p4test $$p4file --std p4-16 || exit 1; \
	done
	@echo "✅ All P4 files are valid"

# 清理生成的文件
.PHONY: clean
clean:
	@echo "==> Cleaning..."
	rm -rf $(OUTPUT_DIR)
	rm -rf path/path.json
	rm -f service.json
	rm -rf log_out
	@echo "✅ Cleaned"

# 深度清理（包括编译产物）
.PHONY: distclean
distclean: clean
	rm -rf *.out *.bfrt.json *.p4info.txt
	@echo "✅ Deep cleaned"

# 显示帮助信息
.PHONY: help
help:
	@echo "Tofino Example Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all        - 编译 PNE 到 P4（默认）"
	@echo "  path       - 生成 path.json"
	@echo "  compile    - 完整编译流程"
	@echo "  debug      - Debug 模式快速编译"
	@echo "  build-p4   - 使用 bf-p4c 编译 P4 文件"
	@echo "  check      - 验证 P4 语法"
	@echo "  clean      - 清理生成的文件"
	@echo "  distclean  - 深度清理"
	@echo "  help       - 显示此帮助信息"
	@echo ""
	@echo "Environment Variables:"
	@echo "  SDE        - Tofino SDE 路径（当前: $(SDE)）"
	@echo ""
	@echo "Examples:"
	@echo "  make compile         # 编译 PNE"
	@echo "  make build-p4        # 编译为 Tofino 二进制"
	@echo "  make SDE=/path/to/sde build-p4  # 指定 SDE 路径"

# 显示生成的文件
.PHONY: show
show:
	@echo "Generated files:"
	@ls -lh $(OUTPUT_DIR)/ 2>/dev/null || echo "No files generated yet. Run 'make compile' first."

# 查看配置
.PHONY: config
config:
	@echo "Configuration:"
	@echo "  PNE File:      $(PNE_FILE)"
	@echo "  Service JSON:  $(SERVICE_JSON)"
	@echo "  Topology JSON: $(TOPOLOGY_JSON)"
	@echo "  Output Dir:    $(OUTPUT_DIR)"
	@echo "  Target:        $(TARGET)"
	@echo "  SDE:           $(SDE)"

