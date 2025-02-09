# node_detail_widget.py
from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QTextEdit, QPushButton, QMessageBox
)
import json

class NodeDetailWidget(QWidget):
    def __init__(self, graph_manager, update_callback):
        super().__init__()
        self.graph_manager = graph_manager
        self.update_callback = update_callback
        self.current_node = None
        self.init_ui()

    def init_ui(self):
        self.layout = QFormLayout()

        # 节点名称（不可编辑）
        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        self.layout.addRow("节点名称", self.name_edit)

        # 节点类型
        self.type_edit = QLineEdit()
        self.layout.addRow("节点类型", self.type_edit)

        # 节点属性（JSON格式）
        self.attr_edit = QTextEdit()
        self.attr_edit.setPlaceholderText("输入JSON格式属性...")
        self.layout.addRow("节点属性", self.attr_edit)

        # 保存按钮
        self.save_btn = QPushButton("保存修改")
        self.save_btn.clicked.connect(self.save_changes)
        self.layout.addRow(self.save_btn)

        self.setLayout(self.layout)

    def show_node(self, node_data):
        """显示节点详情"""
        self.current_node = node_data
        # 尝试同时支持 "id" 和 "name" 字段
        node_id = node_data.get("id", node_data.get("name", ""))
        self.name_edit.setText(node_id)
        self.type_edit.setText(node_data.get("type", ""))
        self.attr_edit.setText(json.dumps(node_data.get("attributes", {}), indent=2))

    def save_changes(self):
        """保存修改到图数据"""
        if not self.current_node:
            return

        try:
            new_type = self.type_edit.text().strip()
            new_attr = json.loads(self.attr_edit.toPlainText())

            if not new_type:
                raise ValueError("节点类型不能为空")

            node_id = self.current_node.get("id", self.current_node.get("name"))
            self.graph_manager.edit_node(node_id, new_type, new_attr)

            # 触发更新
            self.update_callback()
            QMessageBox.information(self, "成功", "节点信息已更新")
        except json.JSONDecodeError:
            QMessageBox.critical(self, "错误", "属性必须是有效的JSON格式")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
