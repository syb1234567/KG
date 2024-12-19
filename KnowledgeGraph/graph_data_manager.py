import networkx as nx
import json
import os

class GraphDataManager:
    def __init__(self, storage_path):
        """
        初始化图数据库管理器
        :param storage_path: 图数据库存储路径，存储为 JSON 格式
        """
        self._storage_path = storage_path
        self._graph = nx.Graph()  # 或 nx.DiGraph()，取决于图的类型（有向或无向）

        # 如果存储路径存在，加载现有数据
        if os.path.exists(self._storage_path):
            self.load_graph_from_json()
        else:
            print(f"[GraphDataManager] No existing graph data found at {self._storage_path}. Starting with an empty graph.")

    def close(self):
        """
        关闭图数据库连接，保存图数据
        """
        self.save_graph_to_json()
        print("[GraphDataManager] Graph data saved and connection closed.")

    # ------------------- 节点操作 -------------------
    def add_node(self, name, node_type, attributes=None):
        """
        添加节点
        :param name: 节点名称
        :param node_type: 节点类型
        :param attributes: 节点属性
        """
        print(f"[GraphDataManager] Adding node: {name}, type: {node_type}, attributes: {attributes}")
        self._graph.add_node(name, type=node_type, attributes=attributes or {})
        self.save_graph_to_json()
        print("[GraphDataManager] Node added successfully.")
        print("[GraphDataManager] Current nodes:", self.get_all_nodes())

    def get_all_nodes(self):
        """
        获取所有节点
        """
        return [{"name": node, "type": data["type"], "attributes": data["attributes"]}
                for node, data in self._graph.nodes(data=True)]

    def update_node(self, name, node_type=None, attributes=None):
        """
        更新节点信息
        """
        if name in self._graph:
            print(f"[GraphDataManager] Updating node: {name}")
            if node_type:
                self._graph.nodes[name]["type"] = node_type
            if attributes:
                self._graph.nodes[name]["attributes"] = attributes
            self.save_graph_to_json()
            print("[GraphDataManager] Node updated successfully.")
        else:
            print(f"[GraphDataManager] Node {name} does not exist. Cannot update.")

    def delete_node(self, name):
        """
        删除节点及相关关系
        """
        if name in self._graph:
            print(f"[GraphDataManager] Deleting node: {name}")
            self._graph.remove_node(name)
            self.save_graph_to_json()
            print("[GraphDataManager] Node deleted successfully.")
        else:
            print(f"[GraphDataManager] Node {name} does not exist. Cannot delete.")

    # ------------------- 关系操作 -------------------
    def add_relationship(self, source_name, target_name, relation_type):
        """
        添加节点之间的关系
        """
        print(f"[GraphDataManager] Adding relationship: {source_name} -> {target_name}, type: {relation_type}")
        if source_name in self._graph and target_name in self._graph:
            self._graph.add_edge(source_name, target_name, relation_type=relation_type)
            self.save_graph_to_json()
            print("[GraphDataManager] Relationship added successfully.")
        else:
            print(f"[GraphDataManager] Cannot add relationship. One of the nodes ({source_name}, {target_name}) does not exist.")
        print("[GraphDataManager] Current edges:", self.get_all_relationships())

    def get_all_relationships(self):
        """
        获取所有关系
        """
        return [
            {"source": source, "target": target, "relation_type": data["relation_type"]}
            for source, target, data in self._graph.edges(data=True)
        ]

    def delete_relationship(self, source_name, target_name):
        """
        删除节点之间的关系
        """
        if self._graph.has_edge(source_name, target_name):
            print(f"[GraphDataManager] Deleting relationship: {source_name} - {target_name}")
            self._graph.remove_edge(source_name, target_name)
            self.save_graph_to_json()
            print("[GraphDataManager] Relationship deleted successfully.")
        else:
            print(f"[GraphDataManager] Relationship between {source_name} and {target_name} does not exist.")

    # ------------------- 辅助方法 -------------------
    def save_graph_to_json(self):
        """
        将图数据保存为 JSON 格式
        """
        graph_data = {
            "nodes": [
                {"name": node, "type": data["type"], "attributes": data["attributes"]}
                for node, data in self._graph.nodes(data=True)
            ],
            "edges": [
                {"source": source, "target": target, "relation_type": data["relation_type"]}
                for source, target, data in self._graph.edges(data=True)
            ]
        }
        with open(self._storage_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=4)
        print(f"[GraphDataManager] Graph saved to {self._storage_path}.")

    def load_graph_from_json(self):
        """
        从 JSON 文件加载图数据
        """
        print(f"[GraphDataManager] Loading graph from JSON file: {self._storage_path}")
        with open(self._storage_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

        # 清空当前图，然后加载数据
        self._graph.clear()

        # 加载节点
        for node in graph_data.get("nodes", []):
            self._graph.add_node(node["name"], type=node.get("type", "Undefined"),
                                 attributes=node.get("attributes", {}))

        # 加载边（关系）
        for edge in graph_data.get("edges", []):
            self._graph.add_edge(edge["source"], edge["target"], relation_type=edge.get("relation_type", "RELATED_TO"))

        print("[GraphDataManager] Graph loaded successfully.")
        print("[GraphDataManager] Current nodes:", self.get_all_nodes())
        print("[GraphDataManager] Current edges:", self.get_all_relationships())
