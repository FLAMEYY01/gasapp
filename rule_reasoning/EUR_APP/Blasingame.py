import streamlit as st
from utils import GasPVT
import pandas as pd
import numpy as np
import scipy.optimize as optimize
# 输入是df,也是st.session_state["parameter_dict"]和st.session_state["data_dict"]
# 调用Blasingame文件夹的方法，
# 输出计算的数据df存储到st.session_state里边

# 那个数据的日期处理需要注意下











parameters_dict={
    "μgi": 1.8,
    "Zi": 1.0,
    "pi": 25,
    "Cti": 0.064,
    "G": 7999257418,
    "K": 20,
    "Φ": 0.12,
    "Ti": 220,
    "h": 20,
}
data_df = pd.read_excel("数据流—D1井生产数据.xlsx")







def Blasingame(parameters_dict,data_df):
    """
    :param parameter:
    :param data:
    :return:
    """
# ——————————————————————————————————参数设置————————————————————————————————————————————————————————————————————————————————————————————————————————————————
    pvt = GasPVT('configs/gas_pvt_properties.csv')
    # μgi, Zi, pi, Cti, G, K, Φ = parameters_dict['μgi'], parameters_dict["Zi"], parameters_dict["pi"], parameters_dict["Cti"], parameters_dict["G"], parameters_dict["K"], parameters_dict["Φ"]
    μgi, Zi, pi, Cti, G, K, Φ, Ti, h = parameters_dict['μgi'], parameters_dict["Zi"], parameters_dict["pi"], \
    parameters_dict["Cti"], parameters_dict["G"], parameters_dict["K"], parameters_dict["Φ"], parameters_dict["Ti"], \
    parameters_dict["h"]

# ——————————————————————————————————函数-压力规整化产量——————————————————————————————————————————————————————————————
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

        P_pi = calculate_normalized_pseudopressure(pi, pvt)

        # 计算井底流压p_wf对应的规整拟压力P_pwf
        P_pwf = calculate_normalized_pseudopressure(p_wf, pvt)

        # 计算ΔP_p
        delta_P_p = P_pi - P_pwf

        # 计算压力规整化产量
        pressure_normalized_rate = q / delta_P_p
        return pressure_normalized_rate

# ——————————————————————————————————计算-压力规整化产量——————————————————————————————————————————————————————————————
    # 遍历每条数据计算压力规整化产量
    data_df['压力规整化产量'] = None  # 新增结果列

    for idx, row in data_df.iterrows():
        try:
            q = row['Qg']  # 实际产量
            p_wf = row['Pwf'] #* 1e6  # 井底流压（假设Excel中单位为MPa，转换为Pa）

            # 计算压力规整化产量
            normalized_rate = calculate_pressure_normalized_rate(q, p_wf)
            data_df.at[idx, '压力规整化产量'] = normalized_rate

        except Exception as e:
            print(f"第{idx + 1}行数据计算失败：{str(e)}")
            data_df.at[idx, '压力规整化产量'] = None  # 标记异常值

