import networkx as nx
import json
from collections import deque
import contextlib

class GraphDataManager:
    def __init__(self, json_path='graph_data.json'):
        self.graph = nx.DiGraph()
        self.undo_stack = deque(maxlen=50)
        self.redo_stack = deque(maxlen=50)
        self.json_path = json_path
        self._current_version = 0
        self.load_graph_from_json()

    def _create_snapshot(self):
        """创建当前图数据的快照"""
        self._current_version += 1
        return {
            "nodes": list(self.graph.nodes(data=True)),
            "edges": list(self.graph.edges(data=True)),
            "version": self._current_version
        }

    def _apply_snapshot(self, snapshot):
        """应用快照恢复图数据"""
        self.graph.clear()
        for node, data in snapshot["nodes"]:
            self.graph.add_node(node, **data)
        for u, v, data in snapshot["edges"]:
            self.graph.add_edge(u, v, **data)

    def load_graph_from_json(self):
        """从 JSON 文件加载图数据"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.graph.clear()
                for node in data["nodes"]:
                    self.graph.add_node(
                        node["name"],
                        type=node["type"],
                        attributes=node.get("attributes", {}),
                        resources=node.get("resources", [])
                    )
                for edge in data["edges"]:
                    self.graph.add_edge(
                        edge["source"],
                        edge["target"],
                        relation_type=edge["relation_type"],
                        resources = edge.get("resources", [])
                    )
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save_graph_to_json(self):
        """将当前图数据保存到 JSON 文件"""
        data = {
            "nodes": [
                {
                    "name": node,
                    "type": data["type"],
                    "attributes": data.get("attributes", {}),
                    "resources": data.get("resources", [])
                } for node, data in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "relation_type": data["relation_type"],
                    "resources": data.get("resources", [])
                } for u, v, data in self.graph.edges(data=True)
            ]
        }
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def graph_to_jsonld(self):
        """将当前图数据转换为 JSON-LD 格式数据"""
        # 定义 JSON-LD 上下文，可根据实际需要调整 URI
        context = {
            "name": "http://schema.org/name",
            "type": "http://schema.org/additionalType",
            "attributes": "http://schema.org/additionalProperty",
            "relatedTo": {
                "@id": "http://schema.org/relatedLink",
                "@container": "@list"
            }
        }
        # 构造一个节点映射，先把每个节点构造成基本数据
        nodes_ld = {}
        for node, data in self.graph.nodes(data=True):
            nodes_ld[node] = {
                "@id": node,
                "name": node,
                "type": data.get("type", ""),
                "attributes": data.get("attributes", {})
                # "relatedTo" 将在下面添加
            }

        # 遍历每条边，为源节点添加关联信息
        for source, target, data in self.graph.edges(data=True):
            # 创建关系对象，包含目标节点 id 和关系类型信息
            relation = {
                "@id": target,
                "relation_type": data.get("relation_type", "")
            }
            # 如果源节点已有 relatedTo 属性，则追加
            if "relatedTo" in nodes_ld[source]:
                nodes_ld[source]["relatedTo"].append(relation)
            else:
                nodes_ld[source]["relatedTo"] = [relation]

        # 组合所有节点为 @graph 的数组
        jsonld_data = {
            "@context": context,
            "@graph": list(nodes_ld.values())
        }
        return jsonld_data

    def save_graph_to_jsonld(self, filepath=None):
        """将当前图数据保存为 JSON-LD 格式文件"""
        if filepath is None:
            filepath = "graph_data.jsonld"
        jsonld_data = self.graph_to_jsonld()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(jsonld_data, f, ensure_ascii=False, indent=4)

    def add_node(self, name, node_type, attributes):
        """添加或更新节点"""
        snapshot = self._create_snapshot()
        self.undo_stack.append(snapshot)
        if self.graph.has_node(name):
            self.graph.nodes[name]['type'] = node_type
            self.graph.nodes[name]['attributes'] = attributes
        else:
            self.graph.add_node(name, type=node_type, attributes=attributes)
        self.redo_stack.clear()
        self.save_graph_to_json()  # 确保节点添加后保存到文件

    def delete_node(self, name):
        """删除指定节点"""
        snapshot = self._create_snapshot()
        self.undo_stack.append(snapshot)
        self.graph.remove_node(name)
        self.redo_stack.clear()
        self.save_graph_to_json()  # 确保节点删除后保存到文件

    def add_relationship(self, source, target, relation_type):
        """添加一条关系"""
        snapshot = self._create_snapshot()
        self.undo_stack.append(snapshot)
        self.graph.add_edge(source, target, relation_type=relation_type)
        self.redo_stack.clear()
        self.save_graph_to_json()  # 确保关系添加后保存到文件

    def delete_relationship(self, source, target):
        """删除指定关系"""
        snapshot = self._create_snapshot()
        self.undo_stack.append(snapshot)
        self.graph.remove_edge(source, target)
        self.redo_stack.clear()
        self.save_graph_to_json()  # 确保关系删除后保存到文件

    def edit_node(self, name, new_type, new_attributes):
        """编辑已有节点的信息"""
        snapshot = self._create_snapshot()
        self.undo_stack.append(snapshot)
        if name in self.graph.nodes:
            self.graph.nodes[name]['type'] = new_type
            self.graph.nodes[name]['attributes'] = new_attributes
        else:
            raise ValueError(f"节点 '{name}' 不存在")
        self.redo_stack.clear()
        self.save_graph_to_json()  # 确保节点编辑后保存到文件

    def edit_relationship(self, source, target, new_relation_type):
        """编辑已有关系的信息"""
        snapshot = self._create_snapshot()
        self.undo_stack.append(snapshot)
        if self.graph.has_edge(source, target):
            self.graph.edges[source, target]['relation_type'] = new_relation_type
        else:
            raise ValueError(f"关系 {source} -> {target} 不存在")
        self.redo_stack.clear()
        self.save_graph_to_json()  # 确保关系编辑后保存到文件

    def batch_edit_relationships(self, updates):
        """批量编辑关系"""
        snapshot = self._create_snapshot()  # 创建当前快照
        self.undo_stack.append(snapshot)  # 将快照加入撤销栈

        for (source, target), new_data in updates.items():
            if self.graph.has_edge(source, target):
                # 如果关系存在，更新关系类型
                self.graph[source][target].update(new_data)
            else:
                print(f"关系 {source} -> {target} 不存在")

        self.redo_stack.clear()  # 清空重做栈
        self.save_graph_to_json()  # 保存图数据到文件

    def get_all_nodes(self):
        """返回所有节点数据"""
        return [
            {
                "name": node,
                "type": data["type"],
                "attributes": data.get("attributes", {}),
                "resources": data.get("resources", [])
            } for node, data in self.graph.nodes(data=True)
        ]

    def get_all_relationships(self):
        """返回所有关系数据"""
        return [
            {
                "source": u,
                "target": v,
                "relation_type": data["relation_type"],
                "resources": data.get("resources", [])
            } for u, v, data in self.graph.edges(data=True)
        ]

    def get_graph_data(self):
        """返回完整的图数据"""
        return {
            "nodes": self.get_all_nodes(),
            "edges": self.get_all_relationships()
        }

    def undo(self):
        """撤销上一步操作"""
        if len(self.undo_stack) > 0:
            snapshot = self.undo_stack.pop()
            self.redo_stack.append(self._create_snapshot())
            self._apply_snapshot(snapshot)
            return True
        return False

    def redo(self):
        """重做撤销的操作"""
        if len(self.redo_stack) > 0:
            snapshot = self.redo_stack.pop()
            self.undo_stack.append(self._create_snapshot())
            self._apply_snapshot(snapshot)
            return True
        return False

    def standardize_node_name(self, input_name):
        """标准化单个节点名称"""
        return self.standardizer.standardize(input_name)

    def batch_update_nodes(self, old_name, new_name):
        """批量更新节点名称（用于自动标准化）"""
        if not self.graph.has_node(old_name):
            return False
        data = self.graph.nodes[old_name]
        self.graph.add_node(new_name, **data)
        for predecessor in list(self.graph.predecessors(old_name)):
            edge_data = self.graph[predecessor][old_name]
            self.graph.add_edge(predecessor, new_name, **edge_data)
        for successor in list(self.graph.successors(old_name)):
            edge_data = self.graph[old_name][successor]
            self.graph.add_edge(new_name, successor, **edge_data)
        self.graph.remove_node(old_name)
        return True

    def auto_standardize(self):
        """自动标准化所有节点名称"""
        for node in list(self.graph.nodes()):
            standardized = self.standardizer.standardize(node)
            if standardized and standardized != node:
                self.batch_update_nodes(node, standardized)

    def has_node(self, node_name):
        """检查节点是否存在"""
        return self.graph.has_node(node_name)
