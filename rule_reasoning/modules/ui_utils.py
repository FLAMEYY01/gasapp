import streamlit as st

# 全局控件唯一编号计数器
widget_counter = 0


def setup_unique_widget_key():
    """
    生成一个唯一控件key，用于避免Streamlit多控件冲突。
    """
    global widget_counter
    key = f"w{widget_counter}"
    widget_counter += 1
    return key


def input_initial_user_facts(prompt_space):
    """
    用户通过多选框选择规则推理的初始事实。

    参数:
        prompt_space (List[str]): 可选事实提示空间

    返回:
        List[str]: 用户选择的初始事实
    """
    key1 = setup_unique_widget_key()
    selected_facts = st.multiselect(
        "从以下多选框中选择用于规则推理的初始用户事实:", prompt_space, key=key1
    )

    key2 = setup_unique_widget_key()
    if st.button("确定", key=key2):
        st.write("✅ 已选定的用户初始事实:")
        st.write(selected_facts)
        return selected_facts
    return []
