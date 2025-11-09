import streamlit as st
import pandas as pd


def setup_reasoning_goal():
    """
    设置推理终止的目标结论标志。
    """
    return ["<推理目标 has-been 达成>"]


def show_rules(rules_list):
    """
    将规则集以表格形式输出展示。

    参数:
        rules_list (List[List[str]]): 规则集嵌套列表，每条规则格式：[CF, Conclusion, Premise1, Premise2, ...]
    """
    rule_n = len(rules_list)
    premises = [[] for _ in range(rule_n)]
    conclusion = ["" for _ in range(rule_n)]
    cf_value = ["" for _ in range(rule_n)]

    for i in range(rule_n):
        for j in range(2, len(rules_list[i])):
            premises[i].append(str(rules_list[i][j]))
        conclusion[i] = "THEN: " + str(rules_list[i][1])
        cf_value[i] = str(rules_list[i][0])

    combined_premises = ["IF: " + " .&. ".join(p) for p in premises]
    table = pd.DataFrame(
        {"前提": combined_premises, "结论": conclusion, "CF值": cf_value}
    )
    st.write("📘 当前规则集:")
    st.write(table)


def show_static_facts(static_facts):
    """
    显示静态事实表。

    参数:
        static_facts (List[str]): 静态事实列表
    """
    table = pd.DataFrame(
        {"静态事实": static_facts, "CF值": ["1.0"] * len(static_facts)}
    )
    st.write("📗 静态事实集:")
    st.write(table)


def initialize_dynamic_stack(initial_user_facts, static_facts):
    """
    构建动态事实栈：由初始事实 + 静态事实组成。

    参数:
        initial_user_facts (List[str]): 用户输入的初始事实
        static_facts (List[str]): 规则集中定义的静态事实

    返回:
        List[str]: 动态事实栈
    """
    return initial_user_facts + static_facts


def get_matched_rule_subset(rule_n, rules_list, dynamic_stack, triggered_rule_ids):
    """
    在规则集中查找所有尚未触发且前提全匹配的规则编号。

    返回:
        List[str]: 匹配成功的规则编号集合
    """
    matched = []
    for i in range(rule_n):
        if str(i) in triggered_rule_ids:
            continue
        premises = rules_list[i][2:]
        if all(p in dynamic_stack for p in premises):
            matched.append(str(i))
    return matched


def trigger_rule_after_conflict_resolution(matched_subset, strategy):
    """
    根据冲突消解策略决定激活哪条规则。
    当前支持策略1：优先激活第一个匹配规则。

    返回:
        List[str]: 当前被触发规则编号
    """
    if not matched_subset:
        st.error("📢 TIPS: 当前规则推理失败，系统退出。")
        st.stop()
    return [matched_subset[0]]


def update_dynamic_stack(triggered_rule_no, rules_list, dynamic_stack):
    """
    将当前被触发规则的结论添加至动态事实栈。

    参数:
        triggered_rule_no (List[str]): 被触发的规则编号
        rules_list (List[List[str]]): 所有规则
        dynamic_stack (List[str]): 当前动态事实栈

    返回:
        List[str]: 更新后的动态事实栈
    """
    rule_idx = int(triggered_rule_no[0])
    conclusion = rules_list[rule_idx][1]
    dynamic_stack.append(conclusion)
    return dynamic_stack


def output_reasoning_results(dynamic_stack, triggered_rule_ids, rules_list):
    """
    显示推理结论和路径。

    参数:
        dynamic_stack (List[str]): 推理中所有事实
        triggered_rule_ids (List[str]): 所有触发规则编号
        rules_list (List[List[str]]): 所有规则
    """
    if len(dynamic_stack) >= 2:
        st.success("🎯 推理最终结论为:")
        st.write(dynamic_stack[-2])

    st.info("🧭 推理路径（激活规则编号）:")
    for i, rule_no in enumerate(triggered_rule_ids):
        st.write(f"第 {i+1} 条激活规则编号: {rule_no}")
        show_rules([rules_list[int(rule_no)]])


def decompose_rule_dataframe(df):
    """
    将规则集Excel表拆分为规则集、静态事实、可输入初始事实提示集。

    参数:
        df (pd.DataFrame): Excel读取后的DataFrame

    返回:
        Tuple: (rules_list, static_facts, prompt_space)
    """
    rule_strings = df["Rule"].dropna().tolist()
    rules_list = [r.split(", ") for r in rule_strings]

    static_facts = df["Static_Fact"].dropna().tolist()
    prompt_space = df["Potential_Input_Fact"].dropna().tolist()
    prompt_space = [p for p in prompt_space if p != "<>"]
    return rules_list, static_facts, prompt_space
