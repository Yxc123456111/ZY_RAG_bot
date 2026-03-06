#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块 - 统一管理应用配置
支持从 .env 文件、环境变量、配置文件读取
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict


class ConfigManager:
    """配置管理器"""
    
    _instance = None
    _config: Dict[str, str] = {}
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_all_configs()
        return cls._instance
    
    def _get_project_root(self) -> Path:
        """获取项目根目录"""
        # 尝试多种方式获取项目根目录
        possible_roots = [
            # 方式1: 当前工作目录
            Path(os.getcwd()),
            # 方式2: 脚本所在目录
            Path(os.path.dirname(os.path.abspath(__file__))),
            # 方式3: 可执行文件所在目录 (PyInstaller)
            Path(sys.executable).parent if getattr(sys, 'frozen', False) else None,
        ]
        
        for root in possible_roots:
            if root and root.exists():
                # 如果目录下有 .env 或 .env.example，认为是根目录
                if (root / ".env").exists() or (root / ".env.example").exists():
                    return root
        
        # 默认返回当前工作目录
        return Path(os.getcwd())
    
    def _load_all_configs(self):
        """加载所有配置来源"""
        self._config = {}
        
        # 1. 首先加载 .env 文件
        self._load_dotenv()
        
        # 2. 然后加载环境变量（环境变量优先级更高）
        self._load_environ()
    
    def _load_dotenv(self):
        """从 .env 文件加载配置"""
        root = self._get_project_root()
        env_paths = [
            root / ".env",
            Path(".env"),
            Path(os.getcwd()) / ".env",
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                try:
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                if key:
                                    self._config[key] = value
                    print(f"[ConfigManager] 已加载配置: {env_path}")
                    return
                except Exception as e:
                    print(f"[ConfigManager] 加载 {env_path} 失败: {e}")
        
        print(f"[ConfigManager] 警告: 未找到 .env 文件，已尝试路径: {[str(p) for p in env_paths]}")
    
    def _load_environ(self):
        """从环境变量加载配置"""
        # 优先的环境变量列表
        env_vars = [
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'DATABASE_URL',
            'OPENAI_API_KEY',
            'API_PORT',
            'WEB_PORT',
        ]
        
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                self._config[var] = value
    
    def get(self, key: str, default: str = "") -> str:
        """获取配置值"""
        return self._config.get(key, default)
    
    def get_supabase_config(self) -> tuple:
        """
        获取 Supabase 配置
        
        Returns:
            (url, key) 元组，如果未配置则返回空字符串
        """
        url = self.get('SUPABASE_URL', '')
        key = self.get('SUPABASE_KEY', '')
        return url, key
    
    def is_supabase_configured(self) -> bool:
        """检查 Supabase 是否已配置"""
        url, key = self.get_supabase_config()
        return bool(url and key)
    
    def save_supabase_config(self, url: str, key: str) -> bool:
        """
        保存 Supabase 配置到 .env 文件
        
        Returns:
            是否保存成功
        """
        try:
            root = self._get_project_root()
            env_path = root / ".env"
            
            # 读取现有配置
            lines = []
            config_dict = {}
            
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 解析现有配置
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        config_dict[k.strip()] = v.strip()
            
            # 更新配置
            config_dict['SUPABASE_URL'] = url
            config_dict['SUPABASE_KEY'] = key
            
            # 写回文件
            with open(env_path, 'w', encoding='utf-8') as f:
                # 先写入 Supabase 配置
                f.write("# ============================================\n")
                f.write("# Supabase 配置 (中药查询功能)\n")
                f.write("# ============================================\n")
                f.write(f"SUPABASE_URL={config_dict.pop('SUPABASE_URL', '')}\n")
                f.write(f"SUPABASE_KEY={config_dict.pop('SUPABASE_KEY', '')}\n\n")
                
                # 写入其他配置
                for k, v in config_dict.items():
                    f.write(f"{k}={v}\n")
            
            # 更新内存中的配置
            self._config['SUPABASE_URL'] = url
            self._config['SUPABASE_KEY'] = key
            
            print(f"[ConfigManager] 配置已保存: {env_path}")
            return True
            
        except Exception as e:
            print(f"[ConfigManager] 保存配置失败: {e}")
            return False
    
    def reload(self):
        """重新加载配置"""
        self._load_all_configs()


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None

def get_config() -> ConfigManager:
    """获取配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reload_config():
    """重新加载配置"""
    global _config_manager
    _config_manager = ConfigManager()


# 便捷函数
def get_supabase_url() -> str:
    """获取 Supabase URL"""
    return get_config().get('SUPABASE_URL', '')

def get_supabase_key() -> str:
    """获取 Supabase Key"""
    return get_config().get('SUPABASE_KEY', '')

def is_supabase_ready() -> bool:
    """检查 Supabase 配置是否就绪"""
    return get_config().is_supabase_configured()


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("配置管理器测试")
    print("=" * 60)
    
    config = get_config()
    
    print(f"\n项目根目录: {config._get_project_root()}")
    print(f"\nSupabase 配置状态: {'✓ 已配置' if config.is_supabase_configured() else '✗ 未配置'}")
    
    url, key = config.get_supabase_config()
    print(f"SUPABASE_URL: {url[:30]}..." if url else "SUPABASE_URL: (空)")
    print(f"SUPABASE_KEY: {key[:20]}..." if key else "SUPABASE_KEY: (空)")
    
    print("\n所有配置:")
    for k, v in config._config.items():
        if 'KEY' in k or 'SECRET' in k or 'PASSWORD' in k:
            print(f"  {k}: {'*' * min(len(v), 10)}...")
        else:
            print(f"  {k}: {v}")