# —————————————————————————————————————函数—物质平衡拟时间——————————————————————————————————————————————————

    def calculate_material_balance_pseudo_time(relative_t, q, Gp):
        """
        计算物质平衡时间tca（原始条件参数μg_i、Z_i、Ct_i为已知特定值）
        :param relative_t: 时间序列（单位：需统一，如天）
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
        n = len(relative_t)
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
            integral[i] = np.trapezoid(integrand[:i + 1], relative_t[:i + 1])

        # 5. 计算tca：tca = (μg_i * Ct_i / q(t)) * 积分值
        q_nonzero = np.where(q == 0, 1e-10, q)  # 避免除以0
        tca = (μgi * Cti / q_nonzero) * integral

        return tca

# —————————————————————————————————————计算—物质平衡拟时间——————————————————————————————————————————————————
    # 处理日期：直接使用Date列的整数值作为相对时间（单位：天）
    # t = data_df['Date'].values  # 时间序列（天）
    data_df['Date'] = pd.to_datetime(data_df['Date'], errors='coerce')
    data_df['relative_t'] = (data_df['Date'] - data_df['Date'].min()).dt.days
    relative_t=data_df['relative_t'].values

    # 提取产量和累积产量
    q = data_df['Qg'].values  # 产量序列
    Gp = data_df['Gp'].values  # 累积产量序列

    tca = calculate_material_balance_pseudo_time(relative_t, q, Gp)

    # 添加tca列到DataFrame
    data_df['tca'] = tca

#______________________________计算压力规整产量积分和积分导数__________________________________

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

    # ------------------- 3. 调用函数计算积分 -------------------
    # 定义列名（需与你的Excel实际列名一致）
    tca_column = "tca"
    rate_column = "压力规整化产量"
    date_column = "relative_t"

    # 调用计算函数
    data_df = calculate_pressure_normalized_rate_integral(
        df=data_df,
        tca_col=tca_column,
        rate_col=rate_column,
        date_col=date_column
    )

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

    # 定义列名（与你的Excel一致）
    tca_column = "tca"
    integral_column = "压力规整化产量积分"
    date_column = "relative_t"

    # 计算并保存
    Blasimgame_normized_df = calculate_pressure_normalized_rate_derivative(
        df=data_df,
        tca_col=tca_column,
        integral_col=integral_column,
        date_col=date_column
    )


#———————————————————————————————————绘制无量纲图版———————————————————————————————————————————————————————————————————————


#______________________计算无量纲时间t_caDd__________________________________________
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

    # 随意设置一组re和rwa
    r_e, r_wa = 100, 5
    # 计算 tcaDd
    tcaDd = [calculate_tcaDd(t_ca, r_e, r_wa) for t_ca in Blasimgame_normized_df['tca']]

    # 将计算结果添加到 DataFrame 的最后一列
    Blasimgame_normized_df['tcaDd'] = tcaDd

#___________________________计算Bgi_____________________________________
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

    Bgi = calculate_Bgi(Ti)

#_______________________________计算无量纲产量q_Dd__________________________________________
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
        denominator = K * h * (
                    calculate_normalized_pseudopressure(pi, pvt) - calculate_normalized_pseudopressure(pwf, pvt))
        q_D = numerator / denominator

        # 3. 计算q_Dd（公式8-79）
        r_eD = re / rw
        q_Dd = q_D * (np.log(r_eD) - 0.5)

        return q_Dd

    # 计算 qDd
    qDd = [calculate_qDd(q, pwf, r_e, r_wa) for q, pwf in zip(Blasimgame_normized_df['Qg'], Blasimgame_normized_df['Pwf'])]

    # 将计算结果添加到 DataFrame 的最后一列
    Blasimgame_normized_df['qDd'] = qDd


#______________________________计算无量纲产量积分qDdj_______________________________________________
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

    # ------------------- 3. 调用函数计算积分 -------------------
    # 定义列名（需与你的Excel实际列名一致）
    tcaDd_column = "tcaDd"
    qDd_column = "qDd"
    date_column = "relative_t"

    # 调用计算函数
    Blasimgame_df = calculate_qDdj(
        df=Blasimgame_normized_df,
        tcaDd_col=tcaDd_column,
        qDd_col=qDd_column,
        date_col=date_column
    )

#________________________计算无量纲产量积分导数qDdjd___________________________________
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

    # 定义列名（与你的Excel一致）
    tcaDd_column = "tcaDd"
    qDdj_column = "qDdj"
    date_column = "relative_t"

    # 计算并保存
    Blasimgame_df = calculate_qDdjd(
        df=Blasimgame_df,
        tcaDd_col=tcaDd_column,
        qDdj_col=qDdj_column,
        date_col=date_column
    )
    # print(Blasimgame_df)

#————————————————————————上面计算规整化和无量纲数据————————————————————————————————————————————————————————————————————————
#——————————————————————————————————————接下来拟合和计算EUR———————————————————————————————————————————————————————————————
    def nihe():
        """
        输入数据应该是1组确定的规整化的时间序列
        一组是有参数的无量纲时间序列




        :return:
        """
        pass


    Blasingame_EUR=1000000000
    return Blasimgame_df,Blasingame_EUR


if __name__=="main":
    a, b = Blasingame(parameters_dict, data_df)
