from flask import jsonify

class GraphVisualizer:
    def __init__(self, data_manager):
        """
        初始化可视化模块
        """
        self.data_manager = data_manager

    def get_graph_data(self, max_nodes=None):
        """
        获取整个知识图谱数据，格式化为前端可用的 JSON 数据
        :param max_nodes: 限制返回的最大节点数，避免过载
        :return: JSON 格式的图谱数据
        """
        # 获取所有节点和关系
        nodes = self.data_manager.get_all_nodes()
        relationships = self.data_manager.get_all_relationships()

        # 如果设置了最大节点数，则截取
        if max_nodes:
            nodes = nodes[:max_nodes]

        # 转换节点为前端格式
        node_map = {node["name"]: {"id": node["name"], "name": node["name"], "type": node["type"], "attributes": node["attributes"]} for node in nodes}

        # 转换关系为前端格式
        edges = []
        for rel in relationships:
            if rel["source"] in node_map and rel["target"] in node_map:  # 确保关系中的节点在返回的节点列表中
                edges.append({"source": rel["source"], "target": rel["target"], "type": rel["type"]})

        # 返回 JSON 数据
        return jsonify({"nodes": list(node_map.values()), "edges": edges})

    def filter_graph_data(self, node_type=None, max_nodes=None):
        """
        按条件筛选知识图谱数据
        :param node_type: 节点类型（如 "药材", "方剂"）
        :param max_nodes: 限制返回的最大节点数
        :return: JSON 格式的筛选后的图谱数据
        """
        # 获取所有节点和关系
        nodes = self.data_manager.get_all_nodes()
        relationships = self.data_manager.get_all_relationships()

        # 筛选节点
        filtered_nodes = [node for node in nodes if not node_type or node["type"] == node_type]

        # 如果设置了最大节点数，则截取
        if max_nodes:
            filtered_nodes = filtered_nodes[:max_nodes]

        # 转换节点为前端格式
        node_map = {node["name"]: {"id": node["name"], "name": node["name"], "type": node["type"], "attributes": node["attributes"]} for node in filtered_nodes}

        # 筛选关系，仅保留节点间的关系
        edges = []
        for rel in relationships:
            if rel["source"] in node_map and rel["target"] in node_map:
                edges.append({"source": rel["source"], "target": rel["target"], "type": rel["type"]})

        # 返回 JSON 数据
        return jsonify({"nodes": list(node_map.values()), "edges": edges})


