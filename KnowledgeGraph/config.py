class Config:
    """
    全局配置类
    """
    # Neo4j 配置
    NEO4J_URI = "bolt://localhost:7687"  # Neo4j 连接 URI
    NEO4J_USER = "neo4j"  # Neo4j 用户名
    NEO4J_PASSWORD = "password"  # Neo4j 密码

    # 应用配置
    DEBUG = True  # 是否启用调试模式
    HOST = "0.0.0.0"  # 主机地址
    PORT = 5000  # 服务运行端口

    # 文件导入相关配置
    ALLOWED_EXTENSIONS = {"json", "docx", "xlsx"}  # 允许导入的文件类型（包括新增的 Excel）

    # 插件配置
    PLUGIN_DIRECTORY = "plugins/"  # 插件文件存储目录

    # 其他配置
    GRAPH_MAX_NODES = 1000  # 可视化时的最大节点数，避免过载

# 可选的开发环境配置（如需要多环境支持）
class DevelopmentConfig(Config):
    """
    开发环境配置
    """
    DEBUG = True
    NEO4J_URI = "bolt://localhost:7687"  # 本地开发环境的 Neo4j 配置

class ProductionConfig(Config):
    """
    生产环境配置
    """
    DEBUG = False
    NEO4J_URI = "bolt://prod.neo4j.com:7687"  # 生产环境的 Neo4j 配置
    NEO4J_USER = "prod_user"  # 生产环境的用户名
    NEO4J_PASSWORD = "prod_password"  # 生产环境的密码

class TestingConfig(Config):
    """
    测试环境配置
    """
    DEBUG = True
    NEO4J_URI = "bolt://localhost:7687"  # 测试环境的 Neo4j 配置
    NEO4J_USER = "test_user"  # 测试环境的用户名
    NEO4J_PASSWORD = "test_password"  # 测试环境的密码

