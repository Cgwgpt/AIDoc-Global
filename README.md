# MedGemma AI 智能诊疗助手

基于先进的 MedGemma 模型构建的企业级AI医疗诊疗助手系统，提供专业的医学图像分析与智能问诊服务。

## ✨ 核心特性

- 🩺 **专业医疗AI**：基于 MedGemma-4B/27B 多模态模型
- 🖼️ **图像分析**：支持医学图像上传与智能分析
- 👥 **多租户管理**：完整的机构级用户管理，支持数据隔离
- 🔐 **分级权限**：系统管理员、医院管理员、普通用户三级权限体系
- 📊 **使用统计**：实时使用统计、配额管理、数据分析
- ⚙️ **管理控制台**：专业的管理员界面，支持批量用户管理
- 🏥 **机构管理**：支持多医院、多机构独立管理和统计
- 📊 **实时统计**：头部实时显示用户信息和配额状态
- 🔄 **实时更新**：管理员控制台用户列表实时更新使用量
- 🎨 **现代化UI**：响应式设计，支持明暗主题切换
- 📱 **移动适配**：完美支持桌面、平板、手机设备

> 📖 详细使用教程请参考：`USAGE.md`

## 🚀 快速开始

### 🐳 Docker 部署（推荐）

**一键启动，无需配置环境！**

```bash
# 方式1: 使用启动脚本（推荐）
./docker-start.sh

# 方式2: 直接使用Docker Compose
docker-compose up -d

# 方式3: 生产环境部署（包含Nginx）
./docker-start.sh production
```

**Docker部署特性：**
- ✅ 一键启动，无需安装Python环境
- ✅ 自动配置Redis缓存服务
- ✅ 包含Nginx反向代理（生产环境）
- ✅ 自动健康检查和重启
- ✅ 数据持久化存储
- ✅ SSL/HTTPS支持（生产环境）

### 🚀 超快速演示

```bash
# 一键演示部署（推荐新手）
./quick-demo.sh

# 测试Docker配置
./test-docker.sh

# 完整功能演示
./docker-start.sh
```

### 💻 本地开发部署

#### 环境要求
- Python 3.12+ 
- 端口 8000 可用

#### 安装与启动

```bash
# 1) 创建并激活虚拟环境
python3 -m venv .venv && source .venv/bin/activate

# 2) 安装依赖
pip install -r requirements.txt

# 3) 设置环境变量（可选）
export MEDGEMMA_UPSTREAM=https://ollama-medgemma-944093292687.us-central1.run.app
export ADMIN_TOKEN=secret-admin  # 管理员令牌

# 4) 初始化管理员账户
python init_admin.py

# 5) 启动服务
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问系统

打开浏览器访问 `http://localhost:8000/ui/`，开始使用 MedGemma AI 诊疗助手！

**预设账户：**
- 系统管理员：`admin@medgemma.com` / `SecureAdmin2024!`
- 医院管理员：`manager@hospital.com` / `HospitalManager123!` (北京协和医院)
- 医院管理员：`manager2@hospital.com` / `HospitalManager456!` (上海瑞金医院)
- 普通用户：`demo@test.com` / `demo123`

## 🐳 Docker 详细部署指南

### 快速部署

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
# 1. 部署包含Nginx的生产环境
./docker-start.sh production

# 2. 配置SSL证书（可选）
# 将SSL证书文件放置在 ssl/ 目录下：
# - ssl/cert.pem (证书文件)
# - ssl/key.pem (私钥文件)

# 3. 访问系统
# HTTP: http://localhost
# HTTPS: https://localhost (需要SSL证书)
```

### Docker 服务管理

```bash
# 查看服务状态
./docker-start.sh status
# 或
docker-compose ps

# 查看服务日志
./docker-start.sh logs
# 或
docker-compose logs -f

# 停止服务
./docker-start.sh stop
# 或
docker-compose down

# 重新构建
./docker-start.sh rebuild
# 或
docker-compose build --no-cache

# 清理资源
./docker-start.sh cleanup
# 或
docker-compose down -v --remove-orphans
```

### Docker 服务架构

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

### 环境变量配置

创建 `.env` 文件自定义配置：

```bash
# 管理员令牌
ADMIN_TOKEN=your-secret-admin-token

# MedGemma上游服务
MEDGEMMA_UPSTREAM=https://your-medgemma-service.com

# 数据库路径
APP_DB_PATH=/app/data/app.db

