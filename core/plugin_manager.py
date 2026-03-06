"""
插件管理器模块
支持动态扩展功能模块
"""

import os
import sys
import importlib
import importlib.util
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum


class PluginType(Enum):
    """插件类型"""
    DATA_SOURCE = "data_source"       # 数据源插件
    QUERY_HANDLER = "query_handler"   # 查询处理器插件
    DIAGNOSIS_MODULE = "diagnosis_module"  # 诊断模块插件
    UI_EXTENSION = "ui_extension"     # UI扩展插件


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str]
    enabled: bool = True
    config: Dict = None


class BasePlugin(ABC):
    """
    插件基类
    所有插件必须继承此类
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.enabled = True
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化插件，返回是否成功"""
        pass
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        pass
    
    def shutdown(self):
        """关闭插件"""
        pass
    
    def get_config_schema(self) -> Dict:
        """获取配置schema"""
        return {}


class DataSourcePlugin(BasePlugin):
    """
    数据源插件基类
    用于添加新的中医知识数据源
    """
    
    @abstractmethod
    def get_data(self, query: str, **kwargs) -> List[Dict]:
        """获取数据"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict:
        """获取数据结构schema"""
        pass


class QueryHandlerPlugin(BasePlugin):
    """
    查询处理器插件基类
    用于添加新的查询类型处理
    """
    
    @abstractmethod
    def can_handle(self, intent: str, entities: Dict) -> bool:
        """判断是否能处理该查询"""
        pass
    
    @abstractmethod
    async def handle(self, query: str, entities: Dict, context: Dict) -> Dict:
        """处理查询"""
        pass


class DiagnosisModulePlugin(BasePlugin):
    """
    诊断模块插件基类
    用于添加新的诊断分析方法
    """
    
    @abstractmethod
    async def analyze(self, inquiry_info: Dict, knowledge: Dict) -> Dict:
        """分析病情"""
        pass
    
    @abstractmethod
    def get_supported_syndromes(self) -> List[str]:
        """获取支持的证型列表"""
        pass


class PluginManager:
    """
    插件管理器
    管理所有插件的加载、启用、禁用
    """
    
    def __init__(self, plugin_dir: str = "./plugins"):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_infos: Dict[str, PluginInfo] = {}
        self.handlers: Dict[str, List[QueryHandlerPlugin]] = {
            PluginType.QUERY_HANDLER.value: []
        }
        
        # 创建插件目录
        os.makedirs(plugin_dir, exist_ok=True)
    
    def load_plugin(self, plugin_path: str) -> Optional[BasePlugin]:
        """
        加载单个插件
        
        Args:
            plugin_path: 插件文件路径
        
        Returns:
            插件实例或None
        """
        try:
            # 获取插件名称
            plugin_name = os.path.basename(plugin_path).replace('.py', '')
            
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BasePlugin) and 
                    attr != BasePlugin and
                    not attr.__name__.startswith('Base')):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                print(f"在 {plugin_path} 中未找到插件类")
                return None
            
            # 实例化插件
            plugin = plugin_class()
            
            # 初始化
            if plugin.initialize():
                info = plugin.get_info()
                self.plugins[info.name] = plugin
                self.plugin_infos[info.name] = info
                
                # 注册处理器
                if isinstance(plugin, QueryHandlerPlugin):
                    self.handlers[PluginType.QUERY_HANDLER.value].append(plugin)
                
                print(f"插件 {info.name} v{info.version} 加载成功")
                return plugin
            else:
                print(f"插件 {plugin_name} 初始化失败")
                return None
        
        except Exception as e:
            print(f"加载插件 {plugin_path} 失败: {e}")
            return None
    
    def load_all_plugins(self):
        """加载所有插件"""
        if not os.path.exists(self.plugin_dir):
            return
        
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_path = os.path.join(self.plugin_dir, filename)
                self.load_plugin(plugin_path)
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        plugin.shutdown()
        
        del self.plugins[plugin_name]
        del self.plugin_infos[plugin_name]
        
        # 从处理器列表中移除
        if isinstance(plugin, QueryHandlerPlugin):
            self.handlers[PluginType.QUERY_HANDLER.value].remove(plugin)
        
        print(f"插件 {plugin_name} 已卸载")
        return True
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            self.plugin_infos[plugin_name].enabled = True
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            self.plugin_infos[plugin_name].enabled = False
            return True
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> List[PluginInfo]:
        """获取所有插件信息"""
        return list(self.plugin_infos.values())
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """获取指定类型的插件"""
        return [
            plugin for plugin in self.plugins.values()
            if plugin.get_info().plugin_type == plugin_type and plugin.enabled
        ]
    
    def find_handler(self, intent: str, entities: Dict) -> Optional[QueryHandlerPlugin]:
        """查找能处理该查询的处理器"""
        for handler in self.handlers[PluginType.QUERY_HANDLER.value]:
            if handler.enabled and handler.can_handle(intent, entities):
                return handler
        return None
    
    def get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            "total_plugins": len(self.plugins),
            "enabled_plugins": sum(1 for p in self.plugins.values() if p.enabled),
            "plugins": [
                {
                    "name": info.name,
                    "version": info.version,
                    "type": info.plugin_type.value,
                    "enabled": info.enabled
                }
                for info in self.plugin_infos.values()
            ]
        }


# ==================== 示例插件 ====================

class PediatricsPlugin(QueryHandlerPlugin):
    """
    儿科插件示例
    展示如何扩展新的查询类型
    """
    
    def initialize(self) -> bool:
        print("儿科插件初始化")
        return True
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="pediatrics",
            version="1.0.0",
            description="儿科疾病查询插件",
            author="TCM Team",
            plugin_type=PluginType.QUERY_HANDLER,
            dependencies=["core"]
        )
    
    def can_handle(self, intent: str, entities: Dict) -> bool:
        """判断是否儿科相关查询"""
        pediatrics_keywords = ["小儿", "儿童", "孩子", "婴儿", "儿科"]
        query = entities.get("query", "")
        return any(kw in query for kw in pediatrics_keywords)
    
    async def handle(self, query: str, entities: Dict, context: Dict) -> Dict:
        """处理儿科查询"""
        return {
            "type": "pediatrics",
            "message": "这是儿科相关查询的处理结果",
            "data": []
        }


# 便捷函数
def create_plugin_manager(plugin_dir: str = "./plugins") -> PluginManager:
    """创建插件管理器"""
    return PluginManager(plugin_dir)
