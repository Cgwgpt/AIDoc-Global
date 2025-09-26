import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

class UpstreamConfig:
    """上游服务配置管理"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            # 如果配置文件不存在，创建默认配置
            default_config = {
                "upstream_services": {
                    "default": {
                        "name": "默认服务",
                        "url": "https://ollama-medgemma-944093292687.us-central1.run.app",
                        "description": "官方默认MedGemma服务",
                        "enabled": True
                    }
                },
                "current_upstream": "default",
                "auto_failover": True,
                "health_check_interval": 30
            }
            self._save_config(default_config)
            return default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"配置文件加载失败: {e}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """获取备用配置"""
        return {
            "upstream_services": {
                "default": {
                    "name": "默认服务",
                    "url": os.getenv("MEDGEMMA_UPSTREAM", "https://ollama-medgemma-944093292687.us-central1.run.app"),
                    "description": "环境变量配置的服务",
                    "enabled": True
                }
            },
            "current_upstream": "default",
            "auto_failover": True,
            "health_check_interval": 30
        }
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"配置文件保存失败: {e}")
    
    def get_current_upstream(self) -> str:
        """获取当前使用的主上游服务URL"""
        current_key = self.config.get("current_upstream", "default")
        services = self.config.get("upstream_services", {})
        
        if current_key in services and services[current_key].get("enabled", False):
            return services[current_key]["url"]
        
        # 如果当前服务不可用，尝试使用默认服务
        if "default" in services and services["default"].get("enabled", False):
            return services["default"]["url"]
        
        # 最后尝试环境变量
        return os.getenv("MEDGEMMA_UPSTREAM", "https://ollama-medgemma-944093292687.us-central1.run.app")
    
    def get_current_model(self) -> str:
        """获取当前使用的主上游服务模型"""
        current_key = self.config.get("current_upstream", "default")
        services = self.config.get("upstream_services", {})
        
        if current_key in services and services[current_key].get("enabled", False):
            return services[current_key].get("model", "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M")
        
        # 如果当前服务不可用，尝试使用默认服务
        if "default" in services and services["default"].get("enabled", False):
            return services["default"].get("model", "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M")
        
        # 最后使用默认模型
        return os.getenv("MEDGEMMA_MODEL", "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M")
    
    def get_all_services(self) -> Dict[str, Dict[str, Any]]:
        """获取所有上游服务配置"""
        return self.config.get("upstream_services", {})
    
    def get_enabled_services(self) -> Dict[str, Dict[str, Any]]:
        """获取所有启用的上游服务"""
        services = self.get_all_services()
        return {k: v for k, v in services.items() if v.get("enabled", False)}
    
    def set_current_upstream(self, service_key: str) -> bool:
        """设置当前使用的主上游服务"""
        services = self.get_all_services()
        if service_key not in services:
            return False
        
        if not services[service_key].get("enabled", False):
            return False
        
        self.config["current_upstream"] = service_key
        self._save_config(self.config)
        return True
    
    def add_service(self, key: str, name: str, url: str, model: str = "hf.co/unsloth/medgemma-4b-it-GGUF:Q4_K_M", description: str = "", enabled: bool = True) -> bool:
        """添加新的上游服务"""
        services = self.get_all_services()
        services[key] = {
            "name": name,
            "url": url.rstrip("/"),
            "model": model,
            "description": description,
            "enabled": enabled
        }
        self.config["upstream_services"] = services
        self._save_config(self.config)
        return True
    
    def update_service(self, key: str, **kwargs) -> bool:
        """更新上游服务配置"""
        services = self.get_all_services()
        if key not in services:
            return False
        
        for field, value in kwargs.items():
            if field in ["name", "url", "model", "description", "enabled"]:
                services[key][field] = value
        
        if "url" in kwargs:
            services[key]["url"] = kwargs["url"].rstrip("/")
        
        self.config["upstream_services"] = services
        self._save_config(self.config)
        return True
    
    def delete_service(self, key: str) -> bool:
        """删除上游服务"""
        if key == "default":
            return False  # 不能删除默认服务
        
        services = self.get_all_services()
        if key not in services:
            return False
        
        del services[key]
        self.config["upstream_services"] = services
        
        # 如果删除的是当前服务，切换到默认服务
        if self.config.get("current_upstream") == key:
            self.config["current_upstream"] = "default"
        
        self._save_config(self.config)
        return True
    
    def get_service_info(self, key: str) -> Optional[Dict[str, Any]]:
        """获取指定服务的详细信息"""
        services = self.get_all_services()
        return services.get(key)
    
    def is_auto_failover_enabled(self) -> bool:
        """检查是否启用自动故障转移"""
        return self.config.get("auto_failover", True)
    
    def set_auto_failover(self, enabled: bool) -> None:
        """设置自动故障转移"""
        self.config["auto_failover"] = enabled
        self._save_config(self.config)
    
    def get_health_check_interval(self) -> int:
        """获取健康检查间隔（秒）"""
        return self.config.get("health_check_interval", 30)

# 全局配置实例
upstream_config = UpstreamConfig()