# Redis密码
REDIS_PASSWORD=your-redis-password

# 端口配置
PORT=8000

# 日志级别
LOG_LEVEL=info
```

### 数据持久化

- **数据库文件**: `./data/app.db` - 用户数据和配置
- **Redis数据**: Docker volume `redis_data` - 缓存数据
- **日志文件**: `./logs/` - 应用日志
- **SSL证书**: `./ssl/` - HTTPS证书（生产环境）

### 故障排除

#### 1. 端口冲突
```bash
# 检查端口占用
lsof -i :8000
lsof -i :80

# 修改端口配置
# 编辑 docker-compose.yml 中的 ports 配置
```

#### 2. 权限问题
```bash
# 修复文件权限
chmod +x docker-start.sh
chmod -R 755 data/
```

#### 3. 服务启动失败
```bash
# 查看详细日志
docker-compose logs medgemma-app

# 重新构建镜像
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

# 重新初始化管理员
docker-compose exec medgemma-app python init_admin.py
```

### 性能优化

#### 1. 生产环境优化
```bash
# 使用生产环境部署
./docker-start.sh production

# 配置资源限制
# 编辑 docker-compose.yml 添加：
# deploy:
#   resources:
#     limits:
#       memory: 2G
#       cpus: '1.0'
```

#### 2. 缓存优化
- Redis缓存自动配置
- Nginx静态文件缓存
- 数据库连接池优化

#### 3. 监控和日志
```bash
# 查看资源使用情况
docker stats

# 查看容器日志
docker-compose logs -f --tail=100

# 健康检查
curl http://localhost:8000/health
```

## 🔧 API 接口

### 核心推理接口

- `POST /api/generate` - AI推理服务
  - `model`: 字符串，默认 `hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M`
  - `prompt`: 字符串，用户输入的问题
  - `images`: 可选，base64 字符串数组，支持医学图像分析
  - `stream`: 布尔，是否流式响应
  - 请求头：`X-User-Id` 用于用户身份识别和配额管理

### 用户认证接口

- `POST /api/users/register` - 用户注册
- `POST /api/users/login` - 用户登录  
- `POST /api/users/{user_id}/password:change` - 修改密码

## ⚙️ 上游服务配置

系统支持多种方式配置MedGemma上游服务，提供灵活的服务选择和管理功能。

### 配置方式

#### 1. 环境变量配置（传统方式）
```bash
export MEDGEMMA_UPSTREAM=https://your-medgemma-service.com
```

#### 2. 配置文件方式（推荐）
系统会自动读取项目根目录下的 `config.json` 配置文件：

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
    "asia_southeast": {
      "name": "亚洲东南服务",
      "url": "https://ollama-backend-944093292687.asia-southeast1.run.app",
      "model": "hf.co/unsloth/medgemma-4b-it-GGUF:BF16",
      "description": "亚洲东南地区MedGemma服务（BF16精度）",
      "enabled": true
    },
    "backup1": {
      "name": "备用服务1",
      "url": "https://backup1-medgemma.example.com",
      "model": "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M",
      "description": "备用MedGemma服务1",
      "enabled": false
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

#### 3. 管理界面配置
通过管理员控制台可以：
- 查看所有配置的上游服务
- 添加新的上游服务
- 编辑现有服务配置
- 删除不需要的服务（默认服务除外）
- 切换当前使用的主服务
- 检查服务健康状态
- 启用/禁用特定服务

### 配置优先级
1. 环境变量 `MEDGEMMA_UPSTREAM`（最高优先级）
2. 配置文件 `config.json` 中的 `current_upstream`
3. 默认服务地址（最低优先级）

可通过环境变量 `MEDGEMMA_UPSTREAM` 自定义上游推理服务地址。


## 💾 数据持久化

系统使用 SQLite3 数据库进行数据持久化，默认数据库文件为项目根目录下的 `app.db`，可通过环境变量 `APP_DB_PATH` 自定义。

应用启动时自动建表（`users`、`subscriptions`、`usage_events`）。支持以下数据管理功能：

### 用户管理

#### 用户注册
- `POST /api/users/register`
  - 请求体：
    ```json
    {
      "name": "张三",
      "organization": "XX医院", 
      "phone": "13800000000",
      "email": "user@example.com",
      "password": "your-password"
    }
    ```
  - 响应：
    ```json
    { 
      "id": 1, 
      "email": "user@example.com", 
      "name": "张三", 
      "organization": "XX医院", 
      "phone": "13800000000", 
      "is_admin": false, 
      "usage_quota": null, 
      "usage_used": 0 
    }
    ```

#### 订阅管理
- `GET /api/users/{user_id}/subscription` - 获取订阅信息
- `PUT /api/users/{user_id}/subscription` - 更新订阅
  - 请求体：
    ```json
    { 
      "plan": "pro", 
      "status": "active", 
      "auto_renew": true 
    }
    ```

快速调用示例：

```bash
curl -sS -X POST http://localhost:8000/api/users/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"张三","organization":"XX医院","phone":"13800000000","email":"user@example.com","password":"secret123"}'

