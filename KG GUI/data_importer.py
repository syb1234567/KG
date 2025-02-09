import pandas as pd
import json
from terminology_standardizer import TerminologyStandardizer


class DataImporter:
    def __init__(self, graph_data_manager):
        self.graph_data_manager = graph_data_manager
        self.standardizer = TerminologyStandardizer()

    def import_nodes_from_csv(self, filepath, encoding="GBK"):
        """从 CSV 导入节点数据"""
        try:
            data = pd.read_csv(filepath, encoding=encoding)
        except Exception as e:
            print(f"导入节点数据失败: {str(e)}")
            return

        for _, row in data.iterrows():
            raw_name = row["name"]
            standardized_name = self.standardizer.standardize(raw_name) or raw_name
            node_type = row["type"]
            attributes = {}

            # 处理节点属性
            if "attributes" in row and pd.notna(row["attributes"]):
                try:
                    attributes = json.loads(row["attributes"])
                except Exception:
                    print(f"节点 '{raw_name}' 的属性格式错误，使用空属性")
                    attributes = {}

            # 添加节点到图数据
            self.graph_data_manager.add_node(standardized_name, node_type, attributes)

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
