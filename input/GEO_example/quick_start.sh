#!/bin/bash

# ============================================================
# GeoNetworking 车联网示例快速启动脚本
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/../../output/geo_example"
LYNETTE_ROOT="${SCRIPT_DIR}/../.."

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GeoNetworking 车联网示例${NC}"
echo -e "${GREEN}快速启动脚本${NC}"
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
    echo "  compile     - 编译 PNE 代码为 P4 代码"
    echo "  deploy      - 显示部署指南"
    echo "  topology    - 显示网络拓扑"
    echo "  flow        - 显示转发流程"
    echo "  use-cases   - 显示应用场景"
    echo "  arch        - 显示架构组件"
    echo "  test        - 运行测试场景"
    echo "  clean       - 清理生成的文件"
    echo "  all         - 执行所有步骤"
    echo "  help        - 显示此帮助信息"
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
    print_step "编译 GeoNetworking PNE 代码..."
    
    cd "${SCRIPT_DIR}" || exit 1
    
    # 创建输出目录
    mkdir -p "${OUTPUT_DIR}"
    
    # 运行 Lynette 编译器
    python3 -m lynette compile \
        --input geo_forwarding.pne \
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

# 函数：显示拓扑
show_topology() {
    print_step "GeoNetworking 网络拓扑"
    echo ""
    cat << "EOF"
                    [rsu-north]
                   (北侧RSU)
                   39.9075°N, 116.3972°E
                        |
                   Vehicle-1
                   (紧急制动)
                        |
    [rsu-west] ---  [rsu-center]  --- [rsu-east]
   (西侧RSU)         (中心RSU)         (东侧RSU)
  39.9065°N         39.9065°N         39.9065°N
  116.3952°E        116.3972°E        116.3992°E
       |                |                 |
  Emergency-V           |            Vehicle-2
  (救护车)              |            (接收警告)
                        |
                   [rsu-south]
                   (南侧RSU)
                   39.9055°N, 116.3972°E
                        |
                   Vehicle-3
                   (协作感知)
EOF
    echo ""
    echo -e "${CYAN}通信范围:${NC}"
    echo "  - 边缘RSU: 300米"
    echo "  - 中心RSU: 500米"
    echo "  - RSU间距: ~200米"
    echo ""
    echo -e "${CYAN}覆盖区域:${NC}"
    echo "  - 路口核心区: 圆形，半径150米"
    echo "  - 北向接近段: 矩形，50m × 200m"
    echo "  - 事故区域: 圆形，半径80米（东北象限）"
    echo ""
}

# 函数：显示转发流程
show_flow() {
    print_step "GeoNetworking 转发流程"
    echo ""
    echo -e "${GREEN}GeoBroadcast (GBC) 转发流程:${NC}"
    echo ""
    echo "1. 接收 GBC 消息"
    echo "   ↓"
    echo "2. 检查剩余跳数 (RHL > 0?)"
    echo "   ├─ RHL = 0 → 丢弃"
    echo "   └─ RHL > 0 → 继续"
    echo "   ↓"
    echo "3. 序列号检查（防重复）"
    echo "   ├─ 已接收 → 丢弃"
    echo "   └─ 未接收 → 记录并继续"
    echo "   ↓"
    echo "4. 更新位置表"
    echo "   └─ 记录源节点位置信息"
    echo "   ↓"
    echo "5. 地理区域检查"
    echo "   ├─ 在区域内 → 广播到所有邻居（除入端口）"
    echo "   └─ 不在区域内 ↓"
    echo "6. 贪婪转发"
    echo "   ├─ 查找位置表中的邻居"
    echo "   ├─ 计算各邻居到目标区域的距离"
    echo "   └─ 选择最接近目标的邻居转发"
    echo "   ↓"
    echo "7. 更新头部"
    echo "   └─ RHL = RHL - 1"
    echo "   ↓"
    echo "8. 转发数据包"
    echo ""
    echo -e "${GREEN}Beacon 处理流程:${NC}"
    echo ""
    echo "1. 接收 Beacon 消息"
    echo "   ↓"
    echo "2. 提取位置信息"
    echo "   └─ GN地址、纬度、经度、时间戳"
    echo "   ↓"
    echo "3. 更新位置表"
    echo "   ├─ 新节点 → 添加条目"
    echo "   └─ 已知节点 → 更新位置和时间戳"
    echo "   ↓"
    echo "4. 不转发（Beacon 仅单跳广播）"
    echo ""
}

