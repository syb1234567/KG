import os
import json
import webbrowser

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QScrollArea, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QFrame,
    QGraphicsDropShadowEffect, QSpacerItem, QGroupBox, QSplitter
)

from plugins.multimodal_data_integration_plugin import ResourceCache

class NodeDetailWidget(QWidget):
    def __init__(self, graph_manager, update_callback, lang_manager):
        super().__init__()
        self.graph_manager = graph_manager
        self.update_callback = update_callback
        self.lang_manager = lang_manager
        self.current_node_name = None
        self.setup_styles()
        self.init_ui()

    def setup_styles(self):
        """设置样式表"""
        self.setStyleSheet("""
            /* 主容器样式 */
            NodeDetailWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 2px;
            }
            
            /* 卡片样式 */
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                color: #2c3e50;
                border: 1px solid #e3f2fd;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 3px 8px;
                background-color: #2196f3;
                color: white;
                border-radius: 4px;
                font-size: 14px;
            }
            
            /* 表单标签样式 */
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #34495e;
                margin: 3px 0;
            }
            
            /* 输入框样式 */
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 14px;
                background-color: white;
                selection-background-color: #e3f2fd;
                min-height: 16px;
            }
            
            QLineEdit:focus {
                border-color: #2196f3;
                background-color: #fafafa;
            }
            
            QLineEdit[readOnly="true"] {
                background-color: #f5f5f5;
                color: #666;
                border-color: #d0d0d0;
            }
            
            /* 文本编辑器样式 */
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                font-family: 'Consolas', 'Monaco', monospace;
                background-color: white;
                selection-background-color: #e3f2fd;
            }
            
            QTextEdit:focus {
                border-color: #2196f3;
                background-color: #fafafa;
            }
            
            /* 按钮样式 - 修复字体显示问题 */
            QPushButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:1 #45a049);
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
                padding: 8px 16px;
                min-width: 80px;
                min-height: 28px;
                margin: 3px;
            }
            
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #45a049, stop:1 #3d8b40);
            }
            
            QPushButton:pressed {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3d8b40, stop:1 #2e6b30);
            }
            
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
            
            /* 预览区域样式 */
            QScrollArea {
                border: 1px solid #e3f2fd;
                border-radius: 6px;
                background-color: white;
                padding: 2px;
            }
            
            QScrollArea QWidget {
                background-color: transparent;
            }
            
            QScrollArea QScrollBar:vertical {
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
            }
            
            QScrollArea QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }
            
            QScrollArea QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            
            /* 分组框样式 */
            QFrame[frameShape="4"] {
                color: #bdc3c7;
                margin: 8px 0;
            }
        """)

    def init_ui(self):
        """初始化界面 - 紧凑布局"""
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)
        
        # 添加轻微阴影效果
        self.add_shadow_effect()
        
        # 节点信息卡片 - 紧凑版
        self.create_compact_node_info_card()
        
        # 媒体预览卡片 - 紧凑版
        self.create_compact_media_preview_card()

    def add_shadow_effect(self):
        """添加阴影效果"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.gray)
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def create_compact_node_info_card(self):
        """创建紧凑的节点信息卡片"""
        # 节点信息组框
        info_group = QGroupBox()
        info_group.setTitle("📝 " + self.get_text_by_language("节点信息", "Node Information"))
        info_group.setMaximumHeight(280)  # 限制最大高度
        
        # 表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(15, 20, 15, 15)
        
        # 节点名称 - 紧凑版
        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        self.name_label = QLabel("🏷️ " + self.get_text_by_language("节点名称", "Node Name"))
        form_layout.addRow(self.name_label, self.name_edit)
        
        # 节点类型 - 紧凑版
        self.type_edit = QLineEdit()
        self.type_label = QLabel("📋 " + self.get_text_by_language("节点类型", "Node Type"))
        form_layout.addRow(self.type_label, self.type_edit)
        
        # 节点属性 - 紧凑版
        self.attr_edit = QTextEdit()
        self.attr_edit.setMinimumHeight(80)
        self.attr_edit.setMaximumHeight(120)
        self.attr_edit.setPlaceholderText(self.get_text_by_language("输入 JSON 格式属性...", "Enter JSON format attributes..."))
        self.attr_label = QLabel("⚙️ " + self.get_text_by_language("节点属性", "Node Attributes"))
        form_layout.addRow(self.attr_label, self.attr_edit)
        
        # 保存按钮 - 修复字体显示
        self.save_btn = QPushButton(self.get_text_by_language("保存修改", "Save Changes"))
        self.save_btn.setMinimumHeight(32)
        self.save_btn.clicked.connect(self.save_changes)
        
        # 按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 5, 0, 0)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        
        form_layout.addRow(button_container)
        
        info_group.setLayout(form_layout)
        self.main_layout.addWidget(info_group)

    def create_compact_media_preview_card(self):
        """创建紧凑的媒体预览卡片"""
        # 媒体预览组框
        media_group = QGroupBox()
        media_group.setTitle("🖼️ " + self.get_text_by_language("关联图片", "Related Images"))
        media_group.setMinimumHeight(180)  # 设置最小高度
        
        media_layout = QVBoxLayout()
        media_layout.setContentsMargins(15, 20, 15, 15)
        media_layout.setSpacing(8)
        
        # 预览状态标签 - 紧凑版
        self.preview_status = QLabel()
        self.preview_status.setStyleSheet("""
            QLabel {
                background-color: #e8f5e9;
                border: 1px solid #4caf50;
                border-radius: 4px;
                padding: 6px 10px;
                color: #2e7d32;
                font-size: 13px;
            }
        """)
        self.preview_status.setAlignment(Qt.AlignCenter)
        media_layout.addWidget(self.preview_status)
        
        # 滚动区域 - 紧凑版
        self.media_scroll = QScrollArea()
        self.media_scroll.setWidgetResizable(True)
        self.media_scroll.setMinimumHeight(120)
        
        # 媒体容器
        self.media_container = QWidget()
        self.media_layout = QVBoxLayout(self.media_container)
        self.media_layout.setAlignment(Qt.AlignTop)
        self.media_layout.setSpacing(6)
        self.media_layout.setContentsMargins(8, 8, 8, 8)
        
        self.media_scroll.setWidget(self.media_container)
        media_layout.addWidget(self.media_scroll)
        
        media_group.setLayout(media_layout)
        self.main_layout.addWidget(media_group)

    def get_text_by_language(self, chinese_text, english_text):
        """根据当前语言返回对应文本"""
        try:
            if hasattr(self.lang_manager, 'current_language'):
                if self.lang_manager.current_language == "en":
                    return english_text
                else:
                    return chinese_text
            return chinese_text
        except:
            return chinese_text

    def get_safe_text(self, key, default_chinese):
        """安全获取文本"""
        try:
            if hasattr(self.lang_manager, 'get_text'):
                text = self.lang_manager.get_text(key)
                if text == key:
                    return default_chinese
                return text
            else:
                return default_chinese
        except:
            return default_chinese

    def update_ui_texts(self):
        """更新界面文本"""
        # 更新组框标题
        if hasattr(self, 'main_layout'):
            info_group = self.main_layout.itemAt(0).widget()
            if info_group:
                info_group.setTitle("📝 " + self.get_text_by_language("节点信息", "Node Information"))
            
            media_group = self.main_layout.itemAt(1).widget()
            if media_group:
                media_group.setTitle("🖼️ " + self.get_text_by_language("关联图片", "Related Images"))
        
        # 更新标签文本
        self.name_label.setText("🏷️ " + self.get_text_by_language("节点名称", "Node Name"))
        self.type_label.setText("📋 " + self.get_text_by_language("节点类型", "Node Type"))
        self.attr_label.setText("⚙️ " + self.get_text_by_language("节点属性", "Node Attributes"))
        self.save_btn.setText(self.get_text_by_language("保存修改", "Save Changes"))
        
        # 更新占位符文本
        self.attr_edit.setPlaceholderText(self.get_text_by_language("输入 JSON 格式属性...", "Enter JSON format attributes..."))

    def clear_media_preview(self):
        """清空所有旧的预览控件"""
        for i in reversed(range(self.media_layout.count())):
            item = self.media_layout.itemAt(i)
            if item.layout():
                sublay = item.layout()
                for j in reversed(range(sublay.count())):
                    subitem = sublay.itemAt(j)
                    if subitem.widget():
                        subitem.widget().deleteLater()
            if item.widget():
                item.widget().deleteLater()

    def show_node(self, node_data):
        """展示节点属性并加载关联图片缩略图"""
        # 1. 填充基础信息
        self.current_node_name = node_data.get("id", node_data.get("name", ""))
        self.name_edit.setText(self.current_node_name)
        self.type_edit.setText(node_data.get("type", ""))
        
        # 格式化JSON显示
        try:
            attrs = node_data.get("attributes", {})
            if attrs:
                formatted_json = json.dumps(attrs, indent=2, ensure_ascii=False)
            else:
                formatted_json = "{}"
            self.attr_edit.setText(formatted_json)
        except:
            self.attr_edit.setText(str(node_data.get("attributes", {})))

        # 2. 清空旧的图片预览
        self.clear_media_preview()

        # 3. 取出所有 Image 类型资源
        resources = node_data.get("resources", [])
        images = [r for r in resources if r.get("type") == "Image"]
        
        if not images:
            self.show_no_images_message()
            return

        # 4. 显示图片数量
        count_text = self.get_text_by_language(f"共 {len(images)} 张图片", f"{len(images)} images")
        self.preview_status.setText(f"📊 {count_text}")
        
        # 5. 遍历并展示图片 - 紧凑版
        for i, res in enumerate(images):
            self.create_compact_image_preview_item(res, i + 1)

    def show_no_images_message(self):
        """显示无图片的消息"""
        no_images_text = self.get_text_by_language("暂无关联图片", "No related images")
        self.preview_status.setText(f"📷 {no_images_text}")
        
        # 添加简化的空状态提示
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(10)
        
        # 简化的图标和文本
        icon_label = QLabel("🖼️")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 36px; color: #bdc3c7;")
        
        hint_text = self.get_text_by_language("该节点暂无关联图片", "No related images")
        hint_label = QLabel(hint_text)
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("color: #7f8c8d; font-size: 14px; font-style: italic;")
        
        empty_layout.addWidget(icon_label)
        empty_layout.addWidget(hint_label)
        
        self.media_layout.addWidget(empty_widget)

    def create_compact_image_preview_item(self, resource, index):
        """创建紧凑的图片预览项"""
        path = resource.get("path")
        if not path:
            return
            
        # 创建紧凑的图片项容器
        item_widget = QWidget()
        item_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 6px;
                margin: 2px;
            }
            QWidget:hover {
                border-color: #2196f3;
                background-color: #f8f9ff;
            }
        """)
        
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(8, 6, 8, 6)
        item_layout.setSpacing(10)
        
        # 获取缩略图
        pix = ResourceCache.get_thumbnail(path)
        
        if pix.isNull():
            # 简化的错误显示
            error_icon = QLabel("⚠️")
            error_icon.setStyleSheet("font-size: 22px; color: #f44336;")
            item_layout.addWidget(error_icon)
            
            error_text = self.get_text_by_language(f"无法加载图片 {index}", f"Failed to load image {index}")
            error_label = QLabel(error_text)
            error_label.setStyleSheet("color: #666; font-size: 13px;")
            item_layout.addWidget(error_label)
        else:
            # 紧凑的缩略图
            thumb = QLabel()
            thumb.setPixmap(pix)
            thumb.setFixedSize(50, 50)
            thumb.setScaledContents(True)
            thumb.setCursor(Qt.PointingHandCursor)
            thumb.setStyleSheet("""
                QLabel {
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 1px;
                }
                QLabel:hover {
                    border-color: #2196f3;
                }
            """)
            
            thumb.mouseReleaseEvent = lambda ev, p=path: self.open_full_image(p)
            item_layout.addWidget(thumb)
            
            # 简化的信息显示
            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)
            
            title_text = f"图片 {index}" if self.lang_manager.current_language == "zh" else f"Image {index}"
            title_label = QLabel(title_text)
            title_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
            
            filename = os.path.basename(path)
            if len(filename) > 20:
                filename = filename[:17] + "..."
            file_label = QLabel(filename)
            file_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            
            info_layout.addWidget(title_label)
            info_layout.addWidget(file_label)
            info_layout.addStretch()
            
            item_layout.addLayout(info_layout)
            
            # 紧凑的操作按钮
            open_btn = QPushButton(self.get_text_by_language("查看", "View"))
            open_btn.setFixedSize(50, 24)
            open_btn.setStyleSheet("""
                QPushButton {
                    background: #2196f3;
                    border-radius: 3px;
                    font-size: 12px;
                    padding: 2px 6px;
                    min-width: 40px;
                }
                QPushButton:hover {
                    background: #1976d2;
                }
            """)
            open_btn.clicked.connect(lambda _, p=path: self.open_full_image(p))
            item_layout.addWidget(open_btn)
        
        self.media_layout.addWidget(item_widget)

    def save_changes(self):
        """保存节点类型和属性的修改"""
        if not self.current_node_name:
            return
            
        try:
            new_type = self.type_edit.text().strip()
            new_attr_text = self.attr_edit.toPlainText().strip()
            
            if not new_type:
                error_msg = self.get_text_by_language("节点类型不能为空", "Node type cannot be empty")
                raise ValueError(error_msg)
            
            # 解析JSON属性
            if new_attr_text:
                try:
                    new_attr = json.loads(new_attr_text)
                except json.JSONDecodeError as e:
                    error_msg = self.get_text_by_language(f"JSON格式错误：{str(e)}", f"JSON format error: {str(e)}")
                    raise ValueError(error_msg)
            else:
                new_attr = {}
            
            # 保存按钮状态
            self.save_btn.setText(self.get_text_by_language("保存中...", "Saving..."))
            self.save_btn.setEnabled(False)
            
            # 更新图数据
            self.graph_manager.edit_node(self.current_node_name, new_type, new_attr)
            
            # 延迟恢复按钮状态
            QTimer.singleShot(500, self.restore_save_button)
            
            # 刷新界面
            self.update_callback()
            
            # 显示成功消息
            success_title = self.get_text_by_language("保存成功", "Save Successful")
            success_msg = self.get_text_by_language("节点信息已更新", "Node information updated")
            QMessageBox.information(self, success_title, success_msg)
            
        except Exception as e:
            # 恢复按钮状态
            self.restore_save_button()
            
            # 显示错误消息
            error_title = self.get_text_by_language("保存失败", "Save Failed")
            QMessageBox.critical(self, error_title, str(e))

    def restore_save_button(self):
        """恢复保存按钮状态"""
        self.save_btn.setText(self.get_text_by_language("保存修改", "Save Changes"))
        self.save_btn.setEnabled(True)

    def open_full_image(self, path):
        """打开原图"""
        if os.path.exists(path):
            try:
                webbrowser.open(path)
            except Exception as e:
                error_title = self.get_text_by_language("打开失败", "Open Failed")
                error_msg = self.get_text_by_language(f"无法打开文件：{str(e)}", f"Cannot open file: {str(e)}")
                QMessageBox.warning(self, error_title, error_msg)
        else:
            error_title = self.get_text_by_language("文件不存在", "File Not Found")
            error_msg = self.get_text_by_language(f"文件不存在：{path}", f"File not found: {path}")
            QMessageBox.warning(self, error_title, error_msg)