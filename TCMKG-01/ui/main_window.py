import sys
import os
import csv
import json
from pathlib import Path

import pandas as pd
import chardet
import networkx as nx

# WebEngine 环境修复 - 必须在PyQt导入前
os.environ['QTWEBENGINE_DISABLE_SANDBOX'] = '1'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu --no-sandbox --disable-software-rasterizer'

from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QListWidget, QMenu, QStatusBar,
    QSplitter, QDialog, QFormLayout, QLineEdit, QTextEdit,
    QLabel, QTextBrowser, QStackedWidget, QApplication  # 添加了QLabel, QTextBrowser, QStackedWidget
)
from PyQt5.QtCore import QTimer, Qt, QUrl

# 其余导入保持不变
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from core.graph_data_manager import GraphDataManager
from core.data_importer import DataImporter
from core.plugin_manager import PluginManager, PluginLoadError
from dialogs.node_dialog import NodeEditDialog
from dialogs.plugin_dialog import PluginManageDialog
from dialogs.node_detail_widget import NodeDetailWidget
from dialogs.relationship_dialog import RelationEditDialog
from ui.graph_view import GraphView
from LanguageManager import  LanguageManager
import rdflib
from rdflib.namespace import RDF, RDFS, OWL



def clean_data(data):
    """清理数据中的 None 值，替换为适当的默认值"""
    if isinstance(data, dict):
        return {key: clean_data(value) for key, value in data.items() if value is not None}
    elif isinstance(data, list):
        return [clean_data(item) for item in data if item is not None]
    else:
        return data