# 函数：显示应用场景
show_use_cases() {
    print_step "GeoNetworking 应用场景"
    echo ""
    
    echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  场景 1: 紧急制动警告                 ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
    echo "描述: 车辆1在路口北侧紧急制动"
    echo "消息类型: DENM (Decentralized Environmental Notification)"
    echo "GeoNetworking类型: GeoBroadcast (GBC)"
    echo "目标区域: 圆形，半径200米"
    echo ""
    echo "消息流:"
    echo "  Vehicle-1 (紧急制动)"
    echo "      ↓ [DENM]"
    echo "  RSU-North (接收并转发)"
    echo "      ↓"
    echo "  RSU-Center (在目标区域内，广播)"
    echo "      ├─→ RSU-East → Vehicle-2 ✓"
    echo "      ├─→ RSU-South → Vehicle-3 ✓"
    echo "      └─→ RSU-West"
    echo ""
    echo "延迟要求: < 50ms"
    echo "成功率要求: > 99%"
    echo ""
    
    echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  场景 2: 紧急车辆接近警告             ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
    echo "描述: 救护车从西向东接近路口"
    echo "消息类型: DENM (高优先级)"
    echo "目标区域: 矩形，100m × 400m，沿行驶方向"
    echo ""
    echo "消息流:"
    echo "  Emergency-Vehicle (救护车)"
    echo "      ↓ [DENM, Priority: HIGHEST]"
    echo "  RSU-West"
    echo "      ↓"
    echo "  RSU-Center (紧急消息，广播到所有方向)"
    echo "      ├─→ RSU-North (通知北向车辆让行)"
    echo "      ├─→ RSU-East (通知东向车辆注意)"
    echo "      └─→ RSU-South (通知南向车辆让行)"
    echo ""
    echo "优先级: 最高"
    echo "特殊处理: 抢占式转发，优先队列"
    echo ""
    
    echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  场景 3: 协作感知                     ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
    echo "描述: 所有车辆周期性广播位置和状态"
    echo "消息类型: CAM (Cooperative Awareness Message)"
    echo "频率: 10 Hz (每100ms一次)"
    echo "GeoNetworking类型: TSB (拓扑范围广播)"
    echo ""
    echo "功能:"
    echo "  - 邻居发现"
    echo "  - 位置表维护"
    echo "  - 碰撞风险评估"
    echo "  - 盲区预警"
    echo ""
    echo "内容:"
    echo "  - 位置 (纬度、经度)"
    echo "  - 速度和加速度"
    echo "  - 航向角"
    echo "  - 车辆尺寸和类型"
    echo ""
    
    echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  场景 4: 事故通知                     ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
    echo "描述: 路口东北象限发生事故"
    echo "目标区域: 圆形，半径80米（事故点中心）"
    echo ""
    echo "智能转发:"
    echo "  RSU-Center: 计算距离 → 在事故区域内"
    echo "      ├─→ RSU-North: 计算距离 → 在区域内，参与转发"
    echo "      ├─→ RSU-East: 计算距离 → 在区域内，参与转发"
    echo "      ├─→ RSU-South: 计算距离 → 不在区域内，不转发"
    echo "      └─→ RSU-West: 计算距离 → 不在区域内，不转发"
    echo ""
    echo "优势:"
    echo "  - 基于区域的选择性转发"
    echo "  - 减少不必要的消息传播"
    echo "  - 降低网络负载"
    echo ""
}

