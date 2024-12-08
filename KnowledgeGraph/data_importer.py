from neo4j import GraphDatabase
import json
import pandas as pd

class DataImporter:
    def __init__(self, data_manager):
        """
        初始化数据导入模块
        """
        self.data_manager = data_manager

    def import_from_word(self, file_path):
        """
        从 Word 文件导入数据
        """
        try:
            document = Document(file_path)


            for table in document.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    if len(cells) >= 5:
                        source_name, source_type, attributes, relation_type, target_name = cells
                        source_id = self._get_or_create_node(source_name, source_type, attributes)
                        target_id = self._get_or_create_node(target_name, "节点类型未定义")
                        self.data_manager.add_relationship(source_id, target_id, relation_type)
            print("Word 文件数据导入成功！")
        except Exception as e:
            print(f"导入 Word 文件时发生错误：{e}")

    def import_from_json(self, file_path):
        """
        从 JSON 文件导入数据
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for node in data.get("nodes", []):
                    cleaned_node = self._clean_node_data(node)
                    self._get_or_create_node(cleaned_node["name"], cleaned_node["type"], cleaned_node.get("attributes"))
                for relation in data.get("relationships", []):
                    source_id = self._get_node_id_by_name(relation["source"])
                    target_id = self._get_node_id_by_name(relation["target"])
                    if source_id and target_id:
                        self.data_manager.add_relationship(source_id, target_id, relation["type"])
            print("JSON 文件数据导入成功！")
        except Exception as e:
            print(f"导入 JSON 文件时发生错误：{e}")

    def import_from_excel(self, file_path):
        """
        从 Excel 文件导入数据
        """
        try:
            # 使用 pandas 读取 Excel 文件
            df = pd.read_excel(file_path, engine='openpyxl')

            for index, row in df.iterrows():
                source_name = row['节点名称']
                source_type = row['节点类型']
                attributes = row['属性']
                relation_type = row['关系类型']
                target_name = row['目标节点']

                # 添加源节点
                source_id = self._get_or_create_node(source_name, source_type, attributes)

                # 添加目标节点
                target_id = self._get_or_create_node(target_name, "节点类型未定义")

                # 添加关系
                self.data_manager.add_relationship(source_id, target_id, relation_type)

            print("Excel 文件数据导入成功！")
        except Exception as e:
            print(f"导入 Excel 文件时发生错误：{e}")

    def _get_or_create_node(self, name, node_type, attributes=None):
        """
        查询节点是否存在，不存在则创建并返回节点 ID
        """
        existing_node = self.data_manager.get_node_by_name(name)
        if existing_node:
            return existing_node["id"]
        # 如果没有找到节点，创建新的节点
        return self.data_manager.add_node(name, node_type, attributes)

    def _get_node_id_by_name(self, name):
        """
        根据名称查找节点 ID
        """
        node = self.data_manager.get_node_by_name(name)
        if node:
            return node["id"]
        return None

    def _clean_node_data(self, node_data):
        """
        清理节点数据，去除无关字段，只保留 id, label 和属性
        """
        cleaned_node = {
            "name": node_data.get("label"),
            "type": node_data.get("type", "未知类型"),
            "attributes": node_data.get("properties", {})
        }
        return cleaned_node


