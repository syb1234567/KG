# plugins/formula_inference.py

def run(data_manager, formula_data):
    """
    方剂推理插件入口
    :param data_manager: 数据管理实例
    :param formula_data: 方剂数据，格式示例：
        {
            "name": "麻黄汤",
            "ingredients": ["麻黄", "桂枝", "杏仁", "甘草"],
            "type": "汤剂",
            "usage": "解表发汗"
        }
    :return: 推理结果列表
    """
    results = []

    # 添加方剂节点
    if "name" in formula_data:
        data_manager.add_node(formula_data["name"], "方剂", formula_data.get("usage", ""))
        results.append(f"方剂 {formula_data['name']} 已添加")

    # 添加药材节点及关系
    if "ingredients" in formula_data:
        for ingredient in formula_data["ingredients"]:
            data_manager.add_node(ingredient, "药材", "")
            data_manager.add_relationship(formula_data["name"], ingredient, "包含")
            results.append(f"方剂 {formula_data['name']} 包含药材 {ingredient}")

    # 添加方剂类别
    if "type" in formula_data:
        data_manager.add_node(formula_data["type"], "方剂类别", "")
        data_manager.add_relationship(formula_data["name"], formula_data["type"], "属于")
        results.append(f"方剂 {formula_data['name']} 属于类别 {formula_data['type']}")

    return results
