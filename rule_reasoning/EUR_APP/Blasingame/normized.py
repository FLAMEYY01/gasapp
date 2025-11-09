
import numpy as np
import pandas as pd
from utils import GasPVT
import json
import scipy.optimize as optimize


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
μgi, Zi, pi,Cti,G,K,Φ,comment= parameters_dict['μgi'],parameters_dict["Zi"],parameters_dict["pi"],parameters_dict["Cti"],parameters_dict["G"],parameters_dict["K"],parameters_dict["Φ"],parameters_dict["comment"]
print("______________________气井参数符号含义及单位_____________________________")
print(comment)




# 计算规整拟压力
def calculate_normalized_pseudopressure(p, pvt):
    """计算规整拟压力（仅输入p即可）"""
    # 构造积分区间（0到p的所有离散点）
    p_integral = np.linspace(0, p, 1000)

    # 核心：对积分区间内的每个点插值获取μg和Z（用于积分计算）
    μg_integral = np.interp(p_integral, pvt.p_values, pvt.μg_values)
    Z_integral = np.interp(p_integral, pvt.p_values, pvt.Z_values)

    # 被积函数与积分计算
    integrand = p_integral / (μg_integral * Z_integral)
    integral_result = np.trapezoid(integrand, p_integral)

    # 规整拟压力公式
    P_p = (μgi * Zi / pi) * integral_result
    return P_p


# ————————————————————————————————加载PVT数据————————————————————————————
pvt = GasPVT('gas_pvt_properties.csv')

# 3. 示例：计算p=25MPa时的规整拟压力

p_target = 25e6  # Pa
P_p = calculate_normalized_pseudopressure(p_target, pvt)
print(f"压强p = {p_target/1e6:.1f}MPa时，规整拟压力 P_p = {P_p:.2e} Pa")


# 计算规整拟压力规整化产量
"""
输入q,pwf，计算得到规整你压力
"""
def calculate_pressure_normalized_rate(q, p_wf):
    """
    计算压力规整化产量 q/ΔP_p

    参数:
        q: 实际产量（单位需与工程场景一致，此处为无量纲示例）
        p_wf: 井底流压，Pa
    返回:
        压力规整化产量，q/ΔP_p
    """

    # 计算初始压力p_i对应的规整拟压力P_pi

    P_pi = calculate_normalized_pseudopressure(pi,pvt)

    # 计算井底流压p_wf对应的规整拟压力P_pwf
    P_pwf = calculate_normalized_pseudopressure(p_wf,pvt)

    # 计算ΔP_p
    delta_P_p = P_pi - P_pwf

    # 计算压力规整化产量
    pressure_normalized_rate = q / delta_P_p
    return pressure_normalized_rate

# 测试参数
q_test = 10.0    # 实际产量（示例值，单位根据工程场景定义）
p_wf_test = 0.8e6  # 井底流压，Pa

# 计算压力规整化产量
result = calculate_pressure_normalized_rate(q_test, p_wf_test)
print(f"压力规整化产量 = {result:.2f} (无量纲，因q和ΔP_p单位已协调)")

# 使用excel测试
print("_____________________________excel测试计算压力规整产量____________________________________")

# 读取Excel数据（请替换为你的Excel文件路径）
excel_path = "规整化—D1井生产数据.xlsx"  # 例如："gas_well_data.xlsx"
df = pd.read_excel(excel_path)

# 检查必要列是否存在
required_columns = ['Qg', 'Pwf']
if not set(required_columns).issubset(df.columns):
    missing = [col for col in required_columns if col not in df.columns]
    raise ValueError(f"Excel文件缺少必要列：{missing}")

# 遍历每条数据计算压力规整化产量
df['压力规整化产量'] = None  # 新增结果列

for idx, row in df.iterrows():
    try:
        q = row['Qg']  # 实际产量
        p_wf = row['Pwf'] * 1e6  # 井底流压（假设Excel中单位为MPa，转换为Pa）

        # 计算压力规整化产量
        normalized_rate = calculate_pressure_normalized_rate(q, p_wf)
        df.at[idx, '压力规整化产量'] = normalized_rate

    except Exception as e:
        print(f"第{idx + 1}行数据计算失败：{str(e)}")
        df.at[idx, '压力规整化产量'] = None  # 标记异常值

# 保存结果到原Excel（或新文件）
output_path =  excel_path  # 避免覆盖原文件
df.to_excel(output_path, index=False)
print(f"计算完成，结果已保存至：{output_path}")


