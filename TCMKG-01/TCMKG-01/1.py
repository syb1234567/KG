
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtCore import QUrl, QTimer

class WebEngineDebugWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebEngine 调试窗口")
        self.setGeometry(100, 100, 900, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        self.status_label = QLabel("状态: 初始化中...")
        self.status_label.setStyleSheet("padding: 10px; background: #f0f0f0; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # 测试按钮
        btn_layout = QVBoxLayout()
        
        self.test1_btn = QPushButton("测试1: 基础HTML")
        self.test1_btn.clicked.connect(self.test_basic_html)
        btn_layout.addWidget(self.test1_btn)
        
        self.test2_btn = QPushButton("测试2: 简单文本")
        self.test2_btn.clicked.connect(self.test_simple_text)
        btn_layout.addWidget(self.test2_btn)
        
        self.test3_btn = QPushButton("测试3: 加载百度")
        self.test3_btn.clicked.connect(self.test_load_baidu)
        btn_layout.addWidget(self.test3_btn)
        
        self.test4_btn = QPushButton("测试4: 检查设置")
        self.test4_btn.clicked.connect(self.test_settings)
        btn_layout.addWidget(self.test4_btn)
        
        layout.addLayout(btn_layout)
        
        # 创建WebView
        self.web_view = QWebEngineView()
        
        # 设置明显的边框便于识别
        self.web_view.setStyleSheet("""
            QWebEngineView {
                border: 5px solid red;
                background-color: yellow;
                min-height: 400px;
            }
        """)
        
        # 连接信号
        self.web_view.loadStarted.connect(self.on_load_started)
        self.web_view.loadFinished.connect(self.on_load_finished)
        self.web_view.loadProgress.connect(self.on_load_progress)
        
        layout.addWidget(self.web_view)
        
        # 启用WebEngine调试
        self.setup_webengine()
        
        # 自动开始第一个测试
        QTimer.singleShot(1000, self.test_basic_html)
    
    def setup_webengine(self):
        """配置WebEngine设置"""
        try:
            settings = self.web_view.page().settings()
            
            # 启用各种功能
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
            settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
            
            # 禁用缓存
            profile = self.web_view.page().profile()
            profile.setHttpCacheType(0)  # 无缓存
            
            self.update_status("WebEngine设置完成")
            
        except Exception as e:
            self.update_status(f"WebEngine设置失败: {e}")
    
    def update_status(self, message):
        """更新状态显示"""
        print(f"状态: {message}")
        self.status_label.setText(f"状态: {message}")
    
    def on_load_started(self):
        self.update_status("开始加载...")
    
    def on_load_progress(self, progress):
        self.update_status(f"加载进度: {progress}%")
    
    def on_load_finished(self, ok):
        if ok:
            self.update_status("✅ 页面加载成功!")
            # 尝试执行JavaScript检查
            self.web_view.page().runJavaScript(
                "document.body ? document.body.innerHTML.length : 0",
                self.js_callback
            )
        else:
            self.update_status("❌ 页面加载失败!")
    
    def js_callback(self, result):
        self.update_status(f"页面内容长度: {result} 字符")
    
    def test_basic_html(self):
        """测试1: 基础HTML"""
        self.update_status("测试1: 加载基础HTML...")
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { 
                    background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                    color: white;
                    font-family: Arial;
                    text-align: center;
                    padding: 50px;
                    margin: 0;
                    height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-direction: column;
                }
                h1 { font-size: 36px; margin: 20px; }
                .box { 
                    background: rgba(255,255,255,0.2);
                    padding: 30px;
                    border-radius: 10px;
                    border: 3px solid white;
                }
            </style>
        </head>
        <body>
            <div class="box">
                <h1>🎨 测试1: 基础HTML</h1>
                <p>如果你看到这个彩色页面，说明HTML渲染正常</p>
                <p id="time">时间: 加载中...</p>
            </div>
            <script>
                console.log('JavaScript开始执行');
                document.getElementById('time').innerHTML = '时间: ' + new Date().toLocaleString();
                console.log('JavaScript执行完成');
                document.title = '测试1完成';
            </script>
        </body>
        </html>
        """
        
        self.web_view.setHtml(html, QUrl("about:blank"))
    
    def test_simple_text(self):
        """测试2: 最简单文本"""
        self.update_status("测试2: 加载简单文本...")
        
        html = """
        <html>
        <body style="background: red; color: white; font-size: 24px; padding: 50px;">
            <h1>简单测试页面</h1>
            <p>这是最基础的HTML测试</p>
        </body>
        </html>
        """
        
        self.web_view.setHtml(html, QUrl("about:blank"))
    
    def test_load_baidu(self):
        """测试3: 加载外部网站"""
        self.update_status("测试3: 加载百度...")
        self.web_view.load(QUrl("https://www.baidu.com"))
    
    def test_settings(self):
        """测试4: 检查WebEngine设置"""
        self.update_status("测试4: 检查设置...")
        
        settings = self.web_view.page().settings()
        
        info = f"""
        <html>
        <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
            <h2>WebEngine 设置信息</h2>
            <ul>
                <li>JavaScript: {'启用' if settings.testAttribute(QWebEngineSettings.JavascriptEnabled) else '禁用'}</li>
                <li>本地内容访问: {'启用' if settings.testAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls) else '禁用'}</li>
                <li>错误页面: {'启用' if settings.testAttribute(QWebEngineSettings.ErrorPageEnabled) else '禁用'}</li>
                <li>插件: {'启用' if settings.testAttribute(QWebEngineSettings.PluginsEnabled) else '禁用'}</li>
            </ul>
            <p>WebView 大小: {self.web_view.width()} x {self.web_view.height()}</p>
            <p>可见性: {'可见' if self.web_view.isVisible() else '不可见'}</p>
        </body>
        </html>
        """
        
        self.web_view.setHtml(info, QUrl("about:blank"))

def main():
    # 设置环境变量（在创建应用前）
    import os
    os.environ['QTWEBENGINE_DISABLE_SANDBOX'] = '1'
    
    app = QApplication(sys.argv)
    
    # 设置应用程序属性（修复版本兼容性）
    try:
        from PyQt5.QtCore import Qt
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        print("注意: 当前PyQt5版本不支持高DPI设置")
    
    window = WebEngineDebugWindow()
    window.show()
    
    print("调试窗口已显示，请测试各个按钮")
    print("特别关注WebView区域（应该有红色边框）")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()