curl -sS http://localhost:8000/api/users/1/subscription

curl -sS -X PUT http://localhost:8000/api/users/1/subscription \
  -H 'Content-Type: application/json' \
  -d '{"plan":"pro","status":"active","auto_renew":true}'
 
# 修改密码
curl -sS -X POST http://localhost:8000/api/users/1/password:change \
  -H 'Content-Type: application/json' \
  -d '{"old_password":"secret123","new_password":"newpass456"}'
```

## 🏥 多租户管理架构

### 权限体系

系统采用三级权限管理体系，确保不同机构间的数据完全隔离：

#### 1. **系统管理员** (System Admin)
- **权限范围**：全系统管理权限
- **账户示例**：`admin@medgemma.com`
- **主要功能**：
  - 管理所有机构用户
  - 查看全系统统计
  - 创建/管理医院管理员
  - 系统配置和参数设置

#### 2. **医院管理员** (Hospital Admin)  
- **权限范围**：仅限本机构内管理
- **账户示例**：`manager@hospital.com`
- **主要功能**：
  - 管理本机构内用户
  - 查看本机构使用统计
  - 设置本机构用户配额
  - 不能跨机构操作

#### 3. **普通用户** (Regular User)
- **权限范围**：基础使用权限
- **主要功能**：
  - 使用AI诊疗服务
  - 查看个人使用统计
  - 修改个人密码

### 数据隔离机制

- **机构隔离**：每个机构的数据完全独立，无法跨机构访问
- **权限控制**：API层面严格控制数据访问权限
- **统计隔离**：使用统计按机构维度独立计算
- **用户管理**：医院管理员只能管理本机构用户

## ⚙️ 管理员控制台

设置环境变量 `ADMIN_TOKEN` 以启用管理员接口鉴权（通过请求头 `X-Admin-Token` 传入）。

### 用户管理
- `GET /api/admin/users` - 列出所有用户
- `POST /api/admin/users` - 创建用户
- `PATCH /api/admin/users/{user_id}` - 更新用户信息/权限/配额
- `DELETE /api/admin/users/{user_id}` - 删除用户
- `GET /api/admin/users:search?q=关键字` - 搜索用户
- `GET /api/admin/users:paged2?page=1&size=20` - 分页查询用户

### 配额管理
- `POST /api/admin/users/{user_id}:reset-usage` - 重置用户用量
- `POST /api/admin/users/{user_id}:reset-password` - 重置用户密码

### 数据导入导出
- `GET /api/admin/users:export-csv` - 导出用户数据
- `POST /api/admin/users:import-csv` - 导入用户数据

### 机构管理
- `GET /api/admin/organizations` - 列出所有机构（仅系统管理员）
- `GET /api/admin/organizations/{org_name}/users` - 列出指定机构用户
- `GET /api/admin/organizations/{org_name}/stats` - 获取机构使用统计
- `POST /api/admin/organizations/{org_name}/users` - 为机构创建用户

### 上游服务配置管理
- `GET /api/admin/upstream-services` - 列出所有上游服务配置
- `POST /api/admin/upstream-services` - 添加新的上游服务
- `PUT /api/admin/upstream-services/{service_key}` - 更新上游服务配置
- `DELETE /api/admin/upstream-services/{service_key}` - 删除上游服务
- `POST /api/admin/upstream-services/switch` - 切换当前使用的主上游服务
- `GET /api/admin/upstream-services/current` - 获取当前使用的主上游服务信息
- `GET /api/admin/upstream-services/health` - 检查所有上游服务的健康状态

### 使用统计分析
- `GET /api/admin/usage:summary?start=...&end=...` - 用量汇总统计
- `GET /api/admin/usage:by-user?start=...&end=...` - 按用户统计
- `GET /api/admin/usage:by-day?start=...&end=...` - 按日期统计

### 🎨 专业管理界面

系统提供现代化的Web管理界面，支持：
- **统一用户管理**：搜索、编辑、配额设置、批量操作
- **实时数据统计**：图表展示、趋势分析
- **CSV导入导出**：批量用户数据管理
- **专业弹窗系统**：替换所有简单alert为专业表格展示

## 📊 使用配额与统计

### 配额限制机制
- 在调用 `POST /api/generate` 时，可通过请求头 `X-User-Id` 指定用户
- 若设置了 `usage_quota`（总配额），`usage_used >= usage_quota` 返回 429（总配额上限）
- 若设置了 `daily_quota`（日配额），`daily_used >= daily_quota` 返回 429（日配额上限）
- 成功调用自动增加 `usage_used` 与 `daily_used`（流式与非流式均按 1 次计）
- **实时统计更新**：使用统计在每次AI响应后立即更新

### 多租户管理示例

```bash
export ADMIN_TOKEN=secret-admin

