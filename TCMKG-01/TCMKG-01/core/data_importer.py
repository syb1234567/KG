import pandas as pd
import json

class DataImporter:
    def __init__(self, graph_data_manager):
        self.graph_data_manager = graph_data_manager

    def import_nodes_from_csv(self, filepath, encoding="GBK"):
        """从 CSV 导入节点数据（移除标准化处理）"""
        try:
            data = pd.read_csv(filepath, encoding=encoding)
            for _, row in data.iterrows():
                self.graph_data_manager.add_node(
                    row["name"],
                    row["type"],
                    json.loads(row["attributes"]) if "attributes" in row else {}
                )
        except Exception as e:
            raise ImportError(f"CSV导入失败: {str(e)}")

    def import_relationships_from_csv(self, filepath, encoding="GBK"):
        """从 CSV 导入关系数据"""
        try:
            data = pd.read_csv(filepath, encoding=encoding)
        except Exception as e:
            print(f"导入关系数据失败: {str(e)}")
            return

        for _, row in data.iterrows():
            source = row["source"]
            target = row["target"]
            relation_type = row["relation_type"]

            # 确保 source 和 target 节点都存在
            if not self.graph_data_manager.has_node(source):
                print(f"源节点 '{source}' 不存在，跳过此关系")
                continue
            if not self.graph_data_manager.has_node(target):
                print(f"目标节点 '{target}' 不存在，跳过此关系")
                continue

            # 添加关系到图数据
            self.graph_data_manager.add_relationship(source, target, relation_type)
