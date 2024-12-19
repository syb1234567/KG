from flask import Flask, jsonify, render_template, request
from config import Config
from graph_data_manager import GraphDataManager
from data_importer import DataImporter
from graph_visualizer import GraphVisualizer
from plugin_manager import PluginManager
import os
from werkzeug.utils import secure_filename

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化 GraphDataManager
    app.graph_data_manager = GraphDataManager(storage_path=app.config["GRAPH_STORAGE_PATH"])
    app.data_importer = DataImporter(app.graph_data_manager)
    app.graph_visualizer = GraphVisualizer(app.graph_data_manager)
    app.plugin_manager = PluginManager(graph_data_manager=app.graph_data_manager)
    app.plugin_manager.load_plugins()

    @app.route("/", methods=["GET"])
    def home():
        """
        主页路由，展示图谱
        """
        # 首页展示index.html
        return render_template("index.html")

    @app.route("/graph_data", methods=["GET"])
    def get_graph_data():
        """
        获取知识图谱数据（JSON格式）
        """
        graph_data = app.graph_visualizer.get_graph_data(max_nodes=50)
        return graph_data  # 返回JSON数据

    @app.route("/graph", methods=["GET"])
    def graph_page():
        """
        图谱页面，提供高级操作
        """
        return render_template("graph.html")

    @app.route("/plugins_data", methods=["GET"])
    def list_plugins_data():
        """
        列出所有已加载的插件（JSON格式）
        """
        return jsonify({"plugins": app.plugin_manager.list_plugins()})

    @app.route("/plugins", methods=["GET"])
    def plugins_page():
        """
        插件页面
        """
        return render_template("plugins.html")

    @app.route("/import", methods=["GET"])
    def show_import_page():
        """
        显示数据导入页面
        """
        return render_template("import.html")

    @app.route("/import", methods=["POST"])
    def import_data():
        """
        处理数据导入请求
        """
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename, app.config["ALLOWED_EXTENSIONS"]):
            filename = secure_filename(file.filename)
            os.makedirs("uploads", exist_ok=True)
            filepath = os.path.join("uploads", filename)
            file.save(filepath)

            file_type = get_file_type(filename)
            file_category = request.form.get("file_type")

            if file_category == "nodes":
                node_file = True
            elif file_category == "relationships":
                node_file = False
            else:
                return jsonify({"error": "Invalid file_type parameter"}), 400

            print(f"Importing data from {filepath}, type={file_type}, node_file={node_file}")
            try:
                app.data_importer.import_data(filepath, file_type, node_file=node_file)
                print("Data import successful!")
                # 导入成功后可返回成功JSON消息，前端可选择跳转或刷新
                return jsonify({"message": "数据导入成功"})
            except ValueError as e:
                print("Data import failed:", str(e))
                return jsonify({"error": str(e)}), 400
        else:
            return jsonify({"error": "Unsupported file type"}), 400

    return app

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'json':
        return 'json'
    elif ext == 'csv':
        return 'csv'
    elif ext in ['xlsx', 'xls']:
        return 'xlsx'
    else:
        return 'unknown'

if __name__ == "__main__":
    app = create_app()
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])

