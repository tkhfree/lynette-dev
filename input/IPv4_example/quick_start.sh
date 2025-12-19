#!/bin/bash
# IPv4 示例快速启动脚本

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}IPv4 企业网络示例${NC}"
echo -e "${GREEN}========================================${NC}"

case "$1" in
    compile)
        echo "编译 IPv4 代码..."
        python3 -m lynette compile \
            --input ipv4_forwarding.pne \
            --topology topology.json \
            --service service.json \
            --output ../../output/ipv4_example/
        ;;
    *)
        echo "用法: $0 {compile|test|clean}"
        ;;
esac

