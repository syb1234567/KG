from neo4j import GraphDatabase

class GraphDataManager:
    def __init__(self, uri, user, password):
        self._uri = uri
        self._user = user
        self._password = password
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def execute_query(self, query, parameters=None):
        with self._driver.session() as session:
            result = session.run(query, parameters)
            return result

    def fetch_all(self, query, parameters=None):
        result = self.execute_query(query, parameters)
        return [record for record in result]

    def fetch_one(self, query, parameters=None):
        result = self.execute_query(query, parameters)
        return result.single()

    def initialize_graph(self):
        # 创建唯一约束等初始化操作
        constraints = [
            "CREATE CONSTRAINT ON (n:Entity) ASSERT n.name IS UNIQUE",
            # 添加其他需要的约束
        ]
        for constraint in constraints:
            self.execute_query(constraint)

    def create_node(self, node_name, node_type, properties):
        query = f"""
        CREATE (n:{node_type} {{name: $name, type: $type}}
        SET n += $properties
        RETURN id(n)
        """
        parameters = {
            "name": node_name,
            "type": node_type,
            "properties": properties
        }
        return self.fetch_one(query, parameters)

    def create_relationship(self, source_node_name, target_node_name, relationship_type):
        query = f"""
        MATCH (source), (target)
        WHERE source.name = $source_name AND target.name = $target_name
        CREATE (source)-[r:{relationship_type}]->(target)
        RETURN type(r)
        """
        parameters = {
            "source_name": source_node_name,
            "target_name": target_node_name,
            "relationship_type": relationship_type
        }
        return self.fetch_one(query, parameters)

# 使用示例
if __name__ == "__main__":
    manager = GraphDataManager("bolt://localhost:7687", "neo4j", "password")
    manager.initialize_graph()
    manager.create_node("Node1", "Entity", {"prop1": "value1"})
    manager.create_relationship("Node1", "Node2", "RELATED_TO")
    manager.close()
