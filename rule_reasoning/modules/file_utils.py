import streamlit as st
import pandas as pd
import os


def select_ruleset_file():
    """
    通用规则集选择器：允许用户从本地或服务器端目录加载 Excel 文件。

    返回:
        pd.DataFrame or None: 返回读取后的规则集数据框，或None（未选文件）
    """
    method = st.radio("📁 选择规则集文件来源:", ["本地上传", "服务器加载"])

    if method == "本地上传":
        uploaded_file = st.file_uploader("上传Excel文件:", type=["xlsx", "xls"])
        if uploaded_file:
            return pd.read_excel(uploaded_file)

    else:
        sub_dir = "./rulesets/"
        if not os.path.exists(sub_dir):
            st.error("❌ 未找到 rulesets 子目录")
            return None

        excel_files = [f for f in os.listdir(sub_dir) if f.endswith((".xlsx", ".xls"))]
        selected_file = st.selectbox("选择服务器端文件:", excel_files)
        if st.button("加载文件"):
            return pd.read_excel(os.path.join(sub_dir, selected_file))

    return None
