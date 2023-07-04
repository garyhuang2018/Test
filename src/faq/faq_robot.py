# encoding= utf-8
# __author__= gary
import jieba
import re
import pandas as pd

# 读取Excel文件
data = pd.read_excel('test.xlsx')

# 数据清洗操作
# 去除重复行
data.drop_duplicates(inplace=True)

text_data = data['问题描述']

# Perform word segmentation using jieba.cut
seg_list = text_data.apply(jieba.cut, cut_all=False)

# Remove unnecessary strings using re.sub
seg_list = seg_list.apply(lambda x: "/ ".join(re.sub(r'[、，：: 。.]', '', word) for word in x))

# Print the segmented text
print(seg_list)