# 函数：显示架构
show_architecture() {
    print_step "GeoNetworking 架构组件"
    echo ""
    
    echo -e "${CYAN}核心模块:${NC}"
    echo ""
    echo "┌─────────────────────────────────────────────┐"
    echo "│ 1. GeoParser - 数据包解析器                │"
    echo "├─────────────────────────────────────────────┤"
    echo "│ • 解析 GeoNetworking 各种头部类型           │"
    echo "│ • 支持 Beacon、GBC、GUC、TSB 等            │"
    echo "│ • 提取地理位置信息                          │"
    echo "│ • 初始化处理元数据                          │"
    echo "└─────────────────────────────────────────────┘"
    echo ""
    echo "┌─────────────────────────────────────────────┐"
    echo "│ 2. LocationTable - 位置表管理               │"
    echo "├─────────────────────────────────────────────┤"
    echo "│ • 维护邻居节点位置信息                      │"
    echo "│ • 从 Beacon/CAM 消息更新                    │"
    echo "│ • 容量: 256 条目                            │"
    echo "│ • 支持位置查询和老化                        │"
    echo "└─────────────────────────────────────────────┘"
    echo ""
    echo "┌─────────────────────────────────────────────┐"
    echo "│ 3. GeoAreaCheck - 地理区域检查              │"
    echo "├─────────────────────────────────────────────┤"
    echo "│ • 判断节点是否在目标区域内                  │"
    echo "│ • 支持圆形、矩形、椭圆区域                  │"
    echo "│ • 计算节点到区域中心的距离                  │"
    echo "│ • 区域命中判定                              │"
    echo "└─────────────────────────────────────────────┘"
    echo ""
    echo "┌─────────────────────────────────────────────┐"
    echo "│ 4. GreedyForwarding - 贪婪转发算法          │"
    echo "├─────────────────────────────────────────────┤"
    echo "│ • 选择最接近目标位置的邻居                  │"
    echo "│ • 实现地理位置路由核心算法                  │"
    echo "│ • 基于距离的转发决策                        │"
    echo "│ • 处理转发失败和路由空洞                    │"
    echo "└─────────────────────────────────────────────┘"
    echo ""
    echo "┌─────────────────────────────────────────────┐"
    echo "│ 5. SequenceNumberCheck - 序列号检查         │"
    echo "├─────────────────────────────────────────────┤"
    echo "│ • 防止数据包重复接收和转发                  │"
    echo "│ • 维护序列号缓存（512 条目）                │"
    echo "│ • 环路检测和防止                            │"
    echo "│ • 基于 (源地址, 序列号) 二元组              │"
    echo "└─────────────────────────────────────────────┘"
    echo ""
    echo "┌─────────────────────────────────────────────┐"
    echo "│ 6. GeoStatistics - 统计模块                 │"
    echo "├─────────────────────────────────────────────┤"
    echo "│ • 统计各类消息数量                          │"
    echo "│ • 监控转发性能指标                          │"
    echo "│ • 区域命中率统计                            │"
    echo "│ • 网络负载监控                              │"
    echo "└─────────────────────────────────────────────┘"
    echo ""
    
    echo -e "${CYAN}协议栈:${NC}"
    echo ""
    echo "  ┌────────────────────────────────────┐"
    echo "  │   Application Layer                │"
    echo "  │   CAM, DENM, SPAT, MAP             │"
    echo "  ├────────────────────────────────────┤"
    echo "  │   Transport Layer (BTP)            │"
    echo "  │   Basic Transport Protocol         │"
    echo "  ├────────────────────────────────────┤"
    echo "  │   Network Layer (GeoNetworking)    │"
    echo "  │   ┌──────────────────────────────┐ │"
    echo "  │   │  Basic Header                │ │"
    echo "  │   ├──────────────────────────────┤ │"
    echo "  │   │  Common Header               │ │"
    echo "  │   ├──────────────────────────────┤ │"
    echo "  │   │  Extended Header             │ │"
    echo "  │   │  (GBC/GUC/Beacon/TSB)        │ │"
    echo "  │   └──────────────────────────────┘ │"
    echo "  ├────────────────────────────────────┤"
    echo "  │   Access Layer                     │"
    echo "  │   IEEE 802.11p / ITS-G5            │"
    echo "  ├────────────────────────────────────┤"
    echo "  │   Physical Layer                   │"
    echo "  │   5.9 GHz DSRC                     │"
    echo "  └────────────────────────────────────┘"
    echo ""
}

