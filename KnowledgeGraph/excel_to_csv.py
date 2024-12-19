import pandas as pd

def excel_to_csv(excel_path, csv_path=None, sheet_name='Sheet1'):
    """
    将Excel文件转换为CSV文件
    :param excel_path: Excel文件路径
    :param csv_path: 输出的CSV文件路径，如不指定则与excel文件同名，仅扩展名变为.csv
    :param sheet_name: 要读取的工作表名称，默认为'Sheet1'
    """
    # 如果没有指定输出路径，则以输入文件名为基础，替换扩展名为.csv
    if csv_path is None:
        if excel_path.lower().endswith('.xlsx'):
            csv_path = excel_path[:-5] + '.csv'
        elif excel_path.lower().endswith('.xls'):
            csv_path = excel_path[:-4] + '.csv'
        else:
            # 没有标准扩展名时，直接加.csv
            csv_path = excel_path + '.csv'

    # 读取Excel文件
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # 导出为CSV文件，使用utf-8编码和逗号分隔
    try:
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"Successfully converted {excel_path} to {csv_path}")
    except Exception as e:
        print(f"Error writing CSV file: {e}")

if __name__ == '__main__':
    # 在此处直接指定输入Excel文件路径和输出CSV文件路径
    excel_file = r"C:\Users\lenovo\Desktop\KG软件开发\input.xlsx"
    csv_file = r"C:\Users\lenovo\Desktop\KG软件开发\input.csv"
    sheet = 'Sheet1'  # 如果你的工作表不是Sheet1，请修改此处

    excel_to_csv(excel_file, csv_file, sheet)
