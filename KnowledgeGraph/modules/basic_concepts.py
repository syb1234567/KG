# modules/basic_concepts.py

class BasicConcepts:
    # 基础概念
    FIVE_ELEMENTS = ["木", "火", "土", "金", "水"]  # 五行
    SIX_QI = ["风", "寒", "暑", "湿", "燥", "火"]  # 六气
    YIN_YANG = ["阴", "阳"]  # 阴阳

    @staticmethod
    def classify(node_name):
        """
        分类节点为基础概念类别
        :param node_name: 节点名称
        :return: 分类结果 (五行, 六气, 阴阳, 未知)
        """
        if node_name in BasicConcepts.FIVE_ELEMENTS:
            return "五行"
        elif node_name in BasicConcepts.SIX_QI:
            return "六气"
        elif node_name in BasicConcepts.YIN_YANG:
            return "阴阳"
        return "未知分类"

    @staticmethod
    def infer_relationships(node1, node2):
        """
        推断基础概念之间的关系
        :param node1: 第一个节点名称
        :param node2: 第二个节点名称
        :return: 推断关系或 None
        """
        # 示例：五行相生关系
        relationships = {
            "木": "火",
            "火": "土",
            "土": "金",
            "金": "水",
            "水": "木"
        }
        if node2 == relationships.get(node1):
            return f"{node1} 生 {node2}"
        elif node1 == relationships.get(node2):
            return f"{node2} 克 {node1}"
        return None
