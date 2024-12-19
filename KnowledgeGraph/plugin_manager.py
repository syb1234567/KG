import os

class PluginManager:
    def __init__(self, graph_data_manager=None):
        """
        初始化插件管理器
        :param graph_data_manager: GraphDataManager 实例（可选）
        """
        self.plugins = []
        self.graph_data_manager = graph_data_manager

    def load_plugins(self):
        """
        动态加载插件
        """
        # 示例：加载 plugins 目录下的所有插件
        plugins_dir = "plugins/"
        if not os.path.exists(plugins_dir):
            return

        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py"):
                plugin_name = filename[:-3]
                module = __import__(f"plugins.{plugin_name}", fromlist=[''])
                if hasattr(module, 'Plugin'):
                    plugin_instance = module.Plugin(self.graph_data_manager)
                    self.plugins.append(plugin_instance)
                    plugin_instance.register()

    def list_plugins(self):
        """
        列出所有已加载的插件
        """
        return [plugin.name for plugin in self.plugins]
