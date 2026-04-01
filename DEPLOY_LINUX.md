# 图审云平台 Docker 部署指南

> 本文档介绍如何使用 Docker 和 Docker Compose 部署图审云平台

---

## 一、环境要求

| 项目 | 要求 |
|------|------|
| Docker | 20.10+ |
| Docker Compose | 2.0+ |
| 磁盘 | 至少 10GB 可用空间 |

---

## 二、快速部署

### 2.1 一键启动

```bash
# 克隆项目
git clone https://github.com/zhangguodong0701/tushen-system.git
cd tushen-system

# 启动所有服务（首次会自动构建）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 2.2 访问服务

| 服务 | 地址 |
|------|------|
| 前端 | http://your-server-ip:80 |
| 后端 API | http://your-server-ip:8000 |
| API 文档 | http://your-server-ip:8000/docs |
| Nginx | http://your-server-ip:80 |

---

## 三、服务架构

```
                    ┌─────────────────────────────────┐
                    │         Nginx (:80)              │
                    │  静态文件 + API 反向代理         │
                    └────────────┬────────────────────┘
                                 │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
    ┌─────────────────┐ ┌─────────────┐ ┌──────────────────┐
    │   Vue Frontend  │ │  Backend    │ │    MySQL         │
    │   (构建产物)     │ │  FastAPI    │ │   (可选数据库)   │
    │   Port: 无       │ │  :8000      │ │   :3306          │
    └─────────────────┘ └──────┬──────┘ └──────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
          ┌─────────────────┐   ┌─────────────────┐
          │   SQLite DB     │   │   Uploads       │
          │   (挂载卷)       │   │   (挂载卷)       │
          └─────────────────┘   └─────────────────┘
```

---

## 四、配置说明

### 4.1 环境变量

创建 `.env` 文件配置环境：

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
nano .env
```

关键配置项：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MYSQL_HOST` | MySQL 主机（可选） | 空（使用 SQLite） |
| `MYSQL_PORT` | MySQL 端口 | 3306 |
| `MYSQL_DATABASE` | MySQL 数据库名 | tushen |
| `MYSQL_USER` | MySQL 用户名 | tushen |
| `MYSQL_PASSWORD` | MySQL 密码 | tushen123 |
| `BACKEND_PORT` | 后端端口 | 8000 |
| `FRONTEND_PORT` | 前端端口（直接访问 Vue） | 5173 |

### 4.2 使用 MySQL（可选，生产推荐）

如果需要使用 MySQL 数据库，取消 `docker-compose.yml` 中 MySQL 服务的注释，并修改后端配置。

---

## 五、目录结构

```
tushen-system/
├── docker-compose.yml      # Docker Compose 配置
├── Dockerfile              # 后端镜像构建
├── Dockerfile.frontend     # 前端镜像构建
├── nginx.conf              # Nginx 配置
├── .dockerignore           # Docker 忽略文件
├── .env.example            # 环境变量示例
├── backend/                # 后端代码
│   ├── main.py
│   ├── uploads/            # 文件上传目录（挂载卷）
│   └── tushen.db           # SQLite 数据库（挂载卷）
└── vue-project/            # 前端代码
    ├── src/
    └── dist/                # 构建产物
```

---

## 六、常用命令

### 6.1 启动/停止

```bash
# 启动所有服务
docker-compose up -d

# 启动并重新构建
docker-compose up -d --build

# 停止服务
docker-compose down

# 停止并删除数据卷（慎用）
docker-compose down -v
```

### 6.2 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend

# 查看 Nginx 日志
docker-compose logs -f nginx
```

### 6.3 进入容器

```bash
# 进入后端容器
docker exec -it tushen-backend bash

# 进入前端容器
docker exec -it tushen-frontend sh
```

### 6.4 数据管理

```bash
# 备份数据库
docker exec tushen-backend sh -c "cp /app/tushen.db /uploads/tushen_backup_$(date +%Y%m%d).db"

# 查看备份
ls -la backend/uploads/

# 恢复数据库
docker cp backup.db tushen-backend:/app/tushen.db
docker-compose restart backend
```

