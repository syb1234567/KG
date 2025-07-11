import json
from functools import wraps

import networkx as nx
from PyQt5.QtWidgets import QMessageBox

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except json.JSONDecodeError as e:
            QMessageBox.critical(args[0], "JSON错误", f"格式错误: {str(e)}")
        except nx.NetworkXError as e:
            QMessageBox.critical(args[0], "图数据错误", f"图操作失败: {str(e)}")
        except Exception as e:
            QMessageBox.critical(args[0], "系统错误", f"未处理异常: {str(e)}")
    return wrapper