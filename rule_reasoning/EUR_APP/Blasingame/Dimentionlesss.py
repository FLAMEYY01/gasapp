# 无量纲时间
import numpy as np
import pandas as pd
import json
from utils import GasPVT
from normized  import calculate_normalized_pseudopressure
# 导入json文件，定义默认初始化参数

# 导入json文件，定义默认初始化参数

with open("parameters.json", "r", encoding="utf-8") as f:
    parameters_dict = json.load(f)

parameters_list=[]
for key, value in parameters_dict.items():
    parameters_list.append(key)
print("______________________气井参数符号_____________________________")
print(parameters_list)

"""
从json文件初始化参数：
        μgi: 初始气体黏度（Pa·s）
        Zi: 初始压缩因子（无量纲）
        pi: 初始压强（Pa）
        Cti: 初始综合压缩系数
        G: 预估气藏储量
"""

μgi, Zi, pi,Cti,G,K,Φ,Ti,h,comment= parameters_dict['μgi'],parameters_dict["Zi"],parameters_dict["pi"],parameters_dict["Cti"],parameters_dict["G"],parameters_dict["K"],parameters_dict["Φ"],parameters_dict["Ti"],parameters_dict["h"],parameters_dict["comment"]
print("______________________气井参数符号含义及单位_____________________________")
print(comment)

# ————————————————————————————————加载PVT数据————————————————————————————
pvt = GasPVT('gas_pvt_properties.csv')

def calculate_tcaDd(t_ca, r_e, r_wa):
    """
    计算无量纲时间t_caDd

    参数：
    t_ca: 时间，单位根据实际场景确定
    r_e: 供给半径，单位ft
    r_wa: 井筒等效半径，单位ft

    返回：
    t_caDd: 无量纲时间
    """
    r_eD = r_e / r_wa  # 无量纲供给半径
    denominator1 = Φ * μgi * Cti * (r_wa ** 2)
    denominator2 = (r_eD ** 2 - 1)
    denominator3 = 0.5 * (np.log(r_eD) - 0.5)
    t_caDd = (0.0864 * K * t_ca) / (denominator1 * denominator2 * denominator3)
    return t_caDd


# 示例调用
t_ca_sample = 10  # 示例时间
r_e_sample = 1000  # 示例供给半径，ft
r_wa_sample = 0.5  # 示例井筒等效半径，ft
tcaDd_result = calculate_tcaDd(t_ca_sample, r_e_sample, r_wa_sample)
print(f"当t_ca={t_ca_sample}, r_e={r_e_sample}ft, r_wa={r_wa_sample}ft时，t_caDd={tcaDd_result:.2f}")

print("__________________________________excel测试tcaDd,选定re=1000，rwa=0.5_________________________________________________________")
# 需要保存到excel吗，毕竟太多re，rwa了

# 读取 Excel 文件
excel_path = '规整化—D1井生产数据.xlsx'
df = pd.read_excel(excel_path)

# 选择合适的 r_e 和 r_wa 数据（这里假设 r_e = 1000，r_wa = 0.5）
r_e = 1000
r_wa = 0.5

# 计算 tcaDd
tcaDd = [calculate_tcaDd(t_ca, r_e, r_wa) for t_ca in df['tca']]

# 将计算结果添加到 DataFrame 的最后一列
df['tcaDd'] = tcaDd

# 将结果保存回 Excel 文件
df.to_excel(excel_path, index=False)

print('tcaDd 计算完成并保存到 Excel 文件最后一列。')


# 计算Bgi
p_sc = 0.101325  # 标准压力，单位：MPa（1标准大气压）
T_sc = 293.15  # 标准温度，单位：K（20℃转换为开尔文）


