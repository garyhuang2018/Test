# encoding= utf-8
# __author__= gary

import pandas as pd


def load_excel_data(file_path, sheet_name=None):
    """
    加载 Excel 文件为 DataFrame。
    参数:
        file_path (str): Excel 文件路径
        sheet_name (str|None): 指定 sheet 名称，若为 None 则读取第一个
    返回:
        pd.DataFrame: 包含产品数据的 DataFrame
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl", skiprows=1)
    return df


def load_product_models():
    # Read the Excel file without skipping rows
    df = pd.read_excel('酒店产品物料模型对照表.xls')

    # Detect the row containing the 'productModel' keyword
    product_model_row = df.apply(lambda row: row.astype(str).str.contains('productModel').any(), axis=1).idxmax()

    # Read the Excel file again, skipping the rows before the detected row
    df = pd.read_excel('酒店产品物料模型对照表.xls', skiprows=product_model_row+1)

    # Extract the productModel column
    product_models = df['productModel'].dropna().unique()
    print(product_models)


def get_product_model(factory_code, factory_type, file_path='酒店产品物料模型对照表.xls'):
    """
    根据 factoryCode 和 factoryType 查询对应的 productModel。
    参数:
        factory_code (int): 工厂代码
        factory_type (int): 工厂类型
        file_path (str): Excel 文件路径，默认为 '酒店产品物料模型对照表.xls'
    返回:
        str: 匹配的产品型号（productModel），若未找到则返回提示
    """
    # 第一次读取，检测 header 行
    df_raw = pd.read_excel(file_path)

    # 找到包含 'productModel' 的列标题行索引
    header_row = df_raw.apply(lambda row: row.astype(str).str.contains('productModel').any(), axis=1).idxmax()

    # 第二次读取，跳过 header_row 行之前的内容
    df = pd.read_excel(file_path, skiprows=header_row + 1)

    # 清理列名空格，确保匹配
    df.columns = df.columns.str.strip()

    # 类型转换确保匹配
    df['factoryCode'] = df['factoryCode'].astype(str)
    df['factoryType'] = df['factoryType'].astype(str)

    # 查找匹配项
    match = df[
        (df['factoryCode'] == str(factory_code)) &
        (df['factoryType'] == str(factory_type))
    ]

    if not match.empty:
        return match.iloc[0]['productModel']
    else:
        return "未找到匹配的产品型号"


def get_product_name(factory_code, factory_type, factorySubtype, file_path='酒店产品物料模型对照表.xls'):
    """
    根据 factoryCode 和 factoryType 查询对应的 productModel。
    参数:
        factory_code (int): 工厂代码
        factory_type (int): 工厂类型
        file_path (str): Excel 文件路径，默认为 '酒店产品物料模型对照表.xls'
    返回:
        str: 匹配的产品型号（productModel），若未找到则返回提示
    """
    # 第一次读取，检测 header 行
    df_raw = pd.read_excel(file_path)

    # 找到包含 'productModel' 的列标题行索引
    header_row = df_raw.apply(lambda row: row.astype(str).str.contains('productModel').any(), axis=1).idxmax()

    # 第二次读取，跳过 header_row 行之前的内容
    df = pd.read_excel(file_path, skiprows=header_row + 1)

    # 清理列名空格，确保匹配
    df.columns = df.columns.str.strip()

    # 类型转换确保匹配
    df['factoryCode'] = df['factoryCode'].astype(str)
    df['factoryType'] = df['factoryType'].astype(str)
    df['factorySubtype'] = df['factorySubtype'].astype(str)
    # 查找匹配项
    match = df[
        (df['factoryCode'] == str(factory_code)) &
        (df['factoryType'] == str(factory_type)) &
        (df['factorySubtype'] == str(factorySubtype))
    ]

    if not match.empty:
        return match.iloc[0]['productName']
    else:
        return "未找到匹配的产品型号"


# 示例使用
if __name__ == "__main__":
    data = get_product_name(287,16,1)
    print(data)
    # # 文件路径
    # excel_file = "酒店产品物料模型对照表.xlsx"
    #
    # # 加载数据
    # df = load_excel_data(excel_file)
    # print(df)
    # # 查询示例
    # result = get_product_name(287, 16, 1, df)
    # print("查询结果:", result)
