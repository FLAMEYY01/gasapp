import streamlit as st
import pandas as pd
import io
import os
import zipfile


def main():
    st.set_page_config(page_title="油田初始数据整理", layout="wide")
    st.title("油田初始数据整理工具")
    st.write("请导入多个Excel文件，每个文件需包含多张子表，每张子表需包含两列（时间列 + 数据列）")

    # 初始化session_state
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'merged_dfs' not in st.session_state:
        st.session_state.merged_dfs = {}  # 字典存储每个文件的合并结果

    # 多文件上传
    uploaded_files = st.file_uploader(
        "选择多个Excel文件",
        type=["xlsx", "xls"],
        key="file_uploader",
        accept_multiple_files=True
    )

    if uploaded_files:
        # 更新session_state
        st.session_state.uploaded_files = uploaded_files

        # 显示上传的文件信息
        st.success(f"已导入 {len(uploaded_files)} 个文件")

        # 预览所有文件的子表信息
        for file in uploaded_files:
            try:
                excel_file = pd.ExcelFile(file)
                sheet_names = excel_file.sheet_names

                with st.expander(f"📄 {file.name} - {len(sheet_names)}张子表"):
                    st.write(f"子表名称: {', '.join(sheet_names)}")

            except Exception as e:
                st.error(f"文件 {file.name} 解析失败：{str(e)}")

    # 按钮区域
    col1, col2 = st.columns(2)

    with col1:
        if st.button("处理所有文件并生成合并结果", use_container_width=True, type="primary"):
            if not st.session_state.uploaded_files:
                st.warning("请先导入文件")
            else:
                try:
                    # 清空之前的合并结果
                    st.session_state.merged_dfs = {}

                    # 处理每个文件
                    for file in st.session_state.uploaded_files:
                        with st.spinner(f"正在处理文件: {file.name}..."):
                            try:
                                excel_file = pd.ExcelFile(file)
                                sheet_names = excel_file.sheet_names

                                # 检查子表数量
                                if len(sheet_names) != 5:
                                    st.warning(f"文件【{file.name}】的子表数量应为5张，当前为{len(sheet_names)}张")

                                # 合并当前文件的所有子表
                                merged_df = None
                                for sheet in sheet_names:
                                    df = pd.read_excel(excel_file, sheet_name=sheet).iloc[:, :2]
                                    if df.shape[1] < 2:
                                        st.error(f"文件【{file.name}】的子表【{sheet}】格式错误，至少需要2列数据")
                                        break
                                    df.columns = ["时间", sheet]

                                    # 按照时间列排序
                                    df = df.sort_values("时间").reset_index(drop=True)

                                    if merged_df is None:
                                        merged_df = df
                                    else:
                                        merged_df = pd.merge(merged_df, df, on="时间", how="outer")

                                if merged_df is not None:
                                    # 最终按时间排序
                                    merged_df = merged_df.sort_values("时间").reset_index(drop=True)
                                    # 保存到session_state
                                    st.session_state.merged_dfs[file.name] = merged_df
                                    st.success(f"文件 {file.name} 处理完成")

                            except Exception as e:
                                st.error(f"处理文件 {file.name} 时出错：{str(e)}")

                    # 显示处理完成信息
                    if st.session_state.merged_dfs:
                        st.success(f"所有文件处理完成！共成功处理 {len(st.session_state.merged_dfs)} 个文件")

                except Exception as e:
                    st.error(f"处理失败：{str(e)}")

    with col2:
        if st.button("清空所有文件", use_container_width=True, type="secondary"):
            st.session_state.uploaded_files = []
            st.session_state.merged_dfs = {}
            st.success("已清空所有文件，可重新上传")
            st.rerun()

    # 显示每个文件的合并结果和下载按钮
    if st.session_state.merged_dfs:
        st.markdown("---")
        st.subheader("合并结果下载")

        for file_name, merged_df in st.session_state.merged_dfs.items():
            with st.expander(f"{file_name} - 合并结果", expanded=False):
                # 显示数据预览
                st.dataframe(merged_df, use_container_width=True)

                # 生成下载文件
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    merged_df.to_excel(writer, index=False, sheet_name="合并数据")
                output.seek(0)

                # 下载按钮
                download_name = f"合并_{os.path.splitext(file_name)[0]}.xlsx"
                st.download_button(
                    label=f"下载 {file_name} 的合并结果",
                    data=output,
                    file_name=download_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{file_name}",
                    use_container_width=True
                )

        # 批量下载所有文件
        st.markdown("---")
        st.subheader("批量下载所有合并结果")

        # 创建ZIP文件包含所有合并结果
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for file_name, merged_df in st.session_state.merged_dfs.items():
                # 为每个文件创建Excel
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                    merged_df.to_excel(writer, index=False, sheet_name="合并数据")
                excel_buffer.seek(0)

                # 添加到ZIP
                zip_file.writestr(f"合并_{file_name}", excel_buffer.getvalue())

        zip_buffer.seek(0)

        st.download_button(
            label="下载所有合并文件的ZIP包",
            data=zip_buffer,
            file_name="所有油田数据合并结果.zip",
            mime="application/zip",
            use_container_width=True
        )


if __name__ == "__main__":
    main()