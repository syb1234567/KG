# plugins/graph_analysis_plugin.py

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem,
    QMessageBox, QInputDialog
)
import networkx as nx
import community


class GraphAnalysisPlugin(QObject):
    """图谱分析插件：提供度数统计、社区发现和路径分析功能。"""
    def __init__(self, graph_manager):
        super().__init__()
        self.name = "图谱分析工具"
        self.graph_manager = graph_manager

    def run(self):
        """插件入口：弹出功能选择菜单。"""
        dlg = QDialog()
        dlg.setWindowTitle(self.name)
        layout = QVBoxLayout(dlg)

        for label, handler in [
            ("节点度数统计", self._degree_centrality),
            ("社区发现分析", self._detect_communities),
            ("路径分析",     self._path_analysis),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        dlg.exec_()

    def _degree_centrality(self):
        G = self._build_nx_graph()
        if not G:
            return
        rows = [(n, d) for n, d in G.degree()]
        self._show_table("节点度数统计", ["节点", "度数"], rows)

    def _detect_communities(self):
        G = self._build_nx_graph()
        if not G:
            return

        partition = community.best_partition(G)
        # 存回原始图（可选）
        for nid, cid in partition.items():
            self.graph_manager.graph.nodes[nid]['community'] = cid

        # 汇总
        comms = {}
        for nid, cid in partition.items():
            comms.setdefault(cid, []).append(nid)

        rows = [
            (cid, len(nodes), ", ".join(nodes[:3]) + ("..." if len(nodes) > 3 else ""))
            for cid, nodes in comms.items()
        ]
        self._show_table("社区分布", ["社区ID", "节点数", "示例节点"], rows)

    def _path_analysis(self):
        G = self._build_nx_graph()
        if not G:
            return

        src, ok1 = QInputDialog.getText(None, self.name, "请输入起始节点名称：")
        if not ok1 or not src.strip():
            return
        dst, ok2 = QInputDialog.getText(None, self.name, "请输入目标节点名称：")
        if not ok2 or not dst.strip():
            return

        try:
            path = nx.shortest_path(G, source=src.strip(), target=dst.strip())
            length = len(path) - 1
            QMessageBox.information(
                None, self.name,
                f"最短路径（共 {length} 步）：\n" + " → ".join(path)
            )
        except nx.NetworkXNoPath:
            QMessageBox.warning(None, self.name, f"节点 “{src}” 与 “{dst}” 之间无可达路径")
        except nx.NodeNotFound as e:
            QMessageBox.warning(None, self.name, str(e))

    def _build_nx_graph(self):
        """从 graph_manager 中构建一个无向 NetworkX 图。"""
        data = self.graph_manager.get_graph_data()
        if not data["nodes"]:
            QMessageBox.warning(None, self.name, "当前图为空，无法执行分析")
            return None

        G = nx.Graph()
        for node in data["nodes"]:
            G.add_node(node["name"])
        for edge in data["edges"]:
            G.add_edge(edge["source"], edge["target"])
        return G

    def _show_table(self, title, headers, rows):
        """在 QTableWidget 中展示分析结果。"""
        dlg = QDialog()
        dlg.setWindowTitle(title)
        dlg.setMinimumSize(500, 300)

        table = QTableWidget(len(rows), len(headers), dlg)
        table.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(val)))

        layout = QVBoxLayout(dlg)
        layout.addWidget(table)
        dlg.exec_()


class Plugin(GraphAnalysisPlugin):
    """Plugin 管理器识别的入口类，保持不变。"""
    pass
