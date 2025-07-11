from PyQt5.QtWidgets import QPushButton, QMessageBox, QTableWidgetItem
from dialogs.base_dialog import BaseTableDialog

from core.plugin_manager import PluginLoadError
import json

class NodeEditDialog(BaseTableDialog):
    def __init__(self, columns, data, parent=None):
        super().__init__("节点批量编辑", columns, parent)
        self.columns = columns  # 记录列定义
        self.attr_col_idx = columns.index("attributes")  # 获取属性列索引
        self._init_ui(data)

    def _init_ui(self, data):
        # 初始化表格数据
        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, col in enumerate(self.columns):
                item = QTableWidgetItem(str(row_data.get(col, '')))
                self.table.setItem(row_idx, col_idx, item)

        # 添加验证按钮
        self.validate_btn = QPushButton("验证JSON格式")
        self.layout.addWidget(self.validate_btn)
        self.validate_btn.clicked.connect(self._validate_json)

    def _validate_json(self):
        """验证所有attributes列的JSON格式"""
        error_rows = []
        for row in range(self.table.rowCount()):
            try:
                json.loads(self.table.item(row, 2).text())
            except:
                error_rows.append(row + 1)

        if error_rows:
            QMessageBox.warning(self, "格式错误", f"以下行JSON格式错误: {error_rows}")
        else:
            QMessageBox.information(self, "验证通过", "所有JSON格式正确")

    def get_modified_data(self):
        """返回修改后的数据"""
        data = []
        for row in range(self.table.rowCount()):
            row_data = {}
            for col, col_name in enumerate(self.columns):
                item = self.table.item(row, col)
                row_data[col_name] = item.text() if item else ""
            data.append(row_data)
        return data