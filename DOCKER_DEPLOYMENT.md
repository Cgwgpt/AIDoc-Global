# 🐳 MedGemma AI 智能诊疗助手 - Docker 部署指南

## 📋 概述

本指南提供了 MedGemma AI 智能诊疗助手的完整 Docker 化部署方案，支持开发环境和生产环境的快速部署。

## 🚀 一键部署

### 快速开始（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd medd

# 2. 一键启动
./docker-start.sh

# 3. 访问系统
# 浏览器打开: http://localhost:8000/ui/
```

### 生产环境部署

```bash
# 部署包含Nginx的生产环境
./docker-start.sh production

# 访问地址
# HTTP: http://localhost
# HTTPS: https://localhost (需要SSL证书)
```

## 🏗️ 服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   MedGemma App  │    │     Redis       │
│  (反向代理)      │────│   (主应用)      │────│    (缓存)       │
│  Port: 80/443   │    │   Port: 8000    │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                        ┌─────────────────┐
                        │   SQLite DB     │
                        │ (数据持久化)     │
                        │  Volume: data/  │
                        └─────────────────┘
```

## 📁 文件结构

```
medd/
├── Dockerfile                 # 主应用镜像构建文件
├── docker-compose.yml         # Docker Compose 配置
├── .dockerignore             # Docker 构建忽略文件
├── docker-start.sh           # 一键启动脚本
├── nginx.conf                # Nginx 配置
├── .env                      # 环境变量配置（自动生成）
├── config.json               # 应用配置文件
├── data/                     # 数据持久化目录
│   └── app.db               # SQLite 数据库
├── ssl/                      # SSL 证书目录（生产环境）
│   ├── cert.pem             # SSL 证书
│   └── key.pem              # SSL 私钥
└── logs/                     # 日志目录
```

## ⚙️ 配置说明

### 环境变量配置

创建 `.env` 文件自定义配置：

```bash
# 管理员令牌
ADMIN_TOKEN=secret-admin

# MedGemma上游服务
MEDGEMMA_UPSTREAM=https://ollama-medgemma-944093292687.us-central1.run.app

# 数据库路径
APP_DB_PATH=/app/data/app.db

# Redis密码
REDIS_PASSWORD=medgemma123

# 端口配置
PORT=8000

# 日志级别
LOG_LEVEL=info
```

### 上游服务配置

编辑 `config.json` 文件配置多个 MedGemma 服务：

```json
{
  "upstream_services": {
    "default": {
      "name": "默认服务",
      "url": "https://ollama-medgemma-944093292687.us-central1.run.app",
      "model": "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M",
      "description": "官方默认MedGemma服务",
      "enabled": true
    },
    "local": {
      "name": "本地服务",
      "url": "http://localhost:11434",
      "model": "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M",
      "description": "本地Ollama服务",
      "enabled": false
    }
  },
  "current_upstream": "default",
  "auto_failover": true,
  "health_check_interval": 30
}
```

## 🛠️ 服务管理

### 基本操作

```bash
# 查看服务状态
./docker-start.sh status
docker-compose ps

# 查看服务日志
./docker-start.sh logs
docker-compose logs -f

# 停止服务
./docker-start.sh stop
docker-compose down

# 重新构建
./docker-start.sh rebuild
docker-compose build --no-cache

# 清理资源
./docker-start.sh cleanup
docker-compose down -v --remove-orphans
```

### 高级操作

```bash
# 进入容器调试
docker-compose exec medgemma-app bash

# 查看容器资源使用
docker stats

# 备份数据库
docker-compose exec medgemma-app cp /app/data/app.db /app/data/app.db.backup

# 恢复数据库
docker-compose exec medgemma-app cp /app/data/app.db.backup /app/data/app.db

# 重新初始化管理员
docker-compose exec medgemma-app python init_admin.py
```

## 🔒 SSL/HTTPS 配置

### 1. 生成自签名证书（开发环境）

```bash
# 创建SSL目录
mkdir -p ssl

# 生成私钥
openssl genrsa -out ssl/key.pem 2048

# 生成证书
openssl req -new -x509 -key ssl/key.pem -out ssl/cert.pem -days 365 -subj "/C=CN/ST=Beijing/L=Beijing/O=MedGemma/OU=IT/CN=localhost"
```

