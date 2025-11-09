import streamlit as st
import pandas as pd
import io
import numpy as np


# 辅助函数：计算斜率（线性拟合）
def calculate_slope(values):
    """计算序列的线性拟合斜率"""
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values))
    slope, _ = np.polyfit(x, values, 1)
    return slope


def main():
    st.set_page_config(page_title="油田数据自动标注", layout="wide")
    st.title("油田数据自动标注工具")
    st.write("请导入包含以下6列数据的Excel文件：\n时间、瞬时流量、油压、回压、套压、温度")

    # 初始化session_state
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'annotated_df' not in st.session_state:
        st.session_state.annotated_df = None
    if 'raw_df' not in st.session_state:
        st.session_state.raw_df = None

    # 文件上传区域
    uploaded_file = st.file_uploader("选择Excel文件", type=["xlsx", "xls"], key="annotate_uploader")

    # 处理文件上传与校验
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        try:
            df = pd.read_excel(uploaded_file)
            required_columns = ["时间", "瞬时流量", "油压", "回压", "套压", "温度"]

            if list(df.columns) != required_columns:
                st.warning(f"文件列名不匹配！需要的列名：\n{required_columns}")
                st.warning(f"当前文件的列名：\n{list(df.columns)}")
                st.session_state.uploaded_file = None
            else:
                # 按时间排序，确保时间逻辑正确
                df = df.sort_values(by="时间").reset_index(drop=True)
                st.success(f"已成功导入文件：{uploaded_file.name}（{len(df)}行数据，列名验证通过，已按时间排序）")
                st.info("数据预览（前5行）：")
                st.dataframe(df.head(), use_container_width=True)
                st.session_state.raw_df = df

        except Exception as e:
            st.error(f"文件解析错误：{str(e)}")
            st.session_state.uploaded_file = None

    # 按钮区域
    col1, col2 = st.columns(2)
    with col1:
        confirm_btn = st.button("确认并进行数据标注", use_container_width=True, type="primary")
    with col2:
        cancel_btn = st.button("取消并重新导入", use_container_width=True, type="secondary")

    # 处理取消按钮
    if cancel_btn:
        st.session_state.uploaded_file = None
        st.session_state.annotated_df = None
        st.session_state.raw_df = None
        st.success("已重置，请重新上传文件")
        st.experimental_rerun()

    # 处理确认按钮（核心逻辑）
    if confirm_btn:
        if st.session_state.raw_df is None:
            st.warning("请先上传符合要求的Excel文件")
        else:
            try:
                df = st.session_state.raw_df.copy()
                # 初始化所有标注列
                df["阶段"] = ""
                df["模式"] = ""
                df["状态"] = ""
                df["积液类型"] = ""  # 新增“积液类型”列

                total_rows = len(df)
                window_size = 144  # 窗口大小144条
                label_count_stage = 12  # 阶段列标注窗口最后12条
                label_count_state = 6  # 状态列标注窗口最后6条
                label_count_liquid = 12  # 积液判断的12条数据窗口

                if total_rows < window_size:
                    st.error(f"数据量不足！需要至少{window_size}条数据，当前只有{total_rows}条")
                    st.stop()

                max_start_idx = total_rows - window_size  # 最后一个完整窗口的起始索引
                for start_idx in range(max_start_idx + 1):
                    # 当前窗口范围：[start_idx, window_end]（144条数据）
                    window_end = start_idx + window_size - 1  # 窗口内最后一条数据索引
                    window_start = start_idx  # 窗口内第一条数据索引

                    # --------------------------
                    # 1. 标注“阶段”列
                    # --------------------------
                    stage_start = window_end - label_count_stage + 1
                    stage_end = window_end
                    sub_data_stage = df.loc[stage_start:stage_end, ["油压", "套压"]]

                    all_pressure_less = (sub_data_stage["油压"] < sub_data_stage["套压"]).all()
                    casing_minus_tubing = sub_data_stage["套压"] - sub_data_stage["油压"]
                    mean_casing_minus = casing_minus_tubing.mean()
                    var_casing_minus = casing_minus_tubing.var()

                    tubing_minus_casing_abs = (sub_data_stage["油压"] - sub_data_stage["套压"]).abs()
                    mean_tubing_minus_abs = tubing_minus_casing_abs.mean()
                    var_tubing_minus_abs = tubing_minus_casing_abs.var()

                    if all_pressure_less and mean_casing_minus > 0.8 and var_casing_minus < 0.5:
                        stage_result = "有节流器"
                    elif mean_tubing_minus_abs < 0.5 or var_tubing_minus_abs > 1:
                        stage_result = "无节流器"
                    else:
                        stage_result = "有节流器"
                    df.loc[stage_start:stage_end, "阶段"] = stage_result

                    # --------------------------
                    # 2. 标注“模式”列
                    # --------------------------
                    sub_data_mode = df.loc[start_idx:window_end, "瞬时流量"]
                    all_flow_gt100 = (sub_data_mode > 100).all()
                    mode_result = "连续生产" if all_flow_gt100 else "间开生产"
                    df.loc[start_idx:window_end, "模式"] = mode_result

                    # --------------------------
                    # --------------------------
                    # 3. 标注“状态”列（修改后逻辑）
                    # --------------------------
                    label_count_state = 6  # 状态列标注窗口最后6条（保持不变）
                    state_start = window_end - label_count_state + 1  # 最后6条数据的起始索引
                    state_end = window_end  # 最后6条数据的结束索引（窗口最后一条）
                    sub_data_state = df.loc[state_start:state_end, ["瞬时流量", "油压", "套压"]]

                    # 步骤1：判断窗口最后2条数据的瞬时流量是否均>100
                    last_two_indices = [window_end - 1, window_end]  # 最后2条数据的索引
                    # 确保索引在有效范围内（避免窗口过小时越界，实际因总数据量≥144，此处不会越界）
                    if all(idx >= state_start for idx in last_two_indices):
                        last_two_flow = df.loc[last_two_indices, "瞬时流量"]
                        all_last_two_gt100 = (last_two_flow > 100).all()  # 最后2条是否均>100
                    else:
                        all_last_two_gt100 = False

                    if all_last_two_gt100:
                        # 规则1：最后2条数据状态标注为“开井”
                        df.loc[last_two_indices, "状态"] = "开井"
                    else:
                        # 步骤2：判断最后连续6条数据是否均≤100，且油压、套压斜率均≤0
                        all_flow_le100 = (sub_data_state["瞬时流量"] <= 100).all()  # 最后6条是否均≤100
                        if all_flow_le100:
                            # 计算最后6条数据的油压斜率和套压斜率
                            slope_oil = calculate_slope(sub_data_state["油压"].values)
                            slope_casing = calculate_slope(sub_data_state["套压"].values)
                            if slope_oil <= 0 and slope_casing <= 0:
                                # 规则2：最后6条数据状态标注为“开井”
                                df.loc[state_start:state_end, "状态"] = "开井"
                            else:
                                # 规则3：不满足斜率条件，最后6条标注为“关井”
                                df.loc[state_start:state_end, "状态"] = "关井"
                        else:
                            # 规则3：最后6条数据不全≤100，标注为“关井”
                            df.loc[state_start:state_end, "状态"] = "关井"
                    # --------------------------
                    # 4. 标注“积液类型”列（优化后逻辑）
                    # --------------------------
                    window_stage = df.loc[start_idx:window_end, "阶段"]  # 当前窗口所有阶段
                    window_mode = df.loc[start_idx:window_end, "模式"]  # 当前窗口所有模式

                    # --------------------------
                    # 前提A：连续144条数据“阶段” = “有节流器”
                    # 顺序：无积液→轻度→中度→重度（同一类型内if-elif，后续覆盖前面）
                    # --------------------------
                    all_stage_has = (window_stage == "有节流器").all()
                    if all_stage_has:
                        # 无积液规则（同一类型内if-elif）
                        liquid_start = window_end - label_count_liquid + 1
                        liquid_end = window_end
                        target_indices_rule1 = range(liquid_start, liquid_end + 1)
                        sub_data_liquid = df.loc[target_indices_rule1, ["状态", "油压", "套压", "瞬时流量"]]
                        all_state_open_12 = (sub_data_liquid["状态"] == "开井").all()
                        mean_oil_12 = sub_data_liquid["油压"].mean() if not sub_data_liquid.empty else 0
                        mean_casing_12 = sub_data_liquid["套压"].mean() if not sub_data_liquid.empty else 0
                        var_flow_12 = sub_data_liquid["瞬时流量"].var() if len(sub_data_liquid) > 1 else 0

                        # 规则1：窗口最后12条开井+压力稳定+流量波动小
                        if all_state_open_12 and mean_oil_12 >= 20 and mean_casing_12 >= 20 and var_flow_12 < 3:
                            df.loc[target_indices_rule1, "积液类型"] = "无积液"
                        # 规则2：窗口末尾+后续2条的开井→关井压力恢复特征（elif互斥）
                        elif (window_end + 2) < total_rows:
                            last_in_window = window_end
                            next1 = last_in_window + 1
                            next2 = last_in_window + 2
                            target_indices_rule2 = [last_in_window, next1, next2]
                            cond1 = (df.loc[last_in_window, "状态"] == "开井")
                            cond2 = (df.loc[last_in_window, "套压"] >= 20)
                            cond3 = (df.loc[last_in_window, "油压"] < 5)
                            cond4 = (df.loc[next1, "状态"] == "关井")
                            # 核心修改：将“油压≥20”改为“油压≥套压”
                            cond5 = (df.loc[next2, "状态"] == "关井") and (
                                        df.loc[next2, "油压"] >= df.loc[next2, "套压"])
                            if cond1 and cond2 and cond3 and cond4 and cond5:
                                df.loc[target_indices_rule2, "积液类型"] = "无积液"

                        # 轻度积液规则（同一类型内if-elif，直接覆盖无积液）
                        # 规则3：全窗口开井+套压18-19+油压<3+流量下降
                        all_state_open_144 = (df.loc[start_idx:window_end, "状态"] == "开井").all()
                        casing_cond_144 = (df.loc[start_idx:window_end, "套压"] > 18) & (df.loc[start_idx:window_end, "套压"] < 19)
                        all_casing_144 = casing_cond_144.all()
                        all_oil_144 = (df.loc[start_idx:window_end, "油压"] < 3).all()
                        flow_slope_144 = calculate_slope(df.loc[start_idx:window_end, "瞬时流量"].values)
                        target_indices_rule3 = range(start_idx, window_end + 1)

                        if all_state_open_144 and all_casing_144 and all_oil_144 and (flow_slope_144 < 0):
                            df.loc[target_indices_rule3, "积液类型"] = "轻度积液"
                        # 规则4：窗口末尾+后续5条的开井→关井特征（elif互斥）
                        elif (window_end + 5) < total_rows:
                            idx_144_light = window_end
                            idx_149_light = idx_144_light + 5
                            target_indices_rule4 = range(idx_144_light, idx_149_light + 1)
                            cond_144 = (df.loc[idx_144_light, "状态"] == "开井") & (18 < df.loc[idx_144_light, "套压"] < 19) & (df.loc[idx_144_light, "油压"] < 3)
                            cond_145 = (df.loc[idx_144_light + 1, "状态"] == "关井")
                            cond_146 = (df.loc[idx_144_light + 2, "状态"] == "关井") & (df.loc[idx_144_light + 2, "油压"] < 10)
                            cond_149 = (df.loc[idx_149_light, "状态"] == "关井") & (df.loc[idx_149_light, "油压"] > df.loc[idx_149_light, "套压"])
                            if cond_144 and cond_145 and cond_146 and cond_149:
                                df.loc[target_indices_rule4, "积液类型"] = "轻度积液"

                        # 中度积液规则（直接覆盖无积液/轻度，1条规则）
                        if (window_end + 120) < total_rows:
                            idx_144_mid = window_end
                            idx_264_mid = idx_144_mid + 120
                            target_indices_mid = range(idx_144_mid, idx_264_mid + 1)
                            cond_mid1 = (df.loc[idx_144_mid, "状态"] == "开井")
                            cond_mid2 = (10 < df.loc[idx_144_mid, "套压"] < 12)
                            cond_mid3 = (df.loc[idx_144_mid, "油压"] < 3)
                            cond_mid4 = (df.loc[idx_144_mid + 1:idx_264_mid, "状态"] == "关井").all()
                            delta_p = df.loc[idx_264_mid, "套压"] - df.loc[idx_144_mid, "油压"]
                            cond_mid5 = (df.loc[idx_144_mid + 48, "油压"] < 0.5 * delta_p)
                            cond_mid6 = (2/3 * delta_p < df.loc[idx_264_mid, "油压"] < 0.8 * delta_p)
                            if cond_mid1 and cond_mid2 and cond_mid3 and cond_mid4 and cond_mid5 and cond_mid6:
                                df.loc[target_indices_mid, "积液类型"] = "中度积液"

                        # 重度积液规则（同一类型内if-elif-elif，覆盖所有前面类型）
                        flow_values = df.loc[start_idx:window_end, "瞬时流量"].values
                        temp_values = df.loc[start_idx:window_end, "温度"].values
                        flow_slope = calculate_slope(flow_values)
                        temp_slope = calculate_slope(temp_values)
                        oil_p_diff = df.loc[window_start, "油压"] - df.loc[window_end, "油压"]
                        casing_minus_oil = df.loc[start_idx:window_end, "套压"] - df.loc[start_idx:window_end, "油压"]
                        target_indices_severe = range(start_idx, window_end + 1)

                        # 规则6
                        if (flow_slope < 0) & (temp_slope < 0) & (casing_minus_oil > 5).all():
                            df.loc[target_indices_severe, "积液类型"] = "重度积液"
                        # 规则7
                        elif (flow_slope < 0) & (temp_slope < 0) & (oil_p_diff > 2):
                            df.loc[target_indices_severe, "积液类型"] = "重度积液"
                        # 规则8
                        elif (flow_slope < 0) & (oil_p_diff > 1) & (casing_minus_oil > 3.5).all():
                            df.loc[target_indices_severe, "积液类型"] = "重度积液"

                    # --------------------------
                    # 前提B：连续144条“阶段=无节流器”且非间开生产
                    # 顺序：轻度→中度→重度（同一类型内if-elif，后续覆盖前面）
                    # --------------------------
                    all_stage_none = (window_stage == "无节流器").all()
                    all_mode_continuous = (window_mode == "连续生产").all()
                    if all_stage_none and all_mode_continuous and not all_stage_has:
                        # 轻度积液规则（同一类型内if-elif）
                        target_indices_light = range(start_idx, window_end + 1)
                        all_state_open_light = (df.loc[target_indices_light, "状态"] == "开井").all()
                        casing_minus_oil_light = df.loc[target_indices_light, "套压"] - df.loc[target_indices_light, "油压"]
                        casing_oil_cond_light = (casing_minus_oil_light > 0) & (casing_minus_oil_light < 1)
                        all_casing_oil_light = casing_oil_cond_light.all()
                        casing_values_light = df.loc[target_indices_light, "套压"].values
                        casing_fluct_light = casing_values_light.max() - casing_values_light.min() if len(casing_values_light) > 1 else 0

                        # 规则1：全窗口开井+套压-油压0-1+套压波动<0.2
                        if all_state_open_light and all_casing_oil_light and (casing_fluct_light < 0.2):
                            df.loc[target_indices_light, "积液类型"] = "轻度积液"
                        # 规则2：窗口末尾+后续12条的开井→关井特征（elif互斥）
                        elif (window_end + 12) < total_rows:
                            idx_144_light = window_end
                            idx_156_light = idx_144_light + 12
                            target_indices_rule2 = range(idx_144_light, idx_156_light + 1)
                            cond1_light = (df.loc[idx_144_light, "状态"] == "开井")
                            cond2_light = (df.loc[idx_144_light + 1:idx_156_light, "状态"] == "关井").all()
                            delta_p_light = df.loc[idx_156_light, "套压"] - df.loc[idx_144_light, "油压"]
                            cond3_light = (df.loc[idx_144_light + 6, "油压"] < 0.5 * delta_p_light)
                            cond4_light = (0.75 * delta_p_light < df.loc[idx_156_light, "油压"] < 0.8 * delta_p_light)
                            if cond1_light and cond2_light and cond3_light and cond4_light:
                                df.loc[target_indices_rule2, "积液类型"] = "轻度积液"

                        # 中度积液规则
                        target_indices_mid = range(start_idx, window_end + 1)
                        all_state_open_mid = (df.loc[target_indices_mid, "状态"] == "开井").all()
                        casing_minus_oil_mid = df.loc[target_indices_mid, "套压"] - df.loc[target_indices_mid, "油压"]
                        casing_oil_cond_mid = (casing_minus_oil_mid > 0.5) & (casing_minus_oil_mid < 2)
                        all_casing_oil_mid = casing_oil_cond_mid.all()


                        # 规则4：窗口末尾+后续12条的开井→关井特征（elif互斥）
                        if (window_end + 12) < total_rows:
                            idx_144_mid = window_end
                            idx_156_mid = idx_144_mid + 12
                            target_indices_rule4 = range(idx_144_mid, idx_156_mid + 1)
                            cond1_mid = (df.loc[idx_144_mid, "状态"] == "开井")
                            cond2_mid = (df.loc[idx_144_mid + 1:idx_156_mid, "状态"] == "关井").all()
                            delta_p_mid = df.loc[idx_156_mid, "套压"] - df.loc[idx_144_mid, "油压"]
                            cond3_mid = (df.loc[idx_144_mid + 6, "油压"] < (1 / 3) * delta_p_mid)
                            cond4_mid = (0.5 * delta_p_mid < df.loc[idx_156_mid, "油压"] < 0.75 * delta_p_mid)
                            if cond1_mid and cond2_mid and cond3_mid and cond4_mid:
                                df.loc[target_indices_rule4, "积液类型"] = "中度积液"

                        # 重度积液规则（同一类型内if-elif-elif，覆盖前面）
                        target_indices_severe = range(start_idx, window_end + 1)
                        if (df.loc[target_indices_severe, "状态"] == "开井").all():
                            casing_minus_oil_severe = df.loc[target_indices_severe, "套压"] - df.loc[target_indices_severe, "油压"]

                            # 规则5
                            if (casing_minus_oil_severe > 2).all():
                                df.loc[target_indices_severe, "积液类型"] = "重度积液"
                            # 规则6
                            elif not (df.loc[target_indices_severe, "积液类型"] == "重度积液").any():
                                casing_slope = calculate_slope(df.loc[target_indices_severe, "套压"].values)
                                oil_slope = calculate_slope(df.loc[target_indices_severe, "油压"].values)
                                if (casing_slope > 0) & (oil_slope < 0):
                                    df.loc[target_indices_severe, "积液类型"] = "重度积液"
                            # 规则7
                            elif not (df.loc[target_indices_severe, "积液类型"] == "重度积液").any():
                                flow_below_100 = (df.loc[target_indices_severe, "瞬时流量"] < 100).sum()
                                if flow_below_100 > 2:
                                    df.loc[target_indices_severe, "积液类型"] = "重度积液"

                    # --------------------------
                    # --------------------------
                    # 前提C：无节流器+间开生产（逻辑重写）
                    # --------------------------
                    all_mode_intermittent = (window_mode == "间开生产").all()
                    all_stage_none_and_intermittent = all_stage_none and all_mode_intermittent
                    if all_stage_none_and_intermittent and not all_stage_has and not (
                            all_stage_none and all_mode_continuous):
                        # 第一步：处理开井数据（集合A）的积液类型
                        # 1. 提取窗口内所有开井数据索引（集合A）
                        open_well_indices = df.loc[start_idx:window_end].query("状态 == '开井'").index.tolist()
                        if open_well_indices:  # 仅当集合A非空时执行
                            # 2. 计算套压均值和波动幅度
                            casing_values = df.loc[open_well_indices, "套压"]
                            mean_casing = casing_values.mean()
                            casing_fluct = casing_values.max() - casing_values.min()

                            # 3. 按规则判断并标注
                            if mean_casing < 4.5:
                                df.loc[open_well_indices, "积液类型"] = "轻度积液"
                            else:
                                if casing_fluct < 0.5:
                                    df.loc[open_well_indices, "积液类型"] = "轻度积液"
                                elif 0.5 <= casing_fluct < 2:
                                    df.loc[open_well_indices, "积液类型"] = "中度积液"
                                else:  # 波动幅度 ≥2
                                    df.loc[open_well_indices, "积液类型"] = "重度积液"

                        # 第二步：处理“关井+后续7条开井”的重度积液判断（覆盖第一步结果）
                        # 遍历窗口内可判断的起始索引（避免后续7条越界）
                        max_check_idx = window_end - 7  # 最后一个可判断的关井索引
                        if max_check_idx >= start_idx:
                            for i in range(start_idx, max_check_idx + 1):
                                # 待判断的8条数据索引：i（关井） + i+1到i+7（7条开井）
                                check_indices = list(range(i, i + 8))
                                # 验证所有索引在窗口内（避免跨窗口越界）
                                if any(idx > window_end for idx in check_indices):
                                    continue
                                # 提取8条数据的状态和最后1条的流量
                                states = df.loc[check_indices, "状态"].values
                                last_flow = df.loc[check_indices[-1], "瞬时流量"]
                                # 判断条件：第1条关井 + 中间7条开井 + 最后1条流量<150
                                if (states[0] == "关井") and \
                                        (all(state == "开井" for state in states[1:])) and \
                                        (last_flow < 150):
                                    df.loc[check_indices, "积液类型"] = "重度积液"

                # 未标注数据向前填充
                def forward_fill_liquid_type(df):
                    """按时间线往前倒推寻找第一个已确认的积液类型"""
                    liquid_type_col = df["积液类型"].copy()

                    for i in range(len(df)):
                        # 如果当前点未被标注（空值或空字符串）
                        if pd.isna(liquid_type_col.iloc[i]) or liquid_type_col.iloc[i] == "":
                            # 往前倒推寻找第一个已确认的点
                            found_type = None
                            for j in range(i - 1, -1, -1):  # 从i-1开始往前找
                                if not pd.isna(liquid_type_col.iloc[j]) and liquid_type_col.iloc[j] != "":
                                    found_type = liquid_type_col.iloc[j]
                                    break

                            # 如果找到了已确认的类型，则赋值给当前点
                            if found_type is not None:
                                liquid_type_col.iloc[i] = found_type

                    return liquid_type_col

                # 应用填充逻辑
                df["积液类型"] = forward_fill_liquid_type(df)

                # 边界提示
                st.info(
                    f"注意：前{max_start_idx}条数据因未形成完整144点窗口可能初始未标注，已通过向前填充规则处理未标注数据")

                # 展示标注结果
                st.dataframe(df[["时间", "瞬时流量", "模式", "油压", "套压", "温度", "阶段", "状态", "积液类型"]],
                             use_container_width=True)

                with st.expander("点击查看全部10列数据"):
                    st.dataframe(df, use_container_width=True)

                # 下载功能
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="标注后数据")
                output.seek(0)
                st.download_button(
                    label="下载标注后的Excel文件",
                    data=output,
                    file_name="标注后的油田数据.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"标注过程出错：{str(e)}")


if __name__ == "__main__":
    main()