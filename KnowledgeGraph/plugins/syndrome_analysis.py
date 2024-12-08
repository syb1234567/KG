# plugins/syndrome_analysis.py

def run(data_manager, syndrome_data):
    """
    症候分析插件入口
    :param data_manager: 数据管理实例
    :param syndrome_data: 症候数据，格式示例：
        {
            "name": "风寒表实症",
            "related_formulas": ["麻黄汤", "桂枝汤"],
            "symptoms": ["恶寒发热", "无汗", "头痛"],
            "pathogenesis": "风寒袭表"
        }
    :return: 分析结果列表
    """
    results = []

    # 添加症候节点
    if "name" in syndrome_data:
        data_manager.add_node(syndrome_data["name"], "症候", syndrome_data.get("pathogenesis", ""))
        results.append(f"症候 {syndrome_data['name']} 已添加")

    # 添加与方剂的关系
    if "related_formulas" in syndrome_data:
        for formula in syndrome_data["related_formulas"]:
            data_manager.add_relationship(syndrome_data["name"], formula, "治疗")
            results.append(f"症候 {syndrome_data['name']} 治疗方剂 {formula}")

    # 添加症状
    if "symptoms" in syndrome_data:
        for symptom in syndrome_data["symptoms"]:
            data_manager.add_node(symptom, "症状", "")
            data_manager.add_relationship(syndrome_data["name"], symptom, "表现为")
            results.append(f"症候 {syndrome_data['name']} 表现为症状 {symptom}")

    return results
