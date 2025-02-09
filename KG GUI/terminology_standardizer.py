# terminology_standardizer.py
# 功能：术语标准化工具（暂时禁用数据库相关功能）
# 说明：该模块目前不加载 tcm_terms.json，也不使用 fuzzywuzzy，
#       直接对输入字符串进行简单处理，后续整理好术语数据库后再启用相应功能。

class TerminologyStandardizer:
    def __init__(self, term_file="tcm_terms.json"):
        # 暂时不加载术语文件，置空数据库
        self.terms = {}
        self.term_list = []

    def standardize(self, input_term, threshold=80):
        """
        暂时禁用术语标准化功能，
        直接返回输入的字符串去除首尾空格的结果
        """
        if isinstance(input_term, str):
            return input_term.strip()
        return input_term

    def get_term_info(self, term):
        # 暂时不提供术语详细信息，返回空字典
        return {}
