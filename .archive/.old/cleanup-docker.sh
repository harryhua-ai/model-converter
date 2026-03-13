#!/bin/bash
# Docker 清理脚本 - 构建完成后使用

echo "=== Docker 清理脚本 ==="
echo ""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 显示当前占用
echo -e "${YELLOW}当前磁盘占用:${NC}"
docker system df
echo ""

# 选项菜单
echo "请选择清理选项:"
echo "  1) 清理构建缓存 (推荐，释放最多空间)"
echo "  2) 清理悬空镜像"
echo "  3) 清理所有未使用资源 (包括未使用镜像)"
echo "  4) 查看详细信息后决定"
echo "  5) 退出"
echo ""
read -p "请输入选项 (1-5): " choice

case $choice in
  1)
    echo -e "${GREEN}清理构建缓存...${NC}"
    docker builder prune -a -f
    echo -e "${GREEN}✅ 构建缓存已清理${NC}"
    ;;
  2)
    echo -e "${GREEN}清理悬空镜像...${NC}"
    docker image prune -f
    echo -e "${GREEN}✅ 悬空镜像已清理${NC}"
    ;;
  3)
    echo -e "${RED}警告: 这将删除所有未使用的镜像和容器!${NC}"
    read -p "确认继续? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      docker system prune -a -f
      echo -e "${GREEN}✅ 系统清理完成${NC}"
    else
      echo "已取消"
    fi
    ;;
  4)
    echo -e "${YELLOW}详细镜像列表:${NC}"
    docker images -a
    echo ""
    echo -e "${YELLOW}详细构建缓存:${NC}"
    docker builder ls
    ;;
  5)
    echo "退出"
    exit 0
    ;;
  *)
    echo -e "${RED}无效选项${NC}"
    exit 1
    ;;
esac

echo ""
echo -e "${GREEN}清理后的磁盘占用:${NC}"
docker system df
