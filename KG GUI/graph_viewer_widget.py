# graph_viewer_widget.py
# 功能：使用 PyQtGraph 绘制图谱（纯 Python 实现）
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import networkx as nx
import numpy as np


class GraphViewerWidget(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 添加 ViewBox 并锁定宽高比例
        self.view = self.addViewBox()
        self.view.setAspectLocked()
        # 创建 GraphItem 用于绘图
        self.graph_item = pg.GraphItem()
        self.view.addItem(self.graph_item)

    def update_view(self, graph_data):
        """
        更新图谱显示。
        graph_data 为字典，包含 "nodes"（列表，每个节点至少含 "name"、"type"）和
        "edges"（列表，每个关系至少含 "source" 和 "target"）。
        """
        # 使用 NetworkX 构建图（此处转换为无向图用于布局计算）
        G = nx.Graph()
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        for node in nodes:
            G.add_node(node["name"], node_type=node.get("type", ""))
        for edge in edges:
            # 仅添加在节点集合中存在的边
            if edge["source"] in G and edge["target"] in G:
                G.add_edge(edge["source"], edge["target"])
        if len(G.nodes()) == 0:
            return

        # 计算节点布局（弹簧算法）
        pos = nx.spring_layout(G, scale=200, center=(0, 0))
        pos_array = np.array([pos[n] for n in G.nodes()])
        node_index = {node: i for i, node in enumerate(G.nodes())}
        adj = np.array([[node_index[u], node_index[v]] for u, v in G.edges()])
        size = np.array([20 for _ in range(len(G.nodes()))])
        symbols = ['o' for _ in range(len(G.nodes()))]

        # 简单设置颜色，根据节点类型分配不同颜色
        brushes = []
        type_color = {}
        colors = [(100, 150, 200), (200, 150, 100), (150, 200, 100), (100, 200, 150)]
        next_color = 0
        for node in G.nodes():
            node_type = G.nodes[node].get("node_type", "")
            if node_type not in type_color:
                type_color[node_type] = colors[next_color % len(colors)]
                next_color += 1
            brushes.append(pg.mkBrush(type_color[node_type]))

        self.graph_item.setData(pos=pos_array, adj=adj, size=size,
                                symbol=symbols, symbolBrush=brushes)
