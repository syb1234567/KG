import sys
import os
import csv
import json
from pathlib import Path

import pandas as pd
import chardet
import networkx as nx

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QListWidget, QMenu, QStatusBar,
    QSplitter, QDialog, QFormLayout, QLineEdit, QTextEdit
)
from PyQt5.QtCore import QTimer, Qt

from core.graph_data_manager import GraphDataManager
from core.data_importer import DataImporter
from core.plugin_manager import PluginManager, PluginLoadError
from dialogs.node_dialog import NodeEditDialog
from dialogs.plugin_dialog import PluginManageDialog
from dialogs.node_detail_widget import NodeDetailWidget
from dialogs.relationship_dialog import RelationEditDialog
from ui.graph_view import GraphView

import rdflib
from rdflib.namespace import RDF, RDFS, OWL



def clean_data(data):
    """清理数据中的 None 值，替换为适当的默认值"""
    if isinstance(data, dict):
        return {key: clean_data(value) for key, value in data.items() if value is not None}
    elif isinstance(data, list):
        return [clean_data(item) for item in data if item is not None]
    else:
        return data

#桥接类

#主窗口类 其中包含了图谱显示，节点详情显示，插件列表显示，工具栏，状态栏，批量编辑功能等功能
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化核心组件
        self.graph_manager = GraphDataManager()
        self.data_importer = DataImporter(self.graph_manager)
        self.plugin_manager = PluginManager(self.graph_manager)

        project_root = Path(__file__).parent.parent
        self.plugin_manager.plugin_dir = project_root / "plugins"
        self.plugin_manager.scan_plugin_dir()


        self.setWindowTitle("中医知识图谱")
        self.setGeometry(100, 100, 1600, 900)
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

    def init_toolbar(self):
        # 主工具栏
        toolbar = self.addToolBar("主工具栏")

        # 文件菜单
        file_menu = QMenu()
        file_menu.addAction("导入数据", self.import_data)
        file_menu.addAction("保存数据", self.save_data)
        file_menu.addAction("导出数据", self.export_data)
        file_menu.addAction("保存 JSON-LD", self.save_data_as_jsonld)
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

        #插件菜单
        plugin_menu = QMenu()
        plugin_menu.addAction("加载插件", self.load_plugin)
        plugin_menu.addAction("管理插件", self.manage_plugins)
        plugin_btn = QPushButton("插件")
        plugin_btn.setMenu(plugin_menu)
        toolbar.addWidget(plugin_btn)

    def open_batch_edit_dialog(self):
        dialog = NodeEditDialog(
            columns=["name", "type", "attributes"],
            data=self.graph_manager.get_all_nodes(),
            parent=self
        )
        if dialog.exec_():  # 如果用户点击了“确定”
            edited_data = dialog.get_data()  # 获取用户编辑的数据

            for node in edited_data:
                try:
                    # 使用 try-except 处理 JSON 格式错误
                    attributes = json.loads(node["attributes"]) if node["attributes"] else {}
                except json.JSONDecodeError:
                    # 如果格式错误，使用默认值 {}，避免程序崩溃
                    attributes = {}
                    QMessageBox.critical(self, "错误",
                                         f"第{edited_data.index(node) + 1}行属性不是有效的JSON格式，已使用默认值")

                try:
                    # 逐个调用 edit_node，传递正确的参数
                    self.graph_manager.edit_node(node["name"], node["type"], attributes)
                except ValueError as e:
                    # 如果节点不存在，捕获异常并显示错误
                    QMessageBox.critical(self, "错误", f"节点编辑失败: {str(e)}")
                    return

            self.safe_update()  # 强制刷新图谱界面

    def open_batch_edit_relationship_dialog(self):
        # 获取所有关系数据（示例格式）

        dialog = RelationEditDialog(
            graph_manager=self.graph_manager,
            data=self.graph_manager.get_all_relationships(),
            parent=self
        )

        if dialog.exec_():
            try:
                # 获取修改后的关系列表
                modified_rels = dialog.get_modified_relations()

                # 转换为图管理器需要的格式
                updates = [{
                    "original": {  # 原始关系标识
                        "source": rel["source"],
                        "target": rel["target"],
                        "type": rel["relation_type"]
                    },
                    "new_data": {  # 新数据
                        "new_source": rel["source"],  # 如果允许修改源/目标需要调整
                        "new_target": rel["target"],
                        "new_type": rel["relation_type"]
                    }
                } for rel in modified_rels]

                self.graph_manager.batch_edit_relationships(updates)
                self.safe_update()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"关系更新失败: {str(e)}")

    def save_data_as_jsonld(self):
        """保存图数据为 JSON-LD 格式文件"""
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "保存 JSON-LD 文件",
            "",
            "JSON-LD Files (*.jsonld)",
            options=options,
        )
        if not filepath:
            return
        try:
            self.graph_manager.save_graph_to_jsonld(filepath)
            self.status_bar.showMessage("JSON-LD 文件保存成功", 3000)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存 JSON-LD 文件失败: {str(e)}")

    def load_plugin(self):
        dialog = PluginManageDialog(
            mode="load",
            columns=["path", "enabled"],
            data=[],
            parent=self
        )
        dialog.setWindowTitle("批量加载插件")

        if dialog.exec_():
            # 获取用户输入的插件路径
            plugins_to_load = [p for p in dialog.get_data() if p["path"]]

            success_count = 0
            for plugin in plugins_to_load:
                try:
                    # 调用插件管理器加载插件
                    self.plugin_manager.load_plugin(
                        plugin_path=Path(plugin["path"]),
                        enabled=plugin["enabled"]
                    )
                    success_count += 1
                except Exception as e:
                    QMessageBox.warning(self, "加载失败", f"无法加载 {plugin['path']}:\n{str(e)}")

            # 刷新插件列表
            self.populate_plugins()
            QMessageBox.information(
                self, "加载完成",
                f"成功加载 {success_count}/{len(plugins_to_load)} 个插件"
            )

    def manage_plugins(self):
        dialog = PluginManageDialog(
            mode="manage",
            columns=["name", "path", "enabled"],
            data=[p.__dict__ for p in self.plugin_manager.plugins],
            parent=self
        )

        dialog.setWindowTitle("插件管理")

        if dialog.exec_():
            updated = dialog.get_data()
            # 确保 enabled 是 bool
            for p in updated:
                p["enabled"] = True if p["enabled"] in (True, "True", "true", 1, "1") else False

            # 然后再
            states = {p["name"]: p["enabled"] for p in updated}
            self.plugin_manager.update_plugin_states(states)

            current = {p["name"] for p in updated}
            for plugin in self.plugin_manager.plugins[:]:
                if plugin.name not in current:
                    self.plugin_manager.unload_plugin(plugin.name)

            self.populate_plugins()
            QMessageBox.information(self, "成功", "插件配置已更新")

    def init_web_view(self):
        # 改成不写关键字，按顺序传参：
        self.graph_view = GraphView(
            graph_manager=self.graph_manager,
            node_detail_widget=self.node_detail,
            update_callback=self.safe_update
        )

        self.left_layout.addWidget(self.graph_view)
        self.graph_view.render()

    def safe_update(self):
        QTimer.singleShot(0, self.graph_view.render)

    def populate_plugins(self):
        """将加载的插件名称显示到右侧列表中"""
        self.plugin_list.clear()
        for plugin in self.plugin_manager.plugins:
            if hasattr(plugin, "name"):
                self.plugin_list.addItem(plugin.name)



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

    def export_data(self):
        """导出知识图谱数据（支持JSON、CSV、GraphML、RDF、OWL格式）"""
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(self, "保存文件", "",
                                              "JSON Files (*.json);;CSV Files (*.csv);;GraphML Files (*.graphml);;RDF Files (*.rdf);;OWL Files (*.owl)",
                                              options=options)

        if file:
            data = self.graph_manager.get_graph_data()  # 获取当前的图数据

            # 根据文件后缀判断导出的文件格式
            try:
                if file.endswith(".json"):
                    with open(file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                elif file.endswith(".csv"):
                    self.export_to_csv(file, data)
                elif file.endswith(".graphml"):
                    self.export_to_graphml(file, data)
                elif file.endswith(".rdf"):
                    self.export_to_rdf(file, data)
                elif file.endswith(".owl"):
                    self.export_to_owl(file, data)
                else:
                    QMessageBox.warning(self, "错误", "不支持的文件格式")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def export_to_csv(self, file, data):
        """导出为 CSV 格式（包括节点和关系）"""
        nodes_data = data["nodes"]
        edges_data = data["edges"]

        try:
            with open(file, 'w', encoding='utf-8', newline='') as f:
                # 写入节点数据
                node_writer = csv.DictWriter(f, fieldnames=nodes_data[0].keys())
                node_writer.writeheader()
                node_writer.writerows(nodes_data)

                # 在节点数据后加一个分隔行（可选）
                f.write("\n")

                # 写入关系数据
                edge_writer = csv.DictWriter(f, fieldnames=edges_data[0].keys())
                edge_writer.writeheader()
                edge_writer.writerows(edges_data)

            QMessageBox.information(self, "成功", "CSV 文件导出成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出 CSV 文件失败: {str(e)}")

    def export_to_graphml(self, file, data):
        try:
            # GraphDataManager 内部保存了 actual networkx 图对象为 .graph
            nx.write_graphml(self.graph_manager.graph, file)
            QMessageBox.information(self, "成功", "GraphML 文件导出成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出 GraphML 文件失败: {str(e)}")

    def export_to_rdf(self, file, data):
        """导出为 RDF 格式"""
        g = rdflib.Graph()

        # 添加命名空间
        namespace = rdflib.Namespace("http://example.org/graph#")
        g.bind("ex", namespace)

        # 将节点和关系转换为 RDF 数据
        for node in data["nodes"]:
            node_uri = namespace[node["name"]]
            g.add((node_uri, RDF.type, RDFS.Class))
            g.add((node_uri, RDFS.label, rdflib.Literal(node["name"])))
            if "type" in node:
                g.add((node_uri, namespace["type"], rdflib.Literal(node["type"])))

        for edge in data["edges"]:
            source_uri = namespace[edge["source"]]
            target_uri = namespace[edge["target"]]
            relation_uri = namespace[edge["relation_type"]]

            g.add((source_uri, relation_uri, target_uri))

        try:
            g.serialize(destination=file, format="rdfxml")  # 导出为 RDF/XML 格式
            QMessageBox.information(self, "成功", "RDF 文件导出成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出 RDF 文件失败: {str(e)}")

    def export_to_owl(self, file, data):
        """导出为 OWL 格式"""
        g = rdflib.Graph()

        # 添加命名空间
        namespace = rdflib.Namespace("http://example.org/graph#")
        g.bind("ex", namespace)

        # 创建 OWL 本体（添加类和实例）
        for node in data["nodes"]:
            node_uri = namespace[node["name"]]
            g.add((node_uri, RDF.type, OWL.Class))
            g.add((node_uri, RDFS.label, rdflib.Literal(node["name"])))
            if "type" in node:
                g.add((node_uri, namespace["type"], rdflib.Literal(node["type"])))

        for edge in data["edges"]:
            source_uri = namespace[edge["source"]]
            target_uri = namespace[edge["target"]]
            relation_uri = namespace[edge["relation_type"]]

            g.add((source_uri, relation_uri, target_uri))

        try:
            g.serialize(destination=file, format="xml")  # 导出为 OWL 格式
            QMessageBox.information(self, "成功", "OWL 文件导出成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出 OWL 文件失败: {str(e)}")

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
