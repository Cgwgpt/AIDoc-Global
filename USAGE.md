# MedGemma AI 智能诊疗助手 - 使用教程

本教程将引导您从零到一运行 MedGemma AI 智能诊疗助手系统，包括用户注册与认证、管理员配额管理、使用统计分析、以及现代化的Web界面使用。

## 🎯 系统概述

MedGemma AI 智能诊疗助手是基于先进的 MedGemma 多模态模型构建的企业级AI医疗诊疗系统，提供：

- 🩺 **专业医疗AI**：支持医学图像分析与智能问诊
- 👥 **完整用户管理**：注册、登录、权限控制、配额管理
- 📊 **实时使用统计**：使用情况实时更新和可视化分析
- ⚙️ **专业管理控制台**：现代化的用户管理和数据分析界面
- 🎨 **现代化UI**：响应式设计，支持明暗主题切换

## 🚀 快速开始

### 1. 环境要求

- **Python 3.12+**（已验证），建议使用虚拟环境
- **操作系统**：macOS、Linux（Windows 需相应调整命令）
- **端口 8000** 可用

### 2. 安装与启动

#### 步骤 1：创建虚拟环境
```bash
cd /path/to/medd
python3 -m venv .venv && source .venv/bin/activate
```

#### 步骤 2：安装依赖
```bash
pip install -r requirements.txt
```

#### 步骤 3：设置环境变量
```bash
export MEDGEMMA_UPSTREAM=https://ollama-medgemma-944093292687.us-central1.run.app
export ADMIN_TOKEN=secret-admin  # 管理员令牌
# 可选：自定义 SQLite 路径
# export APP_DB_PATH=/absolute/path/to/app.db
```

#### 步骤 4：初始化管理员账户
```bash
python init_admin.py
```

#### 步骤 5：启动服务
```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 步骤 6：访问系统
浏览器访问 `http://localhost:8000/ui/`

### 3. 预设账户

系统提供预设账户供快速体验：

| 账户类型 | 邮箱 | 密码 | 权限 |
|---------|------|------|------|
| 管理员 | `admin@medgemma.com` | `SecureAdmin2024!` | 完整管理权限 |
| 普通用户 | `demo@test.com` | `demo123` | 基础使用权限 |

## ⚙️ 系统配置

### 环境变量配置

| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| `MEDGEMMA_UPSTREAM` | 上游推理服务地址 | `https://ollama-medgemma-944093292687.us-central1.run.app` |
| `ADMIN_TOKEN` | 管理员令牌 | 无（需设置） |
| `APP_DB_PATH` | SQLite数据库路径 | `./app.db` |

### 数据库架构

系统使用 SQLite3 数据库，包含以下主要表：

- **`users`**：用户信息表
  - 基础信息：邮箱、姓名、机构、手机号
  - 权限控制：管理员标识、账户状态
  - 配额管理：总配额、日配额、已用量、当日已用量
  - 安全信息：密码哈希、创建时间等

- **`subscriptions`**：订阅信息表
  - 每个用户最多一条订阅记录
  - 订阅计划、状态、自动续费等

- **`usage_events`**：使用事件表
  - 自动记录每次AI推理请求
  - 用于统计分析和配额管理

## 🔧 核心功能与API

### AI推理服务

#### 智能诊疗推理
- **接口**：`POST /api/generate`
- **功能**：基于 MedGemma 模型的医学图像分析与智能问诊
- **请求头**：`X-User-Id` 指定用户（用于配额管理）
- **请求体**：
  ```json
  {
    "model": "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M",
    "prompt": "请分析这张医学图像",
    "images": ["base64_image_data"],  // 可选
    "stream": true
  }
  ```
- **配额控制**：达到配额上限返回 429 状态码
- **实时统计**：成功调用后自动更新使用统计

### 用户认证系统

#### 用户注册
- **接口**：`POST /api/users/register`
- **请求体**：
  ```json
  {
    "name": "张三",
    "organization": "XX医院",
    "phone": "13800000000", 
    "email": "user@example.com",
    "password": "your-password"
  }
  ```

#### 用户登录
- **接口**：`POST /api/users/login`
- **功能**：安全验证用户身份，返回用户信息

#### 密码管理
- **接口**：`POST /api/users/{user_id}/password:change`
- **功能**：修改用户密码

### 管理员控制台

#### 用户管理
- **用户列表**：`GET /api/admin/users`
- **用户搜索**：`GET /api/admin/users:search?q=关键词`
- **分页查询**：`GET /api/admin/users:paged2?page=1&size=20`
- **创建用户**：`POST /api/admin/users`
- **更新用户**：`PATCH /api/admin/users/{user_id}`
- **删除用户**：`DELETE /api/admin/users/{user_id}`