# 系统管理员：列出所有机构
curl -sS http://localhost:8000/api/admin/organizations \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1'

# 系统管理员：查看北京协和医院用户
curl -sS http://localhost:8000/api/admin/organizations/北京协和医院/users \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1'

# 医院管理员：查看本机构用户（只能看到自己机构的用户）
curl -sS http://localhost:8000/api/admin/users \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 2'  # manager@hospital.com

# 医院管理员：为本机构创建用户
curl -sS -X POST http://localhost:8000/api/admin/organizations/北京协和医院/users \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 2' \
  -H 'Content-Type: application/json' \
  -d '{"name":"张三","organization":"北京协和医院","phone":"13800000000","email":"doctor@hospital.com","password":"secret123"}'

# 设定用户配额
curl -sS -X PATCH http://localhost:8000/api/admin/users/1 \
  -H 'X-Admin-Token: secret-admin' -H 'Content-Type: application/json' \
  -d '{"usage_quota":100, "daily_quota":10}'

# 用户身份调用推理
curl -sS -X POST http://localhost:8000/api/generate \
  -H 'Content-Type: application/json' -H 'X-User-Id: 1' \
  -d '{"prompt":"请分析这张医学图像", "images":["base64_image_data"]}'

# 上游服务配置管理示例
curl -sS http://localhost:8000/api/admin/upstream-services \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1'

# 添加上游服务
curl -sS -X POST "http://localhost:8000/api/admin/upstream-services?service_key=backup1" \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1' \
  -H 'Content-Type: application/json' \
  -d '{"name":"备用服务","url":"https://backup.example.com","model":"hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M","description":"备用MedGemma服务","enabled":true}'

# 编辑上游服务
curl -sS -X PUT http://localhost:8000/api/admin/upstream-services/backup1 \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1' \
  -H 'Content-Type: application/json' \
  -d '{"name":"备用服务更新","url":"https://backup-updated.example.com","model":"hf.co/unsloth/medgemma-4b-it-GGUF:BF16","description":"更新后的备用服务","enabled":true}'

# 删除上游服务
curl -sS -X DELETE http://localhost:8000/api/admin/upstream-services/backup1 \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1'

# 切换上游服务
curl -sS -X POST http://localhost:8000/api/admin/upstream-services/switch \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1' \
  -H 'Content-Type: application/json' \
  -d '{"service_key":"backup1"}'

