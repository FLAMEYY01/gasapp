# 计算G
# blasingame给的r_ed和某点（随机的？）的tca\压力规整化产量和tcaDd\qDd
# 画那些red点的图像，找出最佳rwa
# 求出re
# 求出V_p
#求出G
#1

import numpy as np
from scipy.optimize import minimize
from fastdtw import fastdtw  # 安装：pip install fastdtw
import matplotlib.pyplot as plt

# ---------------------- 1. 设定基础数据（需根据你的情况修改） ----------------------
# （1）基准序列L1.5（固定模板，含x和y）
x1_5 = np.linspace(0.5, 5.0, 100)  # L1.5的时间轴（示例）
y1_5 = np.exp(-x1_5) + 0.1  # L1.5的数值轴（示例，可替换为你的真实L1.5）
L1_5 = np.column_stack((x1_5, y1_5))  # 合并为（x,y）二维序列

# （2）实测生产序列L1（已规整化，替换为你的真实数据）
x1 = np.linspace(1.0, 6.0, 50)  # L1的时间轴
y1 = np.exp(-0.8 * x1) + 0.1 + 0.01 * np.random.normal(0, 1, 50)  # 带轻微噪声的实测值
L1 = np.column_stack((x1, y1))

# ---------------------- 2. 核心：L1.5→L2的转化函数（必须修改为你的规则） ----------------------
def generate_L2(r_wa, L1_5=L1_5):
    """
    输入：参数r_wa、基准序列L1.5
    输出：带参数r_wa的理论序列L2（x2, y2）
    核心：修改x2和y2的转化公式！
    """
    x1_5 = L1_5[:, 0]  # 提取L1.5的x轴
    y1_5 = L1_5[:, 1]  # 提取L1.5的y轴

    # 示例转化规则（场景1：线性缩放，需替换为你的规则）
    x2 = r_wa * x1_5  # x轴随r_wa放大（r_wa越大，L2时间范围越宽）
    y2 = y1_5 / (r_wa + 0.1)  # y轴随r_wa缩小（避免r_wa=0出错）

    return x2, y2  # 输出L2的时间序列

# ---------------------- 3. 优化目标：最小化L1与L2的DTW距离（形态相似度） ----------------------
def objective(r_wa):
    x2, y2 = generate_L2(r_wa)  # 生成当前r_wa对应的L2
    L2 = np.column_stack((x2, y2))
    # DTW距离：处理时间错位，精准衡量形态匹配度（越小越好）
    dtw_dist, _ = fastdtw(L1, L2, dist=lambda a, b: np.linalg.norm(a - b))
    return dtw_dist

# ---------------------- 4. 搜索最优r_wa（非线性优化） ----------------------
# 设定r_wa的合理范围（基于物理意义，如r_wa>0）
bounds = [(0.1, 5.0)]  # 避免过小/过大的无意义值（需调整）
# 初始猜测值（基于经验，如0.5，可根据实际调整）
x0 = [0.5]
# 调用优化器（L-BFGS-B适合带边界的单参数优化，收敛快）
result = minimize(objective, x0=x0, bounds=bounds, method='L-BFGS-B')
optimal_rwa = result.x[0]

# ---------------------- 5. 结果可视化与输出 ----------------------
x2_opt, y2_opt = generate_L2(optimal_rwa)  # 最优r_wa对应的L2

plt.figure(figsize=(10, 5))
plt.plot(x1, y1, 'o-', label='L1（生产数据）', color='blue', alpha=0.8, markersize=6)
plt.plot(x2_opt, y2_opt, '-', label=f'L2（最优r_wa={optimal_rwa:.3f}）', color='red', linewidth=2)
plt.plot(x1_5, y1_5, '--', label='L1.5（基准序列）', color='green', alpha=0.6)
plt.xlabel('时间（规整化）')
plt.ylabel('数值（规整化）')
plt.legend(fontsize=11)
plt.title('基准序列→理论序列→生产数据的最优匹配', fontsize=12)
plt.grid(alpha=0.3)
plt.show()

# 输出关键结果
print(f"最优参数r_wa：{optimal_rwa:.3f}")
print(f"最小DTW距离（形态相似度）：{result.fun:.3f}")
print(f"优化收敛状态：{'成功' if result.success else '失败'}")