def calculate_Bgi(Ti):
    """
    计算气体体积系数 Bgi（单位：m³/m³，表征实际状态与标准状态的体积比）
    参数:
        Ti: 气体实际温度（单位：K，函数唯一输入）
    返回:
        Bgi: 气体体积系数
    公式来源: 理想气体状态方程推导（含压缩因子修正）
    """
    if Ti <= 0:
        raise ValueError("实际温度 Ti 必须大于0（单位：K），请检查输入")

    Bgi = (Zi * p_sc * Ti) / (pi * T_sc)
    return Bgi
Bgi=calculate_Bgi(Ti)

# 计算无量纲产量
def calculate_qDd(q, pwf, re, rw):
    """
    计算无量纲产量q_Dd

    参数：
    q: 实际产量，单位需与公式匹配（如STB/D）
    pwf: 井底流压，Pa
    re: 供给半径，ft
    rw: 井筒等效半径，ft


    返回：
    q_Dd: 无量纲产量
    """

    """
    初始化的参数：
            gas_pvt: GasPVT实例，用于获取μ_g
    """
    # 1. 获取μ_g（从PVT表插值）
    μ_g = pvt.get_μg(pwf)

    # 2. 计算q_D（公式8-79.1）
    numerator = 1.842e4 * q * Bgi * μ_g
    denominator = K * h * (calculate_normalized_pseudopressure(pi,pvt) - calculate_normalized_pseudopressure(pwf,pvt))
    q_D = numerator / denominator

    # 3. 计算q_Dd（公式8-79）
    r_eD = re / rw
    q_Dd = q_D * (np.log(r_eD) - 0.5)

    return q_Dd

print("____________________________excel测试qDd,选择一组re=1000,rwa=0.5______________________________________")
# 读取 Excel 文件
excel_path = '规整化—D1井生产数据.xlsx'
df = pd.read_excel(excel_path)

# 选择合适的 re 和 rw 数据（这里假设 re = 1000，rw = 0.5）
re = 1000
rw = 0.5

# 计算 qDd
qDd = [calculate_qDd(q, pwf, re, rw) for q, pwf in zip(df['Qg'], df['Pwf'])]

# 将计算结果添加到 DataFrame 的最后一列
df['qDd'] = qDd

# 将结果保存回 Excel 文件
df.to_excel(excel_path, index=False)

print('qDd 计算完成并保存到 Excel 文件最后一列。')


# 计算无量纲产量积分
def calculate_qDdj(df, tcaDd_col, qDd_col, date_col):
    # 1. 数据预处理：按日期排序，重置索引（确保时间序列顺序正确）
    df_sorted = df.sort_values(by=date_col, ascending=True).reset_index(drop=True)

    # 2. 提取计算所需数组（提高计算效率）
    tcad = df_sorted[tcaDd_col].values  # 无量纲时间数组
    qdh = df_sorted[qDd_col].values  # 无量纲产量数组
    integral_results = np.zeros_like(tcad, dtype=np.float64)  # 初始化结果数组

    # 3. 逐点计算无量纲产量积分（梯形法则）
    for i in range(1, len(tcad)):  # 从第2个点开始计算（第1个点积分值为0）
        current_tcad = tcad[i]
        if current_tcad <= 0:
            integral_results[i] = 0.0
        else:
            # 梯形法则计算[0, i]区间的累积积分
            cumulative_integral = np.trapezoid(qdh[:i + 1], tcad[:i + 1])
            # 无量纲化：积分结果 / 当前无量纲时间
            integral_results[i] = cumulative_integral / current_tcad

    # 4. 结果写入DataFrame
    df_sorted["qDdj"] = integral_results
    return df_sorted



print("_______________________excel测试无量纲产量积分qDdj______________________________________")
# ------------------- 2. 读取Excel数据 -------------------
# 替换为你的Excel文件路径
excel_path = "规整化—D1井生产数据.xlsx"
# 读取数据（假设工作表名为Sheet1，若不同可修改sheet_name参数）
df = pd.read_excel(excel_path, sheet_name="Sheet1")