# 检查服务健康状态
curl -sS http://localhost:8000/api/admin/upstream-services/health \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1'
```

## 🎯 系统特色

### 现代化用户界面
- **专业设计语言**：基于CSS变量系统的现代UI设计
- **响应式布局**：完美适配桌面、平板、移动设备
- **主题切换**：支持明暗主题，保护用户视力
- **专业弹窗系统**：所有消息提示采用专业表格展示

### 智能使用统计
- **实时更新**：每次AI响应后立即更新使用统计
- **头部显示**：界面头部实时显示当前用户、今日使用量和剩余配额
- **配额管理**：支持总配额和日配额双重限制
- **状态提示**：配额不足时显示警告颜色（黄色/红色）
- **数据可视化**：图表展示使用趋势和统计分析
- **用户友好**：清晰的配额状态和使用情况展示

### 企业级多租户管理功能
- **多机构支持**：支持多个医院/机构独立管理和数据隔离
- **分级权限控制**：系统管理员、医院管理员、普通用户三级权限体系
- **统一用户管理**：在一个界面完成所有用户管理操作
- **用户编辑**：支持修改用户基本信息、状态、权限设置
- **用户删除**：安全删除用户账户，支持二次确认机制
- **实时更新**：用户列表每5秒自动刷新使用量统计
- **智能提示**：配额状态颜色编码，使用量变化视觉提示
- **机构级统计**：按机构维度统计使用量和用户数据
- **批量操作**：支持批量重置用量、导入导出用户数据
- **权限控制**：基于角色的访问控制（RBAC）
- **审计日志**：完整的用户操作和使用记录

### 灵活的上游服务配置
- **多服务支持**：支持配置多个MedGemma上游服务
- **模型配置**：每个服务可配置不同的模型和精度（Q4_K_M、BF16、Q8_0等）
- **动态切换**：无需重启即可切换上游服务和模型
- **健康检查**：自动检测服务可用性和健康状态
- **配置管理**：通过管理界面或API管理服务配置
- **编辑删除**：支持编辑现有服务配置和删除不需要的服务
- **故障转移**：支持自动故障转移和手动切换
- **环境兼容**：支持环境变量、配置文件等多种配置方式
- **实时监控**：实时显示当前服务状态、模型和健康信息

## 📝 更新日志

### v2.5 - 上游服务配置管理功能
- ✅ 新增多上游服务配置支持，可配置多个MedGemma服务
- ✅ 新增模型配置支持，每个服务可配置不同的模型和精度
- ✅ 实现动态服务切换，无需重启即可切换上游服务和模型
- ✅ 添加服务健康检查功能，实时监控服务状态
- ✅ 完善管理界面，支持服务配置的增删改查
- ✅ 新增服务编辑功能，支持修改服务名称、URL、模型、描述和状态
- ✅ 新增服务删除功能，支持删除不需要的服务（默认服务除外）
- ✅ 支持多种配置方式：环境变量、配置文件、管理界面
- ✅ 实现配置优先级机制，确保配置的灵活性
- ✅ 添加服务状态实时显示和监控功能

### v2.4 - 用户编辑和删除功能
- ✅ 新增用户编辑功能，支持修改基本信息、状态、权限
- ✅ 新增用户删除功能，支持安全删除确认机制
- ✅ 优化用户管理界面，新增编辑✏️和删除🗑️操作按钮
- ✅ 完善权限控制，支持多租户环境下的用户管理
- ✅ 增强安全机制，防止误删除操作

### v2.3 - 用户管理中心实时更新功能
- ✅ 新增管理员控制台实时更新开关，每5秒自动刷新
- ✅ 实现用户列表使用量变化检测和视觉提示
- ✅ 添加配额状态颜色编码系统（绿色/黄色/红色）
- ✅ 优化实时更新性能和错误处理
- ✅ 完善多租户环境下的实时更新支持
- ✅ 修复管理员登录数据不一致问题，确保个人信息页面和管理中心数据同步

### v2.2 - 实时统计显示功能
- ✅ 新增头部实时统计显示：当前用户、今日使用量、剩余配额
- ✅ 实现配额状态颜色提示：绿色充足、黄色不足、红色用完
- ✅ 优化用户界面布局，支持响应式设计
- ✅ 增强实时更新机制，登录和AI调用后立即更新
- ✅ 完善多用户角色统计显示支持

### v2.1 - 多租户管理架构
- ✅ 实现完整的多租户管理架构
- ✅ 添加三级权限体系：系统管理员、医院管理员、普通用户
- ✅ 实现机构级数据隔离和权限控制
- ✅ 新增机构管理API：机构列表、机构用户、机构统计
- ✅ 完善医院管理员权限：只能管理本机构用户
- ✅ 支持多机构独立统计和配额管理
- ✅ 更新管理员初始化脚本，支持多角色创建

### v2.0 - 企业级功能升级
- ✅ 重构用户管理界面，整合所有管理功能
- ✅ 实现实时使用统计更新
- ✅ 替换所有alert弹窗为专业表格展示
- ✅ 优化管理员控制台，支持批量操作
- ✅ 增强移动端适配和响应式设计
- ✅ 完善用户认证和安全机制

---

**MedGemma AI 智能诊疗助手** - 让AI医疗更智能、更专业、更易用！
