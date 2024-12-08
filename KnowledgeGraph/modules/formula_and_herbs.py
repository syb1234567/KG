# modules/formula_and_herbs.py

class FormulaAndHerbs:
    # 药材分类和方剂类别 这里药材和方剂的类别还需要进一步添加扩展
    HERB_CATEGORIES = ["解表药", "清热药", "补益药", "活血化瘀药"]
    FORMULA_CATEGORIES = ["汤剂", "丸剂", "散剂"]

    @staticmethod
    def classify_herb(herb_name):
        """
        分类药材
        :param herb_name: 药材名称
        :return: 药材类别或未知
        """
        # 示例：药材分类逻辑
        if herb_name in FormulaAndHerbs.HERB_CATEGORIES:
            return herb_name
        return "未知药材"

    @staticmethod
    def classify_formula(formula_name):
        """
        分类方剂
        :param formula_name: 方剂名称
        :return: 方剂类别或未知
        """
        if formula_name in FormulaAndHerbs.FORMULA_CATEGORIES:
            return formula_name
        return "未知方剂"
