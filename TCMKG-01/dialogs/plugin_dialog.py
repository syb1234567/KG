from PyQt5.QtWidgets import QPushButton, QCheckBox, QHBoxLayout, QTableWidgetItem, QFileDialog
from dialogs.base_dialog import BaseTableDialog
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QFileDialog


class PluginManageDialog(BaseTableDialog):
    def __init__(self, mode, columns, data, parent=None):
        title = "加载插件" if mode == "load" else "管理插件"
        super().__init__(title, columns, parent)
        self.mode = mode
        self._init_ui(data)

    def _init_ui(self, data):
        # 初始化操作按钮
        btn_layout = QHBoxLayout()

        if self.mode == "load":
            self.browse_btn = QPushButton("浏览文件")
            self.browse_btn.clicked.connect(self._browse_plugins)
            btn_layout.addWidget(self.browse_btn)

        self.del_btn = QPushButton("删除选中行")
        self.del_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.del_btn)

        self.layout.addLayout(btn_layout)

        # 填充数据
        self._populate_data(data)

    def _populate_data(self, data, QTableWidgetItem=None):
        self.table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, col in enumerate(self.columns):
                if col == "enabled":
                    checkbox = QCheckBox()
                    checkbox.setChecked(row_data.get(col, False))
                    self.table.setCellWidget(row_idx, col_idx, checkbox)
                else:
                    self.table.setItem(row_idx, col_idx,
                                  QTableWidgetItem(str(row_data.get(col, ''))))

    def _browse_plugins(self):
        """实现文件浏览功能"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择插件文件",
            "",
            "Python Files (*.py)"
        )
        if files:
            self.table.setRowCount(len(files))
            for row, path in enumerate(files):
                self.table.setItem(row, 0, QTableWidgetItem(path))
                checkbox = QCheckBox()
                checkbox.setChecked(True)
                self.table.setCellWidget(row, 1, checkbox)

    # plugin_dialog.py 中，替换 BaseTableDialog.get_data 调用
    def get_data(self):
        data = []
        for row in range(self.table.rowCount()):
            row_data = {}
            for col, col_name in enumerate(self.columns):
                if col_name == "enabled":
                    widget = self.table.cellWidget(row, col)
                    row_data[col_name] = bool(widget.isChecked()) if widget else False
                else:
                    item = self.table.item(row, col)
                    row_data[col_name] = item.text() if item else ""
            data.append(row_data)
        return data
