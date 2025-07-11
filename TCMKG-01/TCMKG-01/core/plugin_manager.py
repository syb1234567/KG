# core/plugin_manager.py
import importlib
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import inspect
from PyQt5.QtCore import QObject, pyqtSignal


class PluginLoadError(Exception):
    """自定义插件加载异常"""
    pass


class PluginWrapper(QObject):
    """插件包装类，封装插件实例及其元数据"""
    status_changed = pyqtSignal(bool)  # 启用状态改变信号

    def __init__(self, name: str, path: Path, enabled: bool, instance: QObject):
        super().__init__()
        self.name = name  # 插件显示名称
        self.path = path  # 插件文件路径
        self.enabled = enabled  # 是否启用
        self.instance = instance  # 插件实例
        self.metadata = {}  # 扩展元数据存储

    def set_enabled(self, state: bool):
        """安全更新启用状态并触发信号"""
        if self.enabled != state:
            self.enabled = state
            self.status_changed.emit(state)


class PluginManager(QObject):
    """插件管理核心类"""
    plugins_updated = pyqtSignal()  # 插件列表更新信号

    def __init__(self, graph_manager):
        super().__init__()
        self.graph_manager = graph_manager
        self.plugins: List[PluginWrapper] = []
        self.plugin_dir = Path("plugins")  # 默认插件目录

    def load_plugin(self, plugin_path: Path, enabled: bool = True) -> PluginWrapper:
        """
        加载单个插件
        :param plugin_path: 插件文件路径
        :param enabled: 是否立即启用
        :return: PluginWrapper实例
        """
        try:
            # 增加文件内容校验
            with open(plugin_path, 'r', encoding='utf-8') as f:
                if 'Plugin' not in f.read():
                    raise PluginLoadError("文件不是有效插件（缺少Plugin类）")

            # 防止重复加载
            if any(p.path == plugin_path for p in self.plugins):
                raise PluginLoadError(f"插件已加载: {plugin_path}")

            # 动态导入
            module_name = f"plugins.{plugin_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None:
                raise PluginLoadError("无效的插件模块规格")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 验证插件类
            if not hasattr(module, 'Plugin'):
                raise PluginLoadError("插件必须包含Plugin主类")

            plugin_class = getattr(module, 'Plugin')
            if not inspect.isclass(plugin_class):
                raise PluginLoadError("Plugin必须是一个类")

            # 实例化并验证接口
            plugin_instance = plugin_class(self.graph_manager)
            if not hasattr(plugin_instance, 'name'):
                raise PluginLoadError("插件必须包含name属性")

            # 创建包装器
            wrapper = PluginWrapper(
                name=plugin_instance.name,
                path=plugin_path,
                enabled=enabled,
                instance=plugin_instance
            )

            # 连接信号
            wrapper.status_changed.connect(self._on_plugin_status_changed)

            self.plugins.append(wrapper)
            self.plugins_updated.emit()
            return wrapper


        except Exception as e:
             # 添加详细日志
            import traceback
            traceback.print_exc()
            raise PluginLoadError(f"加载失败: {str(e)}") from e

    def unload_plugin(self, plugin_name: str):
        """安全卸载插件"""
        plugin = next((p for p in self.plugins if p.name == plugin_name), None)
        if plugin:
            # 执行清理操作（如果有）
            if hasattr(plugin.instance, 'cleanup'):
                plugin.instance.cleanup()

            self.plugins.remove(plugin)
            self.plugins_updated.emit()

    def run_plugin(self, plugin_name: str):
        """执行插件主逻辑"""
        plugin = self.get_plugin(plugin_name)
        if not plugin or not plugin.enabled:
            raise PluginLoadError("插件未启用或不存在")

        try:
            if hasattr(plugin.instance, 'run'):
                return plugin.instance.run()
            raise PluginLoadError("插件缺少run方法")
        except Exception as e:
            raise PluginLoadError(f"执行插件失败: {str(e)}") from e

    def get_plugin(self, plugin_name: str) -> Optional[PluginWrapper]:
        """按名称获取插件"""
        return next((p for p in self.plugins if p.name == plugin_name), None)

    def update_plugin_states(self, states: Dict[str, bool]):
        """批量更新插件状态"""
        for name, state in states.items():
            plugin = self.get_plugin(name)
            if plugin:
                plugin.set_enabled(state)

    def scan_plugin_dir(self):
        """扫描插件目录并自动加载"""
        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir()

        for path in self.plugin_dir.glob("*.py"):
            if path.name.startswith("_"):
                continue  # 忽略__init__等文件
            try:
                self.load_plugin(path)
            except PluginLoadError as e:
                print(f"加载插件失败: {path.name} - {str(e)}")

    def _on_plugin_status_changed(self, state: bool):
        """处理插件状态变更"""
        # 这里可以添加状态变更的后续处理逻辑
        self.plugins_updated.emit()

    def save_plugin_config(self, config_path: Path):
        """保存插件配置（启用状态等）"""
        config = {
            p.path.as_posix(): {
                "enabled": p.enabled,
                "metadata": p.metadata
            } for p in self.plugins
        }
        with config_path.open('w') as f:
            json.dump(config, f)

    def load_plugin_config(self, config_path: Path):
        """加载插件配置"""

        if not config_path.exists():
            return

        with config_path.open() as f:
            config = json.load(f)

        for path_str, settings in config.items():
            path = Path(path_str)
            if path.exists():
                plugin = self.load_plugin(path, settings["enabled"])
                plugin.metadata = settings.get("metadata", {})