# ------------------- 3. 调用函数计算积分 -------------------
# 定义列名（需与你的Excel实际列名一致）
tcaDd_column = "tcaDd"
qDd_column = "qDd"
date_column = "Date"

# 调用计算函数
result_df = calculate_qDdj(
    df=df,
    tcaDd_col=tcaDd_column,
    qDd_col=qDd_column,
    date_col=date_column
)

# ------------------- 4. 保存结果到Excel -------------------
# 保存回原文件（若需保留原文件，可修改为新路径，如"结果文件.xlsx"）
result_df.to_excel(excel_path, index=False, sheet_name="Sheet1")

print("计算完成！压力规整化产量积分已添加到Excel文件最后一列。")




# 计算无量纲产量积分导数
def calculate_qDdjd(df, tcaDd_col, qDdj_col, date_col):
    """
    处理tcaDd第一个值为0的情况，计算压力规整化产量积分导数
    """
    # 按日期排序
    df_sorted = df.sort_values(by=date_col).reset_index(drop=True)

    tca = df_sorted[tcaDd_col].values
    integral = df_sorted[qDdj_col].values
    n = len(tca)

    # 处理tca中的非正值（仅允许第一个值为0，其他值必须为正）
    non_positive_indices = np.where(tca <= 0)[0]
    if len(non_positive_indices) > 0:
        # 检查是否只有第一个值为0，其他值是否为正
        if not (non_positive_indices == 0).all() or (tca[1:] <= 0).any():
            raise ValueError("除第一个值外，tcaDd列存在其他非正值，请检查数据！")
        print("警告：tcaDd第一个值为0，将特殊处理该点的导数计算")

    # 计算ln(tca)，对第一个0值临时用第二个值的ln(tca)替代（仅用于差分计算）
    lntca = np.log(tca) if n == 0 else np.zeros(n)
    for i in range(n):
        if i == 0 and tca[i] == 0:
            # 第一个值为0时，用第二个值的ln(tca)临时填充（后续差分计算会修正）
            lntca[i] = np.log(tca[1]) if n > 1 else 0.0
        else:
            lntca[i] = np.log(tca[i])

    deriv_results = []
    for i in range(n):
        if i == 0:
            # 第一个点（tca=0）：直接用i=1和i=0的前向差分（即使tca[0]=0也能计算）
            if n == 1:
                deriv = 0.0  # 只有一行数据时，导数为0
            else:
                delta_integral = integral[1] - integral[0]
                delta_lntca = lntca[1] - lntca[0]
                deriv = -delta_integral / delta_lntca if delta_lntca != 0 else 0.0
        elif i == n - 1:
            # 最后一个点：后向差分
            delta_integral = integral[i] - integral[i - 1]
            delta_lntca = lntca[i] - lntca[i - 1]
            deriv = -delta_integral / delta_lntca if delta_lntca != 0 else 0.0
        else:
            # 中间点：中心差分
            delta_integral = integral[i + 1] - integral[i - 1]
            delta_lntca = lntca[i + 1] - lntca[i - 1]
            deriv = -delta_integral / delta_lntca if delta_lntca != 0 else 0.0

        deriv_results.append(deriv)

    df_sorted["qDdjd"] = deriv_results
    return df_sorted

print("___________________________excel测试无量纲产量积分导数qDdjd_________________________________")
# ------------------- 主流程 -------------------
excel_path = "规整化—D1井生产数据.xlsx"  # 替换为你的文件路径
df = pd.read_excel(excel_path, sheet_name="Sheet1")

# 定义列名（与你的Excel一致）
tcaDd_column = "tcaDd"
qDdj_column = "qDdj"
date_column = "Date"

# 计算并保存
result_df = calculate_qDdjd(
    df=df,
    tcaDd_col=tcaDd_column,
    qDdj_col=qDdj_column,
    date_col=date_column
)
result_df.to_excel(excel_path, index=False, sheet_name="Sheet1")

print("计算完成！已处理tcaDd第一个值为0的情况。")



