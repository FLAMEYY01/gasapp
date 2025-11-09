import matplotlib.pyplot as plt
import pandas as pd

# 读取文件
excel_file = pd.ExcelFile('规整化—D1井生产数据.xlsx')

# 获取所有表名
sheet_names = excel_file.sheet_names
df = excel_file.parse('Sheet1')
# 设置图片清晰度
plt.rcParams['figure.dpi'] = 300

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei']

# 设置负号显示
plt.rcParams['axes.unicode_minus'] = False

# 提取绘图所需的数据
x = df['tcaDd']
y1 = df['qDd']
y2 = df['qDdj']
y3 = df['qDdjd']

# 创建图形和坐标轴
plt.figure(figsize=(10, 6))

# 绘制三条折线图
plt.plot(x, y1, label='无量纲产量')
plt.plot(x, y2, label='无量纲产量积分')
plt.plot(x, y3, label='无量纲积分导数')

# 设置标题和坐标轴标签
plt.title('tcaDd 与无量纲产量、产量积分、产量积分导数关系图')
plt.xlabel('tcaDd')
plt.xticks(rotation=45)
plt.ylabel('数值')

# 添加图例
plt.legend()

# 显示网格线
plt.grid(True)

# 自动调整布局
plt.tight_layout()

# 显示图形
plt.show()