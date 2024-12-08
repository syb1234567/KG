# modules/pathological_factors.py

class PathologicalFactors:
    # 病理因素
    FACTORS = ["痰", "瘀", "毒", "湿", "热", "寒"]

    @staticmethod
    def classify(node_name):
        """
        分类节点为病理因素类别
        :param node_name: 节点名称
        :return: 分类结果 (病理因素, 未知)
        """
        if node_name in PathologicalFactors.FACTORS:
            return "病理因素"
        return "未知分类"
