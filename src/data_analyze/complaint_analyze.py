import pandas as pd
import matplotlib.pyplot as plt


# 读取 Excel 文件
def load_complaint_data(file_path):
    """
    加载客诉数据
    :param file_path: Excel 文件路径
    :return: 包含客诉数据的 DataFrame
    """
    try:
        df = pd.read_excel(file_path)
        # 确保日期列格式正确
        if '问题发起日期' in df.columns:
            df['问题发起日期'] = pd.to_datetime(df['问题发起日期'], errors='coerce')
        else:
            raise ValueError("Excel 文件中缺少 '问题发起日期' 列")
        return df
    except Exception as e:
        print(f"加载数据失败: {str(e)}")
        return None


# 按前缀合并产品型号
def merge_products_by_prefix(df, prefix_length=3):
    """
    按前缀合并产品型号
    :param df: 包含客诉数据的 DataFrame
    :param prefix_length: 前缀长度（默认取前3个字符）
    :return: 合并后的 DataFrame
    """
    if df is None or df.empty:
        return None

    # 提取产品型号前缀
    df['产品前缀'] = df['产品型号'].str[:prefix_length]

    # 按前缀合并
    merged_df = df.groupby(['问题发起日期', '产品前缀']).size().unstack(fill_value=0)

    return merged_df


# 按年份和产品前缀统计客诉数量
def analyze_complaints_by_year_and_prefix(df, prefix_length=3):
    """
    按年份和产品前缀统计客诉数量
    :param df: 包含客诉数据的 DataFrame
    :param prefix_length: 前缀长度（默认取前3个字符）
    :return: 按年份和产品前缀统计的客诉数量 DataFrame
    """
    if df is None or df.empty:
        return None

    # 提取年份
    df['年份'] = df['问题发起日期'].dt.year

    # 提取产品型号前缀
    df['产品前缀'] = df['产品型号'].str[:prefix_length]

    # 按年份和产品前缀统计客诉数量
    yearly_prefix_complaints = df.groupby(['年份', '产品前缀']).size().unstack(fill_value=0)

    # 过滤掉数量较少的产品前缀（可选）
    yearly_prefix_complaints = yearly_prefix_complaints.loc[:, yearly_prefix_complaints.sum() >= 5]  # 只统计客诉数 >= 5 的前缀

    return yearly_prefix_complaints


# 按年份统计客诉数量
def analyze_complaints_by_year(df):
    """
    按年份统计客诉数量
    :param df: 包含客诉数据的 DataFrame
    :return: 包含 2023 和 2024 年客诉数量的字典
    """
    if df is None or df.empty:
        return None

    # 提取年份
    df['年份'] = df['问题发起日期'].dt.year

    # 过滤出 2023 和 2024 年的数据
    filtered_df = df[df['年份'].isin([2023, 2024])]

    # 按年份统计客诉数量
    complaint_counts = filtered_df['年份'].value_counts().to_dict()

    # 确保 2023 和 2024 年都有数据
    complaint_counts.setdefault(2023, 0)
    complaint_counts.setdefault(2024, 0)

    return complaint_counts


# 生成堆叠柱状图
def plot_yearly_product_complaints(yearly_product_complaints):
    """
    生成按年份和产品型号统计的客诉数量堆叠柱状图
    :param yearly_product_complaints: 按年份和产品型号统计的客诉数量 DataFrame
    :return: 图表文件路径
    """
    if yearly_product_complaints is None or yearly_product_complaints.empty:
        print("无有效数据可展示")
        return None

    # 设置图表样式
    # 设置图表样式
    # 设置中文显示和美观样式
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 微软雅黑也可用 'Microsoft YaHei'
    plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(10, 6))
    ax = yearly_product_complaints.plot(kind='bar', stacked=True, colormap='viridis')

    # 添加数据标签
    for container in ax.containers:
        ax.bar_label(container, label_type='center', fmt='%d', color='white', fontsize=10)

    # 设置图表标题和标签
    plt.title('按年份和产品型号统计客诉数量', fontsize=16, pad=20)
    plt.xlabel('年份', fontsize=12, labelpad=10)
    plt.ylabel('客诉数量', fontsize=12, labelpad=10)
    plt.xticks(rotation=0)  # 不旋转 X 轴标签
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='产品型号', bbox_to_anchor=(1.05, 1), loc='upper left')  # 图例放在右侧

    # 保存图表
    chart_path = 'yearly_product_complaints.png'
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    return chart_path


