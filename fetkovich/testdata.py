import pandas as pd
import numpy as np

# 生成1-1000天连续时间序列
time_days = np.arange(1, 1001)

# 分阶段生成产量数据
production = []
for t in time_days:
    if t <= 50:  # 早期不稳定流阶段（径向流模型）
        # 基于修正的不稳定流公式生成数据
        q = 2200 / (np.log(t) + 1.5)  # 模拟r_eD=5000的不稳定流特征
    else:  # 后期边界流阶段（Arps双曲递减模型，b=0.5, d_i=0.15）
        # 分界点产量为1000 m³/d，后续按双曲递减
        q = 1000 / ((1 + 0.5 * 0.15 * (t - 50)) ** (1 / 0.5))

    production.append(round(q, 1))

# 保存为Excel
df = pd.DataFrame({
    "时间（天）": time_days,
    "产量（m³/d）": production
})
df.to_excel("fetkovich_production_data.xlsx", index=False)
print("数据已保存为 fetkovich_production_data.xlsx")