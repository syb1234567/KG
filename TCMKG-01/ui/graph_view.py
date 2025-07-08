import json
from pathlib import Path
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot




#桥接类Bridge 只处理前端回调
class Bridge(QObject):
    def __init__(self, node_detail_widget, graph_manager, update_callback):
        super().__init__()
        self.node_detail_widget = node_detail_widget
        self.graph_manager = graph_manager
        self.update_callback = update_callback  # 用于刷新图谱显示

    @pyqtSlot(str)
    def display_node_info(self, node_info):
        try:
            node_data = json.loads(node_info)
            self.node_detail_widget.show_node(node_data)
        except Exception as e:
            print(f"节点信息显示错误: {str(e)}")

    @pyqtSlot(str)
    def create_node(self, node_json):
        try:
            node = json.loads(node_json)
            # 检查必须字段 label（作为名称）和 type（类型）
            if "label" in node and "type" in node:
                name = node["label"]
                node_type = node["type"]
                attributes = node.get("attributes", {})
                self.graph_manager.add_node(name, node_type, attributes)
                self.update_callback()  # 刷新图谱显示
            else:
                print("创建节点时数据不完整")
        except Exception as e:
            print(f"创建节点错误: {str(e)}")

    @pyqtSlot(str)
    def create_edge(self, edge_json):
        try:
            edge = json.loads(edge_json)
            # 检查必须字段：from, to, label（关系类型）
            if "from" in edge and "to" in edge and "label" in edge:
                source = edge["from"]
                target = edge["to"]
                relation_type = edge["label"]
                self.graph_manager.add_relationship(source, target, relation_type)
                self.update_callback()
            else:
                print("创建边时数据不完整")
        except Exception as e:
            print(f"创建边错误: {str(e)}")

    @pyqtSlot(str)
    def polygon_node_count_result(self, result_json):
        """接收前端返回的多边形区域内节点统计结果"""
        try:
            result = json.loads(result_json)
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(None, "区域统计结果", f"区域内节点数量: {result.get('count', 0)}")
        except Exception as e:
            print(f"统计区域节点数量错误: {str(e)}")

#GraphView 只处理“把数据渲染到 vis.js”
_TPL = (Path(__file__).parent / "webview" / "vis_template.html").read_text(encoding="utf-8")
class GraphView(QWebEngineView):
    def __init__(
                self,
                graph_manager,
                node_detail_widget,
                update_callback,
                parent=None
        ):
            super().__init__(parent)
            self.graph_manager = graph_manager
            self.node_detail_widget = node_detail_widget
            self.update_callback = update_callback

            # WebChannel + Bridge
            self.channel = QWebChannel(self.page())
            self.bridge = Bridge(
                node_detail_widget,
                graph_manager,
                update_callback
            )
            self.channel.registerObject("py_obj", self.bridge)
            self.page().setWebChannel(self.channel)

    # ui/graph_view.py 中的某处

    def render(self):
        data = self.graph_manager.get_graph_data()
        # 先做跟你原来一模一样的颜色映射
        nodes = []
        for node in data["nodes"]:
            bg = "#97C2FC"
            if node["type"] == "方剂":
                bg = "#FFA07A"
            elif node["type"] == "药理":
                bg = "#ADD8E6"
            elif node["type"] == "药材":
                bg = "#98FB98"
            elif node["type"] == "疾病":
                bg = "#D3D3D3"
            nodes.append({
                "id": node["name"],
                "label": node["name"],
                "type": node["type"],
                "color": {
                    "background": bg,
                    "border": "#2B7CE9",
                    "highlight": {"background": "#D2E5FF", "border": "#2B7CE9"},
                }
            })
        edges = [
            {"from": e["source"], "to": e["target"], "label": e["relation_type"]}
            for e in data["edges"]
        ]

        html = _TPL.format(
            nodes_js=json.dumps(nodes),
            edges_js=json.dumps(edges),
        )
        self.setHtml(html, QUrl("about:blank"))