# 主窗口类 - 增加国际化支持
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化语言管理器
        self.lang_manager = LanguageManager()

        # 初始化核心组件
        self.graph_manager = GraphDataManager()
        self.data_importer = DataImporter(self.graph_manager)
        self.plugin_manager = PluginManager(self.graph_manager)

        project_root = Path(__file__).parent.parent
        self.plugin_manager.plugin_dir = project_root / "plugins"
        self.plugin_manager.scan_plugin_dir()

        self.setGeometry(100, 100, 1600, 900)
        self.init_ui()
        self.init_web_view()
        
        self.populate_plugins()
        self.update_window_title()
    def update_window_title(self):
        """更新窗口标题"""
        self.setWindowTitle(self.lang_manager.get_text("window_title"))

    def init_ui(self):
        # 主窗口布局
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # 左侧图谱显示区域
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)

        # 右侧面板（分为节点详情与插件列表）
        self.right_splitter = QSplitter(Qt.Vertical)
        
        
        self.node_detail = NodeDetailWidget(self.graph_manager, self.safe_update, self.lang_manager)
        
        self.plugin_list = QListWidget()
        self.plugin_list.setMinimumHeight(150)
        self.plugin_list.itemDoubleClicked.connect(self.run_plugin)
        self.right_splitter.addWidget(self.node_detail)
        self.right_splitter.addWidget(self.plugin_list)
        self.right_splitter.setSizes([400, 200])

        # 整体分割布局
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([1000, 400])

        self.main_layout.addWidget(self.main_splitter)

        # 初始化工具栏与状态栏
        self.init_toolbar()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
    def init_toolbar(self):
        """增强版工具栏 - 包含显示模式控制和语言切换"""
        # 主工具栏
        toolbar = self.addToolBar(self.lang_manager.get_text("file_menu"))
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 5px;
            }
            QPushButton {
                background-color: white;
                border: 1px solid #ccc;
                padding: 8px 12px;
                margin: 2px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
            }
        """)

        # 文件菜单
        self.file_menu = QMenu()
        self.file_menu.addAction(self.lang_manager.get_text("import_data"), self.import_data)
        self.file_menu.addAction(self.lang_manager.get_text("save_data"), self.save_data)
        self.file_menu.addAction(self.lang_manager.get_text("export_data"), self.export_data)
        self.file_menu.addAction(self.lang_manager.get_text("save_jsonld"), self.save_data_as_jsonld)
        self.file_btn = QPushButton(self.lang_manager.get_text("file_menu"))
        self.file_btn.setMenu(self.file_menu)
        toolbar.addWidget(self.file_btn)

        # 编辑菜单
        self.edit_menu = QMenu()
        self.edit_menu.addAction(self.lang_manager.get_text("add_node"), self.show_add_node_dialog)
        self.edit_menu.addAction(self.lang_manager.get_text("batch_edit_nodes_menu"), self.open_batch_edit_dialog)
        self.edit_menu.addAction(self.lang_manager.get_text("batch_edit_relationships_menu"), self.open_batch_edit_relationship_dialog)
        self.edit_btn = QPushButton(self.lang_manager.get_text("edit_menu"))
        self.edit_btn.setMenu(self.edit_menu)
        toolbar.addWidget(self.edit_btn)

        # 视图菜单
        self.view_menu = QMenu()
        self.view_menu.addAction(self.lang_manager.get_text("reset_layout"), self.reset_layout)
        self.view_menu.addAction(self.lang_manager.get_text("fit_window"), self.fit_graph_to_window)
        self.view_menu.addAction(self.lang_manager.get_text("toggle_theme"), self.toggle_theme)
        self.view_btn = QPushButton(self.lang_manager.get_text("view_menu"))
        self.view_btn.setMenu(self.view_menu)
        toolbar.addWidget(self.view_btn)

        # 语言切换菜单
        self.language_menu = QMenu()
        self.language_menu.addAction(self.lang_manager.get_text("switch_to_chinese"), lambda: self.switch_language("zh"))
        self.language_menu.addAction(self.lang_manager.get_text("switch_to_english"), lambda: self.switch_language("en"))
        self.language_btn = QPushButton(self.lang_manager.get_text("language"))
        self.language_btn.setMenu(self.language_menu)
        toolbar.addWidget(self.language_btn)

        # 显示模式控制区域（分隔符）
        toolbar.addSeparator()

        # 显示模式标签
        self.mode_label = QLabel(self.lang_manager.get_text("display_mode"))
        self.mode_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #666;
                padding: 8px 5px;
            }
        """)
        toolbar.addWidget(self.mode_label)

        # 快速模式切换按钮
        self.quick_mode_btn = QPushButton(self.lang_manager.get_text("graph_mode"))
        self.quick_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.quick_mode_btn.clicked.connect(self.quick_toggle_mode)
        toolbar.addWidget(self.quick_mode_btn)

        # 刷新当前视图按钮
        self.refresh_view_btn = QPushButton(self.lang_manager.get_text("refresh_view"))
        self.refresh_view_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.refresh_view_btn.clicked.connect(self.refresh_current_view)
        toolbar.addWidget(self.refresh_view_btn)

        # 分隔符
        toolbar.addSeparator()

        # 插件菜单
        self.plugin_menu = QMenu()
        self.plugin_menu.addAction(self.lang_manager.get_text("load_plugin"), self.load_plugin)
        self.plugin_menu.addAction(self.lang_manager.get_text("manage_plugins"), self.manage_plugins)
        self.plugin_btn = QPushButton(self.lang_manager.get_text("plugin_menu"))
        self.plugin_btn.setMenu(self.plugin_menu)
        toolbar.addWidget(self.plugin_btn)

        # 分隔符
        toolbar.addSeparator()

        # 数据统计显示（实时更新）
        self.data_stats_label = QLabel(self.lang_manager.get_text("loading"))
        self.data_stats_label.setStyleSheet("""
            QLabel {
                background-color: #e8f5e9;
                border: 1px solid #4caf50;
                padding: 6px 10px;
                border-radius: 4px;
                color: #2e7d32;
                font-weight: bold;
            }
        """)
        toolbar.addWidget(self.data_stats_label)

        # 延迟更新统计信息
        QTimer.singleShot(1000, self.update_toolbar_stats)

    def switch_language(self, language):
        """切换语言"""
        if self.lang_manager.set_language(language):
            self.update_all_ui_texts()
            print(f"✅ Language switched to: {language}")

    def update_all_ui_texts(self):
        """更新所有界面文本"""
        # 更新窗口标题
        self.update_window_title()
        
        # 更新工具栏按钮文本
        self.file_btn.setText(self.lang_manager.get_text("file_menu"))
        self.edit_btn.setText(self.lang_manager.get_text("edit_menu"))
        self.view_btn.setText(self.lang_manager.get_text("view_menu"))
        self.language_btn.setText(self.lang_manager.get_text("language"))
        self.plugin_btn.setText(self.lang_manager.get_text("plugin_menu"))
        
        # 更新菜单项
        self.update_menu_texts()
        
        # 更新模式相关文本
        self.mode_label.setText(self.lang_manager.get_text("display_mode"))
        self.refresh_view_btn.setText(self.lang_manager.get_text("refresh_view"))
        
        # 【修复】：更新控制栏中的显示模式标签
        if hasattr(self, 'display_mode_label'):
            self.display_mode_label.setText(self.lang_manager.get_text("display_mode"))
        
        # 更新快速模式按钮
        self.update_quick_mode_button()
        
        # 更新状态和其他动态文本
        self.update_toolbar_stats()
        
        # 【重要添加】：更新节点详情面板的文本
        self.node_detail.update_ui_texts()
        
        # 如果当前在数据模式，重新渲染以应用新语言
        if hasattr(self, 'current_mode') and self.current_mode == "data":
            self.render_data_mode()
        
        # 更新模式状态标签
        if hasattr(self, 'mode_status_label'):
            if hasattr(self, 'current_mode'):
                if self.current_mode == "graph":
                    self.mode_status_label.setText(self.lang_manager.get_text("current_graph_mode"))
                else:
                    self.mode_status_label.setText(self.lang_manager.get_text("current_data_mode"))

        # 更新其他界面元素
        if hasattr(self, 'mode_switch_btn'):
            if hasattr(self, 'current_mode'):
                if self.current_mode == "graph":
                    self.mode_switch_btn.setText(self.lang_manager.get_text("switch_to_data"))
                else:
                    self.mode_switch_btn.setText(self.lang_manager.get_text("switch_to_graph"))

        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setText(self.lang_manager.get_text("refresh_view"))

        if hasattr(self, 'data_mode_title'):
            self.data_mode_title.setText(self.lang_manager.get_text("data_detail_mode"))

        if hasattr(self, 'export_view_btn'):
            self.export_view_btn.setText(self.lang_manager.get_text("export_current_view"))

        if hasattr(self, 'graph_status'):
            self.update_graph_status(self.lang_manager.get_text("graph_loading"))
    def update_menu_texts(self):
        """更新菜单文本"""
        # 清空并重新添加菜单项以应用新语言
        self.file_menu.clear()
        self.file_menu.addAction(self.lang_manager.get_text("import_data"), self.import_data)
        self.file_menu.addAction(self.lang_manager.get_text("save_data"), self.save_data)
        self.file_menu.addAction(self.lang_manager.get_text("export_data"), self.export_data)
        self.file_menu.addAction(self.lang_manager.get_text("save_jsonld"), self.save_data_as_jsonld)
        
        self.edit_menu.clear()
        self.edit_menu.addAction(self.lang_manager.get_text("add_node"), self.show_add_node_dialog)
        self.edit_menu.addAction(self.lang_manager.get_text("batch_edit_nodes_menu"), self.open_batch_edit_dialog)
        self.edit_menu.addAction(self.lang_manager.get_text("batch_edit_relationships_menu"), self.open_batch_edit_relationship_dialog)
        
        self.view_menu.clear()
        self.view_menu.addAction(self.lang_manager.get_text("reset_layout"), self.reset_layout)
        self.view_menu.addAction(self.lang_manager.get_text("fit_window"), self.fit_graph_to_window)
        self.view_menu.addAction(self.lang_manager.get_text("toggle_theme"), self.toggle_theme)
        
        self.language_menu.clear()
        self.language_menu.addAction(self.lang_manager.get_text("switch_to_chinese"), lambda: self.switch_language("zh"))
        self.language_menu.addAction(self.lang_manager.get_text("switch_to_english"), lambda: self.switch_language("en"))
        
        self.plugin_menu.clear()
        self.plugin_menu.addAction(self.lang_manager.get_text("load_plugin"), self.load_plugin)
        self.plugin_menu.addAction(self.lang_manager.get_text("manage_plugins"), self.manage_plugins)

    def quick_toggle_mode(self):
        """快速切换模式"""
        if hasattr(self, 'toggle_display_mode'):
            self.toggle_display_mode()
            self.update_quick_mode_button()

    def update_quick_mode_button(self):
        """更新快速模式按钮显示"""
        if hasattr(self, 'current_mode'):
            if self.current_mode == "graph":
                self.quick_mode_btn.setText(self.lang_manager.get_text("graph_mode"))
                self.quick_mode_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 8px 15px;
                        border-radius: 5px;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
            else:
                self.quick_mode_btn.setText(self.lang_manager.get_text("data_mode"))
                self.quick_mode_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        border: none;
                        padding: 8px 15px;
                        border-radius: 5px;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #F57C00;
                    }
                """)

    def refresh_current_view(self):
        """刷新当前视图"""
        if hasattr(self, 'refresh_current_mode'):
            self.refresh_current_mode()
            self.update_toolbar_stats()

    def update_toolbar_stats(self):
        """更新工具栏统计信息"""
        try:
            data = self.graph_manager.get_graph_data()
            nodes_count = len(data.get('nodes', []))
            edges_count = len(data.get('edges', []))
            
            # 计算节点类型数量
            types = set(node.get('type', '未知') for node in data.get('nodes', []))
            types_count = len(types)
            
            stats_text = self.lang_manager.get_text("statistics", 
                                                  nodes=nodes_count, 
                                                  edges=edges_count, 
                                                  types=types_count)
            self.data_stats_label.setText(stats_text)
            
            # 定时更新（每30秒）
            QTimer.singleShot(30000, self.update_toolbar_stats)
            
        except Exception as e:
            print(f"❌ 工具栏统计更新失败: {e}")
            self.data_stats_label.setText(self.lang_manager.get_text("stats_unavailable"))

    def fit_graph_to_window(self):
        """适合窗口大小"""
        try:
            if hasattr(self, 'graph_view') and hasattr(self, 'current_mode'):
                if self.current_mode == "graph":
                    # 执行JavaScript适合窗口
                    self.graph_view.page().runJavaScript("""
                        if (typeof network !== 'undefined') {
                            network.fit();
                        }
                    """)
                    print("✅", self.lang_manager.get_text("fit_to_window_success"))
                else:
                    # 数据模式下滚动到顶部
                    if hasattr(self, 'data_browser'):
                        self.data_browser.verticalScrollBar().setValue(0)
                    print("✅", self.lang_manager.get_text("data_view_top"))
        except Exception as e:
            print(f"❌ 适合窗口操作失败: {e}")

    def toggle_theme(self):
        """切换主题"""
        try:
            QMessageBox.information(self, 
                                  self.lang_manager.get_text("theme_switch"), 
                                  self.lang_manager.get_text("theme_switch_coming"))
        except Exception as e:
            print(f"❌ 主题切换失败: {e}")

    def safe_update(self):
        """安全更新 - 增强版"""
        try:
            # 更新所有显示模式
            if hasattr(self, 'update_all_modes'):
                QTimer.singleShot(0, self.update_all_modes)
            else:
                # 回退到原始方法
                QTimer.singleShot(0, self.graph_view.render)
            # 更新导航器
            if hasattr(self, 'navigator'):
                QTimer.singleShot(500, self.navigator.force_refresh)
            # 更新工具栏统计
            QTimer.singleShot(500, self.update_toolbar_stats)
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")

    def open_batch_edit_dialog(self):
        dialog = NodeEditDialog(
            columns=["name", "type", "attributes"],
            data=self.graph_manager.get_all_nodes(),
            parent=self
        )
        if dialog.exec_():  # 如果用户点击了"确定"
            edited_data = dialog.get_data()  # 获取用户编辑的数据

            for node in edited_data:
                try:
                    # 使用 try-except 处理 JSON 格式错误
                    attributes = json.loads(node["attributes"]) if node["attributes"] else {}
                except json.JSONDecodeError:
                    # 如果格式错误，使用默认值 {}，避免程序崩溃
                    attributes = {}
                    QMessageBox.critical(self, self.lang_manager.get_text("error"),
                                         f"第{edited_data.index(node) + 1}行属性不是有效的JSON格式，已使用默认值")

                try:
                    # 逐个调用 edit_node，传递正确的参数
                    self.graph_manager.edit_node(node["name"], node["type"], attributes)
                except ValueError as e:
                    # 如果节点不存在，捕获异常并显示错误
                    QMessageBox.critical(self, self.lang_manager.get_text("error"), f"节点编辑失败: {str(e)}")
                    return

            self.safe_update()  # 强制刷新图谱界面

    def open_batch_edit_relationship_dialog(self):
        # 获取所有关系数据（示例格式）
        dialog = RelationEditDialog(
            graph_manager=self.graph_manager,
            data=self.graph_manager.get_all_relationships(),
            parent=self
        )

        if dialog.exec_():
            try:
                # 获取修改后的关系列表
                modified_rels = dialog.get_modified_relations()

                # 转换为图管理器需要的格式
                updates = [{
                    "original": {  # 原始关系标识
                        "source": rel["source"],
                        "target": rel["target"],
                        "type": rel["relation_type"]
                    },
                    "new_data": {  # 新数据
                        "new_source": rel["source"],  # 如果允许修改源/目标需要调整
                        "new_target": rel["target"],
                        "new_type": rel["relation_type"]
                    }
                } for rel in modified_rels]

                self.graph_manager.batch_edit_relationships(updates)
                self.safe_update()
            except Exception as e:
                QMessageBox.critical(self, self.lang_manager.get_text("error"), f"关系更新失败: {str(e)}")

    def save_data_as_jsonld(self):
        """保存图数据为 JSON-LD 格式文件"""
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "保存 JSON-LD 文件",
            "",
            "JSON-LD Files (*.jsonld)",
            options=options,
        )
        if not filepath:
            return
        try:
            self.graph_manager.save_graph_to_jsonld(filepath)
            self.status_bar.showMessage(self.lang_manager.get_text("save_success"), 3000)
        except Exception as e:
            QMessageBox.critical(self, 
                               self.lang_manager.get_text("error"), 
                               self.lang_manager.get_text("save_error", error=str(e)))

    def load_plugin(self):
        dialog = PluginManageDialog(
            mode="load",
            columns=["path", "enabled"],
            data=[],
            parent=self
        )
        dialog.setWindowTitle(self.lang_manager.get_text("batch_load_plugins"))

        if dialog.exec_():
            # 获取用户输入的插件路径
            plugins_to_load = [p for p in dialog.get_data() if p["path"]]

            success_count = 0
            for plugin in plugins_to_load:
                try:
                    # 调用插件管理器加载插件
                    self.plugin_manager.load_plugin(
                        plugin_path=Path(plugin["path"]),
                        enabled=plugin["enabled"]
                    )
                    success_count += 1
                except Exception as e:
                    QMessageBox.warning(self, 
                                      self.lang_manager.get_text("load_failed"), 
                                      f"无法加载 {plugin['path']}:\n{str(e)}")

            # 刷新插件列表
            self.populate_plugins()
            QMessageBox.information(
                self, self.lang_manager.get_text("load_complete"),
                self.lang_manager.get_text("load_success_count", 
                                         success=success_count, 
                                         total=len(plugins_to_load))
            )

    def manage_plugins(self):
        dialog = PluginManageDialog(
            mode="manage",
            columns=["name", "path", "enabled"],
            data=[p.__dict__ for p in self.plugin_manager.plugins],
            parent=self
        )

        dialog.setWindowTitle(self.lang_manager.get_text("plugin_management"))

        if dialog.exec_():
            updated = dialog.get_data()
            # 确保 enabled 是 bool
            for p in updated:
                p["enabled"] = True if p["enabled"] in (True, "True", "true", 1, "1") else False

            # 然后再
            states = {p["name"]: p["enabled"] for p in updated}
            self.plugin_manager.update_plugin_states(states)

            current = {p["name"] for p in updated}
            for plugin in self.plugin_manager.plugins[:]:
                if plugin.name not in current:
                    self.plugin_manager.unload_plugin(plugin.name)

            self.populate_plugins()
            QMessageBox.information(self, 
                                  self.lang_manager.get_text("success"), 
                                  self.lang_manager.get_text("plugin_config_updated"))

    def init_web_view(self):
        """双模式图谱显示初始化"""
        print("初始化双模式图谱显示...")
        
        try:
            # 创建切换容器
            # 主容器
            self.graph_container = QWidget()
            container_layout = QVBoxLayout(self.graph_container)
            
            # 顶部控制栏
            control_bar = QWidget()
            control_layout = QHBoxLayout(control_bar)
            control_layout.setContentsMargins(10, 5, 10, 5)
            
            # 模式切换按钮
            self.mode_switch_btn = QPushButton(self.lang_manager.get_text("switch_to_data"))
            self.mode_switch_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 6px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            self.mode_switch_btn.clicked.connect(self.toggle_display_mode)
            
            # 状态标签
            self.mode_status_label = QLabel(self.lang_manager.get_text("current_graph_mode"))
            self.mode_status_label.setStyleSheet("""
                QLabel {
                    padding: 8px 12px;
                    background-color: #e8f5e9;
                    border: 1px solid #4caf50;
                    border-radius: 4px;
                    font-weight: bold;
                    color: #2e7d32;
                }
            """)
            
            # 刷新按钮
            self.refresh_btn = QPushButton(self.lang_manager.get_text("refresh_view"))
            self.refresh_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-size: 14px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.refresh_btn.clicked.connect(self.refresh_current_mode)
            
            # 【修复】：将匿名QLabel保存为实例变量
            self.display_mode_label = QLabel(self.lang_manager.get_text("display_mode"))
            
            # 布局控制栏
            control_layout.addWidget(self.display_mode_label)  # 使用实例变量
            control_layout.addWidget(self.mode_status_label)
            control_layout.addWidget(self.mode_switch_btn)
            control_layout.addStretch()
            control_layout.addWidget(self.refresh_btn)
            
            container_layout.addWidget(control_bar)
            
            # 创建堆叠显示区域
            self.display_stack = QStackedWidget()
            
            # 模式1: WebEngine图形模式
            self.graph_mode_widget = self.create_graph_mode()
            self.display_stack.addWidget(self.graph_mode_widget)
            
            # 模式2: 数据显示模式
            self.data_mode_widget = self.create_data_mode()
            self.display_stack.addWidget(self.data_mode_widget)
            
            container_layout.addWidget(self.display_stack)
            
            # 添加到主布局
            self.left_layout.addWidget(self.graph_container)
            
            # 默认显示图形模式
            self.current_mode = "graph"
            self.display_stack.setCurrentWidget(self.graph_mode_widget)
            
            # 初始化图形模式
            self.init_graph_mode()
            
            print("✅ 双模式显示系统初始化完成")
            
        except Exception as e:
            print(f"❌ 双模式显示初始化失败: {e}")
            import traceback
            traceback.print_exc()
    def create_graph_mode(self):
        """创建图形显示模式"""
        try:
            # 创建GraphView
            graph_widget = QWidget()
            layout = QVBoxLayout(graph_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)  # 减少组件间距
            
            # 状态标签 - 设置更紧凑的样式和固定高度
            self.graph_status = QLabel(self.lang_manager.get_text("graph_loading"))
            self.graph_status.setFixedHeight(35)  # 设置固定高度
            self.graph_status.setStyleSheet("""
                QLabel {
                    padding: 5px 10px;  /* 减少内边距 */
                    background-color: #fff3e0;
                    border: 1px solid #ff9800;
                    border-radius: 4px;
                    color: #e65100;
                    font-weight: bold;
                    font-size: 12px;  /* 减小字体 */
                }
            """)
            layout.addWidget(self.graph_status, 0)  # 拉伸因子为0，不占用额外空间
            
            # GraphView容器 - 占用主要空间
            self.graph_view_container = QWidget()
            self.graph_view_container.setStyleSheet("""
                QWidget {
                    border: 2px solid #2196F3;
                    border-radius: 8px;
                    background-color: #fafafa;
                }
            """)
            layout.addWidget(self.graph_view_container, 1)  # 拉伸因子为1，占用主要空间
            
            return graph_widget
            
        except Exception as e:
            print(f"❌ 图形模式创建失败: {e}")
            return QWidget()

    def create_data_mode(self):
        """创建数据显示模式"""
        data_widget = QWidget()
        layout = QVBoxLayout(data_widget)
        
        # 数据模式标题
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.data_mode_title = QLabel(self.lang_manager.get_text("data_detail_mode"))
        self.data_mode_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 12px;
                color: #1565c0;
            }
        """)
        
        # 导出按钮
        self.export_view_btn = QPushButton(self.lang_manager.get_text("export_current_view"))
        self.export_view_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.export_view_btn.clicked.connect(self.export_data_view)
        
        title_layout.addWidget(self.data_mode_title)
        title_layout.addStretch()
        title_layout.addWidget(self.export_view_btn)
        
        layout.addWidget(title_bar)
        
        # 数据显示区域
        self.data_browser = QTextBrowser()
        self.data_browser.setStyleSheet("""
            QTextBrowser {
                border: 2px solid #4caf50;
                border-radius: 8px;
                padding: 15px;
                background-color: #fafafa;
                font-family: Arial, sans-serif;
            }
        """)
        layout.addWidget(self.data_browser)
        
        # 底部统计信息
        self.data_stats = QLabel(self.lang_manager.get_text("loading"))
        self.data_stats.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #e8f5e9;
                border: 1px solid #4caf50;
                border-radius: 4px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        layout.addWidget(self.data_stats)
        
        return data_widget

    def init_graph_mode(self):
        """初始化图形模式"""
        try:
            print("初始化图形显示模式...")
            
            # 设置环境变量
            import os
            os.environ['QTWEBENGINE_DISABLE_SANDBOX'] = '1'
            os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu --no-sandbox'
            
            # 创建GraphView
            self.graph_view = GraphView(
                graph_manager=self.graph_manager,
                node_detail_widget=self.node_detail,
                update_callback=self.safe_update
            )
            
            # WebEngine设置
            try:
                from PyQt5.QtWebEngineWidgets import QWebEngineSettings
                settings = self.graph_view.page().settings()
                settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
                settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
                settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
            except Exception as e:
                print(f"⚠️ WebEngine设置警告: {e}")
            
            # 连接信号
            self.graph_view.loadFinished.connect(self.on_graph_mode_loaded)
            self.graph_view.loadStarted.connect(lambda: self.update_graph_status(self.lang_manager.get_text("graph_loading")))
            
            # 添加到容器
            container_layout = QVBoxLayout(self.graph_view_container)
            container_layout.setContentsMargins(5, 5, 5, 5)
            container_layout.addWidget(self.graph_view)
            
            # 延迟渲染
            QTimer.singleShot(1000, self.render_graph_mode)
             # 在这里创建并添加导航器
             # 在这里创建并添加导航器
            QTimer.singleShot(2000, self.create_navigator)
        except Exception as e:
            print(f"❌ 图形模式初始化失败: {e}")
            
    def create_navigator(self):
        """创建导航器"""
        try:
            from plugins.navigator import NavigatorWidget  # 导入你的导航器
            
            self.navigator = NavigatorWidget(self.graph_manager, self.graph_view, self)
            self.right_splitter.addWidget(self.navigator)
            self.right_splitter.setSizes([100, 100, 100])  # 调整三个部分的大小比例
            
            print("导航器已创建并添加到界面")
            
        except Exception as e:
            print(f"导航器创建失败: {e}")
    def render_graph_mode(self):
        """渲染图形模式"""
        try:
            self.update_graph_status(self.lang_manager.get_text("rendering_graph"))
            self.graph_view.render()
            
            # 延迟检查渲染结果
            QTimer.singleShot(3000, self.check_graph_render)
            
        except Exception as e:
            print(f"❌ 图形模式渲染失败: {e}")
            self.update_graph_status(f"❌ 渲染失败: {str(e)}")

    def check_graph_render(self):
        """检查图形渲染结果"""
        try:
            self.graph_view.page().runJavaScript(
                "typeof vis !== 'undefined' && document.querySelector('#mynetworkid') ? 'success' : 'failed'",
                self.on_graph_render_check
            )
        except Exception as e:
            print(f"❌ 图形渲染检查失败: {e}")
            self.update_graph_status(self.lang_manager.get_text("graph_warning"))

    def on_graph_render_check(self, result):
        """图形渲染检查回调"""
        if result == 'success':
            self.update_graph_status(self.lang_manager.get_text("graph_success"))
        else:
            self.update_graph_status(self.lang_manager.get_text("graph_warning"))

    def on_graph_mode_loaded(self, ok):
        """图形模式加载完成回调"""
        if ok:
            print("✅ 图形模式页面加载成功")
            self.update_graph_status(self.lang_manager.get_text("graph_page_success"))
        else:
            print("❌ 图形模式页面加载失败")
            self.update_graph_status(self.lang_manager.get_text("graph_page_error"))

    def update_graph_status(self, message):
        """更新图形模式状态 - 优化样式"""
        print(f"图形模式: {message}")
        self.graph_status.setText(message)
        
        # 根据状态设置样式，但保持紧凑的设计
        if "✅" in message:
            style = "background-color: #e8f5e9; border-color: #4caf50; color: #2e7d32;"
        elif "❌" in message:
            style = "background-color: #ffebee; border-color: #f44336; color: #c62828;"
        elif "⚠️" in message:
            style = "background-color: #fff3e0; border-color: #ff9800; color: #e65100;"
        else:
            style = "background-color: #e3f2fd; border-color: #2196f3; color: #1565c0;"
        
        self.graph_status.setStyleSheet(f"""
            QLabel {{
                padding: 5px 10px;  /* 保持紧凑的内边距 */
                border: 1px solid;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;  /* 保持较小字体 */
                {style}
            }}
        """)

    def toggle_display_mode(self):
        """切换显示模式"""
        try:
            if self.current_mode == "graph":
                # 切换到数据模式
                self.current_mode = "data"
                self.display_stack.setCurrentWidget(self.data_mode_widget)
                self.mode_switch_btn.setText(self.lang_manager.get_text("switch_to_graph"))
                self.mode_status_label.setText(self.lang_manager.get_text("current_data_mode"))
                self.mode_status_label.setStyleSheet("""
                    QLabel {
                        padding: 8px 12px;
                        background-color: #fff3e0;
                        border: 1px solid #ff9800;
                        border-radius: 4px;
                        font-weight: bold;
                        color: #e65100;
                    }
                """)
                
                # 渲染数据模式
                self.render_data_mode()
                
            else:
                # 切换到图形模式
                self.current_mode = "graph"
                self.display_stack.setCurrentWidget(self.graph_mode_widget)
                self.mode_switch_btn.setText(self.lang_manager.get_text("switch_to_data"))
                self.mode_status_label.setText(self.lang_manager.get_text("current_graph_mode"))
                self.mode_status_label.setStyleSheet("""
                    QLabel {
                        padding: 8px 12px;
                        background-color: #e8f5e9;
                        border: 1px solid #4caf50;
                        border-radius: 4px;
                        font-weight: bold;
                        color: #2e7d32;
                    }
                """)
                
                # 重新渲染图形模式（如果需要）
                if hasattr(self, 'graph_view'):
                    self.render_graph_mode()
            
            print(f"✅ 已切换到 {self.current_mode} 模式")
            
        except Exception as e:
            print(f"❌ 模式切换失败: {e}")

    def refresh_current_mode(self):
        """刷新当前模式"""
        try:
            if self.current_mode == "graph":
                print("🔄 刷新图形模式...")
                if hasattr(self, 'graph_view'):
                    self.render_graph_mode()
            else:
                print("🔄 刷新数据模式...")
                self.render_data_mode()
            
        except Exception as e:
            print(f"❌ 刷新失败: {e}")

    def render_data_mode(self):
        """渲染数据模式"""
        try:
            print("渲染数据显示模式...")
            data = self.graph_manager.get_graph_data()
            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            
            # 统计信息
            type_stats = {}
            for node in nodes:
                node_type = node.get('type', '未分类' if self.lang_manager.current_language == 'zh' else 'Uncategorized')
                type_stats[node_type] = type_stats.get(node_type, 0) + 1
            
            # 关系类型统计
            relation_stats = {}
            for edge in edges:
                relation_type = edge.get('relation_type', '未知关系' if self.lang_manager.current_language == 'zh' else 'Unknown Relation')
                relation_stats[relation_type] = relation_stats.get(relation_type, 0) + 1
            
            # 更新统计标签
            stats_text = self.lang_manager.get_text("statistics", 
                                                  nodes=len(nodes), 
                                                  edges=len(edges), 
                                                  types=len(type_stats))
            self.data_stats.setText(stats_text)
            
            # 生成详细HTML
            html = self.generate_detailed_html(nodes, edges, type_stats, relation_stats)
            self.data_browser.setHtml(html)
            
            print(f"✅ 数据模式渲染完成: {len(nodes)} 节点, {len(edges)} 关系")
            
        except Exception as e:
            print(f"❌ 数据模式渲染失败: {e}")
            self.data_browser.setHtml(f"<h3>Data loading failed</h3><p>{str(e)}</p>")

    def generate_detailed_html(self, nodes, edges, type_stats, relation_stats):
        """生成详细的HTML显示 - 支持国际化"""
        
        # 根据当前语言设置标题
        main_title = self.lang_manager.get_text("knowledge_graph_title")
        subtitle = self.lang_manager.get_text("knowledge_graph_subtitle")
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background: #f8f9fa; }}
                .container {{ max-width: 100%; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; margin: -20px -20px 25px -20px; border-radius: 0 0 15px 15px; }}
                .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 5px solid #667eea; }}
                .section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .section h3 {{ margin-top: 0; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                .type-item {{ background: #f8f9ff; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; border-radius: 0 8px 8px 0; }}
                .relation-item {{ background: #fff8e1; padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 4px solid #ff9800; }}
                .node-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; }}
                .node-card {{ background: #f0f7ff; padding: 12px; border-radius: 8px; border-left: 4px solid #2196f3; }}
                .node-name {{ font-weight: bold; color: #1565c0; }}
                .node-type {{ color: #666; font-size: 0.9em; }}
                .count {{ font-weight: bold; color: #d32f2f; font-size: 1.2em; }}
                .badge {{ display: inline-block; background: #667eea; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; margin: 2px; }}
                .collapsible {{ cursor: pointer; padding: 10px; background: #e3f2fd; border-radius: 5px; margin: 5px 0; }}
                .collapsible:hover {{ background: #bbdefb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{main_title}</h2>
                    <p>{subtitle}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>{self.lang_manager.get_text("node_statistics")}</h3>
                        <p>{self.lang_manager.get_text("total")}: <span class="count">{len(nodes)}</span></p>
                        <p>{self.lang_manager.get_text("types")}: <span class="count">{len(type_stats)}</span></p>
                    </div>
                    <div class="stat-card">
                        <h3>{self.lang_manager.get_text("relationship_statistics")}</h3>
                        <p>{self.lang_manager.get_text("total")}: <span class="count">{len(edges)}</span></p>
                        <p>{self.lang_manager.get_text("types")}: <span class="count">{len(relation_stats)}</span></p>
                    </div>
                </div>
        """
        
        # 节点类型分布
        html += f'<div class="section"><h3>{self.lang_manager.get_text("node_type_distribution")}</h3>'
        for node_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(nodes)) * 100 if nodes else 0
            type_nodes = [n['name'] for n in nodes if n.get('type') == node_type]
            
            html += f"""
            <div class="type-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="font-size: 1.1em;">{node_type}</strong>
                    <div>
                        <span class="badge">{count}</span>
                        <span class="badge">{percentage:.1f}%</span>
                    </div>
                </div>
                <div style="margin-top: 10px;">
                    <div class="collapsible" onclick="toggleNodes('{node_type}')">
                        {self.lang_manager.get_text("view_nodes", type=node_type)}
                    </div>
                    <div id="nodes-{node_type}" style="display: none; margin-top: 10px;">
                        <div class="node-grid">
            """
            
            # 显示该类型的所有节点
            for node_name in type_nodes[:10]:  # 限制显示数量
                html += f'<div class="node-card"><div class="node-name">{node_name}</div></div>'
            
            if len(type_nodes) > 10:
                html += f'<div class="node-card" style="text-align: center; color: #666;">{self.lang_manager.get_text("more_nodes", count=len(type_nodes)-10)}</div>'
            
            html += '</div></div></div></div>'
        
        html += '</div>'
        
        # 关系类型分布
        html += f'<div class="section"><h3>{self.lang_manager.get_text("relationship_type_distribution")}</h3>'
        for relation_type, count in sorted(relation_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(edges)) * 100 if edges else 0
            
            html += f"""
            <div class="relation-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{relation_type}</strong>
                    <div>
                        <span class="badge" style="background: #ff9800;">{count}</span>
                        <span class="badge" style="background: #ff9800;">{percentage:.1f}%</span>
                    </div>
                </div>
            </div>
            """
        
        html += '</div>'
        
        # 关系示例
        html += f'<div class="section"><h3>{self.lang_manager.get_text("relationship_examples")}</h3>'
        html += '<div style="max-height: 400px; overflow-y: auto;">'
        
        for i, edge in enumerate(edges[:15]):
            source = edge.get('source', 'Unknown')
            target = edge.get('target', 'Unknown')
            relation = edge.get('relation_type', 'Unknown')
            
            html += f"""
            <div class="relation-item" style="margin: 8px 0;">
                <strong style="color: #1565c0;">{source}</strong> 
                → <em style="color: #f57c00; font-weight: bold;">{relation}</em> → 
                <strong style="color: #2e7d32;">{target}</strong>
            </div>
            """
        
        if len(edges) > 15:
            html += f'<div style="text-align: center; color: #666; padding: 15px;">{self.lang_manager.get_text("more_relationships", count=len(edges)-15)}</div>'
        
        html += '</div></div>'
        
        # JavaScript交互
        html += """
            <script>
                function toggleNodes(nodeType) {
                    var element = document.getElementById('nodes-' + nodeType);
                    if (element.style.display === 'none') {
                        element.style.display = 'block';
                    } else {
                        element.style.display = 'none';
                    }
                }
            </script>
        </body>
        </html>
        """
        
        return html

    def export_data_view(self):
        """导出当前数据视图"""
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Data View",
                f"knowledge_graph_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html",
                "HTML Files (*.html);;Text Files (*.txt)",
                options=options
            )
            
            if file_path:
                # 获取当前数据
                data = self.graph_manager.get_graph_data()
                nodes = data.get('nodes', [])
                edges = data.get('edges', [])
                
                type_stats = {}
                for node in nodes:
                    node_type = node.get('type', '未分类')
                    type_stats[node_type] = type_stats.get(node_type, 0) + 1
                
                relation_stats = {}
                for edge in edges:
                    relation_type = edge.get('relation_type', '未知关系')
                    relation_stats[relation_type] = relation_stats.get(relation_type, 0) + 1
                
                # 生成完整HTML
                html = self.generate_detailed_html(nodes, edges, type_stats, relation_stats)
                
                # 保存文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                
                QMessageBox.information(self, 
                                      self.lang_manager.get_text("export_success"), 
                                      f"Data view exported to:\n{file_path}")
                
        except Exception as e:
            print(f"❌ Export failed: {e}")
            QMessageBox.critical(self, 
                               self.lang_manager.get_text("error"), 
                               self.lang_manager.get_text("export_error", error=str(e)))

    def update_all_modes(self):
        """更新所有显示模式"""
        try:
            # 更新图形模式
            if hasattr(self, 'graph_view'):
                self.graph_view.render()
            
            # 如果当前在数据模式，也更新数据显示
            if self.current_mode == "data":
                self.render_data_mode()
            
            print("✅ 所有显示模式已更新")
            
        except Exception as e:
            print(f"❌ 模式更新失败: {e}")

    def populate_plugins(self):
        """将加载的插件名称显示到右侧列表中"""
        self.plugin_list.clear()
        for plugin in self.plugin_manager.plugins:
            if hasattr(plugin, "name"):
                self.plugin_list.addItem(plugin.name)

    def show_add_node_dialog(self):
        """显示添加节点对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(self.lang_manager.get_text("add_node_title"))
        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        type_edit = QLineEdit()
        attr_edit = QTextEdit()
        attr_edit.setPlaceholderText(self.lang_manager.get_text("json_placeholder"))

        layout.addRow(self.lang_manager.get_text("node_name"), name_edit)
        layout.addRow(self.lang_manager.get_text("node_type"), type_edit)
        layout.addRow(self.lang_manager.get_text("node_attributes"), attr_edit)

        btn_box = QPushButton(self.lang_manager.get_text("confirm"))
        btn_box.clicked.connect(lambda: self.add_node_from_dialog(
            name_edit.text(), type_edit.text(), attr_edit.toPlainText(), dialog
        ))
        layout.addRow(btn_box)

        dialog.setLayout(layout)
        dialog.exec_()
    def add_node_from_dialog(self, name, node_type, attributes_str, dialog):
        """从对话框中添加节点"""
        try:
            if not name or not node_type:
                raise ValueError(self.lang_manager.get_text("name_type_required"))
            attributes = json.loads(attributes_str) if attributes_str else {}
            self.graph_manager.add_node(name, node_type, attributes)
            self.safe_update()
            dialog.close()
        except json.JSONDecodeError:
            QMessageBox.critical(self, 
                               self.lang_manager.get_text("error"), 
                               self.lang_manager.get_text("invalid_json"))
        except Exception as e:
            QMessageBox.critical(self, self.lang_manager.get_text("error"), str(e))
            QMessageBox.critical(self, self.lang_manager.get_text("error"), str(e))

    def import_data(self):
        """导入 CSV 或 JSON 数据文件"""
        options = QFileDialog.Options()
        filepaths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",
            "CSV Files (*.csv);;JSON Files (*.json)",
            options=options,
        )
        if not filepaths:
            return

        for filepath in filepaths:
            try:
                if filepath.endswith(".csv"):
                    encoding = self.detect_encoding(filepath) or "utf-8"
                    data = pd.read_csv(filepath, encoding=encoding)
                    if {"name", "type"}.issubset(data.columns):
                        self.data_importer.import_nodes_from_csv(filepath)
                    elif {"source", "target", "relation_type"}.issubset(data.columns):
                        self.data_importer.import_relationships_from_csv(filepath)
                    else:
                        QMessageBox.warning(self, 
                                          self.lang_manager.get_text("warning"), 
                                          self.lang_manager.get_text("csv_column_error"))
                        continue
                elif filepath.endswith(".json"):
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "nodes" in data and "edges" in data:
                            for node in data["nodes"]:
                                self.graph_manager.add_node(
                                    node["name"],
                                    node["type"],
                                    node.get("attributes", {})
                                )
                            for edge in data["edges"]:
                                self.graph_manager.add_relationship(
                                    edge["source"],
                                    edge["target"],
                                    edge["relation_type"]
                                )
                        else:
                            QMessageBox.warning(self, 
                                              self.lang_manager.get_text("warning"), 
                                              self.lang_manager.get_text("json_format_error"))
                            continue
                else:
                    QMessageBox.warning(self, 
                                      self.lang_manager.get_text("warning"), 
                                      self.lang_manager.get_text("unsupported_format"))
                    continue

                self.safe_update()
                QMessageBox.information(self, 
                                      self.lang_manager.get_text("success"), 
                                      self.lang_manager.get_text("import_success", filename=os.path.basename(filepath)))
            except Exception as e:
                QMessageBox.critical(self, 
                                   self.lang_manager.get_text("error"), 
                                   self.lang_manager.get_text("import_error", filename=os.path.basename(filepath), error=str(e)))

    def save_data(self):
        """保存当前图数据到 JSON 文件"""
        try:
            self.graph_manager.save_graph_to_json()
            self.status_bar.showMessage(self.lang_manager.get_text("save_success"), 3000)
        except Exception as e:
            QMessageBox.critical(self, 
                               self.lang_manager.get_text("error"), 
                               self.lang_manager.get_text("save_error", error=str(e)))

    def export_data(self):
        """导出知识图谱数据（支持JSON、CSV、GraphML、RDF、OWL格式）"""
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(self, "保存文件", "",
                                              "JSON Files (*.json);;CSV Files (*.csv);;GraphML Files (*.graphml);;RDF Files (*.rdf);;OWL Files (*.owl)",
                                              options=options)

        if file:
            data = self.graph_manager.get_graph_data()  # 获取当前的图数据

            # 根据文件后缀判断导出的文件格式
            try:
                if file.endswith(".json"):
                    with open(file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                elif file.endswith(".csv"):
                    self.export_to_csv(file, data)
                elif file.endswith(".graphml"):
                    self.export_to_graphml(file, data)
                elif file.endswith(".rdf"):
                    self.export_to_rdf(file, data)
                elif file.endswith(".owl"):
                    self.export_to_owl(file, data)
                else:
                    QMessageBox.warning(self, 
                                      self.lang_manager.get_text("error"), 
                                      self.lang_manager.get_text("unsupported_format"))
            except Exception as e:
                QMessageBox.critical(self, 
                                   self.lang_manager.get_text("error"), 
                                   self.lang_manager.get_text("export_error", error=str(e)))

    def export_to_csv(self, file, data):
        """导出为 CSV 格式（包括节点和关系）"""
        nodes_data = data["nodes"]
        edges_data = data["edges"]

        try:
            with open(file, 'w', encoding='utf-8', newline='') as f:
                # 写入节点数据
                node_writer = csv.DictWriter(f, fieldnames=nodes_data[0].keys())
                node_writer.writeheader()
                node_writer.writerows(nodes_data)

                # 在节点数据后加一个分隔行（可选）
                f.write("\n")

                # 写入关系数据
                edge_writer = csv.DictWriter(f, fieldnames=edges_data[0].keys())
                edge_writer.writeheader()
                edge_writer.writerows(edges_data)

            QMessageBox.information(self, 
                                  self.lang_manager.get_text("success"), 
                                  self.lang_manager.get_text("export_csv_success"))
        except Exception as e:
            QMessageBox.critical(self, 
                               self.lang_manager.get_text("error"), 
                               self.lang_manager.get_text("export_error", error=str(e)))

    def export_to_graphml(self, file, data):
        try:
            # GraphDataManager 内部保存了 actual networkx 图对象为 .graph
            nx.write_graphml(self.graph_manager.graph, file)
            QMessageBox.information(self, 
                                  self.lang_manager.get_text("success"), 
                                  self.lang_manager.get_text("export_graphml_success"))
        except Exception as e:
            QMessageBox.critical(self, 
                               self.lang_manager.get_text("error"), 
                               self.lang_manager.get_text("export_error", error=str(e)))

    def export_to_rdf(self, file, data):
        """导出为 RDF 格式"""
        g = rdflib.Graph()

        # 添加命名空间
        namespace = rdflib.Namespace("http://example.org/graph#")
        g.bind("ex", namespace)

        # 将节点和关系转换为 RDF 数据
        for node in data["nodes"]:
            node_uri = namespace[node["name"]]
            g.add((node_uri, RDF.type, RDFS.Class))
            g.add((node_uri, RDFS.label, rdflib.Literal(node["name"])))
            if "type" in node:
                g.add((node_uri, namespace["type"], rdflib.Literal(node["type"])))

        for edge in data["edges"]:
            source_uri = namespace[edge["source"]]
            target_uri = namespace[edge["target"]]
            relation_uri = namespace[edge["relation_type"]]

            g.add((source_uri, relation_uri, target_uri))

        try:
            g.serialize(destination=file, format="rdfxml")  # 导出为 RDF/XML 格式
            QMessageBox.information(self, 
                                  self.lang_manager.get_text("success"), 
                                  self.lang_manager.get_text("export_rdf_success"))
        except Exception as e:
            QMessageBox.critical(self, 
                               self.lang_manager.get_text("error"), 
                               self.lang_manager.get_text("export_error", error=str(e)))

    def export_to_owl(self, file, data):
        """导出为 OWL 格式"""
        g = rdflib.Graph()

        # 添加命名空间
        namespace = rdflib.Namespace("http://example.org/graph#")
        g.bind("ex", namespace)

        # 创建 OWL 本体（添加类和实例）
        for node in data["nodes"]:
            node_uri = namespace[node["name"]]
            g.add((node_uri, RDF.type, OWL.Class))
            g.add((node_uri, RDFS.label, rdflib.Literal(node["name"])))
            if "type" in node:
                g.add((node_uri, namespace["type"], rdflib.Literal(node["type"])))

        for edge in data["edges"]:
            source_uri = namespace[edge["source"]]
            target_uri = namespace[edge["target"]]
            relation_uri = namespace[edge["relation_type"]]

            g.add((source_uri, relation_uri, target_uri))

        try:
            g.serialize(destination=file, format="xml")  # 导出为 OWL 格式
            QMessageBox.information(self, 
                                  self.lang_manager.get_text("success"), 
                                  self.lang_manager.get_text("export_owl_success"))
        except Exception as e:
            QMessageBox.critical(self, 
                               self.lang_manager.get_text("error"), 
                               self.lang_manager.get_text("export_error", error=str(e)))

    def reset_layout(self):
        """重置窗口布局"""
        self.main_splitter.setSizes([1000, 400])
        self.right_splitter.setSizes([400, 200])

    def detect_encoding(self, filepath):
        """检测文件编码"""
        with open(filepath, "rb") as f:
            raw = f.read(10000)
        result = chardet.detect(raw)
        return result.get("encoding", None)

    def run_plugin(self, item):
        """当在插件列表中双击插件时运行该插件"""
        plugin_name = item.text()
        result = self.plugin_manager.run_plugin(plugin_name, parent=self)
        QMessageBox.information(self, 
                              self.lang_manager.get_text("plugin_run_result"), 
                              self.lang_manager.get_text("plugin_result", name=plugin_name, result=result))

    def closeEvent(self, event):
        """退出时保存图数据"""
        try:
            self.graph_manager.save_graph_to_json()
        except Exception as e:
            QMessageBox.critical(self, 
                               self.lang_manager.get_text("error"), 
                               self.lang_manager.get_text("save_error", error=str(e)))
        event.accept()
    

    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())