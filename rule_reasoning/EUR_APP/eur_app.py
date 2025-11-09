import streamlit as st
import pandas as pd
import time
import altair as alt
import os, sys, base64, requests
import streamlit as st
from io import BytesIO
from picture_plot import create_gas_production_plot
from utils import GasPVT
from Blasingame import Blasingame
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def Get_Base64_of_Bin_File(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

#___________________________________需要替换为贝叶斯网络模型______________________________________________________________________
# 定义权重计算函数（可根据实际需求修改逻辑）
def Calculate_bayesian_weights(input_text):
    """
    计算权重的示例函数
    逻辑：基于输入文本长度和字符特征生成权重
    """
    text_length = len(input_text.strip())
    # a权重：文本长度的归一化值（除以100，范围0-~）
    weight_a = round(text_length / 100, 4)
    # b权重：中文汉字占比（假设中文汉字ASCII码大于127）
    chinese_chars = sum(1 for c in input_text if ord(c) > 127)
    weight_b = round(chinese_chars / text_length if text_length > 0 else 0, 4)
    return {"Fetkovich": 0, "Blasingame": 1, "NPI":0}


#_______________________________定义计算方法_________________________________________________________________________________________


def Fetkovich(parameter,data):
    Fetkovich_data=11
    Fetkovich_EUR=1000000000
    return Fetkovich_data,Fetkovich_EUR
def NPI(parameter,data):
    NPI_data=11
    NPI_EUR=1000000000000
    return NPI_data,NPI_EUR

def Calculate_EUR_data(parameter,data):
    Blasingame_data, Blasingame_EUR=Blasingame(parameter,data)
    Fetkovich_data, Fetkovich_EUR=Fetkovich(parameter,data)
    NPI_data, NPI_EUR=NPI(parameter,data)
    caculated_EUR={
        "Blasingame_EUR": Blasingame_EUR,
        "Fetkovich_EUR": Fetkovich_EUR,
        "NPI_EUR": NPI_EUR,
    }
    return caculated_EUR,Blasingame_data,Fetkovich_data,NPI_data

def Calculate_comprehensive_EUR(weight,calculated_EUR):
    comprehensive_EUR = calculated_EUR["Blasingame_EUR"] * weight["Blasingame"] + calculated_EUR["Fetkovich_EUR"]*weight["Fetkovich"] + calculated_EUR["NPI_EUR"]*weight["NPI"]
    return comprehensive_EUR



# def hide_uploader():
#     """文件上传后隐藏上传组件的回调函数"""
#     st.session_state["uploaded"] = True


def parse_parameter_excel(excel_file):
    """
    解析上传的Excel/CSV文件，转换为字典格式

    参数:
        excel_file: streamlit上传的文件对象（st.file_uploader返回值）

    返回:
        dict: 以表头为key，对应数据为value的字典
    """
    if excel_file is None:
        return None

    # 获取文件扩展名
    file_ext = excel_file.name.split(".")[-1].lower()

    try:
        # 读取CSV文件
        if file_ext == "csv":
            # 读取前两行（表头+数据），编码自动识别
            df = pd.read_csv(
                excel_file,
                header=0,  # 第0行为表头
                nrows=1,  # 只读取1行数据（第1行）
                encoding_errors="ignore"  # 忽略编码错误
            )


        # 读取Excel文件（xlsx/xls）
        elif file_ext in ["xlsx", "xls"]:
            # 读取第一个sheet的前两行
            df = pd.read_excel(
                excel_file,
                header=0,  # 第0行为表头
                nrows=1,  # 只读取1行数据
                engine="openpyxl" if file_ext == "xlsx" else "xlrd"
            )

        else:
            st.error("不支持的文件格式！请选择CSV/Excel文件")
            return None
        # 提取Excel的实际表头keys
        parameter_keys = df.columns.tolist()
        st.session_state["parameter_keys"] = parameter_keys

        # 转换为字典（处理可能的NaN值）
        result_dict = df.iloc[0].to_dict()

        # 替换NaN为None（更符合Python习惯）
        result_dict = {
            key: value if pd.notna(value) else None
            for key, value in result_dict.items()
        }

        return result_dict

    except Exception as e:
        st.error(f"文件解析失败：{str(e)}")
        return None


def parse_data_excel(excel_file):
    """
    解析上传的Excel/CSV文件，转换为字典格式

    参数:
        excel_file: streamlit上传的文件对象（st.file_uploader返回值）

    返回:
        dict: 以表头为key，对应数据为value的字典
        外加data数据df
    """
    if excel_file is None:
        return None

    # 获取文件扩展名
    file_ext = excel_file.name.split(".")[-1].lower()

    try:
        # 读取CSV文件
        if file_ext == "csv":
            # 读取前两行（表头+数据），编码自动识别
            data_df = pd.read_csv(
                excel_file,
                header=0,  # 第0行为表头
                # nrows=1,  # 只读取1行数据（第1行）
                encoding_errors="ignore"  # 忽略编码错误
            )


        # 读取Excel文件（xlsx/xls）
        elif file_ext in ["xlsx", "xls"]:
            # 读取第一个sheet的前两行
            data_df = pd.read_excel(
                excel_file,
                header=0,  # 第0行为表头
                # nrows=1,  # 只读取1行数据
                engine="openpyxl" if file_ext == "xlsx" else "xlrd"
            )

        else:
            st.error("不支持的文件格式！请选择CSV/Excel文件")
            return None
        # 提取Excel的实际表头keys
        data_keys = data_df.columns.tolist()
        st.session_state["data_keys"] = data_keys

        # # 转换为字典（处理可能的NaN值）
        # result_dict = df.iloc[0].to_dict()
        #
        # # 替换NaN为None（更符合Python习惯）
        # data_df = {
        #     key: value if pd.notna(value) else None
        #     for key, value in result_dict.items()
        # }

        return data_df

    except Exception as e:
        st.error(f"文件解析失败：{str(e)}")
        return None



# TARGET_PARAMETER_KEYS = ["一", "二", "三"]  # 可根据实际需求修改

# TARGET_DATA_KEYS = ["井名","时间","瞬时产量","井底流压"]  # 可根据实际需求修改

TARGET_PARAMETER_KEYS = ["μgi" ,"Zi","pi","Cti","G","K","Φ","Ti","h",]  # 数据流
TARGET_DATA_KEYS = ["Gas","Date","Qg","Qw","Pwf","Gp"]  # 可根据实际需求修改

TARGET_METHOD_KEYS= ["Fetkovich", "Blasingame", "NPI"]
TARGET_EUR_KEYS= ["Fetkovich_EUR", "Blasingame_EUR", "NPI_EUR"]

if "uploaded" not in st.session_state:
        st.session_state["uploaded"] = False
# 初始化session_state（存储上传状态、文件、解析结果）
if "show_parameter_uploader" not in st.session_state:
    st.session_state["show_parameter_uploader"] = False  # 是否显示上传器
if "uploaded_parameter_file" not in st.session_state:
    st.session_state["uploaded_parameter_file"] = None   # 存储上传的文件对象
if "parameter_dict" not in st.session_state:
    st.session_state["parameter_dict"] = None      # 存储解析后的字典
if "parameter_keys" not in st.session_state:
    st.session_state["parameter_keys"] = []  # 存储上传Excel的实际表头

if "show_data_uploader" not in st.session_state:
    st.session_state["show_data_uploader"] = False  # 是否显示上传器
if "uploaded_data_file" not in st.session_state:
    st.session_state["uploaded_data_file"] = None   # 存储上传的文件对象
if "data_df" not in st.session_state:
    st.session_state["data_df"] = None      # 存储解析后的字典
if "data_keys" not in st.session_state:
    st.session_state["data_keys"] = []  # 存储上传Excel的实际表头


# 1. 初始化session_state存储专家描述（确保和之前的session_state初始化不冲突）
if "expert_description" not in st.session_state:
    st.session_state["expert_description"] = ""

# 存计算的权重
if "bayesian_weight" not in st.session_state:
    st.session_state["bayesian_weight"] = None

# 存计算的EUR
if "calculated_EUR" not in st.session_state:
    st.session_state["calculated_EUR"]=None
# 存综合EUR
if "comprehensive_EUR" not in st.session_state:
    st.session_state["comprehensive_EUR"]=None

# 存方法计算出的结果
if "Blasingame_data" not in st.session_state:
    st.session_state["Blasingame_data"]=None
if "Fetkovich_data" not in st.session_state:
    st.session_state["Fetkovich_data"]=None
if "NPI_data" not in st.session_state:
    st.session_state["NPI_data"]=None







# 虚拟主函数main():
# ====================================================================================
my_login_user="111"
# my_login_user[0]
def main():
    st.set_page_config(layout="wide")
    img_base64 = Get_Base64_of_Bin_File("./images/EUR_predict.png")

    st.markdown(
        f"""
         <div style="
             display: flex; 
             align-items: center; 
             background: linear-gradient(135deg, #f5e6d3 0%, #e8d5c4 100%);
             border-radius: 12px;
             padding: 5px 15px;
             box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
             height: 160px;
         ">
             <div style="flex: 0 0 auto; display: flex; align-items: center; height: 100%;">
                 <img src="data:image/jpeg;base64,{img_base64}" style="
                     height: 150px; 
                     width: auto; 
                     border-radius: 8px; 
                 " />
             </div>
             <div style="
                 flex: 1; 
                 display: flex; 
                 justify-content: center; 
                 align-items: center;
                 margin-left: 20px;
             ">
                 <div style="
                     color: #8B4513;
                     text-align: center;
                     text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.5);
                     line-height: 1.2;
                 ">
                     <div style="font-size: 20px; font-weight: bold; margin-bottom: 5px;">
                         {my_login_user}
                     </div>
                     <div style="font-size: 24px; font-weight: bold;">
                         欢迎您！
                     </div>
                 </div>
             </div>
         </div>
         """,
        unsafe_allow_html=True,
    )

    st.set_page_config(
        page_title="EUR综合预测",
        page_icon="🏠",
        layout="wide"
    )



    big_col1, big_col2 = st.columns([0.2, 0.8])  # 左侧右侧
    with big_col1:

        #————————————————————————————————————上传井参数————————————————————————————————————————————————————————————————————————

        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            if st.button("上传井参数",key="parameter_uphold"):
                # 点击按钮后，设置状态为「显示上传器」
                st.session_state["show_parameter_uploader"] = True
        with col2:
            method = st.selectbox(
                "",  # 清空默认标签
                ["Blasingame", "FetKovich", "NPI"],
                index=0,
                key="method_select",
                label_visibility="collapsed"  # 隐藏标签
            )


        # 显示上传器（仅当show_parameter_uploader为True时）
        if st.session_state["show_parameter_uploader"]:
            uploaded_parameter_file = st.file_uploader(
                "选择文件（支持 CSV/Excel）",
                type=["csv", "xlsx", "xls"],
                key="parameter_uploader",
                label_visibility="visible"  # 显示标签
            )


            # 当用户选择了文件后，进行判断和解析
            if uploaded_parameter_file is not None:
                # 判断是否为Excel文件（xlsx/xls）
                file_ext = uploaded_parameter_file.name.split(".")[-1].lower()
                if file_ext in ["xlsx", "xls"]:
                    # 解析Excel文件为字典
                    st.session_state["parameter_dict"] = parse_parameter_excel(uploaded_parameter_file)
                    st.session_state["uploaded_parameter_file"] = uploaded_parameter_file  # 保存文件对象
                    st.success("Excel文件上传并解析成功！")

                    # 隐藏上传器（设置状态为False）
                    st.session_state["show_parameter_uploader"] = False
                    st.rerun()  # 强制重新运行，立即隐藏上传器
                else:
                    # 非Excel文件，提示错误（不隐藏上传器，允许重新选择）
                    st.error("请选择Excel文件（.xlsx/.xls格式）！")

        # # 页面显示结果（不变）
        # if st.session_state["parameter_dict"] is not None:
        #     with st.container(border=True,height=100):
        #         st.write(st.session_state["parameter_dict"])

        # 带滚动的容器展示参数
        with st.container(border= True, height=100):
            for key in TARGET_PARAMETER_KEYS:
                cols = st.columns([1, 2])
                cols[0].write(f"• {key}")
                if st.session_state["parameter_dict"] is None:
                    cols[1].write(" ")
                else:
                    value = st.session_state["parameter_dict"].get(key, "无")
                    cols[1].write(f"{value}")


        # print(st.session_state["parameter_keys"])
        # 缺失keys提示
        if st.session_state["parameter_keys"]:
            missing_keys = [key for key in TARGET_PARAMETER_KEYS if key not in st.session_state["parameter_keys"]]
            if missing_keys:
                st.write(f"❌ 检测到缺失必要参数：{', '.join(missing_keys)}")



        # __________________________________________上传生产数据________________________________________________________

        if st.button("上传生产数据",key="data_uphold"):
            # 点击按钮后，设置状态为「显示上传器」
            st.session_state["show_data_uploader"] = True

        # 显示上传器（仅当show_data_uploader为True时）
        if st.session_state["show_data_uploader"]:
            uploaded_data_file = st.file_uploader(
                "选择文件（支持 CSV/Excel）",
                type=["csv", "xlsx", "xls"],
                key="data_uploader",
                label_visibility="visible"  # 显示标签
            )


            # 当用户选择了文件后，进行判断和解析
            if uploaded_data_file is not None:
                # 判断是否为Excel文件（xlsx/xls）
                file_ext = uploaded_data_file.name.split(".")[-1].lower()
                if file_ext in ["xlsx", "xls"]:
                    # 解析Excel文件为字典
                    st.session_state["data_df"] = parse_data_excel(uploaded_data_file)  # 这部分出一个data_df，一个data_keys在parse已经存入了
                    st.session_state["uploaded_data_file"] = uploaded_data_file  # 保存文件对象
                    st.success("Excel文件上传并解析成功！")

                    # 隐藏上传器（设置状态为False）
                    st.session_state["show_data_uploader"] = False
                    st.rerun()  # 强制重新运行，立即隐藏上传器
                else:
                    # 非Excel文件，提示错误（不隐藏上传器，允许重新选择）
                    st.error("请选择Excel文件（.xlsx/.xls格式）！")




        # 带滚动的容器展示参数
        with st.container(border=True, height=100):
            if st.session_state["data_df"] is None:
                st.write("未上传生产数据，包括Gas,Date,Qg,Qw,Pwf,Gp")
            else:
                # 缺失keys提示
                if st.session_state["data_keys"]:
                    missing_keys = [key for key in TARGET_DATA_KEYS if key not in st.session_state["data_keys"]]
                    if missing_keys:
                        st.write(f"❌ 检测到缺失必要参数：{', '.join(missing_keys)}")
                    else:
                        st.write("已上传生产数据")






        print(st.session_state["parameter_dict"])
        print(st.session_state["data_df"])

#____________________________________________有俩数据计算EUR__________________________________________________________________


        #这个地方data有得话就计算


        if st.session_state["parameter_dict"] and st.session_state["data_df"] is not None:
            calculated_EUR,Blasingame_data,Fetkovich_data,NPI_data =Calculate_EUR_data(st.session_state["parameter_dict"] , st.session_state["data_df"])
            st.session_state["calculated_EUR"]=calculated_EUR
            st.session_state["Blasingame_data"]=Blasingame_data
            st.session_state["Fetkovich_data"] = Fetkovich_data
            st.session_state["NPI_data"] = NPI_data
        else:
            st.session_state["calculated_EUR"] = None
            st.session_state["Blasingame_data"] = None
            st.session_state["Fetkovich_data"] = None
            st.session_state["NPI_data"] = None


#————————————————————————————————输入专家描述————————————————————————————————————————————————————————————————————

        # 2. 专家描述输入框（带label、默认值、占位提示，自动同步到session_state）
        expert_desc = st.text_area(
            label="请输入专家描述",
            value=st.session_state["expert_description"],  # 保留上次输入值
            placeholder="例如：该井生产稳定，需重点关注压力变化...",
            key="expert_desc_input",  # 唯一key，避免冲突
            height=120  # 输入框高度（可调整）
        )

        # 3. 实时同步输入值到session_state（后续传后端直接取这里的值）
        st.session_state["expert_description"] = expert_desc



        # 4. 添加按钮行（重置 + 计算）
        col1, col2 = st.columns(2)  # 两列布局，按钮并排显示

        with col1:
            # 重置按钮：清空输入框和session_state
            if st.button("重置", type="secondary"):
                st.session_state["expert_description"] = ""
                st.session_state["bayesian_weight"] = None
                st.session_state["comprehensive_EUR"] = None
                # 刷新页面以显示空输入框（streamlit特性，需通过rerun实现）
                st.rerun()

        with col2:
            # 计算按钮：执行权重计算并输出结果
            if st.button("计算", type="primary"):
                # 检查输入是否为空
                if not st.session_state["expert_description"].strip():
                    st.warning("请先输入专家描述再进行计算！")
                else:
                    # 执行计算
                    bayesian_weight = Calculate_bayesian_weights(st.session_state["expert_description"])
                    st.session_state["bayesian_weight"] = bayesian_weight
                    comprehensive_EUR=Calculate_comprehensive_EUR(bayesian_weight,st.session_state["calculated_EUR"])
                    st.session_state["comprehensive_EUR"]=comprehensive_EUR


 # ———————————————————————————————————————————————显示权重—————————————————————————————————————————————————————————————————————————————

        # 带滚动的容器展示参数
        st.write("权重计算")
        with st.container(border= True, height=150):
            for key in TARGET_METHOD_KEYS:
                cols = st.columns([1, 2])
                cols[0].write(f"• {key}")
                if st.session_state["bayesian_weight"] is None:
                    cols[1].write(" ")
                else:
                    # print(st.session_state["bayesian_weight"])
                    value = st.session_state["bayesian_weight"].get(key, "无")
                    cols[1].write(f"{value}")



# ———————————————————————————————————————————————EUR计算—————————————————————————————————————————————————————————————————————————————
        # 带滚动的容器展示参数
        st.write("EUR计算")
        with st.container(border=True, height=250):
            for key in TARGET_EUR_KEYS:
                cols = st.columns([1, 1])
                cols[0].write(f"• {key}")
                if st.session_state["calculated_EUR"] is None:
                    cols[1].write(" ")
                else:
                    # print(st.session_state["calculated_EUR"])
                    value = st.session_state["calculated_EUR"].get(key, "无")
                    cols[1].write(f"{value}")

            # 展示综合EUR
            st.write("_________________________")
            cols = st.columns([1, 1])
            cols[0].write("综合EUR")
            if st.session_state["comprehensive_EUR"] is None:
                cols[1].write(" ")
            else:
                value = st.session_state["comprehensive_EUR"]
                cols[1].write(f"{value}")

# ___________________________________图像区域__________________________________________________
    with big_col2:
        # method = st.selectbox(
        #     "",  # 清空默认标签
        #     ["Blasingame", "FetKovich", "NPI"],
        #     index=0,
        #     key="method_select",
        #     label_visibility="collapsed"  # 隐藏标签
        # )
        if method=="Blasingame":
            if st.session_state["Blasingame_data"] is not None:
                calculated_df=st.session_state["Blasingame_data"]
            else:
                calculated_df=None
        elif method=="FetKovich":
            if st.session_state["FetKovich_data"] is not None:
                calculated_df=st.session_state["FetKovich_data"]
            else:
                calculated_df=None
        elif method=="NPI":
            if st.session_state["NPI_data"] is not None:
                calculated_df=st.session_state["NPI_data"]
            else:
                calculated_df=None

        # 转换Date列为日期格式
        if calculated_df is not None:
            # calculated_df['Date'] = pd.to_datetime(calculated_df['Date'], errors='coerce')
            # 去除日期为空或无效的行
            df = calculated_df.dropna(subset=['tca', '压力规整化产量', '压力规整化产量积分',"压力规整化产量积分导数"])
            # 按日期排序
            df = df.sort_values('tca').reset_index(drop=True)
            fig = create_gas_production_plot(df,method)
            st.pyplot(fig)
        else:
            fig = plt.figure(figsize=(13, 11), facecolor='#3A3A3A')  # 更明显的灰色边框
            # 创建坐标轴，内部为黑色背景
            ax1 = fig.add_axes([0.1, 0.1, 0.8, 0.75], facecolor='black')
            ax2 = ax1.twinx()  # 创建第二个y轴用于累计产量
            # 设置坐标轴样式
            ax1.tick_params(axis='both', colors='white', which='both', labelsize=11)
            ax2.tick_params(axis='y', colors='cyan', which='both', labelsize=11)

            for spine in ax1.spines.values():
                spine.set_color('#E0E0E0')  # 浅灰色边框
                spine.set_linewidth(2)

            for spine in ax2.spines.values():
                spine.set_color('#E0E0E0')  # 浅灰色边框
                spine.set_linewidth(2)

            # 设置标签
            ax1.set_xlabel('Date', color='white', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Normalize Rate, Integral', color='lime', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Beta Derivative', color='cyan', fontsize=14, fontweight='bold')
            st.pyplot(fig)
            pass




# ***********************************************************************************************************
if __name__ == '__main__':
    main()
# ==================== 程序结束！=======================================