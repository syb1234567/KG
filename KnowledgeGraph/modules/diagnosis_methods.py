# modules/diagnosis_methods.py

class DiagnosisMethods:
    # 诊断方法
    METHODS = ["望诊", "闻诊", "问诊", "切诊"]

    @staticmethod
    def classify_method(method_name):
        """
        分类诊断方法
        :param method_name: 方法名称
        :return: 诊断方法类别或未知
        """
        if method_name in DiagnosisMethods.METHODS:
            return method_name
        return "未知诊断方法"
