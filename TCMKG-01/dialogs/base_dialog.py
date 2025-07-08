from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QHeaderView,
    QDialogButtonBox, QScrollArea
)


class BaseTableDialog(QDialog):
    def __init__(self, title, columns, parent=None):
        super().__init__(parent)

        # 基础配置
        self.setWindowTitle(title)
        self.columns = columns

        # 初始化布局
        self.layout = QVBoxLayout(self)

        # 创建带滚动条的表格区域
        self.table = QTableWidget()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.table)
        self.layout.addWidget(self.scroll_area, stretch=1)

        # 添加标准按钮组
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def _on_accept(self):
        """统一确认处理"""
        if self.validate_data():
            self.accept()

    def validate_data(self):
        """供子类重写的验证方法"""
        return True

    def get_data(self):
        """标准数据获取接口"""
        data = []
        for row in range(self.table.rowCount()):
            row_data = {}
            for col, col_name in enumerate(self.columns):
                item = self.table.item(row, col)
                row_data[col_name] = item.text() if item else ""
            data.append(row_data)
        return data