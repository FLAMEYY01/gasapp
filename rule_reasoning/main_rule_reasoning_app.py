#=================================================================================#
# 基于规则的符号知识建模与推理系统                                                   #
#---------------------------------------------------------------------------------#
# 规则模型的数据结构：                                                              #
# (1) 用嵌套list表示                                                               #
# (2) rules[[规则CF值，结论，前提1，前提2，前提3]，[规则CF，结论，前提1，前提2]，...]  #
# (3) 规则数量任意，且每条规则的前提数量动态可变                                      #
# 函数调用结构：                                                                   #
#=================================================================================#
import streamlit as st
import pandas as pd
import os
import signal
import time

# ===== 模块导入 ===================================================================#
from modules.file_utils import select_ruleset_file
from modules.rule_utils import (
    setup_reasoning_goal,
    show_rules,
    show_static_facts,
    initialize_dynamic_stack,
    get_matched_rule_subset,
    trigger_rule_after_conflict_resolution,
    update_dynamic_stack,
    output_reasoning_results,
    decompose_rule_dataframe,
)
from modules.ui_utils import setup_unique_widget_key, input_initial_user_facts
from modules.help_utils import show_help_images

# ===== 全局常量 ===================================================================#
APP_PORT = os.environ.get("APP_PORT", "未知端口")
APP_TEXT = os.environ.get("APP_TEXT", "规则推理App")


#=======================================================================
# 主程序： Main Program
#=======================================================================
def main():
    """
    主程序入口，构建规则推理WebApp的多Tab操作界面。
    """
    # 页面配置：宽屏
    st.set_page_config(layout="wide")
    container_height = 560

    # 页面顶部标题图
    st.image("./webapps_pool/7_others/rule_reasoning/images/title.jpg")

    # 创建四个主功能页签
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📚 选择规则集", "🔭 正向推理求解ing ...", "🗒️ 用户手册", "👣 退出系统"]
    )

    # ===== 初始化空数据变量 =====
    df = pd.DataFrame()
    rules = []
    static_facts = []
    prompt_space = []
    reasoning_goal = []

    # ========== Tab1：规则集选择 ==========
    with tab1:
        with st.container(border=True, height=container_height):
            df = select_ruleset_file()
            if df is not None:
                # 拆解规则表
                rules, static_facts, prompt_space = decompose_rule_dataframe(df)
                reasoning_goal = setup_reasoning_goal()

                # 显示规则与静态事实
                show_rules(rules)
                show_static_facts(static_facts)

    # ========== Tab2：推理过程 ==========
    with tab2:
        with st.container(border=True, height=container_height):
            if df is not None:
                # 用户输入初始事实
                initial_user_facts = input_initial_user_facts(prompt_space)
                if initial_user_facts:
                    # 初始化动态事实栈
                    dynamic_stack = initialize_dynamic_stack(
                        initial_user_facts, static_facts
                    )
                    triggered_rule_no_subset = []

                    # 正向推理主循环
                    while dynamic_stack[-1] != reasoning_goal[0]:
                        matched_subset = get_matched_rule_subset(
                            len(rules), rules, dynamic_stack, triggered_rule_no_subset
                        )
                        triggered_rule_no = trigger_rule_after_conflict_resolution(
                            matched_subset, strategy=1
                        )
                        dynamic_stack = update_dynamic_stack(
                            triggered_rule_no, rules, dynamic_stack
                        )
                        triggered_rule_no_subset.append(triggered_rule_no[0])
                    else:
                        st.success("✅ 推理完成，显示结果：")
                        output_reasoning_results(
                            dynamic_stack, triggered_rule_no_subset, rules
                        )

    # ========== Tab3：帮助说明 ==========
    with tab3:
        with st.container(border=True, height=container_height):
            show_help_images("./webapps_pool/7_others/rule_reasoning/images/", page_n=5)

    # ========== Tab4：退出控制 ==========
    with tab4:
        with st.container(border=True, height=container_height):
            st.info("点击左侧菜单可重新进入系统")
            st.code("🚪 退出子应用")
            st.warning("⚠️ 确认后将终止该 Streamlit 应用进程。")
            if st.button("🔴 确认退出并关闭服务"):
                pid = os.getpid()
                st.success(
                    f"✅ [{APP_TEXT}] 应用已终止（端口 = {APP_PORT}, PID = {pid}）。请关闭浏览器页面。"
                )
                time.sleep(2)
                os.kill(pid, signal.SIGTERM)


#========================= 主程序函数结束 ！ ==========================================#
if __name__ == '__main__':
  main()
#========================= End ！ ====================================================#
