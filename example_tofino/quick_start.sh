#!/bin/bash
# 快速启动脚本 - Tofino 示例项目

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印标题
print_header() {
    echo ""
    echo "======================================================================"
    echo "$1"
    echo "======================================================================"
    echo ""
}

# 检查依赖
check_dependencies() {
    print_header "检查依赖"
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 未安装"
        exit 1
    fi
    info "✓ Python3: $(python3 --version)"
    
    # 检查 Lynette
    if ! python3 -m lynette -h &> /dev/null; then
        error "Lynette 未安装"
        info "请运行: python3 setup.py develop"
        exit 1
    fi
    info "✓ Lynette 已安装"
    
    # 检查路径生成器
    if [ ! -f "../generate_path.py" ]; then
        warning "路径生成器未找到，将手动创建 path.json"
    else
        info "✓ 路径生成器可用"
    fi
    
    success "依赖检查完成"
}

# 生成路径配置
generate_path() {
    print_header "生成路径配置"
    
    if [ -f "../generate_path.py" ]; then
        info "使用自动生成器..."
        mkdir -p path
        python3 ../generate_path.py service.json topology.json path/path.json
        success "path.json 已自动生成"
    else
        warning "手动创建 path.json..."
        mkdir -p path
        cat > path/path.json << 'EOF'
{
    "SimpleRouting": {
        "tofino1": {
            "next": {"tofino2": 1},
            "tables": 16,
            "ip": "192.168.0.1"
        },
        "tofino2": {
            "next": {"tofino3": 2},
            "tables": 16,
            "ip": "192.168.0.2"
        },
        "tofino3": {
            "next": {},
            "tables": 16,
            "ip": "192.168.0.3"
        }
    }
}
EOF
        success "path.json 已手动创建"
    fi
}

# 编译 PNE
compile_pne() {
    print_header "编译 PNE 到 P4"
    
    info "执行编译..."
    python3 -m lynette \
        --config service.json \
        --output-dir pne_out \
        --target tna \
        --clean
    
    success "PNE 编译完成"
}

# 验证生成的 P4 文件
verify_p4() {
    print_header "验证生成的 P4 文件"
    
    if [ ! -d "pne_out" ]; then
        error "输出目录不存在"
        exit 1
    fi
    
    p4_files=$(ls pne_out/*.p4 2>/dev/null | wc -l)
    if [ "$p4_files" -eq 0 ]; then
        error "没有生成 P4 文件"
        exit 1
    fi
    
    info "生成了 $p4_files 个 P4 文件:"
    ls -lh pne_out/*.p4
    
    # 检查 p4test
    if command -v p4test &> /dev/null; then
        info "使用 p4test 验证语法..."
        for p4file in pne_out/*.p4; do
            info "  验证 $(basename $p4file)..."
            if p4test "$p4file" --std p4-16 &> /dev/null; then
                success "  ✓ $(basename $p4file) 语法正确"
            else
                warning "  ⚠ $(basename $p4file) 可能有语法问题"
            fi
        done
    else
        warning "p4test 未安装，跳过语法验证"
    fi
    
    success "验证完成"
}

# 显示结果
show_results() {
    print_header "编译结果"
    
    echo "生成的文件:"
    echo ""
    tree pne_out 2>/dev/null || ls -R pne_out
    
    echo ""
    success "✅ 编译成功！"
    echo ""
    echo "下一步:"
    echo "  1. 查看生成的 P4 文件: ls pne_out/"
    echo "  2. 使用 bf-p4c 编译: make build-p4"
    echo "  3. 部署到 Tofino 交换机"
    echo ""
    echo "详细信息请查看 README.md"
}

# 主函数
main() {
    print_header "Tofino 示例项目 - 快速启动"
    
    # 确保在正确的目录
    if [ ! -f "Example_main.pne" ]; then
        error "请在 example_tofino 目录下运行此脚本"
        exit 1
    fi
    
    # 执行步骤
    check_dependencies
    generate_path
    compile_pne
    verify_p4
    show_results
}

# 运行主函数
main "$@"