# 生成饼图
def plot_product_complaints(product_complaints):
    """
    生成产品客诉数量饼图
    :param product_complaints: 按产品型号统计的客诉数量 Series
    :return: 图表文件路径
    """
    if product_complaints is None or product_complaints.empty:
        print("无有效数据可展示")
        return None

    # 设置中文显示和美观样式
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    
    # 绘制饼图
    plt.pie(product_complaints.values, 
            labels=product_complaints.index,
            autopct='%1.1f%%',  # 显示百分比
            pctdistance=0.85,   # 百分比标签距离圆心的距离
            startangle=90)      # 起始角度
    
    # 设置图表标题
    plt.title('2024年各产品型号客诉数量占比', fontsize=16, pad=20)
    
    # 添加图例
    plt.legend(product_complaints.index,
              title="产品型号",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1))
    
    # 使饼图成为一个圆
    plt.axis('equal')

    # 保存图表
    chart_path = 'product_complaints_pie.png'
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    return chart_path


# 可视化对比结果
def plot_complaint_comparison(complaint_counts):
    """
    可视化客诉数量对比
    :param complaint_counts: 包含 2023 和 2024 年客诉数量的字典
    """
    if not complaint_counts:
        print("无有效数据可展示")
        return

    # 提取数据
    years = [2023, 2024]
    counts = [complaint_counts.get(year, 0) for year in years]

    # 计算2024年相较于2023年的客诉数量降低百分比
    if counts[0] > 0:  # 确保2023年的数量不为零以避免除零错误
        decrease_percentage = ((counts[0] - counts[1]) / counts[0]) * 100
    else:
        decrease_percentage = 0

    # 绘制柱状图
    plt.figure(figsize=(8, 6))
    bars = plt.bar(years, counts, color=['#1f77b4', '#ff7f0e'])

    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height,
                 f'{int(height)}', ha='center', va='bottom')

    # 添加降低百分比标签
    plt.text(2024, counts[1] + max(counts) * 0.05,  # 在2024年柱子上方显示
             f'降低 {decrease_percentage:.1f}%', ha='center', va='bottom', fontsize=10, color='red')

    # 设置图表标题和标签
    plt.title('2023 VS 2024 客诉数量对比', fontsize=16, pad=20)
    plt.xlabel('Year', fontsize=12, labelpad=10)
    plt.ylabel('客诉数量统计', fontsize=12, labelpad=10)
    plt.xticks(years, [str(year) for year in years])
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 保存图表
    plt.savefig('complaint_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()


# 按产品型号统计客诉数量
def analyze_complaints_by_product(df):
    """
    按产品型号统计客诉数量
    :param df: 包含客诉数据的 DataFrame
    :return: 按产品型号统计的客诉数量 Series
    """
    if df is None or df.empty:
        return None
    
    # 只筛选2024年的数据
    df['年份'] = df['问题发起日期'].dt.year
    df_2024 = df[df['年份'] == 2024]
    
    # 按产品型号统计客诉数量
    product_complaints = df_2024['产品型号'].value_counts()
    
    # 过滤掉数量较少的产品（可选）
    product_complaints = product_complaints[product_complaints >= 1]

    return product_complaints


def categorize_product_name(product_name):
    """
    将产品名称归类为更通用的类别
    :param product_name: 产品名称
    :return: 归类后的类别名称
    """
    # 确保产品名称是字符串
    if not isinstance(product_name, str):
        product_name = ""

    # 定义产品名称与类别的映射规则
    category_mapping = {
        "门口机": ["门口", "人脸识别", "P5", "p3整机", "G5", "二次确认机", "H5整机"],
        "室内机&管理机": ["c5", "C5-D整机", "c6", "M3PRO", "M3Pro整机", "C5整机", "室内机", "C7PRO整机","数字智能主机","MM10", "C7Pro-D整机","管理机"],
        "酒店及智能家居网关": ["网关", "GW", "GATEWAY","主机", "HOST", "4寸语控主机"],
        "传感器": ["传感器", "雷达", "毫米波", "转发器","温控器"],
        "开关面板&插座": ["开关", "插卡取电", "复合开关", "面板","M6P智能插座"],
        "电机": ["电机", "开合帘"],
        "平台&APP&小程序": ["平台", "系统","APP", "小程序","服务器","社区生活宝"],
        "其他(网桥，梯控，配置工具)": ["其他(网桥，梯控，配置工具)"]  # 默认类别
    }

    # 遍历映射规则，匹配产品名称
    for category, keywords in category_mapping.items():
        for keyword in keywords:
            if keyword in product_name:
                return category
    return "其他"  # 如果未匹配到任何类别，则归类为"其他"


def analyze_complaints_by_category(df):
    """
    按产品类别统计客诉数量，并打印出属于"其他"类别的产品名称
    :param df: 包含客诉数据的 DataFrame
    :return: 按产品类别统计的客诉数量 Series
    """
    if df is None or df.empty:
        return None

    # 只筛选2024年的数据
    df['年份'] = df['问题发起日期'].dt.year
    df_2024 = df[df['年份'] == 2024]

    # 添加产品类别列
    df_2024['产品类别'] = df_2024['产品名称'].apply(categorize_product_name)

    # 打印属于"其他"类别的产品名称
    other_category_products = df_2024[df_2024['产品类别'] == '其他']['产品名称'].unique()
    print("属于'其他'类别的产品名称：")
    for product in other_category_products:
        print(product)

    # 按产品类别统计客诉数量
    category_complaints = df_2024['产品类别'].value_counts()

    return category_complaints


def plot_category_complaints(category_complaints):
    """
    生成产品类别客诉数量饼图
    :param category_complaints: 按产品类别统计的客诉数量 Series
    :return: 图表文件路径
    """
    if category_complaints is None or category_complaints.empty:
        print("无有效数据可展示")
        return None

    # 设置中文显示和美观样式
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建图表
    plt.figure(figsize=(12, 8))

    # 绘制饼图
    plt.pie(category_complaints.values,
            labels=category_complaints.index,
            autopct='%1.1f%%',  # 显示百分比
            pctdistance=0.85,   # 百分比标签距离圆心的距离
            startangle=90)      # 起始角度

    # 设置图表标题
    plt.title('2024年各产品类别客诉数量占比', fontsize=16, pad=20)

    # 添加图例
    plt.legend(category_complaints.index,
               title="产品类别",
               loc="center left",
               bbox_to_anchor=(1, 0, 0.5, 1))

    # 使饼图成为一个圆
    plt.axis('equal')

    # 保存图表
    chart_path = 'category_complaints_pie.png'
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    return chart_path


def analyze_complaints_by_year_and_product(df):
    """
        按年份和产品型号统计客诉数量
        :param df: 包含客诉数据的 DataFrame
        :return: 按年份和产品型号统计的客诉数量 DataFrame
        """
    if df is None or df.empty:
        return None

    # 提取年份
    df['年份'] = df['问题发起日期'].dt.year

    # 按年份和产品型号统计客诉数量
    yearly_product_complaints = df.groupby(['年份', '产品型号']).size().unstack(fill_value=0)

    # 过滤掉数量较少的产品（可选）
    yearly_product_complaints = yearly_product_complaints.loc[:,
                                yearly_product_complaints.sum() >= 5]  # 只统计客诉数 >= 5 的产品

    return yearly_product_complaints


def analyze_complaints_by_issue(df):
    """
    按问题现象分类统计客诉数量
    :param df: 包含客诉数据的 DataFrame
    :return: 按问题现象统计的客诉数量 Series
    """
    if df is None or df.empty:
        return None
    
    # 只筛选2024年的数据
    df['年份'] = df['问题发起日期'].dt.year
    df_2024 = df[df['年份'] == 2024]
    
    # 按问题现象统计客诉数量
    issue_complaints = df_2024['现象'].value_counts()
    
    # 过滤掉数量较少的问题（可选）
    issue_complaints = issue_complaints[issue_complaints >= 1]
    
    return issue_complaints


def plot_issue_complaints(issue_complaints):
    """
    生成问题现象客诉数量饼图
    :param issue_complaints: 按问题现象统计的客诉数量 Series
    :return: 图表文件路径
    """
    if issue_complaints is None or issue_complaints.empty:
        print("无有效数据可展示")
        return None

    # 设置中文显示和美观样式
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    
    # 绘制饼图
    plt.pie(issue_complaints.values, 
            labels=issue_complaints.index,
            autopct='%1.1f%%',  # 显示百分比
            pctdistance=0.85,   # 百分比标签距离圆心的距离
            startangle=90)      # 起始角度
    
    # 设置图表标题
    plt.title('2024年各问题现象客诉数量占比', fontsize=16, pad=20)
    
    # 添加图例
    plt.legend(issue_complaints.index,
              title="问题现象",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1))
    
    # 使饼图成为一个圆
    plt.axis('equal')

    # 保存图表
    chart_path = 'issue_complaints_pie.png'
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    return chart_path


