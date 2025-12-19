#!/bin/bash

# ============================================================
# NDN 示例快速启动脚本
# 用于快速编译、部署和测试 NDN 网络
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/../../output/ndn_example"
LYNETTE_ROOT="${SCRIPT_DIR}/../.."

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}NDN 网络示例 - 快速启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 函数：打印步骤
print_step() {
    echo -e "${BLUE}>>> $1${NC}"
}

# 函数：打印成功
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 函数：打印警告
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 函数：打印错误
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 函数：显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  compile   - 编译 PNE 代码为 P4 代码"
    echo "  deploy    - 部署到 BMv2 仿真器"
    echo "  test      - 运行测试场景"
    echo "  clean     - 清理生成的文件"
    echo "  all       - 执行所有步骤（编译、部署、测试）"
    echo "  help      - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 compile    # 只编译"
    echo "  $0 all        # 完整流程"
}

# 函数：检查依赖
check_dependencies() {
    print_step "检查依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "未找到 Python3"
        exit 1
    fi
    print_success "Python3: $(python3 --version)"
    
    # 检查 Lynette
    if [ ! -d "${LYNETTE_ROOT}/lynette" ]; then
        print_error "未找到 Lynette 模块"
        exit 1
    fi
    print_success "Lynette 模块存在"
    
    echo ""
}

# 函数：编译 PNE 代码
compile_pne() {
    print_step "编译 PNE 代码为 P4 代码..."
    
    cd "${SCRIPT_DIR}" || exit 1
    
    # 创建输出目录
    mkdir -p "${OUTPUT_DIR}"
    
    # 运行 Lynette 编译器
    python3 -m lynette compile \
        --input ndn_forwarding.pne \
        --topology topology.json \
        --service service.json \
        --output "${OUTPUT_DIR}"
    
    if [ $? -eq 0 ]; then
        print_success "编译成功！"
        echo ""
        echo "生成的文件:"
        ls -lh "${OUTPUT_DIR}"
        echo ""
    else
        print_error "编译失败"
        exit 1
    fi
}

# 函数：部署到 BMv2
deploy_bmv2() {
    print_step "准备部署到 BMv2 仿真器..."
    
    if [ ! -d "${OUTPUT_DIR}" ]; then
        print_error "输出目录不存在，请先运行编译"
        exit 1
    fi
    
    print_warning "BMv2 部署需要手动执行以下命令:"
    echo ""
    echo -e "${YELLOW}终端 1 - 启动 ndn-switch1:${NC}"
    echo "simple_switch_grpc --device-id 1 \\"
    echo "    -i 1@veth1 -i 2@veth2 -i 3@veth3 -i 4@veth4 \\"
    echo "    ${OUTPUT_DIR}/ndn-switch1.p4.json"
    echo ""
    echo -e "${YELLOW}终端 2 - 启动 ndn-switch2:${NC}"
    echo "simple_switch_grpc --device-id 2 \\"
    echo "    -i 1@veth5 -i 2@veth6 \\"
    echo "    ${OUTPUT_DIR}/ndn-switch2.p4.json"
    echo ""
    echo -e "${YELLOW}终端 3 - 启动 ndn-switch3:${NC}"
    echo "simple_switch_grpc --device-id 3 \\"
    echo "    -i 1@veth7 -i 2@veth8 -i 3@veth9 \\"
    echo "    ${OUTPUT_DIR}/ndn-switch3.p4.json"
    echo ""
    echo -e "${YELLOW}注意: 需要先创建 veth 虚拟网络接口${NC}"
    echo ""
}

# 函数：显示拓扑
show_topology() {
    print_step "NDN 网络拓扑:"
    echo ""
    cat << "EOF"
          Consumer1
              |
              | port 3
         [ndn-switch1] ----------- port 1 ----------- [ndn-switch2]
          (Arizona)      |                                  |
              |          |                                  | port 2
              | port 2   |                                  |
         Producer2       |                             [ndn-switch3]
                         |                              (UCLA)
                         |                                  |
                         +---------- port 2 ----------------+
                                                            | port 3
                                                            |
                                                       Producer1
EOF
    echo ""
}

# 函数：显示转发流程
show_flow() {
    print_step "NDN 转发流程:"
    echo ""
    echo -e "${GREEN}Interest 处理流程:${NC}"
    echo "1. 接收 Interest"
    echo "   ↓"
    echo "2. CS 查找"
    echo "   ├─ 命中 → 返回缓存的 Data"
    echo "   └─ 未命中 ↓"
    echo "3. PIT 查找"
    echo "   ├─ 已存在 → Interest 聚合（检查 nonce）"
    echo "   └─ 不存在 ↓"
    echo "4. FIB 查找"
    echo "   ↓"
    echo "5. 转发到下一跳"
    echo "   ↓"
    echo "6. 记录到 PIT"
    echo ""
    echo -e "${GREEN}Data 处理流程:${NC}"
    echo "1. 接收 Data"
    echo "   ↓"
    echo "2. PIT 查找"
    echo "   ├─ 命中 → 按 PIT 记录的 face 转发"
    echo "   │         ↓"
    echo "   │      3. 缓存到 CS"
    echo "   │         ↓"
    echo "   │      4. 清除 PIT 条目"
    echo "   └─ 未命中 → 丢弃（未请求的 Data）"
    echo ""
}

