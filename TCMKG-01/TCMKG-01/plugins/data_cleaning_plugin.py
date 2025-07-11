import os
import json
import csv
import re
import networkx as nx
from pathlib import Path
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QDialogButtonBox, QCheckBox
)


class DataCleaningDialog(QDialog):
    """数据清洗配置对话框，支持内置操作、自定义正则和映射表，以及模板管理"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据清洗配置")
        self.resize(600, 500)

        # 主布局
        layout = QVBoxLayout(self)

        # 模板管理区
        tpl_layout = QHBoxLayout()
        tpl_layout.addWidget(QLabel("模板："))
        self.cb_templates = QComboBox()
        tpl_layout.addWidget(self.cb_templates)
        self.btn_load_tpl = QPushButton("加载")
        tpl_layout.addWidget(self.btn_load_tpl)
        self.btn_save_tpl = QPushButton("另存模板")
        tpl_layout.addWidget(self.btn_save_tpl)
        layout.addLayout(tpl_layout)
        layout.addWidget(QFrame(frameShape=QFrame.HLine))

        # 内置清洗选项
        self.chk_remove_null = QCheckBox("删除空属性")
        self.chk_normalize_names = QCheckBox("标准化名称")
        self.chk_remove_isolated = QCheckBox("删除孤立节点")
        self.chk_deduplicate = QCheckBox("去重边")
        layout.addWidget(self.chk_remove_null)
        layout.addWidget(self.chk_normalize_names)
        layout.addWidget(self.chk_remove_isolated)
        layout.addWidget(self.chk_deduplicate)
        layout.addWidget(QFrame(frameShape=QFrame.HLine))

        # 自定义正则规则表
        layout.addWidget(QLabel("自定义正则规则："))
        self.tbl_regex = QTableWidget(0, 3)
        self.tbl_regex.setHorizontalHeaderLabels(["字段", "正则模式", "替换为"])
        layout.addWidget(self.tbl_regex)
        btn_h = QHBoxLayout()
        self.btn_add_regex = QPushButton("添加规则")
        self.btn_edit_regex = QPushButton("编辑规则")
        self.btn_del_regex = QPushButton("删除规则")
        btn_h.addWidget(self.btn_add_regex)
        btn_h.addWidget(self.btn_edit_regex)
        btn_h.addWidget(self.btn_del_regex)
        layout.addLayout(btn_h)
        layout.addWidget(QFrame(frameShape=QFrame.HLine))

        # 映射表管理
        layout.addWidget(QLabel("映射表（CSV/JSON）："))
        btn_map_h = QHBoxLayout()
        self.btn_load_map = QPushButton("上传映射表")
        self.lbl_map_file = QLabel("未加载")
        btn_map_h.addWidget(self.btn_load_map)
        btn_map_h.addWidget(self.lbl_map_file)
        layout.addLayout(btn_map_h)
        layout.addWidget(QFrame(frameShape=QFrame.HLine))

        # 确认/取消按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(btn_box)

        # 信号连接
        self.btn_load_tpl.clicked.connect(self.load_template)
        self.btn_save_tpl.clicked.connect(self.save_template)
        self.btn_add_regex.clicked.connect(self.add_regex_rule)
        self.btn_edit_regex.clicked.connect(self.edit_regex_rule)
        self.btn_del_regex.clicked.connect(self.delete_regex_rule)
        self.btn_load_map.clicked.connect(self.load_mapping_file)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

        # 模板目录及初始化
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        os.makedirs(self.template_dir, exist_ok=True)
        self.load_templates_list()
        self.mapping = []

    def load_templates_list(self):
        self.cb_templates.clear()
        names = [f[:-5] for f in os.listdir(self.template_dir) if f.endswith('.json')]
        self.cb_templates.addItems([''] + names)

    def load_template(self):
        name = self.cb_templates.currentText()
        if not name:
            return
        path = os.path.join(self.template_dir, f"{name}.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载模板失败: {e}")
            return
        # 内置选项
        builtin = data.get("builtin", [])
        self.chk_remove_null.setChecked("remove_null" in builtin)
        self.chk_normalize_names.setChecked("normalize_names" in builtin)
        self.chk_remove_isolated.setChecked("remove_isolated_nodes" in builtin)
        self.chk_deduplicate.setChecked("deduplicate_edges" in builtin)
        # 正则规则
        self.tbl_regex.setRowCount(0)
        for rule in data.get("regex", []):
            row = self.tbl_regex.rowCount()
            self.tbl_regex.insertRow(row)
            self.tbl_regex.setItem(row, 0, QTableWidgetItem(rule.get("field", "")))
            self.tbl_regex.setItem(row, 1, QTableWidgetItem(rule.get("pattern", "")))
            self.tbl_regex.setItem(row, 2, QTableWidgetItem(rule.get("replacement", "")))
        # 映射表
        self.mapping = data.get("mapping", []) or []
        self.lbl_map_file.setText(f"已加载 {len(self.mapping)} 条映射" if self.mapping else "未加载")

    def save_template(self):
        name, ok = QInputDialog.getText(self, "模板名称", "输入模板名称：")
        if not ok or not name.strip():
            return
        opts = self.get_selected_options()
        data = {
            "builtin": opts["builtin"],
            "regex": opts["regex"],
            "mapping": opts["mapping"]
        }
        path = os.path.join(self.template_dir, f"{name}.json")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", "模板已保存")
            self.load_templates_list()
            idx = self.cb_templates.findText(name)
            if idx >= 0:
                self.cb_templates.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存模板失败: {e}")

    def add_regex_rule(self):
        field, ok1 = QInputDialog.getText(self, "字段", "字段名：")
        if not ok1 or not field:
            return
        pattern, ok2 = QInputDialog.getText(self, "正则", "正则模式：")
        if not ok2:
            return
        repl, ok3 = QInputDialog.getText(self, "替换", "替换为：")
        if not ok3:
            return
        row = self.tbl_regex.rowCount()
        self.tbl_regex.insertRow(row)
        self.tbl_regex.setItem(row, 0, QTableWidgetItem(field))
        self.tbl_regex.setItem(row, 1, QTableWidgetItem(pattern))
        self.tbl_regex.setItem(row, 2, QTableWidgetItem(repl))

    def edit_regex_rule(self):
        row = self.tbl_regex.currentRow()
        if row < 0:
            return
        field = self.tbl_regex.item(row, 0).text()
        pattern = self.tbl_regex.item(row, 1).text()
        repl = self.tbl_regex.item(row, 2).text()
        new_field, ok1 = QInputDialog.getText(self, "字段", "字段名：", text=field)
        if not ok1:
            return
        new_pattern, ok2 = QInputDialog.getText(self, "正则", "正则模式：", text=pattern)
        if not ok2:
            return
        new_repl, ok3 = QInputDialog.getText(self, "替换", "替换为：", text=repl)
        if not ok3:
            return
        self.tbl_regex.setItem(row, 0, QTableWidgetItem(new_field))
        self.tbl_regex.setItem(row, 1, QTableWidgetItem(new_pattern))
        self.tbl_regex.setItem(row, 2, QTableWidgetItem(new_repl))

    def delete_regex_rule(self):
        row = self.tbl_regex.currentRow()
        if row < 0:
            return
        self.tbl_regex.removeRow(row)

    def load_mapping_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "上传映射表", "",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            if path.lower().endswith('.json'):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 如果整个文件是模板结构，取其中的 mapping
                if isinstance(data, dict) and 'mapping' in data and isinstance(data['mapping'], list):
                    mapping = data['mapping']
                # 如果直接是映射列表
                elif isinstance(data, list):
                    mapping = data
                else:
                    raise ValueError("JSON 文件必须是映射列表，或包含 'mapping' 字段")
            else:
                # CSV 文件: 期待每行 old,new
                temp = {}
                with open(path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            temp[row[0]] = row[1]
                mapping = [{"field": "name", "map": temp}]
            # 赋值并更新界面
            self.mapping = mapping
            self.lbl_map_file.setText(f"已加载 {os.path.basename(path)} ({len(mapping)} 条映射)")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载映射表失败: {e}")
            # 保持原有 mapping 不变，避免赋值出错导致崩溃

    def get_selected_options(self):
        builtin = []
        if self.chk_remove_null.isChecked():
            builtin.append("remove_null")
        if self.chk_normalize_names.isChecked():
            builtin.append("normalize_names")
        if self.chk_remove_isolated.isChecked():
            builtin.append("remove_isolated_nodes")
        if self.chk_deduplicate.isChecked():
            builtin.append("deduplicate_edges")
        # 正则规则
        regex = []
        for row in range(self.tbl_regex.rowCount()):
            field = self.tbl_regex.item(row, 0).text()
            pattern = self.tbl_regex.item(row, 1).text()
            repl = self.tbl_regex.item(row, 2).text()
            regex.append({"field": field, "pattern": pattern, "replacement": repl})
        # 映射表
        mapping = getattr(self, 'mapping', []) or []
        return {"builtin": builtin, "regex": regex, "mapping": mapping}


class DataCleaner:
    @staticmethod
    def remove_null(G: nx.Graph):
        """删除所有属性中值为空的键"""
        for u, data in G.nodes(data=True):
            attrs = data.get('attributes', {})
            data['attributes'] = {k: v for k, v in attrs.items() if v not in [None, "", []]}

    @staticmethod
    def normalize_names(G: nx.Graph):
        """统一节点名称格式（例如去除首尾空格，大小写标准化等）"""
        mapping = {u: u.strip().title() for u in G.nodes()}
        nx.relabel_nodes(G, mapping, copy=False)

    @staticmethod
    def remove_isolated_nodes(G: nx.Graph):
        """移除度为0的孤立节点"""
        for node in list(G.nodes()):
            if G.degree(node) == 0:
                G.remove_node(node)

    @staticmethod
    def deduplicate_edges(G: nx.Graph):
        """去除相同源-目标-类型的多重边"""
        seen = set()
        for u, v, data in list(G.edges(data=True)):
            key = (u, v, data.get("relation_type"))
            if key in seen:
                G.remove_edge(u, v)
            else:
                seen.add(key)

    @staticmethod
    def apply_regex_rules(G: nx.Graph, rules: list):
        """根据正则规则对节点名称或属性值进行批量替换"""
        for u, data in list(G.nodes(data=True)):
            # 名称替换
            name = u
            for r in rules:
                if r['field'] == 'name':
                    name = re.sub(r['pattern'], r['replacement'], name)
            if name != u:
                nx.relabel_nodes(G, {u: name}, copy=False)
            # 属性替换
            attrs = data.get('attributes', {})
            for r in rules:
                fld = r['field']
                if fld in attrs:
                    attrs[fld] = re.sub(r['pattern'], r['replacement'], str(attrs[fld]))
            data['attributes'] = attrs

    @staticmethod
    def apply_mapping_rules(G: nx.Graph, mappings: list):
        """根据映射表替换节点名称或属性值"""
        for mp in mappings:
            field = mp.get('field')
            map_dict = mp.get('map', {})
            for u, data in list(G.nodes(data=True)):
                # 名称映射
                if field == 'name' and u in map_dict:
                    nx.relabel_nodes(G, {u: map_dict[u]}, copy=False)
                # 属性映射
                attrs = data.get('attributes', {})
                if field in attrs and attrs[field] in map_dict:
                    attrs[field] = map_dict[attrs[field]]
                data['attributes'] = attrs


class Plugin(QObject):
    """插件入口，弹出对话框并执行清洗操作"""

    def __init__(self, graph_manager):
        super().__init__()
        self.graph_manager = graph_manager
        self.name = "数据清洗插件"

    def run(self):
        dialog = DataCleaningDialog()
        if dialog.exec_() != QDialog.Accepted:
            return
        opts = dialog.get_selected_options()
        G = self.graph_manager.get_graph()
        # 执行内置清洗
        for op in opts['builtin']:
            getattr(DataCleaner, op)(G)
        # 自定义正则
        if opts['regex']:
            DataCleaner.apply_regex_rules(G, opts['regex'])
        # 映射表处理
        if opts['mapping']:
            DataCleaner.apply_mapping_rules(G, opts['mapping'])
        # 保存结果
        self.graph_manager.save_graph_to_json()
        QMessageBox.information(None, "完成", "数据清洗已完成")
