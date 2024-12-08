import os
import importlib.util

class PluginManager:
    def __init__(self, plugin_directory="plugins"):
        """
        初始化插件管理器
        :param plugin_directory: 插件存储目录
        """
        self.plugin_directory = plugin_directory
        self.plugins = {}  # 存储加载的插件信息

        # 初始化插件目录
        if not os.path.exists(self.plugin_directory):
            os.makedirs(self.plugin_directory)

    def load_plugins(self):
        """
        加载插件目录下的所有插件
        """
        for file_name in os.listdir(self.plugin_directory):
            if file_name.endswith(".py") and not file_name.startswith("__"):
                plugin_name = file_name[:-3]  # 去掉 .py 后缀
                self.load_plugin(plugin_name)

    def load_plugin(self, plugin_name):
        """
        加载单个插件
        :param plugin_name: 插件名称（文件名去掉 .py）
        """
        plugin_path = os.path.join(self.plugin_directory, f"{plugin_name}.py")
        if not os.path.exists(plugin_path):
            print(f"插件 {plugin_name} 不存在")
            return

        spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 验证插件是否包含 init 方法
        if hasattr(module, "init"):
            self.plugins[plugin_name] = module
            module.init()  # 调用插件的初始化方法
            print(f"插件 {plugin_name} 已加载")
        else:
            print(f"插件 {plugin_name} 缺少 'init' 方法，未加载")

    def unload_plugin(self, plugin_name):
        """
        卸载单个插件
        :param plugin_name: 插件名称
        """
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            print(f"插件 {plugin_name} 已卸载")
        else:
            print(f"插件 {plugin_name} 未加载，无法卸载")

    def list_plugins(self):
        """
        列出所有已加载的插件
        :return: 已加载插件的列表
        """
        return list(self.plugins.keys())

    def execute_plugin(self, plugin_name, *args, **kwargs):
        """
        执行指定插件的主功能
        :param plugin_name: 插件名称
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 插件功能的执行结果
        """
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            if hasattr(plugin, "run"):
                return plugin.run(*args, **kwargs)
            else:
                print(f"插件 {plugin_name} 缺少 'run' 方法，无法执行")
        else:
            print(f"插件 {plugin_name} 未加载，无法执行")
        return None
