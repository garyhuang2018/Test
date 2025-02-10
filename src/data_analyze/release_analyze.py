# encoding= utf-8
#__author__= gary
import pandas as pd
import matplotlib.pyplot as plt

# 加载提测单数据
def load_test_data(file_path):
    """
    加载提测单数据
    :param file_path: Excel 文件路径
    :return: 包含提测单数据的 DataFrame
    """
    try:
        df = pd.read_excel(file_path)
        # 确保关键列存在
        if '创建时间' not in df.columns:
            raise ValueError("Excel 文件中缺少 '创建时间' 列")
        # 处理日期列
        df['创建时间'] = pd.to_datetime(df['创建时间'], errors='coerce')
        return df
    except Exception as e:
        print(f"加载数据失败: {str(e)}")
        return None

# 按年份统计提测单数量
def analyze_test_requests_by_year(df):
    """
    按年份统计提测单数量
    :param df: 包含提测单数据的 DataFrame
    :return: 包含 2023 和 2024 年提测单数量的字典
    """
    if df is None or df.empty:
        return None

    # 提取年份
    df['年份'] = df['创建时间'].dt.year

    # 过滤出 2023 和 2024 年的数据
    filtered_df = df[df['年份'].isin([2023, 2024])]

    # 按年份统计提测单数量
    test_counts = filtered_df['年份'].value_counts().to_dict()

    # 确保 2023 和 2024 年都有数据
    test_counts.setdefault(2023, 0)
    test_counts.setdefault(2024, 0)

    return test_counts

# 计算百分比变化
def calculate_percentage_change(test_counts):
    """
    计算 2024 年相比 2023 年的提测单数量百分比变化
    :param test_counts: 包含 2023 和 2024 年提测单数量的字典
    :return: 百分比变化值
    """
    if test_counts is None or 2023 not in test_counts or 2024 not in test_counts:
        return None

    count_2023 = test_counts[2023]
    count_2024 = test_counts[2024]

    if count_2023 == 0:
        return None  # 避免除零错误

    percentage_change = ((count_2024 - count_2023) / count_2023) * 100
    return percentage_change

# 可视化对比结果
def plot_test_request_comparison(test_counts, percentage_change):
    """
    可视化提测单数量对比
    :param test_counts: 包含 2023 和 2024 年提测单数量的字典
    :param percentage_change: 百分比变化值
    """
    if not test_counts:
        print("无有效数据可展示")
        return

    # 提取数据
    years = [2023, 2024]
    counts = [test_counts.get(year, 0) for year in years]

    # 绘制柱状图
    # 设置中文显示和美观样式
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 微软雅黑也可用 'Microsoft YaHei'
    plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(1, 1))  # Adjust the figure size if needed
    bars = plt.bar(years, counts, color=['#1f77b4', '#ff7f0e'])

    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height,
                 f'{int(height)}', ha='center', va='bottom')

    # 添加降低百分比标签
    plt.text(2024, counts[1] + max(counts) * 0.05,  # 在2024年柱子上方显示
             f'降低 {percentage_change:.1f}%', ha='center', va='bottom', fontsize=10, color='red')
    # 添加百分比变化标注
    if percentage_change is not None:
        plt.text(1, counts[1] + 10, f'{percentage_change:.1f}%', ha='center', fontsize=12, color='red')

    # 设置图表标题和标签
    plt.title('2023 VS 2024 提测单数量对比', fontsize=16, pad=20)
    plt.xlabel('年份', fontsize=12, labelpad=10)
    plt.ylabel('提测单数量', fontsize=12, labelpad=10)
    plt.xticks(years, [str(year) for year in years])
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 保存图表
    plt.savefig('test_request_comparison.png', dpi=5, bbox_inches='tight')  # Adjust DPI if needed
    plt.show()


# 主函数
def main():
    # 文件路径（替换为实际路径）
    file_path = '过往提测单.xlsx'

    # 加载数据
    df = load_test_data(file_path)

    # 分析数据
    if df is not None:
        test_counts = analyze_test_requests_by_year(df)
        if test_counts:
            print("2023 年提测单数量:", test_counts.get(2023, 0))
            print("2024 年提测单数量:", test_counts.get(2024, 0))

            # 计算百分比变化
            percentage_change = calculate_percentage_change(test_counts)
            if percentage_change is not None:
                print(f"2024 年相比 2023 年提测单数量变化: {percentage_change:.1f}%")

            # 可视化对比
            plot_test_request_comparison(test_counts, percentage_change)
        else:
            print("未找到 2023 或 2024 年的提测单数据")
    else:
        print("数据加载失败，请检查文件路径和格式")


if __name__ == "__main__":
    main()