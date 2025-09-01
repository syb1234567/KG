import sys
import json
import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QSizePolicy, QSlider
)
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
import networkx as nx
from pathlib import Path

class NavigatorWidget(QWidget):
    """导航器小部件 - 显示完整图谱概览并支持视图导航"""
    
    # 信号：当用户在导航器中点击时，通知主视图更新
    view_change_requested = pyqtSignal(float, float, float)  # x, y, zoom
    
    def __init__(self, graph_manager, graph_view=None, parent=None):
        super().__init__(parent)
        self.graph_manager = graph_manager
        self.graph_view = graph_view
        
        # 导航器状态
        self.node_positions = {}
        self.graph_bounds = {"min_x": -1000, "max_x": 1000, "min_y": -1000, "max_y": 1000}
        self.current_viewport = {
            "center_x": 0, "center_y": 0, 
            "scale": 1.0, "view_width": 400, "view_height": 300
        }
        self.scale_factor = 1.0
        
        # vis.js 网络状态追踪
        self.network_initialized = False
        
        # 交互控制状态
        self.navigator_controlling = False  # 导航器是否正在控制主视图
        self.last_navigator_action_time = 0  # 最后一次导航器操作时间
        self.sync_pause_duration = 1000  # 减少暂停时间到1秒
        
        self.init_ui()
        self.calculate_layout()
        
        # 定时更新导航器和同步视图状态
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.sync_with_main_view)
        self.update_timer.start(1000)  # 每秒同步一次
    
    def set_graph_view(self, graph_view):
        """设置图形视图引用（用于延迟初始化）"""
        self.graph_view = graph_view
        print("导航器已连接到图形视图")
        
    def init_ui(self):
        """初始化界面"""
        self.setFixedSize(280, 250)
        self.setStyleSheet("""
            NavigatorWidget {
                border: 2px solid #2196F3;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title = QLabel("图谱导航器")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #1565C0;
                padding: 3px;
                background-color: #E3F2FD;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        
        # 状态指示器
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 16px;")
        self.status_indicator.setToolTip("网络连接状态")
        
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(self.status_indicator)
        layout.addLayout(title_layout)
        
        # 导航显示区域
        self.nav_display = NavigatorDisplay(self)
        self.nav_display.setMinimumHeight(150)
        layout.addWidget(self.nav_display)
        
        # 缩放控制
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("缩放:"))
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 300)  # 0.1x to 3.0x
        self.zoom_slider.setValue(100)  # 1.0x
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel("1.0x")
        self.zoom_label.setFixedWidth(35)
        zoom_layout.addWidget(self.zoom_label)
        layout.addLayout(zoom_layout)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        
        self.fit_btn = QPushButton("适应")
        self.fit_btn.clicked.connect(self.fit_to_window)
        self.fit_btn.setStyleSheet(self.button_style())
        
        self.center_btn = QPushButton("居中")
        self.center_btn.clicked.connect(self.center_view)
        self.center_btn.setStyleSheet(self.button_style())
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.force_refresh)
        self.refresh_btn.setStyleSheet(self.button_style())
        
        btn_layout.addWidget(self.fit_btn)
        btn_layout.addWidget(self.center_btn)
        btn_layout.addWidget(self.refresh_btn)
        layout.addLayout(btn_layout)
        
    def button_style(self):
        return """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 4px 8px;
                font-size: 10px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """
    
    def on_zoom_changed(self, value):
        """缩放滑块变化处理"""
        scale = value / 100.0
        self.zoom_label.setText(f"{scale:.1f}x")
        
        if self.graph_view and self.network_initialized:
            # 标记导航器正在控制
            self.navigator_controlling = True
            self.last_navigator_action_time = self.get_current_time()
            
            # 通过JavaScript控制vis.js网络缩放
            self.graph_view.page().runJavaScript(f"""
                if (typeof network !== 'undefined') {{
                    network.moveTo({{
                        scale: {scale},
                        animation: true
                    }});
                }}
            """)
            
            # 延迟恢复同步
            QTimer.singleShot(self.sync_pause_duration, self.resume_sync)
        
    def calculate_layout(self):
        """计算节点布局位置 - 改进的实现"""
        try:
            if self.graph_view:
                # 首先尝试从vis.js获取实际位置
                self.request_vis_positions()
            else:
                # 使用NetworkX布局计算
                self.fallback_layout_calculation()
                
        except Exception as e:
            print(f"导航器布局计算失败: {e}")
            self.fallback_layout_calculation()
    
    def request_vis_positions(self):
        """请求vis.js的节点位置"""
        if not self.graph_view:
            return
            
        self.graph_view.page().runJavaScript("""
            try {
                if (typeof network !== 'undefined' && network.body && network.body.data) {
                    var positions = network.getPositions();
                    var boundingBox = network.getBoundingBox();
                    
                    var result = {
                        success: true,
                        positions: positions,
                        bounds: boundingBox,
                        nodeCount: Object.keys(positions).length
                    };
                    
                    JSON.stringify(result);
                } else {
                    JSON.stringify({success: false, reason: 'network not ready'});
                }
            } catch(e) {
                JSON.stringify({success: false, reason: e.message});
            }
        """, self.on_layout_data_received)
    
    def on_layout_data_received(self, result):
        """处理从vis.js接收到的布局数据"""
        try:
            if result:
                data = json.loads(result)
                if data.get('success'):
                    positions = data.get('positions', {})
                    bounds = data.get('bounds', {})
                    
                    if positions and len(positions) > 0:
                        # 使用vis.js的实际位置
                        self.node_positions = {}
                        for node_id, pos in positions.items():
                            if isinstance(pos, dict) and 'x' in pos and 'y' in pos:
                                self.node_positions[node_id] = (pos['x'], pos['y'])
                        
                        # 更新边界
                        if bounds and all(key in bounds for key in ['minX', 'maxX', 'minY', 'maxY']):
                            margin = 100
                            self.graph_bounds = {
                                'min_x': bounds['minX'] - margin,
                                'max_x': bounds['maxX'] + margin,
                                'min_y': bounds['minY'] - margin,
                                'max_y': bounds['maxY'] + margin
                            }
                        else:
                            self.update_bounds_from_positions()
                        
                        print(f"从vis.js获取布局: {len(positions)} 个节点")
                        self.network_initialized = True
                        self.nav_display.update()
                        return
                        
        except Exception as e:
            print(f"处理vis.js布局数据失败: {e}")
        
        # 如果无法从vis.js获取，使用回退方案
        self.fallback_layout_calculation()
    
    def fallback_layout_calculation(self):
        """改进的回退布局计算方法"""
        try:
            graph_data = self.graph_manager.get_graph_data()
            nodes = graph_data.get('nodes', [])
            edges = graph_data.get('edges', [])
            
            if not nodes:
                print("没有节点数据，跳过布局计算")
                return
                
            print(f"使用NetworkX计算 {len(nodes)} 个节点的布局")
            
            # 创建NetworkX图用于布局计算
            G = nx.Graph()  # 使用无向图以获得更好的布局
            
            # 添加节点
            for node in nodes:
                node_name = node.get('name', '')
                if node_name:
                    G.add_node(node_name)
            
            # 添加边
            for edge in edges:
                source = edge.get('source', '')
                target = edge.get('target', '')
                if source and target and source in G.nodes() and target in G.nodes():
                    G.add_edge(source, target)
            
            # 计算布局
            if len(G.nodes()) > 0:
                try:
                    # 使用spring布局
                    pos = nx.spring_layout(
                        G, k=2, iterations=100, seed=42, scale=800
                    )
                except Exception as e:
                    print(f"Spring布局失败: {e}")
                    # 使用圆形布局作为备选
                    pos = self.create_circular_layout(list(G.nodes()))
                
                if pos:
                    # 转换位置坐标
                    self.node_positions = {}
                    for node_name, (x, y) in pos.items():
                        self.node_positions[node_name] = (x, y)
                    
                    # 计算边界
                    self.update_bounds_from_positions()
                    
                    print(f"NetworkX布局计算完成: {len(pos)} 个节点")
                
            self.nav_display.update()
            
        except Exception as e:
            print(f"回退布局计算失败: {e}")
            # 创建默认布局
            self.create_default_layout()
    
    def create_circular_layout(self, node_names):
        """创建圆形布局"""
        if not node_names:
            return {}
            
        pos = {}
        radius = 300
        center_x, center_y = 0, 0
        
        for i, node_name in enumerate(node_names):
            angle = 2 * math.pi * i / len(node_names)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            pos[node_name] = (x, y)
            
        return pos
    
    def create_default_layout(self):
        """创建默认的圆形布局"""
        try:
            graph_data = self.graph_manager.get_graph_data()
            nodes = graph_data.get('nodes', [])
            
            if not nodes:
                return
            
            node_names = [node.get('name', '') for node in nodes if node.get('name', '')]
            pos = self.create_circular_layout(node_names)
            
            if pos:
                self.node_positions = pos
                self.update_bounds_from_positions()
                print(f"创建默认圆形布局: {len(nodes)} 个节点")
                
        except Exception as e:
            print(f"创建默认布局失败: {e}")
            
    def sync_with_main_view(self):
        """与主视图同步状态 - 更智能的同步控制"""
        if not self.graph_view:
            self.status_indicator.setStyleSheet("color: #FFC107; font-size: 16px;")
            self.status_indicator.setToolTip("等待图形视图连接...")
            return
        
        # 如果导航器正在控制主视图，减少同步频率但不完全停止
        current_time = self.get_current_time()
        if self.navigator_controlling:
            # 在控制期间，减少同步频率
            time_since_last_action = current_time - self.last_navigator_action_time
            if time_since_last_action < self.sync_pause_duration:
                # 延长下次同步时间
                self.update_timer.setInterval(2000)  # 2秒间隔
                self.status_indicator.setStyleSheet("color: #FF9800; font-size: 16px;")
                self.status_indicator.setToolTip("导航器控制中...")
                return
            else:
                # 控制时间结束，恢复正常同步
                self.navigator_controlling = False
                self.update_timer.setInterval(1000)  # 恢复1秒间隔
                print("导航器控制结束，恢复同步")
        
        # 正常同步
        self.update_timer.setInterval(1000)  # 确保1秒间隔
            
        # 获取当前视图状态
        self.graph_view.page().runJavaScript("""
            try {
                if (typeof network !== 'undefined' && network.body && network.body.view) {
                    var viewPosition = network.getViewPosition();
                    var scale = network.getScale();
                    var canvas = network.canvas.frame.canvas;
                    
                    JSON.stringify({
                        success: true,
                        center_x: viewPosition.x || 0,
                        center_y: viewPosition.y || 0,
                        scale: scale || 1.0,
                        canvas_width: canvas.clientWidth || 400,
                        canvas_height: canvas.clientHeight || 300
                    });
                } else {
                    JSON.stringify({error: 'network not ready'});
                }
            } catch (e) {
                JSON.stringify({error: 'JavaScript error: ' + e.message});
            }
        """, self.on_sync_data_received)
    
    def on_sync_data_received(self, result):
        """处理从主视图接收到的同步数据 - 更宽松的同步策略"""
        try:
            if result:
                data = json.loads(result)
                if data.get('success'):
                    # 更新视口状态
                    self.current_viewport.update({
                        'center_x': data.get('center_x', 0),
                        'center_y': data.get('center_y', 0),
                        'scale': data.get('scale', 1.0),
                        'canvas_width': data.get('canvas_width', 400),
                        'canvas_height': data.get('canvas_height', 300)
                    })
                    
                    # 只有在非控制状态下才更新缩放滑块
                    if not self.navigator_controlling:
                        scale = data.get('scale', 1.0)
                        self.zoom_slider.blockSignals(True)
                        self.zoom_slider.setValue(int(scale * 100))
                        self.zoom_label.setText(f"{scale:.1f}x")
                        self.zoom_slider.blockSignals(False)
                    
                    # 更新显示
                    self.nav_display.update()
                    
                    # 设置状态指示器
                    if self.navigator_controlling:
                        self.status_indicator.setStyleSheet("color: #FF9800; font-size: 16px;")
                        self.status_indicator.setToolTip("导航器控制中...")
                    else:
                        self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 16px;")
                        self.status_indicator.setToolTip("已同步到主视图")
                else:
                    error_msg = data.get('error', 'unknown error')
                    if 'not ready' in error_msg:
                        self.status_indicator.setStyleSheet("color: #FFC107; font-size: 16px;")
                        self.status_indicator.setToolTip("等待网络初始化...")
                    else:
                        self.status_indicator.setStyleSheet("color: #F44336; font-size: 16px;")
                        self.status_indicator.setToolTip(f"同步错误: {error_msg}")
        except Exception as e:
            print(f"处理同步数据失败: {e}")
    
    def update_bounds_from_positions(self):
        """根据实际节点位置更新边界"""
        if not self.node_positions:
            return
            
        x_coords = [pos[0] for pos in self.node_positions.values()]
        y_coords = [pos[1] for pos in self.node_positions.values()]
        
        if x_coords and y_coords:
            # 计算边界，添加适当的边距
            margin = max(200, (max(x_coords) - min(x_coords)) * 0.1)
            self.graph_bounds = {
                "min_x": min(x_coords) - margin,
                "max_x": max(x_coords) + margin,
                "min_y": min(y_coords) - margin,
                "max_y": max(y_coords) + margin
            }
            
            print(f"更新边界: x[{self.graph_bounds['min_x']:.0f}, {self.graph_bounds['max_x']:.0f}], "
                  f"y[{self.graph_bounds['min_y']:.0f}, {self.graph_bounds['max_y']:.0f}]")
            
    def update_viewport_from_main(self, center_x, center_y, scale, width, height):
        """从主视图更新视口信息（外部调用接口）"""
        self.current_viewport.update({
            "center_x": center_x,
            "center_y": center_y,
            "scale": scale,
            "view_width": width,
            "view_height": height
        })
        self.nav_display.update()
        
    def fit_to_window(self):
        """适应窗口大小"""
        if self.graph_view and self.network_initialized:
            # 标记导航器正在控制
            self.navigator_controlling = True
            self.last_navigator_action_time = self.get_current_time()
            
            self.graph_view.page().runJavaScript("""
                if (typeof network !== 'undefined') {
                    network.fit({
                        animation: true
                    });
                }
            """)
            
            # 延迟恢复同步
            QTimer.singleShot(self.sync_pause_duration, self.resume_sync)
            
    def center_view(self):
        """居中显示"""
        if self.graph_view and self.network_initialized:
            # 标记导航器正在控制
            self.navigator_controlling = True
            self.last_navigator_action_time = self.get_current_time()
            
            self.graph_view.page().runJavaScript("""
                if (typeof network !== 'undefined') {
                    network.moveTo({
                        position: {x: 0, y: 0},
                        scale: 1.0,
                        animation: true
                    });
                }
            """)
            
            # 延迟恢复同步
            QTimer.singleShot(self.sync_pause_duration, self.resume_sync)
    
    def force_refresh(self):
        """强制刷新导航器"""
        print("强制刷新导航器...")
        
        # 重置所有状态
        self.network_initialized = False
        self.node_positions.clear()
        self.navigator_controlling = False
        self.last_navigator_action_time = 0
        
        # 重新计算布局
        QTimer.singleShot(100, self.calculate_layout)
        
        # 强制同步视图状态
        if self.graph_view:
            QTimer.singleShot(500, self.sync_with_main_view)
            
        print("导航器刷新完成")

    def get_current_time(self):
            """获取当前时间（毫秒）"""
            from time import time
            return int(time() * 1000)
        
    def resume_sync(self):
            """恢复同步状态"""
            self.navigator_controlling = False
            print("导航器控制结束，恢复同步")
class NavigatorDisplay(QWidget):
    """导航器显示区域 - 负责绘制图谱概览和视口框"""
    
    def __init__(self, navigator_widget):
        super().__init__()
        self.navigator = navigator_widget
        self.setMouseTracking(True)
        self.dragging = False
        self.last_mouse_pos = None
        
        # 拖拽控制
        self.drag_threshold = 5  # 最小拖拽距离
        self.last_navigation_time = 0  # 上次导航时间
        self.navigation_interval = 30  # 导航间隔(毫秒)
        self.drag_end_timer = QTimer()  # 拖拽结束定时器
        self.drag_end_timer.setSingleShot(True)
        self.drag_end_timer.timeout.connect(self.on_drag_end)
        
    def paintEvent(self, event):
        """绘制导航器内容"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 清空背景
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # 绘制边框
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        
        try:
            if self.navigator.node_positions:
                self.draw_edges(painter)
                self.draw_nodes(painter)
                self.draw_viewport_frame(painter)
            else:
                self.draw_loading_message(painter)
                
            self.draw_coordinates_info(painter)
        except Exception as e:
            print(f"导航器绘制失败: {e}")
            self.draw_error_message(painter, str(e))
            
        painter.end()
    
    def draw_loading_message(self, painter):
        """绘制加载消息"""
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.setFont(QFont("Arial", 12))
        
        text = "正在加载图谱数据..."
        rect = painter.fontMetrics().boundingRect(text)
        x = (self.width() - rect.width()) // 2
        y = (self.height() - rect.height()) // 2
        
        painter.drawText(x, y, text)
    
    def draw_error_message(self, painter, error_msg):
        """绘制错误消息"""
        painter.setPen(QPen(QColor(200, 100, 100)))
        painter.setFont(QFont("Arial", 10))
        
        text = f"绘制错误: {error_msg[:30]}..."
        rect = painter.fontMetrics().boundingRect(text)
        x = (self.width() - rect.width()) // 2
        y = (self.height() - rect.height()) // 2
        
        painter.drawText(x, y, text)
        
    def draw_nodes(self, painter):
        """改进的节点绘制方法"""
        if not self.navigator.node_positions:
            return
            
        # 获取节点类型颜色映射
        graph_data = self.navigator.graph_manager.get_graph_data()
        type_colors = self.get_type_colors(graph_data.get('nodes', []))
        
        # 绘制所有节点
        drawn_count = 0
        for node in graph_data.get('nodes', []):
            name = node.get('name', '')
            if name and name in self.navigator.node_positions:
                x, y = self.navigator.node_positions[name]
                
                # 转换到显示坐标
                display_x, display_y = self.transform_coordinates(x, y)
                
                # 绘制节点
                if -20 <= display_x <= self.width() + 20 and -20 <= display_y <= self.height() + 20:
                    # 根据节点类型选择颜色
                    color = type_colors.get(node.get('type', 'default'), QColor(100, 149, 237))
                    
                    painter.setBrush(QBrush(color))
                    painter.setPen(QPen(color.darker(), 1))
                    
                    # 节点大小
                    node_size = 3
                    painter.drawEllipse(
                        int(display_x - node_size), 
                        int(display_y - node_size), 
                        node_size * 2, 
                        node_size * 2
                    )
                    drawn_count += 1
                
        if drawn_count == 0:
            print(f"警告: 没有绘制任何节点 (总共 {len(self.navigator.node_positions)} 个)")
            
    def draw_edges(self, painter):
        """改进的边绘制方法"""
        graph_data = self.navigator.graph_manager.get_graph_data()
        edges = graph_data.get('edges', [])
        
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        
        for edge in edges:
            source = edge.get('source', '')
            target = edge.get('target', '')
            
            if (source and target and 
                source in self.navigator.node_positions and 
                target in self.navigator.node_positions):
                
                x1, y1 = self.navigator.node_positions[source]
                x2, y2 = self.navigator.node_positions[target]
                
                # 转换到显示坐标
                display_x1, display_y1 = self.transform_coordinates(x1, y1)
                display_x2, display_y2 = self.transform_coordinates(x2, y2)
                
                # 绘制边线
                painter.drawLine(
                    int(display_x1), int(display_y1), 
                    int(display_x2), int(display_y2)
                )
                
    def draw_viewport_frame(self, painter):
        """改进的视口框绘制"""
        viewport = self.navigator.current_viewport
        
        if not self.navigator.network_initialized:
            # 显示默认视口框
            frame_width = self.width() // 3
            frame_height = self.height() // 3
            frame_x = (self.width() - frame_width) // 2
            frame_y = (self.height() - frame_height) // 2
        else:
            # 根据实际视口计算框的位置和大小
            center_x = viewport.get('center_x', 0)
            center_y = viewport.get('center_y', 0)
            scale = max(0.01, viewport.get('scale', 1.0))
            canvas_width = viewport.get('canvas_width', 400)
            canvas_height = viewport.get('canvas_height', 300)
            
            # 计算视口在图谱坐标中的实际范围
            actual_view_width = canvas_width / scale
            actual_view_height = canvas_height / scale
            
            # 视口的四个角的坐标
            left = center_x - actual_view_width / 2
            right = center_x + actual_view_width / 2
            top = center_y - actual_view_height / 2
            bottom = center_y + actual_view_height / 2
            
            # 转换到导航器显示坐标
            display_left, display_top = self.transform_coordinates(left, top)
            display_right, display_bottom = self.transform_coordinates(right, bottom)
            
            # 确保框的尺寸和位置正确
            frame_x = int(min(display_left, display_right))
            frame_y = int(min(display_top, display_bottom))
            frame_width = int(abs(display_right - display_left))
            frame_height = int(abs(display_bottom - display_top))
            
            # 限制框的最小大小
            frame_width = max(8, frame_width)
            frame_height = max(8, frame_height)
        
        # 绘制红色视口框
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.setBrush(QBrush(QColor(255, 0, 0, 30)))
        
        # 绘制实心框
        rect = QRect(frame_x, frame_y, frame_width, frame_height)
        painter.drawRect(rect)
        
        # 绘制角标记
        corner_size = min(6, frame_width//4, frame_height//4)
        if corner_size > 1:
            painter.setBrush(QBrush(QColor(255, 0, 0)))
            painter.drawRect(frame_x, frame_y, corner_size, corner_size)
            painter.drawRect(frame_x + frame_width - corner_size, frame_y, corner_size, corner_size)
            painter.drawRect(frame_x, frame_y + frame_height - corner_size, corner_size, corner_size)
            painter.drawRect(frame_x + frame_width - corner_size, frame_y + frame_height - corner_size, corner_size, corner_size)
        
    def draw_coordinates_info(self, painter):
        """绘制坐标和统计信息"""
        info_lines = []
        
        if self.navigator.network_initialized:
            viewport = self.navigator.current_viewport
            info_lines.append(f"中心: ({viewport.get('center_x', 0):.0f}, {viewport.get('center_y', 0):.0f})")
            info_lines.append(f"缩放: {viewport.get('scale', 1.0):.2f}x")
        else:
            info_lines.append("等待网络连接...")
            
        # 添加统计信息
        node_count = len(self.navigator.node_positions)
        if node_count > 0:
            info_lines.append(f"节点: {node_count}")
            
        # 绘制信息
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.setFont(QFont("Arial", 8))
        
        y_offset = self.height() - 5
        for line in reversed(info_lines):
            painter.drawText(5, y_offset, line)
            y_offset -= 12
        
    def get_type_colors(self, nodes):
        """获取节点类型颜色映射"""
        type_color_map = {
            "方剂": QColor(255, 160, 122),
            "药理": QColor(173, 216, 230),
            "药材": QColor(152, 251, 152),
            "疾病": QColor(211, 211, 211),
            "default": QColor(151, 194, 252)
        }
        
        result = {}
        for node in nodes:
            node_type = node.get('type', 'default')
            result[node_type] = type_color_map.get(node_type, type_color_map['default'])
        
        return result
        
    def transform_coordinates(self, x, y):
        """改进的坐标转换方法"""
        bounds = self.navigator.graph_bounds
        
        # 计算图谱的实际范围
        width_range = bounds["max_x"] - bounds["min_x"]
        height_range = bounds["max_y"] - bounds["min_y"]
        
        # 避免除零错误
        if width_range == 0:
            width_range = 1000
        if height_range == 0:
            height_range = 1000
        
        # 计算相对位置 (0-1)
        rel_x = (x - bounds["min_x"]) / width_range
        rel_y = (y - bounds["min_y"]) / height_range
        
        # 转换到显示区域，保留边距
        margin = 5
        display_width = max(10, self.width() - 2 * margin)
        display_height = max(10, self.height() - 2 * margin)
        
        display_x = margin + rel_x * display_width
        display_y = margin + rel_y * display_height
        
        return display_x, display_y
    
    def transform_display_to_graph(self, display_x, display_y):
        """将显示坐标转换为图谱坐标"""
        bounds = self.navigator.graph_bounds
        margin = 5
        
        # 计算相对位置
        display_width = max(10, self.width() - 2 * margin)
        display_height = max(10, self.height() - 2 * margin)
        
        rel_x = (display_x - margin) / display_width
        rel_y = (display_y - margin) / display_height
        
        # 转换到图谱坐标
        width_range = bounds["max_x"] - bounds["min_x"]
        height_range = bounds["max_y"] - bounds["min_y"]
        
        graph_x = bounds["min_x"] + rel_x * width_range
        graph_y = bounds["min_y"] + rel_y * height_range
        
        return graph_x, graph_y
        
    def mousePressEvent(self, event):
        """鼠标按下事件 - 改进版本"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_mouse_pos = event.pos()
            
            # 立即导航一次
            self.navigate_to_position(event.x(), event.y())
            self.last_navigation_time = self.get_current_time()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 改进版本，控制导航频率"""
        if self.dragging and self.last_mouse_pos:
            # 检查是否移动了足够的距离
            dx = abs(event.x() - self.last_mouse_pos.x())
            dy = abs(event.y() - self.last_mouse_pos.y())
            
            if dx < self.drag_threshold and dy < self.drag_threshold:
                return
                
            # 控制导航频率
            current_time = self.get_current_time()
            if current_time - self.last_navigation_time >= self.navigation_interval:
                self.navigate_to_position(event.x(), event.y())
                self.last_navigation_time = current_time
                self.last_mouse_pos = event.pos()
                
            # 重置拖拽结束定时器
            self.drag_end_timer.start(500)  # 500ms后认为拖拽结束
            
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 改进版本"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.last_mouse_pos = None
            
            # 最终导航到释放位置
            self.navigate_to_position(event.x(), event.y())
            
            # 启动拖拽结束定时器
            self.drag_end_timer.start(500)
            
    def on_drag_end(self):
        """拖拽结束处理 - 恢复主视图控制"""
        print("拖拽操作结束，恢复主视图控制")
        if self.navigator:
            self.navigator.navigator_controlling = False
            
    def get_current_time(self):
        """获取当前时间（毫秒）"""
        from time import time
        return int(time() * 1000)
            
    def navigate_to_position(self, display_x, display_y):
        """导航到指定显示位置 - 优化版本，减少冲突"""
        # 将点击位置转换为图谱坐标
        graph_x, graph_y = self.transform_display_to_graph(display_x, display_y)
        
        # 通知主视图移动到该位置
        if self.navigator.graph_view and self.navigator.network_initialized:
            # 只在开始拖拽时标记控制状态，不在每次移动时重复标记
            if not self.navigator.navigator_controlling:
                self.navigator.navigator_controlling = True
                self.navigator.last_navigator_action_time = self.navigator.get_current_time()
                print("开始导航器控制模式")
            
            # 发送导航命令，但不使用动画以减少冲突
            self.navigator.graph_view.page().runJavaScript(f"""
                if (typeof network !== 'undefined') {{
                    network.moveTo({{
                        position: {{x: {graph_x}, y: {graph_y}}},
                        animation: false
                    }});
                }}
            """)
            
            # 不立即恢复同步，等待拖拽结束

    
    # 插件接口
class NavigatorPlugin:
    """导航器插件"""
    
    def __init__(self):
        self.name = "图谱导航器"
        self.description = "显示完整图谱概览，支持实时视图同步和快速导航"
        self.version = "2.1.0"
        self.enabled = True
        
    def get_widget(self, graph_manager, graph_view=None, parent=None):
        """获取导航器部件"""
        return NavigatorWidget(graph_manager, graph_view, parent)
        
    def run(self, graph_manager):
        """插件运行入口（用于插件管理器）"""
        try:
            node_count = len(graph_manager.get_all_nodes())
            edge_count = len(graph_manager.get_all_relationships())
            return f"导航器插件已激活 - 监控 {node_count} 个节点, {edge_count} 条关系"
        except Exception as e:
            return f"导航器插件激活失败: {str(e)}"


# 用于插件系统的工厂函数
def create_plugin():
    """创建插件实例"""
    return NavigatorPlugin()


# 测试代码
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QSplitter
    import sys
    
    # 模拟图数据管理器
    class MockGraphManager:
        def get_graph_data(self):
            # 模拟更多的节点和连接，测试完整布局
            nodes = []
            edges = []
            
            # 创建一个更复杂的测试图
            node_types = ["药材", "方剂", "疾病", "药理"]
            base_nodes = [
                "人参", "黄芪", "当归", "白术", "茯苓", "甘草", "川芎", "熟地黄",
                "四君子汤", "补中益气汤", "当归补血汤", "八珍汤",
                "气虚", "血虚", "脾胃虚弱", "心悸", "失眠", "乏力",
                "补气", "养血", "健脾", "安神", "益气养血", "调和诸药"
            ]
            
            # 创建节点
            for i, name in enumerate(base_nodes):
                node_type = node_types[i % len(node_types)]
                nodes.append({'name': name, 'type': node_type})
            
            # 创建一些边
            connections = [
                ("人参", "补气"), ("黄芪", "补气"), ("当归", "养血"),
                ("四君子汤", "人参"), ("四君子汤", "白术"), ("四君子汤", "茯苓"),
                ("补中益气汤", "人参"), ("补中益气汤", "黄芪"),
                ("当归补血汤", "当归"), ("当归补血汤", "黄芪"),
                ("补气", "气虚"), ("养血", "血虚"), ("健脾", "脾胃虚弱"),
                ("甘草", "调和诸药"), ("川芎", "养血"), ("熟地黄", "养血")
            ]
            
            for source, target in connections:
                if source in base_nodes and target in base_nodes:
                    edges.append({
                        'source': source, 
                        'target': target, 
                        'relation_type': '相关'
                    })
            
            return {'nodes': nodes, 'edges': edges}
        
        def get_all_nodes(self):
            return self.get_graph_data()['nodes']
        
        def get_all_relationships(self):
            return self.get_graph_data()['edges']
    
    app = QApplication(sys.argv)
    
    # 创建主窗口测试
    window = QMainWindow()
    splitter = QSplitter(Qt.Horizontal)
    
    # 左侧：模拟主视图
    main_view = QWidget()
    main_view.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
    main_label = QLabel("主图谱视图区域\n(模拟)\n\n修复后的导航器应该能够:\n• 显示完整的节点布局\n• 正确计算边界和比例\n• 支持点击导航\n• 同步视图状态")
    main_label.setAlignment(Qt.AlignCenter)
    main_layout = QVBoxLayout(main_view)
    main_layout.addWidget(main_label)
    
    # 右侧：导航器
    mock_manager = MockGraphManager()
    navigator = NavigatorWidget(mock_manager)
    
    splitter.addWidget(main_view)
    splitter.addWidget(navigator)
    splitter.setSizes([600, 300])
    
    window.setCentralWidget(splitter)
    window.setWindowTitle("Navigator Plugin Test - Fixed Version")
    window.resize(900, 500)
    window.show()
    
    print("导航器测试启动 - 应该显示完整的图谱布局")
    print(f"测试数据: {len(mock_manager.get_all_nodes())} 个节点")
    
    sys.exit(app.exec_())