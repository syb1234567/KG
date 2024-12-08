# modules/symptoms.py

class Symptoms:
    SYMPTOMS = ["寒热", "疼痛", "咳嗽", "气喘", "汗出", "二便异常"]

    @staticmethod
    def classify(symptom_name):
        """
        分类症状
        :param symptom_name: 症状名称
        :return: 症状类别或未知
        """
        if symptom_name in Symptoms.SYMPTOMS:
            return "症状"
        return "未知分类"
