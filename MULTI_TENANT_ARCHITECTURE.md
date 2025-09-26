# MedGemma AI 多租户管理架构

## 🏗️ 架构概览

MedGemma AI 智能诊疗助手采用完整的多租户管理架构，支持多个医院/机构独立管理和数据隔离。

## 🔐 权限体系

### 三级权限架构

```
系统管理员 (System Admin)
├── 权限范围：全系统
├── 管理对象：所有机构用户
├── 特殊权限：创建医院管理员、系统配置
└── 账户示例：admin@medgemma.com

医院管理员 (Hospital Admin)
├── 权限范围：本机构内
├── 管理对象：本机构用户
├── 特殊权限：本机构配额管理、用户创建
└── 账户示例：manager@hospital.com

普通用户 (Regular User)
├── 权限范围：个人
├── 管理对象：个人设置
├── 特殊权限：AI服务使用
└── 账户示例：doctor@hospital.com
```

## 🏥 机构隔离机制

### 数据隔离策略

1. **API层面隔离**
   - 所有用户管理API自动添加机构过滤条件
   - 医院管理员只能访问本机构数据
   - 系统管理员可以跨机构访问

2. **数据库层面隔离**
   - 用户表通过 `organization` 字段标识机构
   - 所有查询自动添加机构过滤条件
   - 使用统计按机构维度独立计算

3. **权限验证机制**
   - 请求时验证用户权限级别
   - 动态生成数据访问范围
   - 防止跨机构数据泄露

## 📊 机构管理功能

### 机构管理API

| API端点 | 功能 | 权限要求 |
|---------|------|----------|
| `GET /api/admin/organizations` | 列出所有机构 | 系统管理员 |
| `GET /api/admin/organizations/{org}/users` | 机构用户列表 | 医院管理员+ |
| `GET /api/admin/organizations/{org}/stats` | 机构统计 | 医院管理员+ |
| `POST /api/admin/organizations/{org}/users` | 创建机构用户 | 医院管理员+ |

### 机构统计维度

- **用户统计**：总用户数、活跃用户数
- **使用统计**：总使用量、日使用量、事件统计
- **配额统计**：配额使用率、剩余配额
- **时间统计**：按日期、按用户的使用趋势

## 🔧 技术实现

### 权限控制函数

```python
def require_system_admin(current_user: User) -> User:
    """要求系统管理员权限"""
    if not current_user.is_admin or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要系统管理员权限")
    return current_user

def require_hospital_admin_or_system_admin(current_user: User) -> User:
    """要求医院管理员或系统管理员权限"""
    if not (current_user.is_admin or current_user.role == "hospital_admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user

def get_organization_filter(current_user: User, organization: str = None) -> str:
    """根据用户权限获取机构过滤条件"""
    if current_user.role == "admin" or current_user.is_admin:
        return organization if organization else None
    else:
        return current_user.organization
```

### 数据查询示例

```python
# 医院管理员查询用户（自动添加机构过滤）
def admin_list_users(current_user: User = Depends(require_hospital_admin_or_system_admin)):
    allowed_org = get_organization_filter(current_user)
    query = db.query(User)
    if allowed_org:
        query = query.filter(User.organization == allowed_org)
    return query.all()
```

## 🚀 部署配置

### 初始化管理员账户

```bash
# 运行初始化脚本
python init_admin.py
```

预设账户：
- 系统管理员：`admin@medgemma.com` / `SecureAdmin2024!`
- 医院管理员1：`manager@hospital.com` / `HospitalManager123!` (北京协和医院)
- 医院管理员2：`manager2@hospital.com` / `HospitalManager456!` (上海瑞金医院)

### 环境变量配置

```bash
# 设置管理员令牌
export ADMIN_TOKEN=secret-admin

# 设置数据库路径
export APP_DB_PATH=./app.db
```

## 📈 使用示例

### 系统管理员操作

```bash
# 查看所有机构
curl -H 'X-User-Id: 1' http://localhost:8000/api/admin/organizations

# 查看指定机构用户
curl -H 'X-User-Id: 1' http://localhost:8000/api/admin/organizations/北京协和医院/users

# 获取机构统计
curl -H 'X-User-Id: 1' http://localhost:8000/api/admin/organizations/北京协和医院/stats
```

### 医院管理员操作

```bash
# 查看本机构用户（自动过滤）
curl -H 'X-User-Id: 2' http://localhost:8000/api/admin/users

# 为本机构创建用户
curl -X POST -H 'X-User-Id: 2' \
  -H 'Content-Type: application/json' \
  -d '{"name":"医生","email":"doctor@hospital.com","organization":"北京协和医院","password":"123456"}' \
  http://localhost:8000/api/admin/organizations/北京协和医院/users
```

## 🔒 安全特性

1. **数据隔离**：不同机构数据完全隔离，无法跨机构访问
2. **权限控制**：API层面严格控制数据访问权限
3. **审计日志**：完整的用户操作和使用记录
4. **配额管理**：支持机构级和用户级配额控制
5. **状态管理**：支持用户状态管理（启用/禁用）

## 📋 最佳实践

1. **机构命名**：使用统一的机构命名规范
2. **权限分配**：合理分配医院管理员权限
3. **配额设置**：根据机构规模设置合适的配额
4. **定期审计**：定期检查权限分配和数据访问
5. **备份策略**：定期备份数据库文件

---

**MedGemma AI 多租户管理架构** - 为企业级医疗AI应用提供安全、可靠的多机构管理解决方案！