# 计算物质平衡拟时间
print("__________________物质平衡拟时间又引入Ct压缩系数__________________________")
"""
计算0-t的平均p/Z(依据累计采量),由平均p/Z-p.得到平均p(pvt关系表)，得到平均μ和Ct，带入计算tca
"""

def calculate_material_balance_pseudo_time(t, q, Gp):
    """
    计算物质平衡时间tca（原始条件参数μg_i、Z_i、Ct_i为已知特定值）
    :param t: 时间序列（单位：需统一，如天）
    :param q: 产量序列（与t同长度，单位：体积/时间，如m³/天）
    :param Gp: 累积产量序列（与t同长度，单位：体积，如m³）

    :return: tca序列（与t同长度，单位与t一致）
    """
    """
    固定变量：
            :param G: 初始地质储量（单位：体积，如m³）
            :param pvt: GasPVT实例，用于查询开发过程中的PVT参数
            :param p_i: 原始地层压力（单位：Pa）
            :param μg_i: 原始条件下的气体黏度（Pa·s，已知特定值）
            :param Z_i: 原始条件下的压缩因子（无因次，已知特定值）
            :param Ct_i: 原始条件下的总压缩系数（MPa^-1，已知特定值）
    """



    # 1. 原始条件下的p/Z值
    p_over_Z_i = pi / Zi

    # 2. 逐点计算每个时刻的压力、μg、Ct
    n = len(t)
    p_list = []  # 每个时刻的压力（Pa）
    μg_list = []  # 每个时刻的气体黏度（Pa·s）
    Ct_list = []  # 每个时刻的总压缩系数（MPa^-1）

    for i in range(n):
        # 物质平衡计算p/Z
        Gp_i = Gp[i]
        p_over_Z = p_over_Z_i * (1 - Gp_i / G)  # p/Z = (p_i/Z_i) * (1 - Gp/G)

        # 反推压力p：找到满足 p/Z(p) = p_over_Z 的p（通过二分法）
        def f(p_candidate):
            Z_candidate = pvt.get_Z(p_candidate)
            return p_candidate / Z_candidate - p_over_Z  # 目标：使该值为0

        # 二分法求解p（限制在PVT数据范围内）
        p_min, p_max = pvt.p_values.min(), pvt.p_values.max()
        try:
            p = optimize.bisect(f, p_min, p_max)
            p_list.append(p)
        except ValueError as e:
            print(f"二分法求解压力失败：{e}")
            p_list.append(np.nan)

        # 获取该压力下的PVT参数（开发过程中的μg和Ct）
        μg, _, Ct = pvt.get_properties(p)
        μg_list.append(μg)
        Ct_list.append(Ct)

    # 3. 计算积分核：q(τ)/(μg(τ) * Cg(τ))，其中Cg = Z/(p * Ct)（气体压缩系数）
    # 注意：Ct单位是MPa^-1，需转换为Pa^-1（1 MPa = 1e6 Pa → 1 MPa^-1 = 1e-6 Pa^-1）
    Ct_Pa = np.array(Ct_list) * 1e-6  # 转换为Pa^-1
    p_array = np.array(p_list)
    Z_array = np.array([pvt.get_Z(p) for p in p_array])  # 每个压力对应的Z
    Cg = Z_array / (p_array * Ct_Pa)  # 气体压缩系数（Pa^-1）
    integrand = q / (np.array(μg_list) * Cg)  # 积分核

    # 4. 用梯形法计算0~t的积分（每个时刻的累积积分）
    integral = np.zeros(n)
    for i in range(1, n):
        integral[i] = np.trapezoid(integrand[:i + 1], t[:i + 1])
    # print("积分核integrand的值：", integrand)
    # print("积分值integral的值：", integral)

    # 5. 计算tca：tca = (μg_i * Ct_i / q(t)) * 积分值
    q_nonzero = np.where(q == 0, 1e-10, q)  # 避免除以0
    tca = (μgi * Cti / q_nonzero) * integral

    return tca

print("_____________________excel测试计算物质平衡拟时间_________________________________________")
# 读取数据
df = pd.read_excel("规整化—D1井生产数据.xlsx")

# 检查必要列是否存在
required_cols = ['Date', 'Qg', 'Gp']
if not set(required_cols).issubset(df.columns):
    raise ValueError(f"Excel文件必须包含以下列：{required_cols}")

# 处理日期：直接使用Date列的整数值作为相对时间（单位：天）
t = df['Date'].values  # 时间序列（天）

# 提取产量和累积产量
q = df['Qg'].values  # 产量序列
Gp = df['Gp'].values  # 累积产量序列

tca = calculate_material_balance_pseudo_time(t, q, Gp)