def analyze_complaints_by_project(file_path):
    """
    从单独的项目数据文件分析客诉数量
    :param file_path: 项目数据文件路径
    :return: 按所属项目统计的客诉数量 Series
    """
    try:
        # 读取项目数据文件
        df_project = pd.read_excel(file_path)
        
        # 确保数据中包含必要的列
        if '所属项目' not in df_project.columns :
            print("项目数据文件缺少必要的列")
            return None

        # 按所属项目统计客诉数量
        project_complaints = df_project['所属项目'].value_counts()
        
        # 过滤掉数量较少的项目（可选）
        project_complaints = project_complaints[project_complaints >= 1]
        
        return project_complaints
        
    except Exception as e:
        print(f"读取项目数据文件时出错: {str(e)}")
        return None


def plot_project_complaints(project_complaints):
    """
    生成所属项目客诉数量横向条形图
    :param project_complaints: 按所属项目统计的客诉数量 Series
    :return: 图表文件路径
    """
    if project_complaints is None or project_complaints.empty:
        print("无有效数据可展示")
        return None

    # 设置中文显示和美观样式
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建图表
    plt.figure(figsize=(12, 8))

    # 计算总数用于显示百分比
    total = project_complaints.sum()

    # 创建横向条形图
    bars = plt.barh(range(len(project_complaints)), project_complaints.values)

    # 设置y轴标签（项目名称）
    plt.yticks(range(len(project_complaints)), project_complaints.index)

    # 设置x轴标签
    plt.xlabel('客诉数量', fontsize=12)

    # 设置图表标题
    plt.title('2024年各项目客诉数量统计', fontsize=16, pad=20)

    # 为每个条形添加数值标签（数量和百分比）
    for i, bar in enumerate(bars):
        width = bar.get_width()
        percentage = (width / total) * 100
        plt.text(width, i, f'  {int(width)}件 ({percentage:.1f}%)',
                 va='center', fontsize=10)

    # 添加网格线
    plt.grid(axis='x', linestyle='--', alpha=0.7)

    # 调整布局，确保标签不被截断
    plt.tight_layout()

    # 保存图表
    chart_path = 'project_complaints_bar.png'
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    return chart_path