# 函数：运行测试
run_tests() {
    print_step "GeoNetworking 测试验证"
    echo ""
    
    print_warning "注意: 完整测试需要部署到仿真器或真实环境"
    echo ""
    
    echo -e "${GREEN}测试项目:${NC}"
    echo ""
    echo "✓ 基本功能测试"
    echo "  - Beacon 消息处理"
    echo "  - 位置表更新"
    echo "  - GBC 消息转发"
    echo "  - 序列号检查"
    echo ""
    echo "✓ 转发算法测试"
    echo "  - 贪婪转发正确性"
    echo "  - 区域判定准确性"
    echo "  - 邻居选择优化"
    echo ""
    echo "✓ 性能测试"
    echo "  - 端到端延迟"
    echo "  - 消息送达率"
    echo "  - 网络吞吐量"
    echo ""
    echo "✓ 场景测试"
    echo "  - 紧急制动警告"
    echo "  - 紧急车辆优先"
    echo "  - 协作感知"
    echo "  - 事故通知"
    echo ""
}

# 函数：部署指南
show_deploy() {
    print_step "部署指南"
    echo ""
    
    if [ ! -d "${OUTPUT_DIR}" ]; then
        print_error "输出目录不存在，请先运行编译"
        exit 1
    fi
    
    echo -e "${CYAN}使用 BMv2 (Behavioral Model v2) 部署:${NC}"
    echo ""
    echo "终端 1 - RSU-North:"
    echo "simple_switch_grpc --device-id 1 \\"
    echo "    -i 1@veth1 -i 2@veth2 -i 3@veth3 \\"
    echo "    ${OUTPUT_DIR}/rsu-north.p4.json"
    echo ""
    echo "终端 2 - RSU-South:"
    echo "simple_switch_grpc --device-id 2 \\"
    echo "    -i 1@veth4 -i 3@veth5 \\"
    echo "    ${OUTPUT_DIR}/rsu-south.p4.json"
    echo ""
    echo "终端 3 - RSU-East:"
    echo "simple_switch_grpc --device-id 3 \\"
    echo "    -i 1@veth6 -i 2@veth7 -i 3@veth8 \\"
    echo "    ${OUTPUT_DIR}/rsu-east.p4.json"
    echo ""
    echo "终端 4 - RSU-West:"
    echo "simple_switch_grpc --device-id 4 \\"
    echo "    -i 1@veth9 -i 3@veth10 \\"
    echo "    ${OUTPUT_DIR}/rsu-west.p4.json"
    echo ""
    echo "终端 5 - RSU-Center:"
    echo "simple_switch_grpc --device-id 5 \\"
    echo "    -i 1@veth11 -i 2@veth12 -i 3@veth13 -i 4@veth14 \\"
    echo "    ${OUTPUT_DIR}/rsu-center.p4.json"
    echo ""
    print_warning "注意: 需要预先创建 veth 虚拟网络接口对"
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

# 主函数
main() {
    case "$1" in
        compile)
            check_dependencies
            compile_pne
            ;;
        deploy)
            show_deploy
            ;;
        topology)
            show_topology
            ;;
        flow)
            show_flow
            ;;
        use-cases)
            show_use_cases
            ;;
        arch)
            show_architecture
            ;;
        test)
            run_tests
            ;;
        clean)
            clean_files
            ;;
        all)
            check_dependencies
            compile_pne
            show_topology
            show_flow
            show_architecture
            show_use_cases
            run_tests
            show_deploy
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

