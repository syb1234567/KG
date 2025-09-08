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
    QLabel, QTextBrowser, QStackedWidget, QApplication
)
from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtGui import QIcon

# 语言管理类
class LanguageManager:
    def __init__(self):
        self.current_language = "zh"  # 默认中文
        self.translations = {
            "zh": {
                # 窗口标题
                "window_title": "中医知识图谱",
                "add_node_title": "添加节点",
                "batch_edit_nodes": "批量编辑节点",
                "batch_edit_relationships": "批量编辑关系",
                "plugin_management": "插件管理",
                
                # 菜单项
                "file_menu": "📁 文件",
                "import_data": "📁 导入数据",
                "save_data": "💾 保存数据",
                "export_data": "📤 导出数据",
                "save_jsonld": "🔗 保存 JSON-LD",
                
                "edit_menu": "✏️ 编辑",
                "add_node": "➕ 添加节点",
                "batch_edit_nodes_menu": "📝 批量编辑节点",
                "batch_edit_relationships_menu": "🔗 批量编辑关系",
                
                "view_menu": "👁️ 视图",
                "reset_layout": "🔄 重置布局",
                "fit_window": "🔍 适合窗口",
                "toggle_theme": "🎨 切换主题",
                
                "plugin_menu": "🧩 插件",
                "load_plugin": "🔌 加载插件",
                "manage_plugins": "⚙️ 管理插件",
                
                # 模式切换
                "display_mode": "显示模式:",
                "graph_mode": "🌐 图形",
                "data_mode": "📊 数据",
                "switch_to_data": "📊 切换到数据模式",
                "switch_to_graph": "🌐 切换到图形模式",
                "refresh_view": "🔄 刷新视图",
                "current_graph_mode": "🌐 图形模式",
                "current_data_mode": "📊 数据模式",
                
                # 状态信息
                "loading": "🔄 加载中...",
                "graph_loading": "🔄 图形模式加载中...",
                "rendering_graph": "🎨 渲染图谱...",
                "graph_success": "✅ 图形模式运行正常",
                "graph_error": "❌ 图形模式不可用",
                "graph_warning": "⚠️ 图形模式可能有问题，建议切换到数据模式",
                "graph_page_success": "✅ 图形界面加载成功",
                "graph_page_error": "❌ 图形界面加载失败",
                
                # 统计信息
                "nodes": "节点",
                "relationships": "关系",
                "types": "类型",
                "statistics": "📊 节点: {nodes} | 🔗 关系: {edges} | 📂 类型: {types}",
                "stats_unavailable": "📊 统计信息不可用",
                
                # 对话框
                "node_name": "节点名称",
                "node_type": "节点类型",
                "node_attributes": "节点属性",
                "json_placeholder": "输入JSON格式属性...",
                "confirm": "确定",
                "cancel": "取消",
                "success": "成功",
                "error": "错误",
                "warning": "警告",
                
                # 数据模式
                "data_detail_mode": "📊 数据详情模式",
                "export_current_view": "📤 导出当前视图",
                "node_statistics": "📊 节点统计",
                "relationship_statistics": "🔗 关系统计",
                "total": "总数",
                "node_type_distribution": "📋 节点类型分布",
                "relationship_type_distribution": "🔗 关系类型分布",
                "relationship_examples": "🔗 关系示例",
                "view_nodes": "🔍 查看 {type} 节点 (点击展开/收起)",
                "more_nodes": "... 还有 {count} 个节点",
                "more_relationships": "📄 还有 {count} 个关系...",
                "knowledge_graph_title": "🏥 中医知识图谱 - 详细数据视图",
                "knowledge_graph_subtitle": "完整的知识图谱数据分析与浏览",
                
                # 错误信息
                "name_type_required": "节点名称和类型不能为空",
                "invalid_json": "属性必须是有效的JSON格式",
                "csv_column_error": "CSV文件列名不符合要求",
                "json_format_error": "JSON文件格式不正确",
                "unsupported_format": "不支持的文件格式",
                "import_success": "文件 '{filename}' 导入成功！",
                "import_error": "文件 '{filename}' 导入失败：{error}",
                "save_success": "数据保存成功",
                "save_error": "保存失败: {error}",
                "export_success": "导出成功",
                "export_error": "导出失败: {error}",
                
                # 语言切换
                "language": "🌐 Language",
                "switch_to_english": "🇺🇸 English",
                "switch_to_chinese": "🇨🇳 中文",
                
                # 其他
                "theme_switch_coming": "主题切换功能即将推出！",
                "theme_switch": "主题切换",
                "plugin_result": "插件 '{name}' 返回: {result}",
                "plugin_run_result": "插件运行结果",
                
                "search_title": "知识图谱检索",
                "search_type": "搜索类型:",
                "search_all": "全部",
                "search_nodes": "仅节点",
                "search_relationships": "仅关系",
                "search_placeholder": "输入搜索关键词...",
                "search": "搜索",
                "search_results": "搜索结果",
                "search_ready": "准备搜索",
                "search_empty": "请输入搜索关键词",
                "search_no_results": "未找到匹配的结果",
                "search_found_results": "找到 {} 个相关结果",
                "clear": "清空",
                "locate_in_graph": "在图中定位"
            },
            
            "en": {
                # 窗口标题
                "window_title": "Traditional Chinese Medicine Knowledge Graph",
                "add_node_title": "Add Node",
                "batch_edit_nodes": "Batch Edit Nodes",
                "batch_edit_relationships": "Batch Edit Relationships",
                "plugin_management": "Plugin Management",
                
                # 菜单项
                "file_menu": "📁 File",
                "import_data": "📁 Import Data",
                "save_data": "💾 Save Data",
                "export_data": "📤 Export Data",
                "save_jsonld": "🔗 Save JSON-LD",
                
                "edit_menu": "✏️ Edit",
                "add_node": "➕ Add Node",
                "batch_edit_nodes_menu": "📝 Batch Edit Nodes",
                "batch_edit_relationships_menu": "🔗 Batch Edit Relationships",
                
                "view_menu": "👁️ View",
                "reset_layout": "🔄 Reset Layout",
                "fit_window": "🔍 Fit to Window",
                "toggle_theme": "🎨 Toggle Theme",
                
                "plugin_menu": "🧩 Plugins",
                "load_plugin": "🔌 Load Plugin",
                "manage_plugins": "⚙️ Manage Plugins",
                
                # 模式切换
                "display_mode": "Display Mode:",
                "graph_mode": "🌐 Graph",
                "data_mode": "📊 Data",
                "switch_to_data": "📊 Switch to Data Mode",
                "switch_to_graph": "🌐 Switch to Graph Mode",
                "refresh_view": "🔄 Refresh View",
                "current_graph_mode": "🌐 Graph Mode",
                "current_data_mode": "📊 Data Mode",
                
                # 状态信息
                "loading": "🔄 Loading...",
                "graph_loading": "🔄 Loading graph mode...",
                "rendering_graph": "🎨 Rendering graph...",
                "graph_success": "✅ Graph mode running normally",
                "graph_error": "❌ Graph mode unavailable",
                "graph_warning": "⚠️ Graph mode may have issues, recommend switching to data mode",
                "graph_page_success": "✅ Graph interface loaded successfully",
                "graph_page_error": "❌ Graph interface failed to load",
                
                # 统计信息
                "nodes": "Nodes",
                "relationships": "Relationships",
                "types": "Types",
                "statistics": "📊 Nodes: {nodes} | 🔗 Relationships: {edges} | 📂 Types: {types}",
                "stats_unavailable": "📊 Statistics unavailable",
                
                # 对话框
                "node_name": "Node Name",
                "node_type": "Node Type",
                "node_attributes": "Node Attributes",
                "json_placeholder": "Enter JSON format attributes...",
                "confirm": "OK",
                "cancel": "Cancel",
                "success": "Success",
                "error": "Error",
                "warning": "Warning",
                
                # 数据模式
                "data_detail_mode": "📊 Data Detail Mode",
                "export_current_view": "📤 Export Current View",
                "node_statistics": "📊 Node Statistics",
                "relationship_statistics": "🔗 Relationship Statistics",
                "total": "Total",
                "node_type_distribution": "📋 Node Type Distribution",
                "relationship_type_distribution": "🔗 Relationship Type Distribution",
                "relationship_examples": "🔗 Relationship Examples",
                "view_nodes": "🔍 View {type} nodes (click to expand/collapse)",
                "more_nodes": "... {count} more nodes",
                "more_relationships": "📄 {count} more relationships...",
                "knowledge_graph_title": "🏥 TCM Knowledge Graph - Detailed Data View",
                "knowledge_graph_subtitle": "Complete knowledge graph data analysis and browsing",
                
                # 错误信息
                "name_type_required": "Node name and type cannot be empty",
                "invalid_json": "Attributes must be in valid JSON format",
                "csv_column_error": "CSV file column names do not meet requirements",
                "json_format_error": "JSON file format is incorrect",
                "unsupported_format": "Unsupported file format",
                "import_success": "File '{filename}' imported successfully!",
                "import_error": "File '{filename}' import failed: {error}",
                "save_success": "Data saved successfully",
                "save_error": "Save failed: {error}",
                "export_success": "Export successful",
                "export_error": "Export failed: {error}",
                
                # 语言切换
                "language": "🌐 语言",
                "switch_to_english": "🇺🇸 English",
                "switch_to_chinese": "🇨🇳 中文",
                
                # 其他
                "theme_switch_coming": "Theme switching feature coming soon!",
                "theme_switch": "Theme Switch",
                "plugin_result": "Plugin '{name}' returned: {result}",
                "plugin_run_result": "Plugin Run Result",
                "search_title": "Knowledge Graph Search",

                "search_title": "Knowledge Graph Search",
                "search_type": "Search Type:",
                "search_all": "All",
                "search_nodes": "Nodes Only", 
                "search_relationships": "Relationships Only",
                "search_placeholder": "Enter search keywords...",
                "search": "Search",
                "search_results": "Search Results",
                "search_ready": "Ready to search",
                "search_empty": "Please enter search keywords",
                "search_no_results": "No results found for '{}'",
                "search_found_results": "Found {} results for '{}'",
                "clear": "Clear",
                "locate_in_graph": "Locate in Graph"
            }
        }
    
    def get_text(self, key, **kwargs):
        """获取指定语言的文本，支持格式化参数"""
        text = self.translations.get(self.current_language, {}).get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text
    
    def set_language(self, language):
        """设置当前语言"""
        if language in self.translations:
            self.current_language = language
            return True
        return False
    
    def get_current_language(self):
        """获取当前语言"""
        return self.current_language