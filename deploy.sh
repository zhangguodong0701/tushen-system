#!/bin/bash
# ============================================
# 图审云平台 Docker 一键部署脚本
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   图审云平台 Docker 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 检查 Docker
echo -e "\n${YELLOW}[1/6] 检查 Docker 环境...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker Compose${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 环境检查通过${NC}"

# 2. 检查端口
echo -e "\n${YELLOW}[2/6] 检查端口占用...${NC}"
PORTS=(80 8000)
for PORT in "${PORTS[@]}"; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -an | grep -q ":$PORT.*LISTEN" 2>/dev/null; then
        echo -e "${RED}⚠️  端口 $PORT 已被占用${NC}"
    else
        echo -e "  端口 $PORT: ${GREEN}可用${NC}"
    fi
done

# 3. 创建必要目录
echo -e "\n${YELLOW}[3/6] 创建必要目录...${NC}"
mkdir -p backend/uploads
touch backend/uploads/.gitkeep
echo -e "${GREEN}✅ 目录创建完成${NC}"

# 4. 拉取最新代码
echo -e "\n${YELLOW}[4/6] 检查代码更新...${NC}"
if [ -d ".git" ]; then
    read -p "是否拉取最新代码？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git pull origin master
        echo -e "${GREEN}✅ 代码更新完成${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  非 Git 仓库，跳过代码更新${NC}"
fi

# 5. 构建并启动
echo -e "\n${YELLOW}[5/6] 构建并启动服务...${NC}"
docker-compose down 2>/dev/null || true
docker-compose up -d --build

# 6. 验证服务
echo -e "\n${YELLOW}[6/6] 验证服务状态...${NC}"
sleep 10

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   服务状态${NC}"
echo -e "${GREEN}========================================${NC}"

docker-compose ps

echo -e "\n${GREEN}✅ 部署完成！${NC}"
echo -e "\n访问地址："
echo -e "  前端：http://localhost"
echo -e "  API：http://localhost:8000"
echo -e "  API 文档：http://localhost:8000/docs"

echo -e "\n常用命令："
echo -e "  查看日志：docker-compose logs -f"
echo -e "  停止服务：docker-compose down"
echo -e "  重启服务：docker-compose restart"
echo -e "${GREEN}========================================${NC}"
