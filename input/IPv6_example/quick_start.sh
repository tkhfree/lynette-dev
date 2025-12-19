#!/bin/bash
# IPv6 示例快速启动脚本

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}IPv6 网络示例${NC}"

case "$1" in
    compile)
        echo "编译 IPv6 代码..."
        python3 -m lynette compile \
            --input ipv6_forwarding.pne \
            --topology topology.json \
            --service service.json \
            --output ../../output/ipv6_example/
        ;;
    *)
        echo "用法: $0 {compile|clean}"
        ;;
esac

