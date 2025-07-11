from PyQt5.QtCore import QObject

class Plugin(QObject):
    def __init__(self, graph_manager):
        super().__init__()
        self.name = "示例插件"

    def run(self):
        print("插件运行成功！")
        return "Hello World"