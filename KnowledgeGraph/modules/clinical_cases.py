# modules/clinical_cases.py

class ClinicalCases:
    CASES = []

    @staticmethod
    def add_case(case):
        """
        添加病例
        :param case: 病例信息字典
        """
        ClinicalCases.CASES.append(case)

    @staticmethod
    def get_cases():
        """
        获取所有病例
        :return: 病例列表
        """
        return ClinicalCases.CASES
