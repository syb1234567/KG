import json
from pathlib import Path
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot


# 桥接类Bridge 处理前端回调和删除操作
class Bridge(QObject):
    def __init__(self, node_detail_widget, graph_manager, update_callback):
        super().__init__()
        self.node_detail_widget = node_detail_widget
        self.graph_manager = graph_manager
        self.update_callback = update_callback  # 用于刷新图谱显示
        self.layout_file = Path("graph_layout.json")  # 布局保存文件

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
                
                # 使用增量更新而不是完全重新渲染
                if hasattr(self, 'web_view') and self.web_view:
                    self.web_view.add_node_incrementally(node)
                
                print(f"创建节点成功: {name}")
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
                
                # 使用增量更新而不是完全重新渲染
                if hasattr(self, 'web_view') and self.web_view:
                    self.web_view.add_edge_incrementally(edge)
                
                print(f"创建关系成功: {source} -> {target} ({relation_type})")
            else:
                print("创建边时数据不完整")
        except Exception as e:
            print(f"创建边错误: {str(e)}")

    @pyqtSlot(str)
    def delete_node(self, node_name):
        """删除节点"""
        try:
            if self.graph_manager.has_node(node_name):
                self.graph_manager.delete_node(node_name)
                
                # 使用增量更新
                if hasattr(self, 'web_view') and self.web_view:
                    self.web_view.remove_node_incrementally(node_name)
                
                print(f"删除节点成功: {node_name}")
            else:
                print(f"节点不存在: {node_name}")
        except Exception as e:
            print(f"删除节点错误: {str(e)}")

    @pyqtSlot(str)
    def delete_edge(self, edge_json):
        """删除边"""
        try:
            edge = json.loads(edge_json)
            if "source" in edge and "target" in edge:
                source = edge["source"]
                target = edge["target"]
                self.graph_manager.delete_relationship(source, target)
                
                # 使用增量更新
                if hasattr(self, 'web_view') and self.web_view:
                    self.web_view.remove_edge_incrementally(source, target)
                
                print(f"删除关系成功: {source} -> {target}")
            else:
                print("删除边时数据不完整")
        except Exception as e:
            print(f"删除边错误: {str(e)}")

    @pyqtSlot(str)
    def edit_node(self, node_json):
        """编辑节点"""
        try:
            node = json.loads(node_json)
            if "old_name" in node and "new_name" in node:
                old_name = node["old_name"]
                new_name = node["new_name"]
                node_type = node.get("type", "")
                attributes = node.get("attributes", {})
                
                # 如果名称发生变化，需要重命名节点
                if old_name != new_name:
                    if self.graph_manager.has_node(old_name):
                        # 先获取旧节点的所有连接信息
                        old_data = self.graph_manager.graph.nodes[old_name]
                        predecessors = list(self.graph_manager.graph.predecessors(old_name))
                        successors = list(self.graph_manager.graph.successors(old_name))
                        
                        # 收集边的信息
                        in_edges = []
                        out_edges = []
                        for pred in predecessors:
                            edge_data = self.graph_manager.graph[pred][old_name]
                            in_edges.append((pred, edge_data))
                        for succ in successors:
                            edge_data = self.graph_manager.graph[old_name][succ]
                            out_edges.append((succ, edge_data))
                        
                        # 删除旧节点
                        self.graph_manager.graph.remove_node(old_name)
                        
                        # 添加新节点
                        self.graph_manager.add_node(new_name, node_type, attributes)
                        
                        # 重新创建边
                        for pred, edge_data in in_edges:
                            self.graph_manager.graph.add_edge(pred, new_name, **edge_data)
                        for succ, edge_data in out_edges:
                            self.graph_manager.graph.add_edge(new_name, succ, **edge_data)
                        
                        self.graph_manager.save_graph_to_json()
                        
                        # 使用增量更新
                        if hasattr(self, 'web_view') and self.web_view:
                            self.web_view.update_node_incrementally(old_name, node)
                        
                        print(f"节点重命名成功: {old_name} -> {new_name}")
                    else:
                        print(f"节点不存在: {old_name}")
                else:
                    # 只更新节点属性
                    self.graph_manager.edit_node(old_name, node_type, attributes)
                    
                    # 使用增量更新
                    if hasattr(self, 'web_view') and self.web_view:
                        self.web_view.update_node_incrementally(old_name, node)
                    
                    print(f"节点编辑成功: {old_name}")
            else:
                print("编辑节点时数据不完整")
        except Exception as e:
            print(f"编辑节点错误: {str(e)}")

    @pyqtSlot(str)
    def edit_edge(self, edge_json):
        """编辑边"""
        try:
            edge = json.loads(edge_json)
            if "source" in edge and "target" in edge and "new_relation_type" in edge:
                source = edge["source"]
                target = edge["target"]
                new_relation_type = edge["new_relation_type"]
                self.graph_manager.edit_relationship(source, target, new_relation_type)
                
                # 使用增量更新
                if hasattr(self, 'web_view') and self.web_view:
                    self.web_view.update_edge_incrementally(source, target, new_relation_type)
                
                print(f"关系编辑成功: {source} -> {target} ({new_relation_type})")
            else:
                print("编辑边时数据不完整")
        except Exception as e:
            print(f"编辑边错误: {str(e)}")

    @pyqtSlot(str)
    def save_layout(self, layout_json):
        """保存布局到文件"""
        try:
            layout_data = json.loads(layout_json)
            with open(self.layout_file, 'w', encoding='utf-8') as f:
                json.dump(layout_data, f, ensure_ascii=False, indent=2)
            print(f"布局已保存到: {self.layout_file}")
        except Exception as e:
            print(f"保存布局失败: {str(e)}")

    @pyqtSlot()
    def load_layout(self):
        """加载布局并应用到前端"""
        try:
            if self.layout_file.exists():
                with open(self.layout_file, 'r', encoding='utf-8') as f:
                    layout_data = json.load(f)
                
                # 调用前端的JavaScript函数来应用布局
                layout_json = json.dumps(layout_data)
                script = f"if (typeof window.applyLayoutFromPython === 'function') {{ window.applyLayoutFromPython('{layout_json}'); }}"
                
                # 如果有web view的引用，执行脚本
                if hasattr(self, 'web_view') and self.web_view:
                    self.web_view.page().runJavaScript(script)
                
                print(f"布局已从文件加载: {self.layout_file}")
            else:
                print("没有找到保存的布局文件")
        except Exception as e:
            print(f"加载布局失败: {str(e)}")

    @pyqtSlot()
    def clear_layout(self):
        """清除保存的布局文件"""
        try:
            if self.layout_file.exists():
                self.layout_file.unlink()
                print("布局文件已删除")
            else:
                print("没有找到布局文件")
        except Exception as e:
            print(f"清除布局失败: {str(e)}")

    @pyqtSlot(str)
    def polygon_node_count_result(self, result_json):
        """接收前端返回的多边形区域内节点统计结果"""
        try:
            result = json.loads(result_json)
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(None, "区域统计结果", f"区域内节点数量: {result.get('count', 0)}")
        except Exception as e:
            print(f"统计区域节点数量错误: {str(e)}")

    def set_web_view(self, web_view):
        """设置web view引用，用于执行JavaScript"""
        self.web_view = web_view