# 函数：运行测试
run_tests() {
    print_step "NDN 测试场景"
    echo ""
    
    echo -e "${GREEN}场景 1: 基本内容检索${NC}"
    echo "  描述: Consumer1 从 Producer1 获取内容"
    echo "  内容名: /ndn/edu/ucla/video/lecture1"
    echo "  路径: Consumer1 -> ndn-switch1 -> ndn-switch3 -> Producer1"
    echo ""
    
    echo -e "${GREEN}场景 2: 本地内容检索${NC}"
    echo "  描述: Consumer1 从 Producer2（本地）获取内容"
    echo "  内容名: /ndn/edu/arizona/data/sensor1"
    echo "  路径: Consumer1 -> ndn-switch1 -> Producer2"
    echo ""
    
    echo -e "${GREEN}场景 3: 内容缓存测试${NC}"
    echo "  描述: 多次请求相同内容，测试 CS 缓存效果"
    echo "  内容名: /ndn/edu/ucla/popular/news"
    echo "  第一次: 从 Producer 获取并缓存"
    echo "  第二次: 从 ndn-switch2 的 CS 直接返回"
    echo ""
    
    echo -e "${GREEN}场景 4: Interest 聚合${NC}"
    echo "  描述: 多个 Interest 请求相同内容"
    echo "  行为: 第一个 Interest 转发，后续 Interest 聚合到 PIT"
    echo "  结果: 只发送一次 Interest，Data 返回时满足所有请求"
    echo ""
    
    print_warning "注意: 实际测试需要部署到仿真器或真实环境"
    echo ""
}

# 函数：清理文件
clean_files() {
    print_step "清理生成的文件..."
    
    if [ -d "${OUTPUT_DIR}" ]; then
        rm -rf "${OUTPUT_DIR}"
        print_success "已删除 ${OUTPUT_DIR}"
    else
        print_warning "输出目录不存在，无需清理"
    fi
    echo ""
}

# 函数：显示架构信息
show_architecture() {
    print_step "NDN 架构组件"
    echo ""
    echo -e "${GREEN}核心模块:${NC}"
    echo "  1. ${YELLOW}Content Store (CS)${NC}"
    echo "     - 功能: 缓存经过的 Data 包"
    echo "     - 容量: 256 条目/交换机"
    echo "     - 文件: ndn_forwarding.pne -> ContentStore 模块"
    echo ""
    echo "  2. ${YELLOW}Pending Interest Table (PIT)${NC}"
    echo "     - 功能: 跟踪待处理的 Interest"
    echo "     - 容量: 1024 条目/交换机"
    echo "     - 特性: Interest 聚合、环路检测"
    echo "     - 文件: ndn_forwarding.pne -> PendingInterestTable 模块"
    echo ""
    echo "  3. ${YELLOW}Forwarding Information Base (FIB)${NC}"
    echo "     - 功能: 基于名字前缀的路由决策"
    echo "     - 容量: 512 条目/交换机"
    echo "     - 特性: 最长前缀匹配"
    echo "     - 文件: ndn_forwarding.pne -> ForwardingInformationBase 模块"
    echo ""
    echo "  4. ${YELLOW}NDN Parser${NC}"
    echo "     - 功能: 解析 Interest/Data 包"
    echo "     - 文件: ndn_forwarding.pne -> NDNParser 模块"
    echo ""
    echo "  5. ${YELLOW}Statistics${NC}"
    echo "     - 功能: 统计网络性能指标"
    echo "     - 文件: ndn_forwarding.pne -> NDNStatistics 模块"
    echo ""
}

# 主函数
main() {
    case "$1" in
        compile)
            check_dependencies
            compile_pne
            ;;
        deploy)
            show_topology
            deploy_bmv2
            ;;
        test)
            run_tests
            ;;
        clean)
            clean_files
            ;;
        topology)
            show_topology
            ;;
        flow)
            show_flow
            ;;
        arch|architecture)
            show_architecture
            ;;
        all)
            check_dependencies
            compile_pne
            show_topology
            show_flow
            show_architecture
            run_tests
            deploy_bmv2
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 如果没有参数，显示帮助
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

# 执行主函数
main "$@"