# 生成堆叠柱状图
def plot_yearly_prefix_complaints(yearly_prefix_complaints):
    """
    生成按年份和产品前缀统计的客诉数量堆叠柱状图
    :param yearly_prefix_complaints: 按年份和产品前缀统计的客诉数量 DataFrame
    :return: 图表文件路径
    """
    if yearly_prefix_complaints is None or yearly_prefix_complaints.empty:
        print("无有效数据可展示")
        return None

    # 设置图表样式
    plt.figure(figsize=(12, 6))
    ax = yearly_prefix_complaints.plot(kind='bar', stacked=True, colormap='viridis')
    # 设置中文显示和美观样式
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    # # 添加数据标签
    # for container in ax.containers:
    #     ax.bar_label(container, label_type='center', fmt='%d', color='white', fontsize=10)

    # 设置图表标题和标签
    plt.title('按年份和产品前缀统计客诉数量', fontsize=16, pad=20)
    plt.xlabel('年份', fontsize=12, labelpad=10)
    plt.ylabel('客诉数量', fontsize=12, labelpad=10)
    plt.xticks(rotation=0)  # 不旋转 X 轴标签
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='产品前缀', bbox_to_anchor=(1.05, 1), loc='upper left')  # 图例放在右侧

    # 保存图表
    chart_path = 'yearly_prefix_complaints.png'
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    return chart_path


