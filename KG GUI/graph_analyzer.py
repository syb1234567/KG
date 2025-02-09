# graph_analyzer.py
import networkx as nx
#该模块用于分析网络图的度分布和弱连通分量。
class GraphAnalyzer:
    def __init__(self, graph_data_manager):
        self.graph = graph_data_manager.graph

    def degree_distribution(self):
        """计算各节点的度分布"""
        return {node: degree for node, degree in self.graph.degree()}

    def connected_components(self):
        """
        获取弱连通分量（适用于有向图）。
        如果需要强连通分量，可另行扩展。
        """
        return [list(component) for component in nx.weakly_connected_components(self.graph)]
