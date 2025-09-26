# 上游服务配置使用示例

本文档展示如何使用MedGemma AI诊疗助手的上游服务配置功能。

## 🚀 快速开始

### 1. 使用默认配置启动
```bash
# 直接启动，使用默认配置
./start.sh
```

### 2. 使用环境变量配置
```bash
# 设置环境变量
export MEDGEMMA_UPSTREAM=https://your-custom-medgemma.com
export ADMIN_TOKEN=secret-admin

# 启动服务
./start.sh
```

### 3. 使用配置文件
```bash
# 配置文件已存在，直接启动
./start.sh
```

## ⚙️ 配置管理

### 通过管理界面配置

1. **登录管理控制台**
   - 访问 `http://localhost:8000/ui/`
   - 点击右上角的管理员按钮 ⚙️
   - 输入管理员令牌：`secret-admin`

2. **查看当前服务**
   - 在右侧"上游服务配置"区域
   - 查看当前使用的服务信息

3. **列出所有服务**
   - 点击"列出服务"按钮
   - 查看所有配置的上游服务

4. **添加新服务**
   - 点击"添加服务"按钮
   - 输入服务信息：
     - 服务键名：`backup1`
     - 服务名称：`备用服务1`
     - 服务URL：`https://backup1.example.com`
     - 服务描述：`备用MedGemma服务`

5. **编辑服务**
   - 在服务列表中点击"✏️ 编辑"按钮
   - 修改服务信息（名称、URL、描述、启用状态）
   - 确认保存更改

6. **删除服务**
   - 在服务列表中点击"🗑️ 删除"按钮
   - 确认删除操作（默认服务无法删除）
   - 服务将被永久删除

7. **切换服务**
   - 点击"切换服务"按钮
   - 选择要切换到的服务键名

8. **健康检查**
   - 点击"健康检查"按钮
   - 查看所有服务的健康状态

### 通过API配置

#### 列出所有服务
```bash
curl -sS http://localhost:8000/api/admin/upstream-services \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1'
```

#### 添加新服务
```bash
curl -sS -X POST "http://localhost:8000/api/admin/upstream-services?service_key=backup1" \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "备用服务1",
    "url": "https://backup1.example.com",
    "description": "备用MedGemma服务1",
    "enabled": true
  }'
```

#### 切换服务
```bash
curl -sS -X POST http://localhost:8000/api/admin/upstream-services/switch \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1' \
  -H 'Content-Type: application/json' \
  -d '{"service_key": "backup1"}'
```

#### 检查健康状态
```bash
curl -sS http://localhost:8000/api/admin/upstream-services/health \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1'
```

## 📝 配置文件示例

### 基本配置
```json
{
  "upstream_services": {
    "default": {
      "name": "默认服务",
      "url": "https://ollama-medgemma-944093292687.us-central1.run.app",
      "description": "官方默认MedGemma服务",
      "enabled": true
    }
  },
  "current_upstream": "default",
  "auto_failover": true,
  "health_check_interval": 30
}
```

### 多服务配置
```json
{
  "upstream_services": {
    "default": {
      "name": "默认服务",
      "url": "https://ollama-medgemma-944093292687.us-central1.run.app",
      "description": "官方默认MedGemma服务",
      "enabled": true
    },
    "backup1": {
      "name": "备用服务1",
      "url": "https://backup1-medgemma.example.com",
      "description": "备用MedGemma服务1",
      "enabled": true
    },
    "backup2": {
      "name": "备用服务2",
      "url": "https://backup2-medgemma.example.com",
      "description": "备用MedGemma服务2",
      "enabled": false
    },
    "local": {
      "name": "本地服务",
      "url": "http://localhost:11434",
      "description": "本地Ollama服务",
      "enabled": false
    }
  },
  "current_upstream": "default",
  "auto_failover": true,
  "health_check_interval": 30
}
```

## 🔧 配置优先级

系统按以下优先级选择上游服务：

1. **环境变量** `MEDGEMMA_UPSTREAM`（最高优先级）
2. **配置文件** `config.json` 中的 `current_upstream`
3. **默认服务地址**（最低优先级）

## 🏥 健康检查

系统支持对配置的上游服务进行健康检查：

- **healthy**: 服务正常响应
- **unhealthy**: 服务响应异常
- **unreachable**: 服务无法连接
- **disabled**: 服务已禁用

## 🔄 故障转移

系统支持自动故障转移功能：

- 当主服务不可用时，自动切换到备用服务
- 支持手动切换服务
- 实时监控服务状态

## 📊 监控和日志

- 实时显示当前服务状态
- 记录服务切换历史
- 提供详细的健康检查报告

## 🚨 故障排除

### 常见问题

1. **服务无法连接**
   - 检查服务URL是否正确
   - 确认服务是否正在运行
   - 检查网络连接

2. **配置不生效**
   - 确认配置文件格式正确
   - 检查配置优先级
   - 重启服务

3. **健康检查失败**
   - 检查服务是否支持 `/health` 端点
   - 确认服务响应格式
   - 检查超时设置

### 调试方法

1. **查看日志**
   ```bash
   # 启动时查看配置加载日志
   ./start.sh
   ```

2. **API测试**
   ```bash
   # 测试服务连接
   curl -sS http://your-service.com/health
   ```

3. **配置验证**
   ```bash
   # 验证配置文件格式
   python -m json.tool config.json
   ```

## 📚 更多信息

- 详细API文档请参考 `README.md`
- 系统管理功能请参考 `USAGE.md`
- 多租户架构请参考 `MULTI_TENANT_ARCHITECTURE.md`
