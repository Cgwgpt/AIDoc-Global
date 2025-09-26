# 模型配置使用示例

本文档展示如何使用MedGemma AI诊疗助手的模型配置功能，支持不同精度和版本的模型。

## 🎯 功能概述

现在系统不仅支持配置不同的上游服务URL，还支持为每个服务配置不同的模型：

- **URL配置**：指定MedGemma服务的地址
- **模型配置**：指定使用的模型和精度
- **动态切换**：可以同时切换服务和模型
- **精度选择**：支持Q4_K_M、BF16、Q8_0等不同精度

## 📋 支持的模型精度

### 常用精度类型

| 精度 | 描述 | 内存占用 | 推理速度 | 质量 |
|------|------|----------|----------|------|
| `Q4_K_M` | 4位量化，中等质量 | 低 | 快 | 中等 |
| `BF16` | 16位浮点 | 中 | 中等 | 高 |
| `Q8_0` | 8位量化 | 中 | 中等 | 高 |
| `F16` | 16位浮点 | 中 | 中等 | 高 |
| `F32` | 32位浮点 | 高 | 慢 | 最高 |

### 模型命名规则

```
hf.co/unsloth/medgemma-4b-it-GGUF:精度
```

例如：
- `hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M`
- `hf.co/unsloth/medgemma-4b-it-GGUF:BF16`
- `hf.co/unsloth/medgemma-4b-it-GGUF:Q8_0`

## 🚀 配置示例

### 1. 通过配置文件配置

```json
{
  "upstream_services": {
    "default": {
      "name": "默认服务",
      "url": "https://ollama-medgemma-944093292687.us-central1.run.app",
      "model": "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M",
      "description": "官方默认MedGemma服务（Q4_K_M精度）",
      "enabled": true
    },
    "asia_southeast": {
      "name": "亚洲东南服务",
      "url": "https://ollama-backend-944093292687.asia-southeast1.run.app",
      "model": "hf.co/unsloth/medgemma-4b-it-GGUF:BF16",
      "description": "亚洲东南地区MedGemma服务（BF16精度）",
      "enabled": true
    },
    "high_quality": {
      "name": "高质量服务",
      "url": "https://high-quality-medgemma.example.com",
      "model": "hf.co/unsloth/medgemma-4b-it-GGUF:Q8_0",
      "description": "高质量MedGemma服务（Q8_0精度）",
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

### 2. 通过环境变量配置

```bash
# 设置服务URL
export MEDGEMMA_UPSTREAM=https://your-service.com

# 设置模型（可选）
export MEDGEMMA_MODEL=hf.co/unsloth/medgemma-4b-it-GGUF:BF16
```

### 3. 通过管理界面配置

1. 访问 `http://localhost:8000/ui/`
2. 登录管理员账户
3. 在"上游服务配置"区域：
   - 点击"添加服务"添加新服务
   - 点击"列出服务"查看所有服务
   - 点击"✏️ 编辑"修改服务配置
   - 点击"切换服务"切换当前使用的服务

## 🔧 API使用示例

### 添加带模型配置的服务

```bash
curl -sS -X POST "http://localhost:8000/api/admin/upstream-services?service_key=bf16_service" \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "BF16精度服务",
    "url": "https://bf16-medgemma.example.com",
    "model": "hf.co/unsloth/medgemma-4b-it-GGUF:BF16",
    "description": "使用BF16精度的MedGemma服务",
    "enabled": true
  }'
```

### 编辑服务模型

```bash
curl -sS -X PUT http://localhost:8000/api/admin/upstream-services/bf16_service \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "BF16精度服务",
    "url": "https://bf16-medgemma.example.com",
    "model": "hf.co/unsloth/medgemma-4b-it-GGUF:Q8_0",
    "description": "更新为Q8_0精度的MedGemma服务",
    "enabled": true
  }'
```

### 查看当前服务信息

```bash
curl -sS http://localhost:8000/api/admin/upstream-services/current \
  -H 'X-Admin-Token: secret-admin' -H 'X-User-Id: 1'
```

响应示例：
```json
{
  "key": "asia_southeast",
  "name": "亚洲东南服务",
  "url": "https://ollama-backend-944093292687.asia-southeast1.run.app",
  "model": "hf.co/unsloth/medgemma-4b-it-GGUF:BF16",
  "description": "亚洲东南地区MedGemma服务（BF16精度）",
  "enabled": true
}
```

## 🎯 使用场景

### 场景1：不同精度的服务

**需求**：需要快速响应的服务和高质量的服务

**配置**：
- 快速服务：`Q4_K_M`精度，响应快
- 高质量服务：`BF16`精度，质量高

### 场景2：不同地区的服务

**需求**：根据用户地理位置选择最近的服务

**配置**：
- 亚洲服务：`https://ollama-backend-944093292687.asia-southeast1.run.app`
- 美国服务：`https://ollama-medgemma-944093292687.us-central1.run.app`

### 场景3：本地和云端服务

**需求**：本地开发使用本地服务，生产环境使用云端服务

**配置**：
- 本地服务：`http://localhost:11434`
- 云端服务：`https://production-medgemma.com`

## ⚙️ 配置优先级

系统按以下优先级选择模型：

1. **环境变量** `MEDGEMMA_MODEL`（最高优先级）
2. **配置文件** `config.json` 中的 `current_upstream` 对应的模型
3. **默认模型** `hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M`（最低优先级）

## 🔍 模型选择建议

### 根据使用场景选择

| 场景 | 推荐精度 | 理由 |
|------|----------|------|
| 开发测试 | `Q4_K_M` | 快速响应，资源占用少 |
| 生产环境 | `BF16` | 平衡质量和性能 |
| 高质量需求 | `Q8_0` | 最高质量，适合重要任务 |
| 资源受限 | `Q4_K_M` | 最低资源占用 |

### 根据硬件选择

| 硬件配置 | 推荐精度 | 理由 |
|----------|----------|------|
| 低端GPU | `Q4_K_M` | 内存占用少 |
| 中端GPU | `BF16` | 平衡质量和性能 |
| 高端GPU | `Q8_0` | 充分利用硬件性能 |

## 🧪 测试模型配置

### 测试脚本

```python
import requests

def test_model_config():
    # 测试当前服务
    response = requests.get(
        'http://localhost:8000/api/admin/upstream-services/current',
        headers={'X-Admin-Token': 'secret-admin', 'X-User-Id': '1'}
    )
    current_service = response.json()
    print(f"当前服务: {current_service['name']}")
    print(f"当前模型: {current_service['model']}")
    
    # 测试AI推理
    response = requests.post(
        'http://localhost:8000/api/generate',
        headers={'X-User-Id': '1', 'Content-Type': 'application/json'},
        json={'prompt': '请分析这个医学图像', 'stream': False}
    )
    print(f"推理结果: {response.json()}")

if __name__ == "__main__":
    test_model_config()
```

## 📚 相关文档

- [上游服务配置使用示例](UPSTREAM_CONFIG_DEMO.md)
- [上游服务编辑删除指南](UPSTREAM_EDIT_DELETE_GUIDE.md)
- [系统管理功能](USAGE.md)
- [API接口文档](README.md)

## 🎉 总结

通过模型配置功能，您可以：

- 为不同服务配置不同的模型精度
- 根据需求选择最适合的模型
- 在服务切换时同时切换模型
- 灵活管理多个服务和模型组合

这使得MedGemma AI诊疗助手能够更好地适应不同的使用场景和性能需求！
