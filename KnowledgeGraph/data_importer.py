import json
import chardet
import pandas as pd

class DataImporter:
    def __init__(self, graph_data_manager):
        self.graph_data_manager = graph_data_manager

    def detect_encoding(self, file_path):
        """检测文件编码"""
        with open(file_path, "rb") as f:
            result = chardet.detect(f.read())
            encoding = result.get("encoding", "utf-8")
            return encoding

    def read_csv_with_fallback(self, file_path, primary_encoding):
        """
        尝试使用 primary_encoding 解码和常见分隔符，如果失败则尝试其它编码和分隔符
        优先使用指定编码，若失败则尝试常用编码集和分隔符集
        """
        encodings_to_try = [primary_encoding, "GB18030", "GBK", "UTF-8", "latin-1"]
        delimiters_to_try = [',', '\t', ';']

        # 尝试各种编码和分隔符
        for enc in encodings_to_try:
            for sep in delimiters_to_try:
                try:
                    print(f"Trying to read CSV with encoding: {enc} and delimiter: {repr(sep)}")
                    # 使用engine='python'和on_bad_lines='skip'（需要pandas>=1.3）
                    # 如果pandas版本较低可尝试error_bad_lines=False
                    df = pd.read_csv(file_path, encoding=enc, sep=sep, engine='python', on_bad_lines='skip')
                    print(f"Successfully read CSV with encoding: {enc} and delimiter: {repr(sep)}")
                    return df
                except UnicodeDecodeError as e:
                    print(f"Failed with encoding {enc} sep {repr(sep)} (UnicodeDecodeError): {e}")
                except pd.errors.ParserError as pe:
                    print(f"Parser error with encoding {enc} sep {repr(sep)}: {pe}")
                except Exception as ex:
                    print(f"Unexpected error with encoding {enc} sep {repr(sep)}: {ex}")

        # 如果全部失败，最后尝试使用latin-1和python engine跳过行
        print("All common encodings and delimiters failed, trying latin-1 with python engine and skipping bad lines")
        df = pd.read_csv(file_path, encoding='latin-1', sep=',', engine='python', on_bad_lines='skip')
        return df

    def import_data_from_json(self, json_filepath):
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for node in data.get("nodes", []):
            self.graph_data_manager.add_node(
                name=node["name"],
                node_type=node.get("type", "Undefined"),
                attributes=node.get("attributes", {})
            )

        for edge in data.get("edges", []):
            self.graph_data_manager.add_relationship(
                source_name=edge["source"],
                target_name=edge["target"],
                relation_type=edge.get("relation_type", "RELATED_TO")
            )

    def import_data_from_csv(self, csv_filepath, node_file=True):
        encoding = self.detect_encoding(csv_filepath)
        print(f"Detected file encoding: {encoding}")

        # 尝试用检测到的编码，如果失败则用备用编码和分隔符
        df = self.read_csv_with_fallback(csv_filepath, encoding)

        # 检查必须列是否存在
        if node_file:
            required_columns = ["name", "type", "attributes"]
            for col in required_columns:
                if col not in df.columns:
                    print(f"Warning: {col} column not found in node file. Please check file format.")
        else:
            required_columns = ["source", "target", "relation_type"]
            for col in required_columns:
                if col not in df.columns:
                    print(f"Warning: {col} column not found in relationship file. Please check file format.")

        if node_file:
            # 节点文件应有 name, type, attributes 列
            for _, row in df.iterrows():
                attributes = {}
                if "attributes" in df.columns and pd.notna(row.get("attributes")):
                    try:
                        attributes = json.loads(row["attributes"])
                    except json.JSONDecodeError:
                        attributes = {}
                self.graph_data_manager.add_node(
                    name=row["name"],
                    node_type=row.get("type", "Undefined"),
                    attributes=attributes
                )
        else:
            # 关系文件应有 source, target, relation_type 列
            for _, row in df.iterrows():
                self.graph_data_manager.add_relationship(
                    source_name=row["source"],
                    target_name=row["target"],
                    relation_type=row.get("relation_type", "RELATED_TO")
                )

    def import_data_from_excel(self, excel_filepath, sheet_name='Sheet1', node_file=True):
        df = pd.read_excel(excel_filepath, sheet_name=sheet_name)
        if node_file:
            for _, row in df.iterrows():
                attributes = {}
                if "attributes" in df.columns and pd.notna(row.get("attributes")):
                    try:
                        attributes = json.loads(row["attributes"])
                    except json.JSONDecodeError:
                        attributes = {}
                self.graph_data_manager.add_node(
                    name=row["name"],
                    node_type=row.get("type", "Undefined"),
                    attributes=attributes
                )
        else:
            for _, row in df.iterrows():
                self.graph_data_manager.add_relationship(
                    source_name=row["source"],
                    target_name=row["target"],
                    relation_type=row.get("relation_type", "RELATED_TO")
                )

    def import_data(self, file_path, file_type, node_file=True):
        if file_type == 'json':
            self.import_data_from_json(file_path)
        elif file_type == 'csv':
            self.import_data_from_csv(file_path, node_file=node_file)
        elif file_type in ['xlsx', 'xls']:
            self.import_data_from_excel(file_path, node_file=node_file)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
