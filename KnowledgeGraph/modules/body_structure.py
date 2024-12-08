# modules/body_structure.py

class BodyStructure:
    # 五脏、六腑、经络、奇经八脉
    ORGANS = ["心", "肝", "脾", "肺", "肾"]  # 五脏
    FU_ORGANS = ["胆", "小肠", "胃", "大肠", "膀胱", "三焦"]  # 六腑
    MERIDIANS = ["手三阳", "足三阳", "手三阴", "足三阴"]  # 经络
    EXTRA_MERIDIANS = ["任脉", "督脉", "冲脉", "带脉"]  # 奇经八脉

    @staticmethod
    def classify(node_name):
        """
        分类节点为人体架构类别
        :param node_name: 节点名称
        :return: 分类结果 (五脏, 六腑, 经络, 奇经八脉, 未知)
        """
        if node_name in BodyStructure.ORGANS:
            return "五脏"
        elif node_name in BodyStructure.FU_ORGANS:
            return "六腑"
        elif node_name in BodyStructure.MERIDIANS:
            return "经络"
        elif node_name in BodyStructure.EXTRA_MERIDIANS:
            return "奇经八脉"
        return "未知分类"
