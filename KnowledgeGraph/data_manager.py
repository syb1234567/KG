from neo4j import GraphDatabase
import json

class GraphDataManager:
    def __init__(self, uri, user, password):
        """
        初始化图数据库连接
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

    # ------------------- 节点操作 -------------------

    def add_node(self, name, node_type, attributes=None):
        """
        添加节点
        :param name: 节点名称
        :param node_type: 节点类型
        :param attributes: 节点属性
        """
        query = """
        CREATE (n:Node {name: $name, type: $node_type, attributes: $attributes})
        """
        self._execute_query(query, {"name": name, "node_type": node_type, "attributes": json.dumps(attributes) if attributes else "{}"})

    def get_all_nodes(self):
        """
        获取所有节点
        """
        query = "MATCH (n:Node) RETURN n.name, n.type, n.attributes"
        return self._fetch_all(query)

    def update_node(self, name, node_type=None, attributes=None):
        """
        更新节点信息
        """
        query = """
        MATCH (n:Node {name: $name})
        SET 
            n.type = COALESCE($node_type, n.type),
            n.attributes = COALESCE($attributes, n.attributes)
        """
        self._execute_query(query, {"name": name, "node_type": node_type, "attributes": json.dumps(attributes) if attributes else None})

    def delete_node(self, name):
        """
        删除节点及相关关系
        """
        query = """
        MATCH (n:Node {name: $name})
        DETACH DELETE n
        """
        self._execute_query(query, {"name": name})

    # ------------------- 关系操作 -------------------

    def add_relationship(self, source_name, target_name, relation_type):
        """
        添加节点之间的关系
        """
        query = """
        MATCH (source:Node {name: $source_name}), (target:Node {name: $target_name})
        CREATE (source)-[:RELATES {type: $relation_type}]->(target)
        """
        self._execute_query(query, {"source_name": source_name, "target_name": target_name, "relation_type": relation_type})

    def get_all_relationships(self):
        """
        获取所有关系
        """
        query = """
        MATCH (source:Node)-[r:RELATES]->(target:Node)
        RETURN source.name, target.name, r.type
        """
        return self._fetch_all(query)

    def delete_relationship(self, source_name, target_name):
        """
        删除节点之间的关系
        """
        query = """
        MATCH (source:Node {name: $source_name})-[r:RELATES]->(target:Node {name: $target_name})
        DELETE r
        """
        self._execute_query(query, {"source_name": source_name, "target_name": target_name})

    # ------------------- 辅助方法 -------------------

    def _execute_query(self, query, parameters=None):
        """
        执行查询，不返回结果
        """
        parameters = parameters or {}
        with self._driver.session() as session:
            session.run(query, parameters)

    def _fetch_all(self, query, parameters=None):
        """
        执行查询并返回所有结果
        """
        parameters = parameters or {}
        with self._driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]