---

## 七、升级更新

### 7.1 拉取最新代码

```bash
cd tushen-system
git pull origin master
```

### 7.2 重新构建并启动

```bash
docker-compose down
docker-compose up -d --build
```

### 7.3 单独更新某个服务

```bash
# 只更新后端
docker-compose up -d --build backend

# 只更新前端
docker-compose up -d --build frontend
```

---

## 八、Nginx 配置说明

`nginx.conf` 主要配置：

- **静态文件服务**：直接提供 Vue 构建产物
- **API 反向代理**：将 `/api` 请求转发到后端
- **上传文件访问**：`/uploads` 路径直接访问上传文件
- **SPA 支持**：所有路由重定向到 `index.html`
- **Gzip 压缩**：减少传输体积
- **安全头**：X-Frame-Options、X-Content-Type-Options 等

---

## 九、数据持久化

以下目录作为 Docker 挂载卷，删除容器后数据保留：

| 宿主机路径 | 容器内路径 | 说明 |
|-----------|-----------|------|
| `./backend/uploads` | `/app/uploads` | 上传文件 |
| `./backend/tushen.db` | `/app/tushen.db` | SQLite 数据库 |
| `./frontend/dist` | `/usr/share/nginx/html` | Vue 构建产物 |

---

## 十、故障排查

### 10.1 服务启动失败

```bash
# 查看详细日志
docker-compose logs

# 检查容器状态
docker-compose ps

# 检查端口占用
netstat -tlnp | grep -E '80|8000|3306'
```

### 10.2 前端无法访问

```bash
# 检查 Nginx 容器
docker-compose logs nginx

# 检查前端构建产物是否存在
ls -la frontend/dist/
```

### 10.3 后端 API 无法访问

```bash
# 检查后端容器
docker-compose logs backend

# 进入容器检查
docker exec -it tushen-backend bash
curl http://localhost:8000/api/demands
```

### 10.4 数据库问题

```bash
# 检查数据库文件
ls -la backend/tushen.db

# 重新初始化数据库（慎用，会丢失数据）
rm backend/tushen.db
docker-compose restart backend
```

---

## 十一、安全建议

1. **修改默认端口**：生产环境修改 `docker-compose.yml` 中的端口映射
2. **配置防火墙**：只开放 80/443 端口
3. **定期备份**：执行 `backend/uploads/tushen_backup_*.db` 备份
4. **HTTPS 配置**：使用 Let's Encrypt 配置 HTTPS

```bash
# 安装 Certbot
docker exec tushen-nginx apt-get update
docker exec tushen-nginx apt-get install -y certbot python3-certbot-nginx

# 获取证书
docker exec tushen-nginx certbot --nginx -d your-domain.com
```

---

## 十二、一键部署脚本

创建 `deploy.sh`：

```bash
#!/bin/bash
set -e

echo "========== 图审云平台 Docker 部署 =========="

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

# 2. 拉取最新代码
echo "[1/4] 拉取最新代码..."
git pull origin master

# 3. 停止旧服务
echo "[2/4] 停止旧服务..."
docker-compose down

# 4. 重新构建并启动
echo "[3/4] 构建并启动服务..."
docker-compose up -d --build

# 5. 验证
echo "[4/4] 验证服务..."
sleep 5
if curl -sf http://localhost:80 > /dev/null; then
    echo "✅ 前端服务正常"
else
    echo "⚠️ 前端服务可能未正常启动"
fi

if curl -sf http://localhost:8000/docs > /dev/null; then
    echo "✅ 后端服务正常"
else
    echo "⚠️ 后端服务可能未正常启动"
fi

echo ""
echo "========== 部署完成 =========="
echo "前端：http://$(hostname -I | awk '{print $1}')"
echo "API：http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "================================"
```

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 十三、快速命令汇总

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重新构建
docker-compose up -d --build

# 进入后端容器
docker exec -it tushen-backend bash

# 备份数据库
docker exec tushen-backend sh -c "cp /app/tushen.db /uploads/backup_$(date +%Y%m%d).db"

# 更新代码并重启
git pull && docker-compose up -d --build
```