#### 配额管理
- **重置用量**：`POST /api/admin/users/{user_id}:reset-usage`
- **重置密码**：`POST /api/admin/users/{user_id}:reset-password`

#### 数据导入导出
- **导出CSV**：`GET /api/admin/users:export-csv`
- **导入CSV**：`POST /api/admin/users:import-csv`

#### 统计分析
- **用量汇总**：`GET /api/admin/usage:summary?start=...&end=...`
- **按用户统计**：`GET /api/admin/usage:by-user?start=...&end=...`
- **按日期统计**：`GET /api/admin/usage:by-day?start=...&end=...`

## 🖥️ Web界面使用指南

### 系统访问
1. 打开浏览器访问 `http://localhost:8000/ui/`
2. 系统提供现代化的响应式界面，支持桌面和移动设备

### 用户操作流程

#### 1. 用户注册与登录
- 点击右上角 🔑 按钮打开登录/注册界面
- **注册新用户**：填写姓名、机构、手机号、邮箱、密码
- **用户登录**：使用邮箱和密码登录
- **预设账户**：可直接使用系统提供的演示账户

#### 2. AI诊疗服务使用
- 在输入框中输入医疗相关问题
- 支持上传医学图像进行分析（JPEG/PNG/GIF/WebP/BMP格式）
- 点击发送按钮，AI将提供专业的医疗分析
- **实时统计**：每次使用后，个人使用统计会自动更新

#### 3. 个人信息管理
- 点击右上角 👤 按钮查看个人信息
- 查看使用统计：总使用次数、今日使用次数、剩余配额
- 修改密码：在账户设置中修改登录密码

### 管理员操作指南

#### 1. 管理员登录
- 使用管理员账户登录：`admin@medgemma.com` / `SecureAdmin2024!`
- 点击右上角 ⚙️ 按钮打开管理控制台
- 输入管理员令牌：`secret-admin`

#### 2. 用户管理中心
- **统一用户管理**：在一个界面完成所有用户管理操作
- **搜索功能**：按邮箱、姓名、机构搜索用户
- **批量操作**：支持批量重置用量、导出数据
- **实时刷新**：一键刷新获取最新用户数据

#### 3. 配额管理
- **设置配额**：为每个用户设置总配额和日配额
- **重置用量**：清零用户的使用统计
- **配额监控**：实时查看用户配额使用情况

#### 4. 数据分析
- **用量统计**：查看系统总体使用情况
- **用户分析**：按用户统计使用数据
- **趋势分析**：按日期查看使用趋势
- **图表展示**：专业的图表可视化数据

## 📊 数据管理

### CSV导入导出

#### 导出用户数据
- 管理员控制台 → 导出CSV
- 包含完整用户信息和配额数据

#### 导入用户数据
- 管理员控制台 → 导入CSV
- **CSV格式要求**：
  ```
  email;name;organization;phone;is_admin;status;notes;usage_quota;daily_quota
  user@example.com;张三;XX医院;13800000000;0;active;;100;10
  ```
- `is_admin`：1表示管理员，0或空表示普通用户
- 导入用户默认密码：`changeme123`

### 数据备份

#### 备份策略
- **数据库备份**：直接复制 `app.db` 文件
- **定期备份**：建议每日备份数据库文件
- **备份恢复**：停止服务，替换数据库文件即可

## 🛠️ 故障排除

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| `email-validator` 缺失 | `pip install email-validator` |
| 端口 8000 被占用 | `lsof -ti:8000 \| xargs -r kill -9` |
| 管理员接口 401 错误 | 确认已设置 `ADMIN_TOKEN` |
| AI响应超时 | 检查网络连接和上游服务状态 |
| 使用统计不更新 | 确认用户已正确登录 |

### 系统监控

#### 日志查看
- 服务启动日志：终端输出
- 错误日志：检查终端错误信息
- 用户操作：通过数据库 `usage_events` 表查看

#### 性能优化
- **数据库优化**：定期清理旧的使用事件记录
- **内存管理**：监控服务内存使用情况
- **并发处理**：根据用户量调整服务器配置

## 🚀 生产部署建议

### 安全配置
- **HTTPS部署**：使用SSL证书保护数据传输
- **防火墙配置**：限制数据库访问端口
- **定期更新**：保持依赖包和系统更新

### 数据库升级
- **迁移管理**：使用 Alembic 管理数据库迁移
- **数据库替换**：生产环境建议使用 PostgreSQL 或 MySQL
- **备份策略**：建立完善的数据库备份机制

### 监控告警
- **系统监控**：监控CPU、内存、磁盘使用率
- **业务监控**：监控API响应时间和错误率
- **用户监控**：监控用户活跃度和使用情况

---

**MedGemma AI 智能诊疗助手** - 专业、智能、易用的AI医疗解决方案！

如需技术支持或功能建议，欢迎在 Issues 中反馈。


