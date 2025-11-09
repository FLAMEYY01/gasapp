import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.integrate import cumulative_trapezoid
import io
import math

# 页面标题
st.title("Fetkovich方法拟合曲线分析")
st.write("上传数据文件（CSV或Excel），进行Fetkovich产量递减曲线拟合分析")

# ----------------------
# 1. 数据上传与处理
# ----------------------
uploaded_file = st.file_uploader("选择数据文件", type=["csv", "xlsx"])

if uploaded_file is not None:
    # 读取数据
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("数据预览")
        st.dataframe(df.head())

        # 让用户选择时间列和产量列
        time_col = st.selectbox("选择时间列", df.columns)
        rate_col = st.selectbox("选择产量列", df.columns)

        # 提取数据
        time_data = df[time_col]
        rate_data = df[rate_col].values


        # 处理时间数据 - 修复TimedeltaIndex问题
        def convert_time_to_days(time_series):
            """将时间数据转换为天数"""
            # 如果是日期时间类型
            if pd.api.types.is_datetime64_any_dtype(time_series):
                start_date = time_series.min()
                return (time_series - start_date).dt.total_seconds() / (24 * 3600)
            # 如果是时间差类型
            elif hasattr(time_series, 'dtype') and np.issubdtype(time_series.dtype, np.timedelta64):
                return time_series / np.timedelta64(1, 'D')
            # 如果是数值类型，直接返回
            elif pd.api.types.is_numeric_dtype(time_series):
                return time_series
            # 其他情况尝试转换为数值
            else:
                try:
                    return pd.to_numeric(time_series, errors='coerce')
                except:
                    st.error("无法处理时间列数据，请确保时间列是数值、日期或时间差格式")
                    st.stop()


        # 转换时间数据
        time_data_days = convert_time_to_days(time_data)

        # 检查是否有NaN值
        if time_data_days.isna().any() or np.isnan(rate_data).any():
            st.error("数据中包含无效值 (NaN)，请检查数据")
            st.stop()

        # 转换为numpy数组并确保是浮点型
        time_data_float = time_data_days.values.astype(float)
        rate_data_float = rate_data.astype(float)

        # 按时间排序
        sorted_indices = np.argsort(time_data_float)
        time_data_float = time_data_float[sorted_indices]
        rate_data_float = rate_data_float[sorted_indices]

        # 显示转换后的时间范围
        st.write(f"时间范围: {time_data_float.min():.1f} 到 {time_data_float.max():.1f} (单位: 天)")
        st.write(f"产量范围: {rate_data_float.min():.1f} 到 {rate_data_float.max():.1f} m³/d")

    except Exception as e:
        st.error(f"数据读取错误: {str(e)}")
        st.stop()

    # ----------------------
    # 2. 储层物性参数输入
    # ----------------------
    st.subheader("储层物性参数")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**基本参数**")
        porosity = st.number_input("孔隙度 φ (小数)", value=0.15, min_value=0.01, max_value=0.4, format="%.3f")
        viscosity = st.number_input("初始条件下流体粘度 μ_i (mPa·s)", value=0.02, min_value=0.001, format="%.4f")
        compressibility = st.number_input("综合压缩系数 c_t (MPa⁻¹)", value=2.068e-5, min_value=1e-6, format="%.2e")
        gas_deviation_factor = st.number_input("天然气偏差系数 Z_i", value=0.85, min_value=0.1, max_value=1.5,
                                               format="%.3f")
        reservoir_temperature = st.number_input("地层温度 T_i (K)", value=350.0, min_value=100.0, format="%.1f")
        water_saturation = st.number_input("含水饱和度 S (小数)", value=0.3, min_value=0.0, max_value=0.8,
                                           format="%.2f")

    with col2:
        st.markdown("**几何参数**")
        actual_wellbore_radius = st.number_input("实际井筒半径 r_w (m)", value=0.09144, min_value=0.01, format="%.5f")
        skin_factor = st.number_input("表皮系数 S", value=0.0, format="%.2f")
        formation_thickness = st.number_input("储层厚度 h (m)", value=15.24, min_value=1.0, format="%.2f")
        initial_pressure = st.number_input("初始地层压力 p_i (MPa)", value=20.0, min_value=1.0, format="%.1f")
        flowing_pressure = st.number_input("井底流压 p_wf (MPa)", value=5.0, min_value=0.1, format="%.1f")

    # 标准条件参数
    p_sc = 0.101325  # MPa
    T_sc = 293.15  # K

    # 计算有效井筒半径
    effective_radius = actual_wellbore_radius * math.exp(-skin_factor)


    # ----------------------
    # 3. Fetkovich模型定义
    # ----------------------
    def fetkovich_model(t, q_i, d_i, b):
        """
        Fetkovich产量递减模型
        q_i: 初始产量
        d_i: 初始递减率
        b: 递减指数（0-1之间）
        """
        return q_i / ((1 + b * d_i * t) ** (1 / b))


    def calculate_gas_volume_factor(Z_i, p_sc, T_i, p_i, T_sc):
        """
        计算气体体积系数 B_gi
        B_gi = Z_i * p_sc * T_i / (p_i * T_sc)
        """
        return Z_i * p_sc * T_i / (p_i * T_sc)


    def calculate_pseudopressure(p, mu, Z, p_ref=0):
        """
        计算拟压力 ψ_p = ∫ [2p/(μZ)] dp 从 p_ref 到 p
        使用数值积分
        """
        # 创建压力数组
        p_array = np.linspace(p_ref, p, 100)

        # 计算被积函数 2p/(μZ)
        # 这里假设 μ 和 Z 不随压力变化，使用输入的常数值
        # 在实际应用中，μ 和 Z 可能随压力变化，需要更复杂的模型
        integrand = 2 * p_array / (mu * Z)

        # 使用梯形法则进行数值积分
        psi_p = np.trapz(integrand, p_array)

        return psi_p


    def calculate_permeability(q_i, pressure_case, B_gi, mu, h, p_i, p_wf, r_eD, Z_i=None, T_i=None, p_sc=None,
                               T_sc=None):
        """
        根据压力情况计算渗透率 K
        """
        geometric_factor = np.log(r_eD) - 0.5

        if pressure_case == "high_pressure":  # 压力高于25MPa
            # K = (1.842×10^4) * q_i * B_gi * μ * [ln(r_eD) - 0.5] / [h * (p_i - p_wf)]
            K = (1.842e4 * q_i * B_gi * mu * geometric_factor) / (h * (p_i - p_wf))
        elif pressure_case == "low_pressure":  # 压力小于13MPa
            # K = 3.684×10^4 * q_i * p_sc * T_i * μ * Z_i * [ln(r_eD) - 0.5] / [h * T_sc * (p_i² - p_wf²)]
            K = (3.684e4 * q_i * p_sc * T_i * mu * Z_i * geometric_factor) / (h * T_sc * (p_i ** 2 - p_wf ** 2))
        else:  # 中间压力范围 (13-25 MPa)
            # K = 3.684×10^4 * q_i * p_sc * T_i * [ln(r_eD) - 0.5] / [h * T_sc * (ψ_pi - ψ_pwf)]
            # 计算拟压力
            psi_pi = calculate_pseudopressure(p_i, mu, Z_i)
            psi_pwf = calculate_pseudopressure(p_wf, mu, Z_i)
            K = (3.684e4 * q_i * p_sc * T_i * geometric_factor) / (h * T_sc * (psi_pi - psi_pwf))

        return K


    def calculate_pore_volume(q_i, d_i, pressure_case, B_gi, c_t, p_i, p_wf, r_eD, Z_i=None, T_i=None, p_sc=None,
                              T_sc=None):
        """
        计算单井控制范围内的孔隙体积 V_p
        """
        if pressure_case == "high_pressure":  # 压力高于25MPa
            # V_p = B_gi * (q_i / D_i) / [c_t * (p_i - p_wf) * (1 - 1/r_eD²)]
            # 可约等于为 B_gi * (q_i / D_i) / [c_t * (p_i - p_wf)]
            V_p = (B_gi * (q_i / d_i)) / (c_t * (p_i - p_wf))
        elif pressure_case == "low_pressure":  # 压力小于13MPa
            # V_p = 2 * p_sc * Z_i * T_i * (q_i / D_i) / [c_t * T_sc * (p_i² - p_wf²) * (1 - 1/r_eD²)]
            V_p = (2 * p_sc * Z_i * T_i * (q_i / d_i)) / (c_t * T_sc * (p_i ** 2 - p_wf ** 2))
        else:  # 中间压力范围 (13-25 MPa)
            # V_p = [2 * p_sc * T_i * (q_i / D_i)] / [C_ti * T_sc * μ * (ψ_pi - ψ_pwf) * (1 - 1/r_eD²)]
            # 约等于 [2 * p_sc * T_i * (q_i / D_i)] / [C_ti * T_sc * μ * (ψ_pi - ψ_pwf)]
            # 计算拟压力
            psi_pi = calculate_pseudopressure(p_i, viscosity, Z_i)
            psi_pwf = calculate_pseudopressure(p_wf, viscosity, Z_i)
            V_p = (2 * p_sc * T_i * (q_i / d_i)) / (c_t * T_sc * viscosity * (psi_pi - psi_pwf))

        return V_p


    def calculate_gas_reserves(V_p, S, B_gi):
        """
        计算天然气地质储量 G
        G = 10^(-4) * V_p * (1 - S) / B_gi
        单位: 10^8 m³
        """
        G = 1e-4 * V_p * (1 - S) / B_gi
        return G


    def calculate_drainage_radius(V_p, h, phi):
        """
        计算井控半径 r_e
        r_e = sqrt( (10^4 * V_p) / (π * h * φ) )
        """
        # V_p 单位是 10^4 m³
        # 计算井控半径 (m)
        r_e = math.sqrt(V_p * 10000 / (math.pi * h * phi))

        return r_e


    def theoretical_dimensionless_time(t, k, phi, mu_i, c_t, r_wa, r_e):
        """
        计算理论无量纲时间
        根据Fetkovich方法，无量纲时间定义为:

        t_D = \frac{0.0864 \cdot k \cdot t}{\phi \cdot \mu_i \cdot c_t \cdot (r_e^2 - r_{wa}^2)} \times \frac{1}{0.5 \cdot \left[\ln\left(\frac{r_e}{r_{wa}}\right) - 0.5\right]}
        """
        # 计算分子
        numerator = 0.0864 * k * t

        # 计算分母
        denominator = phi * mu_i * c_t * (r_e ** 2 - r_wa ** 2)

        # 计算几何因子
        geometric_factor = 0.5 * (np.log(r_e / r_wa) - 0.5)

        # 计算无量纲时间
        t_D = (numerator / denominator) / geometric_factor

        return t_D


    def dimensionless_rate_fetkovich(q, B_gi, mu, K, h, p_i, p_wf, r_e, r_wa):
        """
        计算Fetkovich方法中的无量纲产量 q_Dd
        q_Dd = (1.842e4 * q * B_gi * μ) / (K * h * (p_i - p_wf)) * [ln(r_e/r_wa) - 0.5]
        """
        # 计算渗透模型中的无量纲产量 q_D
        q_D = (1.842e4 * q * B_gi * mu) / (K * h * (p_i - p_wf))

        # 计算几何因子
        geometric_factor = np.log(r_e / r_wa) - 0.5

        # 计算Fetkovich方法中的无量纲产量 q_Dd
        q_Dd = q_D * geometric_factor

        return q_Dd


    def theoretical_dimensionless_rate(t_D, r_eD, flow_regime="boundary_dominated"):
        """
        计算理论无量纲产量
        对于边界主导流阶段，使用Fetkovich典型曲线
        """
        if flow_regime == "boundary_dominated":
            # 边界主导流阶段的简化表达式
            return 1 / (np.log(r_eD) - 0.5) * np.exp(-2 * t_D / (r_eD ** 2 * (np.log(r_eD) - 0.75)))
        else:
            # 无限作用径向流阶段
            return 0.5 * (np.log(t_D) + 0.80907)


    def dimensionless_cumulative(t_D, b):
        """无量纲累计产量公式"""
        if b == 1:  # 调和递减
            return np.log(1 + t_D)
        else:  # 双曲递减
            return (1 / (1 - b)) * (1 - (1 + b * t_D) ** ((b - 1) / b))


    def calculate_dimensionless_cumulative_production(t_D, q_Dd):
        """
        计算无量纲累计产量 N_pDd
        N_pDd = ∫ q_Dd dt_D 从 0 到 t_D
        使用cumulative_trapezoid进行数值积分
        """
        return cumulative_trapezoid(q_Dd, t_D, initial=0)


    # ----------------------
    # 4. 曲线拟合
    # ----------------------
    st.subheader("拟合参数设置")
    col1, col2, col3 = st.columns(3)
    with col1:
        q_i_init = st.number_input("初始产量初始值 (m³/d)",
                                   value=float(max(rate_data_float)) if len(rate_data_float) > 0 else 10000.0,
                                   min_value=100.0, max_value=10000000.0)
    with col2:
        d_i_init = st.number_input("初始递减率初始值", value=0.1, min_value=0.001, max_value=1.0)
    with col3:
        b_init = st.number_input("递减指数初始值", value=0.5, min_value=0.001, max_value=0.999)

    if st.button("开始拟合"):
        try:
            # 曲线拟合
            popt, pcov = curve_fit(
                fetkovich_model,
                time_data_float,
                rate_data_float,
                p0=[q_i_init, d_i_init, b_init],
                bounds=([0, 0.001, 0.001], [max(rate_data_float) * 2, 1.0, 0.999])
            )

            # 提取拟合参数
            q_i_fit, d_i_fit, b_fit = popt

            # 计算拟合值
            rate_fit = fetkovich_model(time_data_float, q_i_fit, d_i_fit, b_fit)

            # 计算气体体积系数
            B_gi = calculate_gas_volume_factor(
                gas_deviation_factor, p_sc, reservoir_temperature,
                initial_pressure, T_sc
            )

            # 确定压力情况
            if initial_pressure > 25.0:  # 高压情况
                pressure_case = "high_pressure"
            elif initial_pressure < 13.0:  # 低压情况
                pressure_case = "low_pressure"
            else:  # 中间压力情况
                pressure_case = "intermediate_pressure"

            # 初始假设无量纲供给半径 (用于计算渗透率)
            initial_drainage_radius = 1000.0  # 初始假设值
            dimensionless_drainage_radius_initial = initial_drainage_radius / effective_radius

            # 计算渗透率
            if pressure_case == "high_pressure":
                permeability = calculate_permeability(
                    q_i_fit, pressure_case, B_gi, viscosity, formation_thickness,
                    initial_pressure, flowing_pressure, dimensionless_drainage_radius_initial
                )
            elif pressure_case == "low_pressure":
                permeability = calculate_permeability(
                    q_i_fit, pressure_case, B_gi, viscosity, formation_thickness,
                    initial_pressure, flowing_pressure, dimensionless_drainage_radius_initial,
                    Z_i=gas_deviation_factor, T_i=reservoir_temperature,
                    p_sc=p_sc, T_sc=T_sc
                )
            else:
                permeability = calculate_permeability(
                    q_i_fit, pressure_case, B_gi, viscosity, formation_thickness,
                    initial_pressure, flowing_pressure, dimensionless_drainage_radius_initial,
                    Z_i=gas_deviation_factor, T_i=reservoir_temperature,
                    p_sc=p_sc, T_sc=T_sc
                )

            # 计算孔隙体积
            if pressure_case == "high_pressure":
                pore_volume = calculate_pore_volume(
                    q_i_fit, d_i_fit, pressure_case, B_gi, compressibility,
                    initial_pressure, flowing_pressure, dimensionless_drainage_radius_initial
                )
            elif pressure_case == "low_pressure":
                pore_volume = calculate_pore_volume(
                    q_i_fit, d_i_fit, pressure_case, B_gi, compressibility,
                    initial_pressure, flowing_pressure, dimensionless_drainage_radius_initial,
                    Z_i=gas_deviation_factor, T_i=reservoir_temperature,
                    p_sc=p_sc, T_sc=T_sc
                )
            else:
                pore_volume = calculate_pore_volume(
                    q_i_fit, d_i_fit, pressure_case, B_gi, compressibility,
                    initial_pressure, flowing_pressure, dimensionless_drainage_radius_initial,
                    Z_i=gas_deviation_factor, T_i=reservoir_temperature,
                    p_sc=p_sc, T_sc=T_sc
                )

            # 计算天然气地质储量
            gas_reserves = calculate_gas_reserves(pore_volume, water_saturation, B_gi)

            # 计算井控半径
            drainage_radius = calculate_drainage_radius(pore_volume, formation_thickness, porosity)

            # 更新无量纲供给半径
            dimensionless_drainage_radius = drainage_radius / effective_radius

            # 显示拟合参数
            st.subheader("拟合结果参数")
            param_df = pd.DataFrame({
                "参数": ["初始产量 (q_i)", "初始递减率 (d_i)", "递减指数 (b)"],
                "拟合值": [f"{q_i_fit:.4f}", f"{d_i_fit:.4f}", f"{b_fit:.4f}"]
            })
            st.dataframe(param_df, use_container_width=True)

            # 显示储层物性参数
            st.subheader("储层物性参数")
            reservoir_df = pd.DataFrame({
                "参数": ["渗透率 K (mD)", "孔隙度 φ", "粘度 μ_i (mPa·s)", "压缩系数 c_t (MPa⁻¹)",
                         "气体偏差系数 Z_i", "气体体积系数 B_gi", "含水饱和度 S",
                         "实际井筒半径 r_w (m)", "表皮系数 S", "有效井筒半径 r_wa (m)", "压力情况"],
                "值": [f"{permeability:.3f}", f"{porosity:.3f}", f"{viscosity:.4f}",
                       f"{compressibility:.2e}", f"{gas_deviation_factor:.3f}",
                       f"{B_gi:.5f}", f"{water_saturation:.2f}",
                       f"{actual_wellbore_radius:.5f}", f"{skin_factor:.2f}",
                       f"{effective_radius:.5f}", pressure_case]
            })
            st.dataframe(reservoir_df, use_container_width=True)

            # 显示储层体积参数
            st.subheader("储层体积参数")
            volume_df = pd.DataFrame({
                "参数": ["孔隙体积 V_p (10^4 m³)", "井控半径 r_e (m)", "无量纲供给半径 r_eD",
                         "天然气地质储量 G (10^8 m³)"],
                "值": [f"{pore_volume:.2f}", f"{drainage_radius:.1f}",
                       f"{dimensionless_drainage_radius:.1f}", f"{gas_reserves:.2f}"]
            })
            st.dataframe(volume_df, use_container_width=True)

            # 如果是中间压力范围，显示拟压力计算结果
            if pressure_case == "intermediate_pressure":
                psi_pi = calculate_pseudopressure(initial_pressure, viscosity, gas_deviation_factor)
                psi_pwf = calculate_pseudopressure(flowing_pressure, viscosity, gas_deviation_factor)
                st.subheader("拟压力计算结果")
                psi_df = pd.DataFrame({
                    "参数": ["初始地层压力拟压力 ψ_pi", "井底流压拟压力 ψ_pwf", "拟压力差 (ψ_pi - ψ_pwf)"],
                    "值": [f"{psi_pi:.2f}", f"{psi_pwf:.2f}", f"{psi_pi - psi_pwf:.2f}"]
                })
                st.dataframe(psi_df, use_container_width=True)

            # ----------------------
            # 5. Draw Fetkovich-Arps Type Curves (Black Background)
            # ----------------------
            st.subheader("Fetkovich-Arps Type Curves")

            # Calculate theoretical dimensionless time
            t_D_theoretical = theoretical_dimensionless_time(
                time_data_float, permeability, porosity, viscosity,
                compressibility, effective_radius, drainage_radius
            )

            # Calculate dimensionless rate using Fetkovich method
            q_Dd_theoretical = dimensionless_rate_fetkovich(
                rate_data_float, B_gi, viscosity, permeability,
                formation_thickness, initial_pressure, flowing_pressure,
                drainage_radius, effective_radius
            )

            # Calculate dimensionless cumulative production
            N_pDd_theoretical = calculate_dimensionless_cumulative_production(t_D_theoretical, q_Dd_theoretical)

            # Generate theoretical curve data range
            t_D_range = np.logspace(-3, 3, 500)

            # Create figure with black background
            plt.style.use('dark_background')
            fig, ax1 = plt.subplots(figsize=(14, 9))
            fig.patch.set_facecolor('black')
            ax1.set_facecolor('black')

            # Define complete range of b values
            b_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            colors = plt.cm.plasma(np.linspace(0, 1, len(b_values)))

            # =============================================
            # Plot Dimensionless Rate vs Dimensionless Time (Left Y-axis)
            # =============================================

            # Plot theoretical rate decline curves (solid lines)
            for i, b_val in enumerate(b_values):
                if b_val == 1:  # Harmonic decline
                    q_D = 1.0 / (1 + t_D_range)
                else:  # Hyperbolic decline
                    q_D = 1.0 / ((1 + b_val * t_D_range) ** (1 / b_val))

                # Plot theoretical curves
                ax1.loglog(t_D_range, q_D,
                           color=colors[i], linewidth=2, alpha=0.8,
                           label=f'Rate b={b_val:.1f}')

            # Plot actual dimensionless rate data points
            ax1.loglog(t_D_theoretical, q_Dd_theoretical,
                       'o', markersize=6, markerfacecolor='red',
                       markeredgecolor='white', markeredgewidth=1,
                       label='Rate Data', zorder=10)

            # Plot best fit curve
            best_fit_curve = fetkovich_model(t_D_range, q_i_fit, d_i_fit, b_fit)
            best_fit_q_D = dimensionless_rate_fetkovich(
                best_fit_curve, B_gi, viscosity, permeability,
                formation_thickness, initial_pressure, flowing_pressure,
                drainage_radius, effective_radius
            )

            ax1.loglog(t_D_range, best_fit_q_D,
                       color='yellow', linewidth=2.5, alpha=0.9,
                       label=f'Best Fit Rate b={b_fit:.3f}', zorder=5)

            # Set left Y-axis
            ax1.set_xlabel('Dimensionless Time (t_D)', fontsize=12, fontweight='bold', color='white')
            ax1.set_ylabel('Dimensionless Rate (q_D)', fontsize=12, fontweight='bold', color='cyan')
            ax1.tick_params(axis='both', which='major', labelsize=10, colors='white')
            ax1.tick_params(axis='y', labelcolor='cyan')

            # =============================================
            # Plot Dimensionless Cumulative Production vs Dimensionless Time (Right Y-axis)
            # =============================================

            # Create right Y-axis
            ax2 = ax1.twinx()

            # Plot theoretical cumulative production curves (dashed lines)
            for i, b_val in enumerate(b_values):
                # Calculate dimensionless cumulative production
                if b_val == 1:  # Harmonic decline
                    N_pD = np.log(1 + t_D_range)
                else:  # Hyperbolic decline
                    N_pD = (1 / (1 - b_val)) * (1 - (1 + b_val * t_D_range) ** ((b_val - 1) / b_val))

                # Plot theoretical curves
                ax2.loglog(t_D_range, N_pD,
                           color=colors[i], linewidth=2, alpha=0.8, linestyle='--',
                           label=f'Cumulative b={b_val:.1f}')

            # Plot actual dimensionless cumulative production data points
            ax2.loglog(t_D_theoretical, N_pDd_theoretical,
                       's', markersize=6, markerfacecolor='blue',
                       markeredgecolor='white', markeredgewidth=1,
                       label='Cumulative Data', zorder=10)

            # Plot best fit cumulative production curve
            best_fit_N_pD = dimensionless_cumulative(t_D_range, b_fit)
            ax2.loglog(t_D_range, best_fit_N_pD,
                       color='orange', linewidth=2.5, alpha=0.9, linestyle='--',
                       label=f'Best Fit Cumulative b={b_fit:.3f}', zorder=5)

            # Set right Y-axis
            ax2.set_ylabel('Dimensionless Cumulative Production (N_pD)', fontsize=12, fontweight='bold',
                           color='magenta')
            ax2.tick_params(axis='y', labelcolor='magenta', labelsize=10)

            # =============================================
            # Chart Settings
            # =============================================

            # Set title
            ax1.set_title('Fetkovich-Arps Type Curves (Rate & Cumulative)',
                          fontsize=14, fontweight='bold', color='white', pad=20)

            # Set axis ranges
            ax1.set_xlim(1e-3, 1e3)
            ax1.set_ylim(1e-4, 2)
            ax2.set_ylim(1e-2, 1e2)

            # Add grid
            ax1.grid(True, which='both', linestyle='--', alpha=0.3, color='gray')

            # Combine legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()

            # Create unified legend
            all_lines = lines1 + lines2
            all_labels = labels1 + labels2

            # Place legend on the right side of the plot
            ax1.legend(all_lines, all_labels,
                       loc='center left',
                       bbox_to_anchor=(1.05, 0.5),
                       fontsize=10,
                       frameon=True,
                       framealpha=0.9,
                       facecolor='darkblue',
                       edgecolor='white',
                       labelcolor='white')

            # Adjust layout to make space for legend
            plt.tight_layout()
            st.pyplot(fig)

            # Add description
            st.info("""
            **Legend Description:**
            - **Solid lines**: Theoretical rate decline curves for different b values
            - **Dashed lines**: Theoretical cumulative production curves for different b values  
            - **Red circles**: Actual rate data points
            - **Blue squares**: Actual cumulative production data points
            - **Yellow solid line**: Best fit rate curve
            - **Orange dashed line**: Best fit cumulative production curve
            """)

        except Exception as e:
            st.error(f"拟合过程中出现错误: {str(e)}")
            st.info("提示：请检查输入参数是否合理，或尝试调整初始拟合参数")

else:
    st.info("请上传包含时间和产量数据的CSV或Excel文件开始分析")
    # 示例数据格式说明
    st.subheader("数据格式说明")
    example_data = pd.DataFrame({
        "时间（天）": [10, 20, 30, 40, 50],
        "产量（m³/d）": [1000, 850, 730, 630, 550]
    })
    st.dataframe(example_data)
    st.caption("数据应包含至少两列：时间列（如天数、月数）和产量列（如日产油量）")