# graph_visualizer.py
import json
#该模块用于将图数据保存为json文件
class GraphVisualizer:
    def __init__(self, graph_data_manager):
        self.graph_data_manager = graph_data_manager

    def get_graph_data(self):
        nodes = self.graph_data_manager.get_all_nodes()
        edges = self.graph_data_manager.get_all_relationships()
        return {"nodes": nodes, "edges": edges}

    def save_graph_as_json(self, filepath):
        graph_data = self.get_graph_data()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=4)
