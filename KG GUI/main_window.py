import json
import os
import sys
import pandas as pd
import chardet
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QListWidget, QMenu, QStatusBar,
    QSplitter, QDialog, QFormLayout, QLineEdit, QTextEdit
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, QTimer, Qt
from PyQt5.QtWebChannel import QWebChannel


from graph_data_manager import GraphDataManager
from data_importer import DataImporter
from node_detail_widget import NodeDetailWidget
from plugin_manager import PluginManager
from table_dialog import TableEditDialog



# from table_dialog import TableEditDialog

def clean_data(data):
    """清理数据中的 None 值，替换为适当的默认值"""
    if isinstance(data, dict):
        return {key: clean_data(value) for key, value in data.items() if value is not None}
    elif isinstance(data, list):
        return [clean_data(item) for item in data if item is not None]
    else:
        return data
#桥接类
class Bridge(QObject):
    def __init__(self, node_detail_widget):
        super().__init__()
        self.node_detail_widget = node_detail_widget

    @pyqtSlot(str)
    def display_node_info(self, node_info):
        try:
            node_data = json.loads(node_info)
            self.node_detail_widget.show_node(node_data)
        except Exception as e:
            print(f"节点信息显示错误: {str(e)}")
#主窗口类 其中包含了图谱显示，节点详情显示，插件列表显示，工具栏，状态栏，批量编辑功能等功能
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("中医知识图谱")
        self.setGeometry(100, 100, 1600, 900)

        # 初始化核心组件
        self.graph_manager = GraphDataManager()
        self.data_importer = DataImporter(self.graph_manager)
        self.plugin_manager = PluginManager(self.graph_manager)
        self.plugin_manager.load_plugins()

        self.init_ui()
        self.init_web_view()
        self.populate_plugins()

    def init_ui(self):
        # 主窗口布局
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # 左侧图谱显示区域
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)

        # 右侧面板（分为节点详情与插件列表）
        self.right_splitter = QSplitter(Qt.Vertical)
        self.node_detail = NodeDetailWidget(self.graph_manager, self.safe_update)
        self.plugin_list = QListWidget()
        self.plugin_list.setMinimumHeight(150)
        self.plugin_list.itemDoubleClicked.connect(self.run_plugin)
        self.right_splitter.addWidget(self.node_detail)
        self.right_splitter.addWidget(self.plugin_list)
        self.right_splitter.setSizes([400, 200])

        # 整体分割布局
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([1000, 400])

        self.main_layout.addWidget(self.main_splitter)

        # 初始化工具栏与状态栏
        self.init_toolbar()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def open_batch_edit_dialog(self):
        """用于批量编辑节点数据的方法"""
        # 假设我们先加载一些节点数据展示在表格中
        columns = ["name", "type", "attributes"]
        nodes_data = self.graph_manager.get_all_nodes()  # 从 graph_manager 获取实际的节点数据

        # 将实际的节点数据传递给 TableEditDialog
        dialog = TableEditDialog(columns, nodes_data, self)

        if dialog.exec_():  # 如果用户点击了“确定”
            edited_data = dialog.get_data()  # 获取用户编辑的数据
            # 在这里处理编辑数据并更新图数据
            updates = {node["name"]: {"type": node["type"], "attributes": json.loads(node["attributes"])} for node in
                       edited_data}

            try:
                self.graph_manager.batch_edit_nodes(updates)  # 执行批量编辑
                self.safe_update()  # 强制刷新图谱界面
            except Exception as e:
                QMessageBox.critical(self, "错误", f"批量编辑节点失败: {str(e)}")

    def open_batch_edit_relationship_dialog(self):
            # 获取所有关系数据
            columns = ["source", "target", "relation_type"]
            relationships_data = self.graph_manager.get_all_relationships()  # 获取所有关系数据

            # 打开批量编辑表格对话框，展示关系数据
            dialog = TableEditDialog(columns, relationships_data, self)  # 传入关系数据

            if dialog.exec_():  # 用户点击“确定”
                # 获取编辑后的数据
                edited_data = dialog.get_data()

                # 构建更新字典
                # 关系数据：{(source, target): {"relation_type": "new_relation_type"}}
                updates = {(r["source"], r["target"]): {"relation_type": r["relation_type"]} for r in edited_data}

                # 调用图数据管理器的批量更新方法
                self.graph_manager.batch_edit_relationships(updates)  # 批量更新关系

    def init_toolbar(self):
        # 主工具栏
        toolbar = self.addToolBar("主工具栏")

        # 文件菜单
        file_menu = QMenu()
        file_menu.addAction("导入数据", self.import_data)
        file_menu.addAction("保存数据", self.save_data)
        file_menu.addAction("导出数据", self.save_data)
        file_btn = QPushButton("文件")
        file_btn.setMenu(file_menu)
        toolbar.addWidget(file_btn)

        # 编辑菜单
        edit_menu = QMenu()
        edit_menu.addAction("添加节点", self.show_add_node_dialog)
        edit_menu.addAction("批量编辑节点", self.open_batch_edit_dialog)
        edit_menu.addAction("批量编辑关系", self.open_batch_edit_relationship_dialog)
        edit_btn = QPushButton("编辑")
        edit_btn.setMenu(edit_menu)
        toolbar.addWidget(edit_btn)

        # 视图菜单
        view_menu = QMenu()
        view_menu.addAction("重置布局", self.reset_layout)
        view_btn = QPushButton("视图")
        view_btn.setMenu(view_menu)
        toolbar.addWidget(view_btn)

    def init_web_view(self):
        # 图谱显示区域（使用 QWebEngineView 展示 vis.js 图谱）
        self.graph_view = QWebEngineView()
        self.left_layout.addWidget(self.graph_view)

        # 初始化 WebChannel 实现前后端交互
        self.channel = QWebChannel()
        self.bridge = Bridge(self.node_detail)
        self.channel.registerObject("py_obj", self.bridge)
        self.graph_view.page().setWebChannel(self.channel)

        self.update_graph_view()

    def populate_plugins(self):
        """将加载的插件名称显示到右侧列表中"""
        self.plugin_list.clear()
        for plugin in self.plugin_manager.plugins:
            if hasattr(plugin, "name"):
                self.plugin_list.addItem(plugin.name)

    def safe_update(self):
        QTimer.singleShot(0, self.update_graph_view)

    def update_graph_view(self, background=None, to=None, enabled=None, color=None):
        """更新图谱显示内容，同时根据节点类型设置不同颜色，并调整边的长度"""
        graph_data = self.graph_manager.get_graph_data()

        # 构建节点数据，根据节点类型设置不同颜色
        nodes_js = []
        for node in graph_data["nodes"]:
            node_type = node["type"]
            # 默认颜色
            color_bg = "#97C2FC"
            if node_type == "方剂":
                color_bg = "#FFA07A"
            elif node_type == "药理":
                color_bg = "#ADD8E6"
            elif node_type == "药材":
                color_bg = "#98FB98"
            elif node_type == "疾病":
                color_bg = "#D3D3D3"

            nodes_js.append({
                "id": node["name"],
                "label": node["name"],
                "type": node["type"],
                "attributes": node.get("attributes", {}),
                "color": {
                    "background": color_bg,
                    "border": "#2B7CE9",
                    "highlight": { "background": "#D2E5FF", "border": "#2B7CE9" },
                    "font": "#000000"
                }
            })

        # 构建边数据
        edges_js = clean_data([
            {"from": e["source"], "to": e["target"], "label": e["relation_type"]}
            for e in graph_data["edges"]
        ])

        # 定义 HTML 模板，设置 vis.js 的参数
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style>
                #mynetwork {{
                    width: 100%;
                    height: 100vh;
                    border: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <div id="mynetwork"></div>
            <script>
                var nodes = new vis.DataSet({json.dumps(nodes_js)});
                var edges = new vis.DataSet({json.dumps(edges_js)});
                var container = document.getElementById('mynetwork');
                var options = {{
                    physics: {{
                        stabilization: {{ iterations: 1000 }},
                        forceAtlas2Based: {{
                            gravitationalConstant: -50,
                            centralGravity: 0.01,
                            springLength: 200,  // 调整此值使边界变长
                            springConstant: 0.08
                        }}
                    }},
                    nodes: {{
                        font: {{ size: 14, color: "#333" }},
                        borderWidth: 1,
                        shape: "dot",
                        shadow: false
                    }},
                    edges: {{
                        arrows: {{ to: {{ enabled: true, scaleFactor: 1 }} }},
                        smooth: {{ type: "continuous" }},
                        color: {{ color: "#848484", highlight: "#848484" }}
                    }},
                    interaction: {{ hover: true }}
                }};
                var network = new vis.Network(container, {{ nodes: nodes, edges: edges }}, options);

                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    window.py_obj = channel.objects.py_obj;
                }});

                network.on("click", function(params) {{
                    if(params.nodes.length) {{
                        var node = nodes.get(params.nodes[0]);
                        py_obj.display_node_info(JSON.stringify(node));
                    }}
                }});
            </script>
        </body>
        </html>
        """
        self.graph_view.setHtml(html_content, QUrl("about:blank"))

    def show_add_node_dialog(self):
        """显示添加节点对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加节点")
        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        type_edit = QLineEdit()
        attr_edit = QTextEdit()
        attr_edit.setPlaceholderText("输入JSON格式属性...")

        layout.addRow("节点名称", name_edit)
        layout.addRow("节点类型", type_edit)
        layout.addRow("节点属性", attr_edit)

        btn_box = QPushButton("确定")
        btn_box.clicked.connect(lambda: self.add_node_from_dialog(
            name_edit.text(), type_edit.text(), attr_edit.toPlainText(), dialog
        ))
        layout.addRow(btn_box)

        dialog.setLayout(layout)
        dialog.exec_()

    def add_node_from_dialog(self, name, node_type, attributes_str, dialog):
        """从对话框中添加节点"""
        try:
            if not name or not node_type:
                raise ValueError("节点名称和类型不能为空")
            attributes = json.loads(attributes_str) if attributes_str else {}
            self.graph_manager.add_node(name, node_type, attributes)
            self.safe_update()
            dialog.close()
        except json.JSONDecodeError:
            QMessageBox.critical(self, "错误", "属性必须是有效的JSON格式")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def import_data(self):
        """导入 CSV 或 JSON 数据文件"""
        options = QFileDialog.Options()
        filepaths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",
            "CSV Files (*.csv);;JSON Files (*.json)",
            options=options,
        )
        if not filepaths:
            return

        for filepath in filepaths:
            try:
                if filepath.endswith(".csv"):
                    encoding = self.detect_encoding(filepath) or "utf-8"
                    data = pd.read_csv(filepath, encoding=encoding)
                    if {"name", "type"}.issubset(data.columns):
                        self.data_importer.import_nodes_from_csv(filepath)
                    elif {"source", "target", "relation_type"}.issubset(data.columns):
                        self.data_importer.import_relationships_from_csv(filepath)
                    else:
                        QMessageBox.warning(self, "警告", "CSV文件列名不符合要求")
                        continue
                elif filepath.endswith(".json"):
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "nodes" in data and "edges" in data:
                            for node in data["nodes"]:
                                self.graph_manager.add_node(
                                    node["name"],
                                    node["type"],
                                    node.get("attributes", {})
                                )
                            for edge in data["edges"]:
                                self.graph_manager.add_relationship(
                                    edge["source"],
                                    edge["target"],
                                    edge["relation_type"]
                                )
                        else:
                            QMessageBox.warning(self, "警告", "JSON文件格式不正确")
                            continue
                else:
                    QMessageBox.warning(self, "警告", "不支持的文件格式")
                    continue

                self.safe_update()
                QMessageBox.information(self, "成功", f"文件 '{os.path.basename(filepath)}' 导入成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"文件 '{os.path.basename(filepath)}' 导入失败：{str(e)}")

    def save_data(self):
        """保存当前图数据到 JSON 文件"""
        try:
            self.graph_manager.save_graph_to_json()
            self.status_bar.showMessage("数据保存成功", 3000)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def reset_layout(self):
        """重置窗口布局"""
        self.main_splitter.setSizes([1000, 400])
        self.right_splitter.setSizes([400, 200])

    def detect_encoding(self, filepath):
        """检测文件编码"""
        with open(filepath, "rb") as f:
            raw = f.read(10000)
        result = chardet.detect(raw)
        return result.get("encoding", None)

    def run_plugin(self, item):
        """当在插件列表中双击插件时运行该插件"""
        plugin_name = item.text()
        result = self.plugin_manager.run_plugin(plugin_name)
        QMessageBox.information(self, "插件运行结果", f"插件 '{plugin_name}' 返回: {result}")

    def closeEvent(self, event):
        """退出时保存图数据"""
        try:
            self.graph_manager.save_graph_to_json()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
        event.accept()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
