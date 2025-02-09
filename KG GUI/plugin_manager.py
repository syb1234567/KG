# plugin_manager.py
import os
import importlib
#该模块用于管理插件，包括加载插件、运行插件等功能
class PluginManager:
    def __init__(self, graph_data_manager):
        self.plugins = []
        self.graph_data_manager = graph_data_manager

    def load_plugins(self, plugins_dir="plugins"):
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f"plugins.{module_name}")
                    if hasattr(module, "Plugin"):
                        plugin = module.Plugin(self.graph_data_manager)
                        self.plugins.append(plugin)
                except Exception as e:
                    print(f"加载插件 {module_name} 失败: {e}")

    def run_plugin(self, plugin_name, **kwargs):
        for plugin in self.plugins:
            if getattr(plugin, "name", None) == plugin_name:
                return plugin.run(**kwargs)
        return None
