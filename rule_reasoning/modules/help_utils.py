import streamlit as st


def show_help_images(image_dir_prefix, page_n):
    """
    循环展示用户手册图像，适用于多页文档。

    参数:
        image_dir_prefix (str): 图像文件路径前缀
        page_n (int): 总页数
    """
    for i in range(page_n):
        image_path = f"{image_dir_prefix}page{i+1}.png"
        st.image(image_path)