def main():
    # 主数据文件路径
    main_file_path = '过往客诉问题.xlsx'
    # 项目数据文件路径
    project_file_path = '2024_release.xlsx'  # 新的项目数据文件

    # 加载主数据
    df = load_complaint_data(main_file_path)

    # 分析数据
    if df is not None:
        # 分析产品类别
        category_complaints = analyze_complaints_by_category(df)
        if category_complaints is not None:
            print("\n2024年各产品类别客诉数量统计：")
            print(category_complaints)
            # 生成产品类别图表
            chart_path = plot_category_complaints(category_complaints)
        
        # 统计2023和2024年的客诉数量
        complaint_counts = analyze_complaints_by_year(df)
        if complaint_counts is not None:
            print("\n2023和2024年客诉数量统计：")
            print(complaint_counts)
            # 生成客诉数量对比图表
            plot_complaint_comparison(complaint_counts)
        else:
            print("未找到有效的客诉数据")
    else:
        print("数据加载失败，请检查文件路径和格式")
    # # 分析数据
    # if df is not None:
    #     # 分析产品型号
    #     product_complaints = analyze_complaints_by_product(df)
    #     if product_complaints is not None:
    #         print("\n2024年各产品型号客诉数量统计：")
    #         print(product_complaints)
    #         top_n = 30  # 只显示客诉数量最多的前30个产品
    #         product_complaints = product_complaints.nlargest(top_n)
    #         # 生成产品型号图表
    #         chart_path = plot_product_complaints(product_complaints)
    #
    #     # 分析问题现象
    #     issue_complaints = analyze_complaints_by_issue(df)
    #     if issue_complaints is not None:
    #         print("\n2024年各问题现象客诉数量统计：")
    #         print(issue_complaints)
    #         top_n = 20  # 只显示客诉数量最多的前20个问题现象
    #         # issue_complaints = issue_complaints.nlargest(top_n)
    #         # 生成问题现象图表
    #         # chart_path = plot_issue_complaints(issue_complaints)
    # else:
    #     print("主数据文件加载失败，请检查文件路径和格式")
    
    # # 从单独的文件分析项目数据
    # project_complaints = analyze_complaints_by_project(project_file_path)
    # if project_complaints is not None:
    #     print("\n2024年各项目客诉数量统计：")
    #     print(project_complaints)
    #     # 生成所属项目图表
    #     chart_path = plot_project_complaints(project_complaints)
    # else:
    #     print("项目数据文件加载失败，请检查文件路径和格式")


if __name__ == "__main__":
    main()