import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# 设置中文字体（如果需要显示中文）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']  # 支持中文
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号


# 创建气井生产数据图表
def create_gas_production_plot(df,method):
    """创建气井生产数据图表，使用您提供的外观设计"""

    # 创建图形，设置更宽的灰色边框
    fig = plt.figure(figsize=(13, 11), facecolor='#3A3A3A')  # 更明显的灰色边框

    # 创建坐标轴，内部为黑色背景
    ax1 = fig.add_axes([0.1, 0.1, 0.8, 0.75], facecolor='black')
    ax2 = ax1.twinx()  # 创建第二个y轴用于累计产量

    # 在灰色区域顶部添加标题，需要输入添加well_name
    # fig.suptitle(f'{well_name} - GAS PRODUCTION ANALYSIS',
    #              fontsize=22,
    #              color='white',
    #              y=0.1,
    #              fontweight='bold',
    #              fontfamily='sans-serif')
    fig.suptitle(f'{method} Typecurve Analysis',color='white',y=0.83,)
    # 设置坐标轴样式
    ax1.tick_params(axis='both', colors='white', which='both', labelsize=11)
    ax2.tick_params(axis='y', colors='cyan', which='both', labelsize=11)

    for spine in ax1.spines.values():
        spine.set_color('#E0E0E0')  # 浅灰色边框
        spine.set_linewidth(2)

    for spine in ax2.spines.values():
        spine.set_color('#E0E0E0')  # 浅灰色边框
        spine.set_linewidth(2)

    # 绘制瞬时产气量曲线（左侧y轴，Qg）- 去掉无用的line1变量
    ax1.plot(df['tca'], df['压力规整化产量'],
             color='lime', linewidth=2.5, label='压力规整化产量')
    ax1.plot(df['tca'], df['压力规整化产量积分'],
             color='lime', linewidth=2.5, label='压力规整化产量积分')

    # 绘制累计产气量曲线（右侧y轴，Gp）- 去掉无用的line2变量
    ax2.plot(df['tca'], df['压力规整化产量积分导数'],
             color='cyan', linewidth=2.5, label='压力规整化产量积分导数')

    # 设置标签
    ax1.set_xlabel('tca', color='white', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Normalized Rate, Integral', color='lime', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Beta Derivative ', color='cyan', fontsize=14, fontweight='bold')

    # # 格式化x轴日期
    # ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    # ax1.xaxis.set_major_locator(mdates.YearLocator())
    # # 如果数据跨度小于1年，可以使用月Locator
    # if (df['Date'].max() - df['Date'].min()).days < 365:
    #     ax1.xaxis.set_major_locator(mdates.MonthLocator())
    #     ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    # plt.setp(ax1.xaxis.get_majorticklabels(), rotation=0, ha='center')

    # 精细网格
    ax1.grid(True, which='major', alpha=0.3, color='gray', linestyle='-', linewidth=0.8)
    ax1.grid(True, which='minor', alpha=0.2, color='gray', linestyle=':', linewidth=0.5)

    # 组合图例（依然正常工作，因为legend从axes获取handle，不需要line变量）
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               facecolor='#505050', edgecolor='white',
               labelcolor='white', fontsize=12,
               loc='upper right', framealpha=0.9)

    # # 添加统计信息文本框
    # latest_data = df.iloc[-1]
    # stats_text = f"""
    # Latest Data ({latest_data['Date'].strftime('%Y-%m-%d')}):
    # Daily Rate (Qg): {latest_data['Qg']:,.0f} m³/day
    # Cumulative (Gp): {latest_data['Gp']:,.0f} m³
    # Max Daily Rate: {df['Qg'].max():,.0f} m³/day
    # Total Days: {len(df):,}
    # Average Daily Rate: {df['Qg'].mean():,.0f} m³/day
    # """
    #
    # ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, fontsize=10,
    #          verticalalignment='top', color='white',
    #          bbox=dict(boxstyle='round', facecolor='#404040', alpha=0.8))

    return fig


# Streamlit 主程序
def main():
    st.title("📊 气井生产数据分析（Excel读取版）")
    st.markdown("---")

    # 上传Excel文件
    uploaded_file = st.file_uploader("请上传Excel文件", type=['xlsx', 'xls'])

    if uploaded_file is not None:
        try:
            # 读取Excel文件
            df = pd.read_excel(uploaded_file)

            # 显示数据预览
            st.subheader("数据预览")
            st.dataframe(df.head(10))

            # 数据预处理
            st.subheader("数据预处理")

            # 检查必要的列是否存在
            required_columns = ['Date', 'Qg', 'Gp']
            missing_cols = [col for col in required_columns if col not in df.columns]

            if missing_cols:
                st.error(f"Excel文件缺少必要的列：{', '.join(missing_cols)}")
                st.info(f"请确保Excel表头包含：{', '.join(required_columns)}（对应你的表头：Date-Qg-Gp）")
                return

            # 转换Date列为日期格式
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            # 去除日期为空或无效的行
            df = df.dropna(subset=['Date', 'Qg', 'Gp'])

            # 按日期排序
            df = df.sort_values('Date').reset_index(drop=True)

            # 检查数据有效性
            if len(df) < 2:
                st.error("有效数据不足，请确保Excel中有至少2条有效记录")
                return

            st.success(f"数据预处理完成！共 {len(df)} 条有效记录")
            st.write(f"数据时间范围：{df['Date'].min().strftime('%Y-%m-%d')} 至 {df['Date'].max().strftime('%Y-%m-%d')}")

            # 选择气井名称（如果Excel中有Gas列，使用Gas列作为井名；否则手动输入）
            if 'Gas' in df.columns and df['Gas'].nunique() > 0:
                well_names = df['Gas'].unique()
                selected_well = st.selectbox("选择气井", well_names)
                # 筛选选中井的数据
                df_filtered = df[df['Gas'] == selected_well].copy()
            else:
                selected_well = st.text_input("输入气井名称", value="气井1")
                df_filtered = df.copy()

            # 确保筛选后还有数据
            if len(df_filtered) == 0:
                st.error("所选气井没有有效数据")
                return

            # 创建并显示图表
            st.subheader("生产曲线图表")
            fig = create_gas_production_plot(selected_well, df_filtered)
            st.pyplot(fig, use_container_width=True)

            # 下载处理后的数据（可选）
            if st.button("下载处理后的数据"):
                df_filtered.to_excel("processed_production_data.xlsx", index=False)
                with open("processed_production_data.xlsx", "rb") as file:
                    st.download_button(
                        label="点击下载",
                        data=file,
                        file_name="processed_production_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        except Exception as e:
            st.error(f"处理过程中出现错误：{str(e)}")
            st.info("请检查Excel文件格式是否正确，表头是否为：Gas	Date	Qg	Qw	Pwf	Gp")

    else:
        st.info("请上传Excel文件开始分析")
        # 显示示例表头格式
        st.markdown("### 示例Excel表头格式")
        sample_df = pd.DataFrame({
            'Gas': ['井1', '井1', '井1'],
            'Date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'Qg': [12000, 11800, 11500],
            'Qw': [50, 48, 45],
            'Pwf': [15.2, 14.8, 14.5],
            'Gp': [12000, 23800, 35300]
        })
        st.dataframe(sample_df)


if __name__ == "__main__":
    main()