# 添加tca列到DataFrame
df['tca'] = tca

# 将结果写入新的Excel文件，避免覆盖原文件
excel_path = '规整化—D1井生产数据.xlsx'

output_path =  excel_path  # 避免覆盖原文件
df.to_excel(output_path, index=False)
print(f"计算完成，结果已保存至：{output_path}")

# 计算压力规整产量积分和积分导数


# ------------------- 1. 定义积分计算函数 -------------------
def calculate_pressure_normalized_rate_integral(df, tca_col, rate_col, date_col):
    """
    计算压力规整化产量积分

    参数：
    df: DataFrame，包含原始数据
    tca_col: str，tca列的列名
    rate_col: str，压力规整化产量列的列名
    date_col: str，日期列的列名（用于排序）

    返回：
    DataFrame，包含原始数据及新增的积分结果列
    """
    # 按日期排序，确保时间序列正确
    df_sorted = df.sort_values(by=date_col).reset_index(drop=True)

    # 提取计算所需数据
    tca = df_sorted[tca_col].values
    pressure_rate = df_sorted[rate_col].values
    integral_results = []

    # 逐点计算积分（梯形法则）
    for i in range(len(tca)):
        current_tca = tca[i]
        if current_tca <= 0:
            # 避免tca为0或负数导致的计算错误
            integral_results.append(0.0)
        else:
            # 计算从第0到第i个点的积分（梯形法则）
            segment_integral = np.trapezoid(pressure_rate[:i + 1], tca[:i + 1])
            # 压力规整化产量积分 = 积分结果 / 当前tca
            integral = segment_integral / current_tca
            integral_results.append(integral)

    # 将结果添加为新列
    df_sorted["压力规整化产量积分"] = integral_results
    return df_sorted

print("_______________________excel测试压力规整化产量积分______________________________________")
# ------------------- 2. 读取Excel数据 -------------------
# 替换为你的Excel文件路径
excel_path = "规整化—D1井生产数据.xlsx"
# 读取数据（假设工作表名为Sheet1，若不同可修改sheet_name参数）
df = pd.read_excel(excel_path, sheet_name="Sheet1")

# ------------------- 3. 调用函数计算积分 -------------------
# 定义列名（需与你的Excel实际列名一致）
tca_column = "tca"
rate_column = "压力规整化产量"
date_column = "Date"

# 调用计算函数
result_df = calculate_pressure_normalized_rate_integral(
    df=df,
    tca_col=tca_column,
    rate_col=rate_column,
    date_col=date_column
)

# ------------------- 4. 保存结果到Excel -------------------
# 保存回原文件（若需保留原文件，可修改为新路径，如"结果文件.xlsx"）
result_df.to_excel(excel_path, index=False, sheet_name="Sheet1")

print("计算完成！压力规整化产量积分已添加到Excel文件最后一列。")


# 计算压力规整化产量积分导数
def calculate_pressure_normalized_rate_derivative(df, tca_col, integral_col, date_col):
    """
    处理tca第一个值为0的情况，计算压力规整化产量积分导数
    """
    # 按日期排序
    df_sorted = df.sort_values(by=date_col).reset_index(drop=True)

    tca = df_sorted[tca_col].values
    integral = df_sorted[integral_col].values
    n = len(tca)

    # 处理tca中的非正值（仅允许第一个值为0，其他值必须为正）
    non_positive_indices = np.where(tca <= 0)[0]
    if len(non_positive_indices) > 0:
        # 检查是否只有第一个值为0，其他值是否为正
        if not (non_positive_indices == 0).all() or (tca[1:] <= 0).any():
            raise ValueError("除第一个值外，tca列存在其他非正值，请检查数据！")
        print("警告：tca第一个值为0，将特殊处理该点的导数计算")

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

    df_sorted["压力规整化产量积分导数"] = deriv_results
    return df_sorted

print("___________________________excel测试计压力规整积分导数_________________________________")
# ------------------- 主流程 -------------------
excel_path = "规整化—D1井生产数据.xlsx"  # 替换为你的文件路径
df = pd.read_excel(excel_path, sheet_name="Sheet1")

# 定义列名（与你的Excel一致）
tca_column = "tca"
integral_column = "压力规整化产量积分"
date_column = "Date"

# 计算并保存
result_df = calculate_pressure_normalized_rate_derivative(
    df=df,
    tca_col=tca_column,
    integral_col=integral_column,
    date_col=date_column
)
result_df.to_excel(excel_path, index=False, sheet_name="Sheet1")

print("计算完成！已处理tca第一个值为0的情况。")

