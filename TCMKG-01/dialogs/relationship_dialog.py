from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
from dialogs.base_dialog import BaseTableDialog



class RelationEditDialog(BaseTableDialog):
    def __init__(self, graph_manager, data, parent=None):
        # 关系列配置（不含属性）
        relation_columns = ["source", "target", "relation_type"]
        super().__init__("关系批量编辑", relation_columns, parent)

        self.graph_manager = graph_manager
        self._init_data(data)

    def _init_data(self, data):
        """初始化关系数据"""
        self.table.setRowCount(len(data))
        for row_idx, rel_data in enumerate(data):
            self._set_item(row_idx, 0, rel_data.get("source", ""))
            self._set_item(row_idx, 1, rel_data.get("target", ""))
            self._set_item(row_idx, 2, rel_data.get("relation_type", ""))

    def _set_item(self, row, col, value):
        """安全设置表格项"""
        item = QTableWidgetItem(str(value))
        self.table.setItem(row, col, item)

    def validate_data(self):
        """自定义关系验证逻辑"""
        error_messages = []
        for row in range(self.table.rowCount()):
            # 检查源节点
            source = self.table.item(row, 0).text()
            if not source:
                error_messages.append(f"行 {row + 1}: 源节点不能为空")
            elif not self.graph_manager.node_exists(source):
                error_messages.append(f"行 {row + 1}: 源节点不存在")

            # 检查目标节点
            target = self.table.item(row, 1).text()
            if not target:
                error_messages.append(f"行 {row + 1}: 目标节点不能为空")
            elif not self.graph_manager.node_exists(target):
                error_messages.append(f"行 {row + 1}: 目标节点不存在")

            # 检查关系类型
            rel_type = self.table.item(row, 2).text()
            if not rel_type.strip():
                error_messages.append(f"行 {row + 1}: 关系类型不能为空")

        if error_messages:
            QMessageBox.warning(self, "验证失败", "\n".join(error_messages))
            return False
        return True

    def get_modified_relations(self):
        """获取结构化关系数据"""
        return [{
            "source": self.table.item(row, 0).text(),
            "target": self.table.item(row, 1).text(),
            "relation_type": self.table.item(row, 2).text()
        } for row in range(self.table.rowCount())]