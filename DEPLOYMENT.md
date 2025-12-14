# MingJing 明镜 - 部署文档

## 📋 目录

- [快速开始](#快速开始)
- [环境要求](#环境要求)
- [部署方式](#部署方式)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [维护指南](#维护指南)

---

## 🚀 快速开始

### 一键部署（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd MingJing

# 2. 一键启动
./deploy.sh start

# 3. 访问系统
# 前端: http://localhost
# 后端: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

就这么简单！🎉

---

## 📦 环境要求

### 必需
- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0

### 可选
- **Git**: 用于克隆代码
- **Make**: 用于快捷命令

### 系统要求
- **CPU**: 2核心+
- **内存**: 2GB+
- **磁盘**: 5GB+
- **操作系统**: Linux / macOS / Windows (WSL2)

---

## 🛠️ 部署方式

### 方式一：Docker Compose（推荐）

#### 1. 准备工作

```bash
# 检查 Docker 版本
docker --version
docker-compose --version

# 创建数据目录
mkdir -p data/db data/logs
```

#### 2. 配置环境变量

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置（可选）
vim .env
```

#### 3. 启动服务

```bash
# 使用部署脚本
./deploy.sh start

# 或直接使用 docker-compose
docker-compose up -d --build
```

#### 4. 验证部署

```bash
# 查看服务状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 测试后端 API
curl http://localhost:8000/health

# 测试前端
curl http://localhost
```

---

### 方式二：手动部署

#### 后端部署

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 下载 NLP 模型
python -m spacy download zh_core_web_sm

# 启动服务
python main.py
```

#### 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 使用 Nginx 或其他 Web 服务器部署 dist 目录
```

---

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `BACKEND_PORT` | 后端端口 | 8000 |
| `FRONTEND_PORT` | 前端端口 | 80 |
| `LOG_LEVEL` | 日志级别 | INFO |
| `MAX_FILE_SIZE` | 最大文件大小（字节） | 52428800 (50MB) |
| `CORS_ORIGINS` | CORS 允许的源 | * |

### 端口配置

- **80**: 前端 Web 界面
- **8000**: 后端 API 服务

如需修改端口，编辑 `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 修改为 8080
  backend:
    ports:
      - "8001:8000"  # 修改为 8001
```

### 数据持久化

数据存储在 `data` 目录：

```
data/
├── db/          # SQLite 数据库
│   └── history.db
└── logs/        # 应用日志
    └── app.log
```

---

## 🔧 常用命令

### 部署脚本命令

```bash
./deploy.sh start      # 启动服务
./deploy.sh stop       # 停止服务
./deploy.sh restart    # 重启服务
./deploy.sh logs       # 查看日志
./deploy.sh status     # 查看状态
./deploy.sh backup     # 备份数据
./deploy.sh clean      # 清理数据
```

### Docker Compose 命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps

# 重新构建
docker-compose up -d --build

# 清理所有（包括数据卷）
docker-compose down -v
```

---

## ❓ 常见问题

### 1. 端口被占用

**问题**: `Error: port is already allocated`

**解决**:
```bash
# 查看占用端口的进程
lsof -i :80
lsof -i :8000

# 停止占用进程或修改端口
```

### 2. 权限问题

**问题**: `Permission denied`

**解决**:
```bash
# 给部署脚本执行权限
chmod +x deploy.sh

# 或使用 sudo
sudo ./deploy.sh start
```

### 3. 数据库文件权限

**问题**: 无法写入数据库

**解决**:
```bash
# 修改数据目录权限
chmod -R 777 data/
```

### 4. 前端无法访问后端

**问题**: API 请求失败

**解决**:
- 检查 Nginx 配置中的代理设置
- 确认后端服务正常运行
- 查看浏览器控制台错误

### 5. 容器无法启动

**问题**: 容器一直重启

**解决**:
```bash
# 查看容器日志
docker logs mingjing-backend
docker logs mingjing-frontend

# 检查健康检查
docker inspect mingjing-backend | grep Health
```

---

## 🔒 安全建议

### 生产环境

1. **修改默认端口**
2. **启用 HTTPS**（使用 Let's Encrypt）
3. **配置防火墙**
4. **限制 CORS 源**
5. **定期备份数据**
6. **更新依赖版本**

### HTTPS 配置示例

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # ... 其他配置
}
```

---

## 📊 监控和维护

### 日志管理

```bash
# 查看实时日志
./deploy.sh logs

# 查看特定服务日志
docker-compose logs backend
docker-compose logs frontend

# 导出日志
docker-compose logs > logs_$(date +%Y%m%d).txt
```

### 数据备份

```bash
# 使用部署脚本备份
./deploy.sh backup

# 手动备份
tar -czf backup_$(date +%Y%m%d).tar.gz data/
```

### 数据恢复

```bash
# 停止服务
./deploy.sh stop

# 恢复数据
tar -xzf backup_20231214.tar.gz

# 启动服务
./deploy.sh start
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 或使用部署脚本
./deploy.sh restart
```

---

## 🌐 生产环境部署

### 使用 Nginx 反向代理

```nginx
upstream mingjing_backend {
    server localhost:8000;
}

upstream mingjing_frontend {
    server localhost:80;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://mingjing_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://mingjing_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
```

---

## 📞 技术支持

如有问题，请：

1. 查看 [常见问题](#常见问题)
2. 查看容器日志
3. 提交 Issue

---

## 📝 更新日志

### v1.0.0 (2024-12-14)
- ✅ 初始版本
- ✅ Docker 容器化
- ✅ 一键部署脚本
- ✅ 完整文档

---

**祝部署顺利！** 🎉
