import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import pandas as pd
from datetime import datetime
import matplotlib.dates as mdates

# 设置页面
st.set_page_config(page_title="气井生产数据分析", page_icon="⛽", layout="wide")


# 数据库连接函数
def get_well_data(well_name):
    """从数据库获取气井数据"""
    conn = sqlite3.connect('database/gas_wells_production.db')

    query = """
    SELECT 
        p.record_date,
        p.daily_gas_rate,
        p.cumulative_gas
    FROM production_data p
    JOIN wells w ON p.well_id = w.well_id
    WHERE w.well_name = ?
    ORDER BY p.record_date
    """

    df = pd.read_sql_query(query, conn, params=(well_name,))
    conn.close()

    # 转换日期格式
    df['record_date'] = pd.to_datetime(df['record_date'])

    return df


def get_wells_list():
    """获取气井列表"""
    conn = sqlite3.connect('database/gas_wells_production.db')

    query = "SELECT well_name FROM wells ORDER BY well_name"
    df = pd.read_sql_query(query, conn)
    conn.close()

    return df['well_name'].tolist()


# 创建气井生产数据图表
def create_gas_production_plot(well_name, df):
    """创建气井生产数据图表，使用您提供的外观设计"""

    # 创建图形，设置更宽的灰色边框
    fig = plt.figure(figsize=(13, 11), facecolor='#3A3A3A')  # 更明显的灰色边框

    # 创建坐标轴，内部为黑色背景
    ax1 = fig.add_axes([0.1, 0.1, 0.8, 0.75], facecolor='black')
    ax2 = ax1.twinx()  # 创建第二个y轴用于累计产量

    # 在灰色区域顶部添加标题
    fig.suptitle(f'{well_name} - GAS PRODUCTION ANALYSIS',
                 fontsize=22,
                 color='white',
                 y=0.93,
                 fontweight='bold',
                 fontfamily='sans-serif')

    # 添加副标题
    fig.text(0.5, 0.87, 'Daily Rate & Cumulative Production',
             fontsize=16,
             color='lightgray',
             ha='center',
             style='italic')

    # 设置坐标轴样式
    ax1.tick_params(axis='both', colors='white', which='both', labelsize=11)
    ax2.tick_params(axis='y', colors='cyan', which='both', labelsize=11)

    for spine in ax1.spines.values():
        spine.set_color('#E0E0E0')  # 浅灰色边框
        spine.set_linewidth(2)

    for spine in ax2.spines.values():
        spine.set_color('#E0E0E0')  # 浅灰色边框
        spine.set_linewidth(2)

    # 绘制瞬时产气量曲线（左侧y轴）
    line1 = ax1.plot(df['record_date'], df['daily_gas_rate'],
                     color='lime', linewidth=2.5, label='Daily Gas Rate')[0]

    # 绘制累计产气量曲线（右侧y轴）
    line2 = ax2.plot(df['record_date'], df['cumulative_gas'],
                     color='cyan', linewidth=2.5, label='Cumulative Gas')[0]

    # 设置标签
    ax1.set_xlabel('Date', color='white', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Daily Gas Rate (m³/day)', color='lime', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Cumulative Gas (m³)', color='cyan', fontsize=14, fontweight='bold')

    # 格式化x轴日期
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

    # 精细网格
    ax1.grid(True, which='major', alpha=0.3, color='gray', linestyle='-', linewidth=0.8)
    ax1.grid(True, which='minor', alpha=0.2, color='gray', linestyle=':', linewidth=0.5)

    # 组合图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               facecolor='#505050', edgecolor='white',
               labelcolor='white', fontsize=12,
               loc='upper right', framealpha=0.9)

    # 添加统计信息文本框
    latest_data = df.iloc[-1]
    stats_text = f"""
    Latest Data ({latest_data['record_date'].strftime('%Y-%m-%d')}):
    Daily Rate: {latest_data['daily_gas_rate']:,.0f} m³/day
    Cumulative: {latest_data['cumulative_gas']:,.0f} m³
    Max Daily: {df['daily_gas_rate'].max():,.0f} m³/day
    Total Days: {len(df):,}
    """

    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', color='white',
             bbox=dict(boxstyle='round', facecolor='#404040', alpha=0.8))

    return fig




# 获取气井列表
if __name__=="__main__":
    wells = get_wells_list()

    # 创建选择框
    selected_well = st.selectbox(
    "选择气井:",
    wells,
    index=0,
    help="选择要分析的气井"
    )


    # 获取数据
    df = get_well_data(selected_well)


    # 显示基本信息
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="数据点数",
            value=f"{len(df):,}",
            help="总生产天数"
        )

    with col2:
        st.metric(
            label="数据期间",
            value=f"{df['record_date'].min().strftime('%Y-%m')} 至 {df['record_date'].max().strftime('%Y-%m')}",
            help="数据覆盖的时间范围"
        )

    with col3:
        latest_rate = df['daily_gas_rate'].iloc[-1]
        st.metric(
            label="当前日产量",
            value=f"{latest_rate:,.0f} m³/天",
            help="最新日期的瞬时产气量"
        )

    with col4:
        cumulative = df['cumulative_gas'].iloc[-1]
        st.metric(
            label="累计产量",
            value=f"{cumulative:,.0f} m³",
            help="截至最新日期的累计产气量"
        )

    # 创建并显示图表
    fig = create_gas_production_plot(selected_well, df)
    st.pyplot(fig)




