class Config:
    """
    全局配置类
    """
    # NetworkX 图数据库配置
    GRAPH_STORAGE_PATH = "graph.json"  # 本地图数据库存储文件路径（JSON 格式）
    GRAPH_MAX_NODES = 1000  # 可视化时的最大节点数，避免过载

    # 应用配置
    DEBUG = True  # 是否启用调试模式
    HOST = "0.0.0.0"  # 主机地址
    PORT = 5000  # 服务运行端口

    # 文件导入相关配置
    ALLOWED_EXTENSIONS = {"json", "docx", "xlsx","csv"}  # 允许导入的文件类型（包括新增的 Excel）

    # 插件配置
    PLUGIN_DIRECTORY = "plugins/"  # 插件文件存储目录

# 可选的开发环境配置（如需要多环境支持）
class DevelopmentConfig(Config):
    """
    开发环境配置
    """
    DEBUG = True
    GRAPH_STORAGE_PATH = "graph_dev.json"  # 开发环境图数据库存储文件

class ProductionConfig(Config):
    """
    生产环境配置
    """
    DEBUG = False
    GRAPH_STORAGE_PATH = "graph_prod.json"  # 生产环境图数据库存储文件

class TestingConfig(Config):
    """
    测试环境配置
    """
    DEBUG = True
    GRAPH_STORAGE_PATH = "graph_test.json"  # 测试环境图数据库存储文件

