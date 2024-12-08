from neo4j import GraphDatabase

class GraphDatabase:
    def __init__(self, uri, user, password):
        """
        初始化图数据库模块
        :param uri: Neo4j 数据库 URI
        :param user: Neo4j 用户名
        :param password: Neo4j 密码
        """
        self._uri = uri
        self._user = user
        self._password = password
        self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))

    def close(self):
        """
        关闭图数据库连接
        """
        self._driver.close()

    def execute_query(self, query, parameters=None):
        """
        执行数据库查询（增、删、改）
        :param query: Cypher 查询语句
        :param parameters: 查询参数（可选）
        :return: 查询结果
        """
        parameters = parameters or {}
        with self._driver.session() as session:
            return session.run(query, parameters)

    def fetch_all(self, query, parameters=None):
        """
        执行查询并返回所有结果
        :param query: Cypher 查询语句
        :param parameters: 查询参数（可选）
        :return: 查询结果列表
        """
        parameters = parameters or {}
        with self._driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def fetch_one(self, query, parameters=None):
        """
        执行查询并返回第一条结果
        :param query: Cypher 查询语句
        :param parameters: 查询参数（可选）
        :return: 查询结果或 None
        """
        parameters = parameters or {}
        with self._driver.session() as session:
            result = session.run(query, parameters)
            return result.single()

    def initialize_graph(self):
        """
        初始化图数据库的必要节点和关系
        """
        # 创建一个初始的节点（例如：知识图谱的基本节点，如药材、方剂、症候等）
        queries = [
            """
            CREATE CONSTRAINT ON (n:Node) ASSERT n.name IS UNIQUE;
            """,
            """
            CREATE CONSTRAINT ON (r:Relationship) ASSERT r.type IS UNIQUE;
            """
        ]

        for query in queries:
            self.execute_query(query)
        print("图数据库表结构已初始化")

    def create_node(self, name, node_type, attributes=None):
        """
        创建一个节点
        :param name: 节点名称
        :param node_type: 节点类型
        :param attributes: 节点的属性（可选）
        """
        query = """
        CREATE (n:Node {name: $name, type: $type, attributes: $attributes})
        """
        self.execute_query(query, {"name": name, "type": node_type, "attributes": attributes or {}})

    def create_relationship(self, node1_name, node2_name, relationship_type):
        """
        创建节点之间的关系
        :param node1_name: 源节点名称
        :param node2_name: 目标节点名称
        :param relationship_type: 关系类型
        """
        query = """
        MATCH (n1:Node {name: $node1_name}), (n2:Node {name: $node2_name})
        CREATE (n1)-[r:RELATES {type: $relationship_type}]->(n2)
        """
        self.execute_query(query, {"node1_name": node1_name, "node2_name": node2_name, "relationship_type": relationship_type})