### 2. 使用正式证书（生产环境）

将您的SSL证书文件放置在 `ssl/` 目录：

```bash
ssl/
├── cert.pem    # 证书文件
└── key.pem     # 私钥文件
```

### 3. 启用HTTPS

```bash
# 生产环境部署（包含HTTPS）
./docker-start.sh production

# 访问HTTPS
curl -k https://localhost/health
```

## 📊 监控和日志

### 健康检查

```bash
# 检查应用健康状态
curl http://localhost:8000/health

# 检查所有服务状态
docker-compose ps

# 查看容器健康状态
docker inspect medgemma-app --format='{{.State.Health.Status}}'
```

### 日志管理

```bash
# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f medgemma-app

# 查看最近100行日志
docker-compose logs --tail=100

# 查看错误日志
docker-compose logs | grep ERROR
```

### 性能监控

```bash
# 查看资源使用情况
docker stats

# 查看容器详细信息
docker inspect medgemma-app

# 查看网络连接
docker network ls
docker network inspect medd_medgemma-network
```

## 🚨 故障排除

### 常见问题

#### 1. 端口冲突

```bash
# 检查端口占用
lsof -i :8000
lsof -i :80
lsof -i :443

# 修改端口配置
# 编辑 docker-compose.yml 中的 ports 配置
```

#### 2. 权限问题

```bash
# 修复文件权限
chmod +x docker-start.sh
chmod -R 755 data/
chmod -R 644 ssl/
```

#### 3. 服务启动失败

```bash
# 查看详细错误日志
docker-compose logs medgemma-app

# 检查镜像构建
docker-compose build --no-cache

# 清理并重新启动
docker-compose down -v
./docker-start.sh
```

#### 4. 数据库问题

```bash
# 重置数据库
rm -rf data/app.db
docker-compose restart medgemma-app

# 重新初始化
docker-compose exec medgemma-app python init_admin.py
```

#### 5. Redis连接问题

```bash
# 检查Redis状态
docker-compose exec redis redis-cli ping

# 重启Redis
docker-compose restart redis

# 查看Redis日志
docker-compose logs redis
```

### 性能优化

#### 1. 资源限制

编辑 `docker-compose.yml` 添加资源限制：

```yaml
services:
  medgemma-app:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

#### 2. 缓存优化

- Redis缓存自动配置
- Nginx静态文件缓存
- 数据库连接池优化

#### 3. 网络优化

```bash
# 使用自定义网络
docker network create medgemma-network

# 配置网络参数
# 在 docker-compose.yml 中设置网络参数
```

## 🔄 更新和维护

### 应用更新

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像
docker-compose build --no-cache

# 3. 重启服务
docker-compose restart

# 4. 验证更新
curl http://localhost:8000/health
```

### 数据备份

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
docker-compose exec -T medgemma-app cp /app/data/app.db /app/data/app.db.backup
docker cp medgemma-app:/app/data/app.db.backup ./backups/app.db.$DATE
echo "Backup created: ./backups/app.db.$DATE"
EOF

chmod +x backup.sh
./backup.sh
```

### 数据恢复

```bash
# 恢复指定备份
BACKUP_FILE="backups/app.db.20241201_120000"
docker cp $BACKUP_FILE medgemma-app:/app/data/app.db
docker-compose restart medgemma-app
```

## 📈 扩展部署

### 集群部署

```bash
# 使用Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml medgemma-stack

# 使用Kubernetes
kubectl apply -f k8s/
```

### 负载均衡

```bash
# 多实例部署
docker-compose up -d --scale medgemma-app=3

# 配置负载均衡器
# 编辑 nginx.conf 添加多个后端
```

## 📞 技术支持

如遇到部署问题，请：

1. 查看本文档的故障排除部分
2. 检查服务日志：`docker-compose logs`
3. 验证系统资源：`docker stats`
4. 提交Issue到项目仓库

---

**MedGemma AI 智能诊疗助手** - 让AI医疗部署更简单、更可靠！
