# node_detail_widget.py

import os
import json
import webbrowser

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QScrollArea, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
)

from plugins.multimodal_data_integration_plugin import ResourceCache

class NodeDetailWidget(QWidget):
    def __init__(self, graph_manager, update_callback):
        super().__init__()
        self.graph_manager = graph_manager
        self.update_callback = update_callback
        self.current_node_name = None
        self.init_ui()

    def init_ui(self):
        # 主垂直布局
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # —— 原有表单区 ——
        form_layout = QFormLayout()
        # 节点名称（只读）
        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        form_layout.addRow("节点名称", self.name_edit)
        # 节点类型
        self.type_edit = QLineEdit()
        form_layout.addRow("节点类型", self.type_edit)
        # 节点属性 (JSON)
        self.attr_edit = QTextEdit()
        self.attr_edit.setPlaceholderText("输入 JSON 格式属性...")
        form_layout.addRow("节点属性", self.attr_edit)
        # 保存按钮
        self.save_btn = QPushButton("保存修改")
        self.save_btn.clicked.connect(self.save_changes)
        form_layout.addRow(self.save_btn)

        self.main_layout.addLayout(form_layout)

        # —— 新增：多媒体预览区 ——
        media_label = QLabel("关联图片预览：")
        media_label.setAlignment(Qt.AlignLeft)
        self.main_layout.addWidget(media_label)

        self.media_scroll = QScrollArea()
        self.media_scroll.setWidgetResizable(True)
        self.media_scroll.setMinimumHeight(200)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignTop)
        self.media_layout = container_layout
        self.media_scroll.setWidget(container)
        self.main_layout.addWidget(self.media_scroll)

    def clear_media_preview(self):
        """清空所有旧的预览控件"""
        # 先删除布局中的所有 widget
        for i in reversed(range(self.media_layout.count())):
            item = self.media_layout.itemAt(i)
            # 如果是子布局，先删除它的子 widget
            if item.layout():
                sublay = item.layout()
                for j in reversed(range(sublay.count())):
                    subitem = sublay.itemAt(j)
                    if subitem.widget():
                        subitem.widget().deleteLater()
            # 删除自身 widget（如果有的话）
            if item.widget():
                item.widget().deleteLater()

    def show_node(self, node_data):
        """展示节点属性并加载关联图片缩略图"""
        # 1. 填充基础信息
        self.current_node_name = node_data.get("id", node_data.get("name", ""))
        self.name_edit.setText(self.current_node_name)
        self.type_edit.setText(node_data.get("type", ""))
        self.attr_edit.setText(json.dumps(node_data.get("attributes", {}), indent=2))



        # 2. 清空旧的图片预览
        self.clear_media_preview()

        # 3. 取出所有 Image 类型资源
        resources = node_data.get("resources", [])
        images = [r for r in resources if r.get("type") == "Image"]
        if not images:
            lbl = QLabel("（无关联图片）")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: gray; font-style: italic;")
            self.media_layout.addWidget(lbl)
            return

        # 4. 遍历并展示
        for res in images:
            path = res.get("path")
            pix = ResourceCache.get_thumbnail(path)
            # 如果缩略图加载失败，显示错误文字
            if pix.isNull():
                err = QLabel(f"无法加载：{os.path.basename(path)}")
                self.media_layout.addWidget(err)
                continue

            # 水平布局：缩略图 + 打开按钮
            hbox = QHBoxLayout()
            # 缩略图控件
            thumb = QLabel()
            thumb.setPixmap(pix)
            thumb.setFixedSize(pix.size())
            thumb.setCursor(Qt.PointingHandCursor)
            # 点击缩略图打开原图
            thumb.mouseReleaseEvent = lambda ev, p=path: self.open_full_image(p)
            hbox.addWidget(thumb)

            # “打开原图”按钮
            btn = QPushButton("打开原图")
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn.clicked.connect(lambda _, p=path: self.open_full_image(p))
            hbox.addWidget(btn)

            self.media_layout.addLayout(hbox)

    def save_changes(self):
        """保存节点类型和属性的修改"""
        if not self.current_node_name:
            return
        try:
            new_type = self.type_edit.text().strip()
            new_attr = json.loads(self.attr_edit.toPlainText())
            if not new_type:
                raise ValueError("节点类型不能为空")
            # 更新图数据
            self.graph_manager.edit_node(self.current_node_name, new_type, new_attr)
            self.update_callback()
            QMessageBox.information(self, "成功", "节点信息已更新")
        except json.JSONDecodeError:
            QMessageBox.critical(self, "错误", "属性必须是有效的 JSON 格式")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def open_full_image(self, path):
        """打开原图：调用系统默认查看器"""
        if os.path.exists(path):
            webbrowser.open(path)
        else:
            QMessageBox.warning(self, "错误", f"文件不存在：{path}")
