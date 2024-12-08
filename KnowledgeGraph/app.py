from flask import Flask, jsonify, render_template
from config import Config
from graph_data_manager import GraphDataManager  # 使用新的图数据库管理类
from data_importer import DataImporter
from graph_visualizer import GraphVisualizer
from plugin_manager import PluginManager

def create_app():
    """
    创建并配置 Flask 应用
    """
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(Config)

    # 初始化 Neo4j 图数据库管理器
    app.graph_data_manager = GraphDataManager(
        uri=app.config["NEO4J_URI"],
        user=app.config["NEO4J_USER"],
        password=app.config["NEO4J_PASSWORD"]
    )  # 这里使用 GraphDataManager 来替代 DataManager

    # 初始化各模块
    app.data_importer = DataImporter(app.graph_data_manager)  # 数据导入模块
    app.graph_visualizer = GraphVisualizer(app.graph_data_manager)  # 图谱可视化模块
    app.plugin_manager = PluginManager()  # 插件管理模块

    # 动态加载插件
    app.plugin_manager.load_plugins()

    # 添加 RESTful API 路由
    @app.route("/", methods=["GET"])
    def home():
        """
        主页路由，提供基本信息
        """
        return render_template("index.html")

    @app.route("/plugins", methods=["GET"])
    def list_plugins():
        """
        列出所有已加载的插件
        """
        return jsonify({"plugins": app.plugin_manager.list_plugins()})

    @app.route("/graph", methods=["GET"])
    def get_graph_data():
        """
        获取知识图谱的可视化数据
        """
        graph_data = app.graph_visualizer.get_graph_data(max_nodes=50)
        return jsonify(graph_data)

    @app.route("/import", methods=["POST"])
    def import_data():
        """
        数据导入接口（示例）
        """
        # 示例请求处理逻辑
        # 使用 `app.data_importer` 从 JSON 或 Word 文档导入数据
        return jsonify({"message": "数据导入功能开发中"})

    return app

if __name__ == "__main__":
    # 创建 Flask 应用实例
    app = create_app()

    # 启动服务
    app.run(host="0.0.0.0", port=5000, debug=True)



