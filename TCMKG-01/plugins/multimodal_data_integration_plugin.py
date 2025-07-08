# plugins/multimodal_data_integration_plugin.py

import os
import hashlib

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton,
    QFileDialog, QListWidget, QListWidgetItem,
    QMessageBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap

# 可选依赖：PyMuPDF 用于渲染 PDF 首页
try:
    import fitz
    _HAS_FITZ = True
except ImportError:
    _HAS_FITZ = False

# 缓存目录，用于存放生成的缩略图
CACHE_DIR = os.path.expanduser("~/.cache/graph_plugin_multimodal")
os.makedirs(CACHE_DIR, exist_ok=True)


class ResourceCache:
    """本地缓存 & 缩略图生成"""

    @staticmethod
    def get_thumbnail(path: str) -> QPixmap:
        # 根据文件路径生成唯一 hash
        h = hashlib.md5(path.encode("utf-8")).hexdigest()
        thumb_path = os.path.join(CACHE_DIR, f"{h}.png")
        if os.path.exists(thumb_path):
            return QPixmap(thumb_path)

        ext = os.path.splitext(path)[1].lower()
        # PDF -> 用 PyMuPDF 渲染第一页
        if ext == ".pdf" and _HAS_FITZ:
            try:
                doc = fitz.open(path)
                page = doc.load_page(0)
                mat = fitz.Matrix(0.2, 0.2)
                pix = page.get_pixmap(matrix=mat)
                pix.save(thumb_path)
                return QPixmap(thumb_path)
            except Exception:
                pass

        # 其它图片格式
        pix = QPixmap(path)
        if pix.isNull():
            return QPixmap()
        pix = pix.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pix.save(thumb_path)
        return pix


class MultimodalDataDialog(QDialog):
    """插件主界面：选择节点/关系、关联文件、预览缩略图"""

    def __init__(self, graph_manager, parent=None):
        super().__init__(parent)
        self.graph_manager = graph_manager
        self.setWindowTitle("多模态数据整合")
        self.resize(700, 450)

        # 左侧：节点/关系 选择 & 已关联资源 列表
        self.selector = QComboBox()
        self.selector.addItems(self._list_items())
        self.selector.currentIndexChanged.connect(self._load_resources)

        self.res_list = QListWidget()
        self.res_list.itemClicked.connect(self._show_preview)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("选择节点或关系："))
        left_layout.addWidget(self.selector)
        left_layout.addWidget(QLabel("已关联资源："))
        left_layout.addWidget(self.res_list)

        # 右侧：文件选择 & 预览
        self.cb_type = QComboBox()
        self.cb_type.addItems(["Image", "Diagram", "PDF Abstract"])

        self.btn_browse = QPushButton("浏览文件…")
        self.btn_browse.clicked.connect(self._browse_file)

        self.btn_add = QPushButton("添加关联")
        self.btn_add.clicked.connect(self._add_resource)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(QLabel("资源类型："))
        ctrl_layout.addWidget(self.cb_type)
        ctrl_layout.addWidget(self.btn_browse)
        ctrl_layout.addWidget(self.btn_add)

        self.preview_label = QLabel("预览区域")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_layout = QVBoxLayout()
        right_layout.addLayout(ctrl_layout)
        right_layout.addWidget(self.preview_label)

        # 底部：确定／取消
        btn_ok     = QPushButton("确定")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)

        # 整体布局
        main_layout = QHBoxLayout(self)
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 4)
        main_layout.addLayout(btn_layout, 1)

        self._current_file = None
        self._load_resources()

    def _list_items(self):
        items = []
        for n, data in self.graph_manager.graph.nodes(data=True):
            items.append(f"N:{n}")
        for u, v, data in self.graph_manager.graph.edges(data=True):
            items.append(f"E:{u}->{v}")
        return items

    def _load_resources(self):
        self.res_list.clear()
        key = self.selector.currentText()
        kind, ident = key.split(":", 1)
        if kind == "N":
            resources = self.graph_manager.graph.nodes[ident].get("resources", [])
        else:
            src, dst = ident.split("->", 1)
            resources = []
            for u, v, data in self.graph_manager.graph.edges(data=True):
                if u == src and v == dst:
                    resources = data.get("resources", [])
                    break

        for r in resources:
            item = QListWidgetItem(f"{r['type']}: {os.path.basename(r['path'])}")
            item.setData(Qt.UserRole, r)
            self.res_list.addItem(item)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择多模态文件", "", "All Files (*.*)")
        if path:
            self._current_file = path
            pix = ResourceCache.get_thumbnail(path)
            if not pix.isNull():
                self.preview_label.setPixmap(pix)
            else:
                self.preview_label.setText("无法预览此文件")

    def _add_resource(self):
        if not self._current_file:
            QMessageBox.warning(self, "警告", "请先选择文件")
            return
        key = self.selector.currentText()
        kind, ident = key.split(":", 1)
        res = {"path": self._current_file, "type": self.cb_type.currentText()}

        if kind == "N":
            self.graph_manager.graph.nodes[ident].setdefault("resources", []).append(res)
        else:
            src, dst = ident.split("->", 1)
            for u, v, data in self.graph_manager.graph.edges(data=True):
                if u == src and v == dst:
                    data.setdefault("resources", []).append(res)
                    break

        self._current_file = None
        self._load_resources()
        self.preview_label.clear()

    def _show_preview(self, item: QListWidgetItem):
        res = item.data(Qt.UserRole)
        pix = ResourceCache.get_thumbnail(res["path"])
        if not pix.isNull():
            self.preview_label.setPixmap(pix)
        else:
            self.preview_label.setText("无法预览此文件")


class Plugin(QObject):
    """多模态数据整合插件 - 必须包含 Plugin 主类"""

    def __init__(self, graph_manager):
        super().__init__()
        self.graph_manager = graph_manager
        self.name = "多模态数据整合插件"

    def run(self):
        dlg = MultimodalDataDialog(self.graph_manager)
        if dlg.exec_():
            self.graph_manager.save_graph_to_json()
            QMessageBox.information(None, "多模态资源", "资源已关联并保存")
            return "多模态资源关联完成"
        return "已取消多模态资源关联"
