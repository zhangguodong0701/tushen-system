# 图审云平台 - Linux 部署指南

> 本文档介绍如何将图审云平台部署到 Linux 生产环境

---

## 一、环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 20.04+ / CentOS 7+ |
| Python | 3.9+ |
| Node.js | 18+ |
| Nginx | 1.18+ |
| 磁盘 | 至少 10GB可用空间 |

---

## 二、项目结构

```
tushen-system/
├── backend/          # FastAPI 后端
│   ├── main.py       # 主程序
│   ├── models.py     # 数据模型
│   ├── tushen.db     # SQLite 数据库
│   └── uploads/      # 上传文件目录
└── vue-project/     # Vue 3 前端
    ├── src/          # 源代码
    └── dist/         # 构建产物（需执行 build 后生成）
```

---

## 三、后端部署（FastAPI）

### 3.1 安装系统依赖

```bash
# Ubuntu
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx certbot

# CentOS
sudo yum install -y python3 python3-pip nginx
```

### 3.2 创建部署用户（可选）

```bash
sudo useradd -m -s /bin/bash tushen
sudo mkdir -p /opt/tushen-system
sudo chown tushen:tushen /opt/tushen-system
```

### 3.3 上传代码

```bash
# 将项目上传到服务器
scp -r tushen-system.tar.gz tushen@your-server:/opt/
ssh tushen@your-server
cd /opt
tar -xzf tushen-system.tar.gz
```

### 3.4 安装 Python 依赖

```bash
cd /opt/tushen-system/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy python-multipart \
  passlib bcrypt python-jose pydantic python-dotenv

# 初始化数据库（如需要）
# python main.py  # 首次启动会自动创建数据库表
```

### 3.5 配置环境变量（可选）

```bash
# 创建 .env 文件
cat > /opt/tushen-system/backend/.env << EOF
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./tushen.db
EOF
```

### 3.6 直接启动（开发/测试用）

```bash
cd /opt/tushen-system/backend
source venv/bin/activate
nohup python main.py > backend.log 2>&1 &
echo "Backend started"
```

验证后端是否正常运行：
```bash
curl http://localhost:8000/api/demands
```

### 3.7 生产环境：Gunicorn + Uvicorn Worker（推荐）

```bash
pip install gunicorn

# 启动（4个worker）
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 127.0.0.1:8000 \
  --access-logfile /opt/tushen-system/backend/access.log \
  --error-logfile /opt/tushen-system/backend/error.log \
  --daemon

echo "Gunicorn started with 4 workers"
```

### 3.8 用 systemd 管理后端进程（推荐）

```bash
sudo tee /etc/systemd/system/tushen-backend.service > /dev/null << 'EOF'
[Unit]
Description=Tushen Backend API
After=network.target

[Service]
User=tushen
Group=tushen
WorkingDirectory=/opt/tushen-system/backend
ExecStart=/opt/tushen-system/backend/venv/bin/gunicorn main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 127.0.0.1:8000
Restart=always
RestartSec=5
StandardOutput=append:/opt/tushen-system/backend/stdout.log
StandardError=append:/opt/tushen-system/backend/stderr.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable tushen-backend
sudo systemctl start tushen-backend
sudo systemctl status tushen-backend
```

常用命令：
```bash
sudo systemctl status tushen-backend   # 查看状态
sudo systemctl restart tushen-backend  # 重启
sudo systemctl stop tushen-backend     # 停止
sudo journalctl -u tushen-backend -f   # 查看日志
```

---

## 四、前端部署（Vue 3）

### 4.1 安装 Node.js（如未安装）

```bash
# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证
node -v   # v18.x.x
npm -v
```

### 4.2 安装依赖并构建

```bash
cd /opt/tushen-system/vue-project

# 安装依赖
npm install

# 构建生产版本
npm run build
```

构建完成后，`dist/` 目录即为静态文件。

### 4.3 配置 Nginx

```bash
sudo tee /etc/nginx/sites-available/tushen > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;   # 替换为你的域名或IP

    # 前端静态文件
    root /opt/tushen-system/vue-project/dist;
    index index.html;

    # Vue Router SPA 支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理到后端
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 上传文件访问
    location /uploads {
        alias /opt/tushen-system/backend/uploads;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/tushen /etc/nginx/sites-enabled/

# 测试并重载
sudo nginx -t
sudo systemctl reload nginx
```

### 4.4 HTTPS 配置（使用 Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书（需要域名已解析）
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

---

## 五、目录权限配置

```bash
# 设置目录所有者
sudo chown -R tushen:tushen /opt/tushen-system

# 确保 uploads 目录可写
sudo chmod -R 755 /opt/tushen-system/backend/uploads
sudo chmod 777 /opt/tushen-system/backend/uploads

# 数据库文件权限
sudo chmod 644 /opt/tushen-system/backend/tushen.db
```

