import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import mpld3
from streamlit.components.v1 import html

# 你的画图函数（保持不变，新增返回 HTML 的逻辑）
def create_gas_production_plot(df):
    """创建气井生产数据图表，返回 Matplotlib 图形对象"""
    fig = plt.figure(figsize=(13, 11), facecolor='#3A3A3A')
    ax1 = fig.add_axes([0.1, 0.1, 0.8, 0.75], facecolor='black')
    ax2 = ax1.twinx()

    # 坐标轴样式
    ax1.tick_params(axis='both', colors='white', which='both', labelsize=11)
    ax2.tick_params(axis='y', colors='cyan', which='both', labelsize=11)
    for spine in ax1.spines.values():
        spine.set_color('#E0E0E0')
        spine.set_linewidth(2)
    for spine in ax2.spines.values():
        spine.set_color('#E0E0E0')
        spine.set_linewidth(2)

    # 绘制曲线
    ax1.plot(df['Date'], df['Qg'], color='lime', linewidth=2.5, label='Daily Gas Rate (Qg)')
    ax2.plot(df['Date'], df['Gp'], color='cyan', linewidth=2.5, label='Cumulative Gas (Gp)')

    # 标签设置
    ax1.set_ylabel('Daily Gas Rate (Qg, m³/day)', color='lime', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Cumulative Gas (Gp, m³)', color='cyan', fontsize=14, fontweight='bold')

    # 日期格式化
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    if (df['Date'].max() - df['Date'].min()).days < 365:
        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=0, ha='center')

    # 网格和图例
    ax1.grid(True, which='major', alpha=0.3, color='gray', linestyle='-', linewidth=0.8)
    ax1.grid(True, which='minor', alpha=0.2, color='gray', linestyle=':', linewidth=0.5)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               facecolor='#505050', edgecolor='white',
               labelcolor='white', fontsize=12,
               loc='upper right', framealpha=0.9)

    # 统计文本框
    latest_data = df.iloc[-1]
    stats_text = f"""
    Latest Data ({latest_data['Date'].strftime('%Y-%m-%d')}):
    Daily Rate (Qg): {latest_data['Qg']:,.0f} m³/day
    Cumulative (Gp): {latest_data['Gp']:,.0f} m³
    Max Daily Rate: {df['Qg'].max():,.0f} m³/day
    Total Days: {len(df):,}
    Average Daily Rate: {df['Qg'].mean():,.0f} m³/day
    """
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', color='white',
             bbox=dict(boxstyle='round', facecolor='#404040', alpha=0.8))

    return fig

# 模拟数据（替换为你的实际数据解析逻辑）
def get_sample_data():
    dates = pd.date_range("2025-01-01", "2025-12-31")
    qg = [42175, 38000, 55000, 76082] + list(range(40000, 42175, 50)) * 10
    gp = [5257418]
    for q in qg[1:]:
        gp.append(gp[-1] + q)
    min_len = min(len(dates), len(qg), len(gp))
    return pd.DataFrame({
        "Date": dates[:min_len],
        "Qg": qg[:min_len],
        "Gp": gp[:min_len]
    })

# 主逻辑：创建图表 + 嵌入下拉框
data_df = get_sample_data()
fig = create_gas_production_plot(data_df)

# 步骤1：将 Matplotlib 图表转为 HTML
fig_html = mpld3.fig_to_html(fig)

# 步骤2：创建 Streamlit 下拉框（隐藏默认样式，后续嵌入图表）
st.markdown(
    """
    <style>
    /* 隐藏 Streamlit 原生下拉框的容器，只保留下拉框本身 */
    #method-select-container {
        position: absolute;
        top: 50px;  /* 图表内垂直位置（可调整） */
        right: 80px; /* 图表内水平位置（可调整） */
        z-index: 100;
    }
    /* 美化下拉框，适配图表黑色背景 */
    #method-select {
        background-color: #404040;
        color: white;
        border: 1px solid #E0E0E0;
        border-radius: 5px;
        padding: 8px 12px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 步骤3：创建下拉框（用 key 绑定，方便后续获取值）
method = st.selectbox(
    "",  # 清空默认标签
    ["Blasingame", "FetKovich", "NPI"],
    index=0,
    key="method_select",
    label_visibility="collapsed"  # 隐藏标签
)

# 步骤4：将下拉框和图表 HTML 合并，嵌入页面
combined_html = f"""
<div style="position: relative;">
    {fig_html}  <!-- 图表 HTML -->
    <div id="method-select-container">
        <label style="color: white; font-weight: bold; margin-right: 8px;">方法:</label>
        <div id="method-select">{st.session_state['method_select']}</div>
    </div>
</div>
"""

# 渲染合并后的 HTML（关键：用 streamlit.components.v1.html 确保样式生效）
html(combined_html, width=1300, height=1100)

# 验证：打印选中的方法（后续可用于切换图表逻辑）
st.success(f"当前选中方法：{method}")