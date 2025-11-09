import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# 创建气井生产数据图表
def create_gas_production_plot(well_name, df,title): # GAS PRODUCTION ANALYSIS
    """创建气井生产数据图表，使用您提供的外观设计"""

    # 创建图形，设置更宽的灰色边框
    fig = plt.figure(figsize=(13, 11), facecolor='#3A3A3A')  # 更明显的灰色边框

    # 创建坐标轴，内部为黑色背景
    ax1 = fig.add_axes([0.1, 0.1, 0.8, 0.75], facecolor='black')
    ax2 = ax1.twinx()  # 创建第二个y轴用于累计产量

    # 在灰色区域顶部添加标题
    fig.suptitle(f'{well_name} - {title}',
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