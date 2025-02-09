# table_dialog.py
import csv
import json

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QDialogButtonBox, QSizePolicy
from PyQt5.QtWidgets import QFileDialog, \
    QMessageBox


class TableEditDialog(QDialog):
    """通用表格编辑对话框"""

    def __init__(self, columns, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("表格编辑")
        self.layout = QVBoxLayout()

        # 表格设置
        self.table = QTableWidget()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(data))
        self.layout.addWidget(self.table)

        for i, row_data in enumerate(data):
            for j, col in enumerate(columns):

                self.table.setItem(i, j, QTableWidgetItem(str(row_data.get(col, ''))))

        # 操作按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)
        self.resize(600, 400)

    def get_data(self):
        """获取表格数据"""
        data = []
        for row in range(self.table.rowCount()):
            row_data = {}
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item is not None:
                    row_data[self.table.horizontalHeaderItem(col).text()] = item.text().strip()
            if any(row_data.values()):
                data.append(row_data)
        return data


    def export_to_file(self):
        """导出为文件"""
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "JSON Files (*.json);;CSV Files (*.csv)",
                                              options=options)

        if file:
            data = self.get_data()

            if file.endswith(".json"):
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            elif file.endswith(".csv"):
                with open(file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
            else:
                QMessageBox.warning(self, "错误", "仅支持导出为 JSON 或 CSV 格式文件")
