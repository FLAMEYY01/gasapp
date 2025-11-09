import streamlit as st
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import numpy as np
import pandas as pd
import os,sys,base64
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
from fetkovich_plot import create_gas_production_plot

# 数据库连接函数
def get_well_data(well_name):
    """从数据库获取气井数据"""
    conn = sqlite3.connect('EUR_Predict/database/gas_wells_production.db')

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
    conn = sqlite3.connect('EUR_Predict/database/gas_wells_production.db')

    query = "SELECT well_name FROM wells ORDER BY well_name"
    df = pd.read_sql_query(query, conn)
    conn.close()

    return df['well_name'].tolist()


def Get_Base64_of_Bin_File(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# 虚拟主函数main():
#====================================================================================
def main():
    st.set_page_config(layout="wide")
    img_base64 = Get_Base64_of_Bin_File("./EUR_Predict/images/EUR_predict.png")
    st.markdown(
        f"""
          <div style="text-align: center;">
              <img src="data:image/jpeg;base64,{img_base64}" style="max-width: 100%; height: auto;" />
          </div>
          """,
        unsafe_allow_html=True,
    )
    st.set_page_config(
      page_title="EUR综合预测",
      page_icon="🏠",
      layout="wide"
    )

    wells = get_wells_list()

    # 创建选择框
    selected_well = st.selectbox(
        "选择气井:",
        wells,
        index=0,
        help="选择要分析的气井"
    )
    df = get_well_data(selected_well)

    col0,col1,col2,col3,col4=st.columns(5)
    with col0:
        st.write("井信息")
        with st.container(border=True,height=225):
            st.write(f"井名：{selected_well}")
            st.write(f"总生产天数:{len(df)}")
            st.write(f"数据期间：{df['record_date'].min().strftime('%Y-%m')} 至 {df['record_date'].max().strftime('%Y-%m')}")
            latest_rate = df['daily_gas_rate'].iloc[-1]
            st.write(f"当前日产量：{latest_rate:,.0f} m³/天")
            cumulative = df['cumulative_gas'].iloc[-1]
            st.write(f"累计产量：{cumulative:,.0f} m³")
    with col1:
        st.write("井参数")
        st.container(border=True,height=225)
    with col2:
        st.write("专家描述")
        st.container(border=True,height=225)
    with col3:
        st.write("权重计算")
        st.container(border=True,height=225)
    with col4:
        st.write("大模型问答")
        st.container(border=True,height=225)

    col1,col2=st.columns(2)
    with col1:
        title="FetKovich"
        fig = create_gas_production_plot(selected_well, df,title)
        st.pyplot(fig)

    with col2:
        title="Comprehensive"
        fig = create_gas_production_plot(selected_well, df,title)
        st.pyplot(fig)


    return

#***********************************************************************************************************
if __name__ == '__main__':
  main()
#==================== 程序结束！=======================================