---

## 六、一键部署脚本

将以下脚本保存为 `deploy.sh`，在服务器上执行即可完成部署：

```bash
#!/bin/bash
# deploy.sh - 图审云平台一键部署脚本

set -e

APP_DIR="/opt/tushen-system"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/vue-project"

echo "========== 图审云平台部署脚本 =========="

# 1. 停止旧服务
echo "[1/7] 停止旧服务..."
sudo systemctl stop tushen-backend 2>/dev/null || true
pkill -f "gunicorn.*main:app" 2>/dev/null || true

# 2. 更新代码（如使用 git）
# cd $APP_DIR && git pull origin master

# 3. 安装后端依赖
echo "[2/7] 安装后端依赖..."
cd $BACKEND_DIR
source venv/bin/activate
pip install --quiet -r requirements.txt 2>/dev/null || pip install --quiet fastapi uvicorn sqlalchemy python-multipart passlib bcrypt python-jose pydantic

# 4. 构建前端
echo "[3/7] 构建前端..."
cd $FRONTEND_DIR
npm install --silent
npm run build --silent

# 5. 启动后端
echo "[4/7] 启动后端服务..."
cd $BACKEND_DIR
source venv/bin/activate
nohup gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 \
  --access-logfile access.log --error-logfile error.log --daemon

# 6. 重载 Nginx
echo "[5/7] 重载 Nginx..."
sudo nginx -t && sudo systemctl reload nginx

# 7. 验证服务
echo "[6/7] 验证服务状态..."
sleep 2
if curl -sf http://localhost:8000/api/demands > /dev/null; then
    echo "✅ 后端服务正常"
else
    echo "⚠️ 后端服务可能未正常启动，请检查日志"
fi

if [ -d "$FRONTEND_DIR/dist" ]; then
    echo "✅ 前端构建成功"
else
    echo "⚠️ 前端构建可能失败"
fi

echo ""
echo "========== 部署完成 =========="
echo "前端访问：http://your-domain.com"
echo "API 文档：http://your-domain.com/docs"
echo "================================"
```

```bash
# 使用方式
chmod +x deploy.sh
./deploy.sh
```

---

## 七、备份策略

### 7.1 数据库备份

```bash
# 手动备份
cp /opt/tushen-system/backend/tushen.db /backup/tushen_$(date +%Y%m%d).db

# 自动备份（每天凌晨2点）
sudo tee /etc/cron.d/tushen-backup > /dev/null << 'EOF'
0 2 * * * root cp /opt/tushen-system/backend/tushen.db /backup/tushen_$(date +\%Y\%m\%d).db && find /backup -name "tushen_*.db" -mtime +7 -delete
EOF
```

### 7.2 文件备份

```bash
# 备份上传文件
tar -czf /backup/uploads_$(date +%Y%m%d).tar.gz /opt/tushen-system/backend/uploads
```

---

## 八、常见问题

### Q1: 后端启动报错 `ModuleNotFoundError`
```bash
# 确保在虚拟环境中
cd /opt/tushen-system/backend
source venv/bin/activate
pip install -r requirements.txt
```

### Q2: 前端构建失败 `npm ERR!`
```bash
# 清除缓存重试
cd /opt/tushen-system/vue-project
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
npm run build
```

### Q3: Nginx 502 Bad Gateway
```bash
# 检查后端是否运行
sudo systemctl status tushen-backend
curl http://127.0.0.1:8000/api/demands

# 检查 Nginx 日志
sudo tail -f /var/log/nginx/error.log
```

### Q4: 上传文件失败
```bash
# 检查 uploads 目录权限
ls -la /opt/tushen-system/backend/uploads
sudo chmod 777 /opt/tushen-system/backend/uploads
```

### Q5: 数据库并发写入问题（高并发场景）
SQLite 不适合高并发写入，建议切换到 PostgreSQL：
```python
# 修改 .env
DATABASE_URL=postgresql://user:password@localhost:5432/tushen
```

---

## 九、安全加固建议

1. **修改默认端口**：后端不要直接暴露在公网
2. **配置防火墙**：只开放 80/443 端口
3. **定期更新依赖**：`pip list --outdated` 检查过期包
4. **关闭 DEBUG 模式**：生产环境确保 `debug=False`
5. **设置文件大小限制**：Nginx 限制上传大小

```nginx
# Nginx 上传大小限制（默认 1M）
client_max_body_size 50M;
```

---

## 十、快速命令汇总

```bash
# 查看后端状态
sudo systemctl status tushen-backend

# 查看后端日志
sudo journalctl -u tushen-backend -f

# 重启后端
sudo systemctl restart tushen-backend

# 重载 Nginx
sudo systemctl reload nginx

# 重启 Nginx
sudo systemctl restart nginx

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 检查端口占用
sudo ss -tlnp | grep -E '80|443|8000'
```