# GraphView 增强版 - 支持增量更新
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
            self.is_initialized = False  # 标记是否已初始化

            # WebChannel + Bridge
            self.channel = QWebChannel(self.page())
            self.bridge = Bridge(
                node_detail_widget,
                graph_manager,
                update_callback
            )
            # 设置web view引用到bridge
            self.bridge.set_web_view(self)
            
            self.channel.registerObject("py_obj", self.bridge)
            self.page().setWebChannel(self.channel)
            
            # 页面加载完成后的延迟加载布局
            self.loadFinished.connect(self._on_load_finished)

    def _on_load_finished(self, success):
        """页面加载完成后的回调"""
        if success:
            self.is_initialized = True
            # 页面加载完成后立即尝试加载布局
            QTimer.singleShot(200, self.bridge.load_layout)

    def render(self):
        """渲染图谱数据 - 只在初始化时使用"""
        if self.is_initialized:
            # 如果已经初始化，使用增量更新
            self.update_all_data()
            return
            
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
                "resources": node.get("resources", []),
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

    def update_all_data(self):
        """更新所有数据但保持布局"""
        if not self.is_initialized:
            return
            
        data = self.graph_manager.get_graph_data()
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
                "resources": node.get("resources", []),
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

        # 通过JavaScript更新数据而不重置布局
        script = f"""
        if (typeof updateGraphData === 'function') {{
            updateGraphData({json.dumps(nodes)}, {json.dumps(edges)});
        }}
        """
        self.page().runJavaScript(script)

    def add_node_incrementally(self, node_data):
        """增量添加单个节点"""
        if not self.is_initialized:
            return
            
        # 确定节点颜色
        bg = "#97C2FC"
        node_type = node_data.get("type", "")
        if node_type == "方剂":
            bg = "#FFA07A"
        elif node_type == "药理":
            bg = "#ADD8E6"
        elif node_type == "药材":
            bg = "#98FB98"
        elif node_type == "疾病":
            bg = "#D3D3D3"
            
        vis_node = {
            "id": node_data["label"],
            "label": node_data["label"],
            "type": node_type,
            "resources": node_data.get("resources", []),
            "color": {
                "background": bg,
                "border": "#2B7CE9",
                "highlight": {"background": "#D2E5FF", "border": "#2B7CE9"},
            }
        }
        
        script = f"""
        if (typeof addNodeIncremental === 'function') {{
            addNodeIncremental({json.dumps(vis_node)});
        }}
        """
        self.page().runJavaScript(script)

    def add_edge_incrementally(self, edge_data):
        """增量添加单个边"""
        if not self.is_initialized:
            return
            
        vis_edge = {
            "from": edge_data["from"],
            "to": edge_data["to"],
            "label": edge_data["label"]
        }
        
        script = f"""
        if (typeof addEdgeIncremental === 'function') {{
            addEdgeIncremental({json.dumps(vis_edge)});
        }}
        """
        self.page().runJavaScript(script)

    def remove_node_incrementally(self, node_id):
        """增量删除节点"""
        if not self.is_initialized:
            return
            
        script = f"""
        if (typeof removeNodeIncremental === 'function') {{
            removeNodeIncremental('{node_id}');
        }}
        """
        self.page().runJavaScript(script)

    def remove_edge_incrementally(self, source, target):
        """增量删除边"""
        if not self.is_initialized:
            return
            
        script = f"""
        if (typeof removeEdgeIncremental === 'function') {{
            removeEdgeIncremental('{source}', '{target}');
        }}
        """
        self.page().runJavaScript(script)

    def update_node_incrementally(self, node_id, node_data):
        """增量更新节点"""
        if not self.is_initialized:
            return
            
        script = f"""
        if (typeof updateNodeIncremental === 'function') {{
            updateNodeIncremental('{node_id}', {json.dumps(node_data)});
        }}
        """
        self.page().runJavaScript(script)

    def update_edge_incrementally(self, source, target, new_label):
        """增量更新边"""
        if not self.is_initialized:
            return
            
        script = f"""
        if (typeof updateEdgeIncremental === 'function') {{
            updateEdgeIncremental('{source}', '{target}', '{new_label}');
        }}
        """
        self.page().runJavaScript(script)

    def save_layout_manually(self):
        """手动保存布局的方法，可以从外部调用"""
        script = "if (typeof saveLayout === 'function') { saveLayout(); }"
        self.page().runJavaScript(script)

    def reset_layout_manually(self):
        """手动重置布局的方法，可以从外部调用"""
        script = "if (typeof resetLayout === 'function') { resetLayout(); }"
        self.page().runJavaScript(script)

    def auto_layout_manually(self):
        """手动自动排列的方法，可以从外部调用"""
        script = "if (typeof autoLayout === 'function') { autoLayout(); }"
        self.page().runJavaScript(script)

    def on_view_changed(self, x, y, width, height, zoom):
        if hasattr(self, 'navigator'):
            self.navigator.update_viewport(x, y, width, height, zoom)