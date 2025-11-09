import base64
import html
import streamlit as st
from PIL import Image
import pandas as pd
import streamlit.components.v1 as components
import subprocess
import time
import signal
import socket
import os, sys

SERVER_IP = os.getenv('SERVER_IP', 'localhost')  # 从环境变量获取服务器IP
# *********************************************************************************************
# 全局变量定义：用于widgets-UI控件的唯一key设置
global mywidgets_key_n
mywidgets_key_n = 0
port_pid_map = {}


# ---------------------------------------------------------------------------------------------
#
def Setup_a_Unique_Widget_Key():
    global mywidgets_key_n
    mywidgets_key = "w" + chr(mywidgets_key_n)
    mywidgets_key_n = mywidgets_key_n + 1
    return mywidgets_key


# - 读取Excel文件 -------------------------------------------------------------------------------
#
def Read_Apps_from_Excel(file_path):
    df = pd.read_excel(file_path)
    return df


# ====== 启动 Streamlit 子应用并记录其 PID/Port/App name ===========================================
#                     link,
#                     port=port,
#                     text=text,
#                     user=my_login_user[0],
#                     role=my_login_user[1],
#                     password=st.session_state.get("password", "")

def start_streamlit_app(app_path, port, text, user=None, password=None):
    env = os.environ.copy()  # 创建当前系统环境变量的一份副本并保存到 env 变量中
    env["APP_PORT"] = str(port)
    env["APP_TEXT"] = text
    env["STREAMLIT_SERVER_HEADLESS"] = (
        "true"  # ✅ 关键，加上这句！streamlit不会自动打开浏览器  无头模式
    )
    if user:
        env["APP_USER"] = user
    if password:
        env["APP_PASSWORD"] = password

    proc = subprocess.Popen(
        ["streamlit", "run", app_path, "--server.port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    port_pid_map[port] = proc.pid
    print(f"🚀 子进程 PID = {proc.pid} 启动成功，监听端口 {port}，名称为 {text}")
    return proc.pid


# ====== 综合启动函数：启动 + 注册监听 ===========================================================
#                     link,
#                     port=port,
#                     text=text,
#                     user=my_login_user[0],
#                     role=my_login_user[1],
#                     password=st.session_state.get("password", "")
def launch_streamlit_with_monitor(
        app_path, port, text, user=None, password=None
):
    pid = start_streamlit_app(app_path, port, text, user, password)
    return pid


# - 加载基于"User_RoleLIST_Password"的excel文件，返回选择的User和Role -----------------------------
#
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.warning("⚠️ 背景图片文件未找到，使用默认背景")
        return ""


def Login_Control():
    # 检查登录状态
    if st.session_state.get("logged_in", False):
        my_login_user = [[] for i in range(1)]
        my_login_user[0] = st.session_state.get("employee_info", {}).get("user", "NIL")
        return my_login_user

    # 应用登录页面样式
    img_base64 = get_base64_image("integrator_config/equipement.jpg")
    logo_base64 = get_base64_image("integrator_config/shiyou.png")

    # 自定义CSS样式
    css_with_background = f"""
    <style>
        /* 设置背景图片 */
        .stApp {{
            background-image: url("data:image/jpeg;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* 企业logo和名称容器 */
        .company-header {{
            position: fixed;
            top: 30px;
            left: 30px;
            z-index: 1000;
            display: flex;
            align-items: center;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 10px 15px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}

        .company-logo {{
            width: 80px;
            height: auto;
            margin-right: 15px;
        }}

        .company-logo img {{
            width: 100%;
            height: auto;
            display: block;
        }}

        .company-name {{
            color: #2E86AB;
            font-size: 18px;
            font-weight: bold;
            margin: 0;
            white-space: nowrap;
        }}

        /* 项目名称样式 - 水平居中 */
        .project-title {{
            position: fixed;
            top: 12%;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background-color: rgba(255, 255, 255, 0.95);
            padding: 10px 10px;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 3px solid #2E86AB;
            max-width: 900px;

        }}

        .project-title h1 {{
            color: #c34a36;
            font-size: 38px;
            font-weight: bold;
            line-height: 1.2;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
            text-align: central;
        }}

        .project-title h2 {{
            color: #1a5f7a;
            font-size: 28px;
            font-weight: normal;
            margin: 0;
            line-height: 1.3;
            text-align: right;
        }}

        /* 隐藏Streamlit默认的header */
        .stApp > header {{
            background-color: transparent !important;
            height: 0px !important;
        }}

        /* 隐藏Streamlit默认的顶部空白 */
        .stApp > div:first-child {{
            padding-top: 0px !important;
        }}

        /* 移除默认的顶部边距 */
        .main > div:first-child {{
            padding-top: 0px !important;
        }}

        /* 隐藏Streamlit默认菜单 */
        #MainMenu {{
            visibility: hidden;
        }}

        /* 隐藏footer */
        footer {{
            visibility: hidden;
        }}

        /* 隐藏header */
        header {{
            visibility: hidden;
        }}

        /* 添加半透明遮罩 - 减轻背景深度 */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.5);
            z-index: -1;
        }}

        /* 重置主容器为全宽 */
        .main .block-container {{
            max-width: 100% !important;
            padding: 2rem !important;
            margin: 0 !important;
        }}

        .success-message {{
            color: #28a745;
            text-align: center;
            padding: 10px;
            border-radius: 5px;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            margin: 10px 0;
        }}

        .error-message {{
            color: #dc3545;
            text-align: center;
            padding: 10px;
            border-radius: 5px;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            margin: 10px 0;
        }}

        .stButton > button {{
            width: 100%;
            background-color: #2E86AB;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px;
            font-size: 16px;
            font-weight: bold;
            margin-top: 20px;
        }}

        .stButton > button:hover {{
            background-color: #1d5f7a;
        }}
    </style>
    """

    st.markdown(css_with_background, unsafe_allow_html=True)

    # 添加企业logo和名称
    if logo_base64:
        st.markdown(f'''
        <div class="company-header">
            <div class="company-logo">
                <img src="data:image/png;base64,{logo_base64}" alt="企业Logo">
            </div>
            <div class="company-name">玉门油田</div>
        </div>
        ''', unsafe_allow_html=True)

    # 添加项目名称
    st.markdown('''
    <div class="project-title">
        <h1>玉门油田气井智能生产管控平台</h1>
    </div>
    ''', unsafe_allow_html=True)

    # 读取Excel配置文件
    users_df = Read_Apps_from_Excel(
        "./integrator_config/User_RoleSTRING_Password_for_Using_MES.xlsx"
    )
    users = users_df.values.tolist()
    users_n = len(users)
    users_list = [users[i][0] for i in range(users_n)]
    password_list = [users[i][1] for i in range(users_n)]

    # 使用CSS固定定位的登录表单
    with st.form("login_form", clear_on_submit=False):
        st.markdown("""
        <style>
        div[data-testid="stForm"] {
            background-color: #ffffff !important;
            padding: 40px !important;
            border-radius: 15px !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
            border: 2px solid #e0e0e0 !important;
            margin: 0 !important;
            min-height: 500px !important;

             /* CSS精确定位 - 水平居中 */
             position: fixed !important;
             top: 36% !important;
             left: 50% !important;
             transform: translateX(-50%) !important;
             width: 450px !important;
            height: auto !important;
            max-height: 70vh !important;
            overflow-y: auto !important;
            z-index: 1000 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("### 请输入您的登录信息")

        # 用户名选择
        my_selected_user = st.selectbox("用户名", users_list, key="login_user")

        # 获取password序列
        located_seq_no = 0
        for i in range(users_n):
            if users[i][0] == my_selected_user:
                located_seq_no = i
                break

        # 密码输入
        my_password = st.text_input("密码", type="password", key="login_password")

        remember_me = st.checkbox("记住我", key="remember_me")
        login_button = st.form_submit_button("登录")

        if login_button:
            if my_password == password_list[located_seq_no]:
                st.session_state.logged_in = True
                st.session_state.employee_info = {
                    "user": my_selected_user,
                }
                st.markdown('<div class="success-message">✅ 登录成功！正在跳转...</div>',
                            unsafe_allow_html=True)
                time.sleep(1)
                st.rerun()
            else:
                st.markdown('<div class="error-message">❌ 密码错误，请重新输入！</div>',
                            unsafe_allow_html=True)

    # 返回默认值
    my_login_user = [[] for i in range(2)]
    my_login_user[0] = "NIL"
    my_login_user[1] = "NIL"
    return my_login_user


# - 将本地图片文件转换为 base64 编码字符串 --------------------------------------------------------
#
def Get_Base64_of_Bin_File(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


# ============================================================================================
# 指定端口范围
def find_available_port(min_port=8502, max_port=8599):
    for port in range(min_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError(
        f"❌ 没有找到可用端口！请检查 {min_port}-{max_port} 区间是否已被占用。"
    )


# --- 显示图标和文字和跳转 "image_path": row.Icon, "link": row.Link, "text": row.Text -----------------------------------------------------------------------
#
def Show_an_Icon_Link(image_link_pairs, my_login_user):
    img = image_link_pairs["image_path"]
    link = image_link_pairs["link"]
    text = image_link_pairs["text"]

    img_base64 = Get_Base64_of_Bin_File(img)
    text_escaped = html.escape(text)
    container_font_size = "12px"
    font_size = "1em"

    # 统一样式：图标 + 应用名 + 启动按钮
    if link.startswith("http://") or link.startswith("https://"):
        # HTTP链接 - 显示图标、名称和启动按钮
        st.markdown(
            f"""
            <div style="text-align: center; font-size: {container_font_size};">
                <img src="data:image/png;base64,{img_base64}" width="50" height="50" title="{text_escaped}" style="display: block; margin: 0 auto;">
                <p style="font-size: {font_size}; margin: 4px 0 8px 0; color: #555; font-weight: 500;">{text}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 启动按钮（点击后打开HTTP链接）
        if st.button("启动", key=f"http_btn_{text}", use_container_width=True):
            components.html(
                f"""
                <script>
                    window.open("{link}", "_blank");
                </script>
                """,
                height=0
            )
    else:
        # 本地子应用程序 - 显示图标、名称和启动按钮
        button_key = f"icon_button_{text}"

        st.markdown(
            f"""
            <div style="text-align: center; font-size: {container_font_size};">
                <img src="data:image/png;base64,{img_base64}" width="50" height="50" title="{text_escaped}" style="display: block; margin: 0 auto;">
                <p style="font-size: {font_size}; margin: 4px 0 8px 0; color: #555; font-weight: 500;">{text}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 启动按钮（点击后启动本地应用）
        clicked = st.button("启动", key=button_key, use_container_width=True)

        if clicked:
            try:

                port = find_available_port()
                print(link)
                launch_streamlit_with_monitor(
                    link,
                    port=port,
                    text=text,
                    user=my_login_user[0],
                    password=st.session_state.get("password", ""),
                )
                components.html(
                    f"""
                    <script>
                        window.open("http://{SERVER_IP}:{port}", "_blank", "width=1000,height=800,left=200,top=100,resizable=yes");
                    </script>
                    """,
                    height=0,
                )

            except Exception as e:
                st.error(f"❌ 启动失败: {e}")


# ----------------------------------------------------------------------------------------------
#
def Show_Clickable_Icons_and_Start_Webapp_for_a_DataFrame_with_a_User_and_the_Role(
        apps_df, my_login_user
):
    if apps_df.empty:
        st.write(
            ":blue[ TIPS 3: 用户 <]",
            my_login_user[0],
            ":blue[ > 在角色 <]",
            my_login_user[1],
            ":blue[> 下无功能webapp可用! ]",
        )
        return
    #
    # 显示对应于所选radio菜单项下，基于所规定的"用户角色"的图标icon子集
    cols = st.columns(8)
    for idx, row in enumerate(apps_df.itertuples()):
        with cols[idx % 8]:
            Show_an_Icon_Link(
                {"image_path": row.Icon, "link": row.Link, "text": row.Text},
                my_login_user,
            )
    return


# --- 处理Radio菜单项 ---------------------------------------------------------------------------
#
def Generate_Clickable_Icons_and_Start_Webapp_for_a_Radio_Menu_Item_with_a_User_and_the_Role(
        apps_df, radio_menu_item, my_login_user
):
    apps_df = apps_df[
        apps_df["Radio"] == radio_menu_item
        ]  # 把excel配置文件中radio列中，属于radio_menu_item的数据项赛选出来，再赋给app_df
    # 当用户User的角色role是"Admin"时，显示radio_menu_item菜单项下的所有图标icon链接及其对应的webapp
    Show_Clickable_Icons_and_Start_Webapp_for_a_DataFrame_with_a_User_and_the_Role(
        apps_df, my_login_user
    )
    return


# ----------------------------------------------------------------------------------------------
#
def Generate_All_Clickable_Icons_and_Start_Webapp(apps_df, my_login_user):
    # 显示所有icons，这里的DataFrame类型的变量apps_df是由原始的excel表导入的
    if my_login_user[1] != "Admin":
        st.write(
            ":blue[ TIPS 4: 用户 <]",
            my_login_user[0],
            ":blue[ > 在角色 <]",
            my_login_user[1],
            ":blue[> 下无权限访问Admin功能! ]",
        )
        return
    else:
        Show_Clickable_Icons_and_Start_Webapp_for_a_DataFrame_with_a_User_and_the_Role(
            apps_df, my_login_user
        )
        return


# 整合后的 main 函数和 Handle_a_Radio_Menu_Item 函数 apps_df, myradio, my_login_user
def Handle_a_Radio_Menu_Item(apps_df, radio_menu_item, my_login_user):
    # 获取当前 Radio 下所有记录（不区分角色）
    full_df = apps_df[apps_df["Radio"] == radio_menu_item]
    filtered_df = full_df

    if filtered_df.empty:
        st.info(f"当前用户 **{my_login_user[0]}** 在【{radio_menu_item}】下无可用功能")
    else:
        cols = st.columns(8)
        for idx, row in enumerate(filtered_df.itertuples()):  # tabe_apps按行遍历
            with cols[idx % 8]:  # 返回余数
                Show_an_Icon_Link(
                    {"image_path": row.Icon, "link": row.Link, "text": row.Text},
                    my_login_user
                )


def Help_for_Using_Webapp_Integrator(
        page_n, my_login_user
):  # page_n: 平台简介的总页数
    if my_login_user[0] == "西交团队":
        doc_images_path = "./integrator_config/doc_images/" + "page"
        for i in range(page_n):
            doc_image = doc_images_path + str(i + 1) + ".png"
            st.image(doc_image)
    else:
        st.write(
            ":blue[ TIPS 3: 用户 <]",
            my_login_user[0],
            ":blue[> 下无权限访问用户手册! ]",
        )
    return


# = 虚拟主函数main(): ===========================================================================
#
def main():
    st.set_page_config(layout="wide")
    st.set_page_config(
        page_title="气井智能管控",
        page_icon="🏠",
        layout="wide"
    )

    my_login_user = Login_Control()

    # 如果未登录，显示登录页面（Login_Control函数内部已处理）
    if my_login_user[0] == "NIL":
        return

    # 如果已登录，显示主界面
    container_heigth = 580
    img_base64 = Get_Base64_of_Bin_File("./integrator_config/yumen.png")

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
                        {my_login_user[0]}
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

    col1, col2 = st.columns([0.2, 0.8])
    with col1:
        with st.container(border=True, height=container_heigth):
            myradio = st.radio("🏠" + ":rainbow[ 导航栏:]",
                               ['平台简介',
                                '地质分析',
                                '工艺设计',
                                '智能采气',
                                '数据资产',
                                '相关工具',
                                '相关链接',
                                '退出'])
            st.divider()
            mynote = [
                "开发: 西安交通大学机械工程学院",
                "      网络化智造与服务系统工程团队",
                "日期: 2025年3月",
                "版本: v1.0.0",
                "版权: ©️网络化智造与服务系统工程™️"
            ]
            st.code("\n".join(mynote))

    with col2:
        with st.container(border=True, height=container_heigth):
            st.write("🤹‍♂️" + f":rainbow[ > 处理Radio菜单项: {myradio}]")

            # 处理相关工具模块，创建container和两个空白页面跳转按钮
            if myradio == "相关工具":
                # 移除外部边框容器，直接使用列布局
                col_btn1, col_btn2 = st.columns(2, gap="large")

                # 自定义按钮样式（通过CSS美化）
                st.markdown("""
                <style>
                .knowledge-btn {
                    width: 100% !important;
                    padding: 15px 0 !important;
                    font-size: 18px !important;
                    font-weight: bold !important;
                    border-radius: 10px !important;
                    border: none !important;
                    transition: all 0.3s ease !important;
                }
                .btn1 {
                    background-color: #2E86AB !important;
                    color: white !important;
                }
                .btn1:hover {
                    background-color: #1d5f7a !important;
                    transform: translateY(-2px) !important;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
                }
                .btn2 {
                    background-color: #c34a36 !important;
                    color: white !important;
                }
                .btn2:hover {
                    background-color: #a83c2c !important;
                    transform: translateY(-2px) !important;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
                }
                </style>
                """, unsafe_allow_html=True)

                # 第一个按钮：油田初始数据整理
                with col_btn1:
                    # 使用自定义样式的按钮（通过components.html实现样式控制）
                    btn_key1 = Setup_a_Unique_Widget_Key()
                    if st.button("油田初始数据整理", key=btn_key1, use_container_width=True):
                        try:
                            port = find_available_port()
                            app_path = "数据标注工具/data_prepare.py"
                            if not os.path.exists(app_path):
                                st.error(f"子应用文件不存在：{app_path}")
                                st.stop()

                            pid = launch_streamlit_with_monitor(
                                app_path,
                                port=port,
                                text="油田初始数据整理",
                                user=my_login_user[0],
                                password=st.session_state.get("password", "")
                            )
                            time.sleep(3)
                            components.html(
                                f"""
                                <script>
                                    window.open("http://{SERVER_IP}:{port}", "_blank", "width=1200,height=800,left=200,top=100");
                                </script>
                                """,
                                height=0
                            )
                        except Exception as e:
                            st.error(f"启动失败：{str(e)}")

                # 第二个按钮：油田数据自动标注
                with col_btn2:
                    btn_key2 = Setup_a_Unique_Widget_Key()
                    if st.button("油田数据自动标注", key=btn_key2, use_container_width=True):
                        try:
                            port = find_available_port()
                            app_path = "数据标注工具/data_processing.py"
                            if not os.path.exists(app_path):
                                st.error(f"子应用文件不存在：{app_path}")
                                st.stop()

                            pid = launch_streamlit_with_monitor(
                                app_path,
                                port=port,
                                text="油田数据自动标注",
                                user=my_login_user[0],
                                password=st.session_state.get("password", "")
                            )
                            time.sleep(3)
                            components.html(
                                f"""
                                <script>
                                    window.open("http://{SERVER_IP}:{port}", "_blank", "width=1200,height=800,left=400,top=200");
                                </script>
                                """,
                                height=0
                            )
                        except Exception as e:
                            st.error(f"启动失败：{str(e)}")

            # 处理智能采气模块 - 仅显示Excel配置的应用
            elif myradio == "智能采气":
                # 显示Excel配置的应用
                apps_df = Read_Apps_from_Excel("./integrator_config/Radio_Icon_Text_Link_RoleSTRING_for_webURLs.xlsx")
                Handle_a_Radio_Menu_Item(apps_df, myradio, my_login_user)

            # 处理其他菜单选项
            elif myradio in ['地质分析', '工艺设计', '数据资产', '相关链接']:
                apps_df = Read_Apps_from_Excel("./integrator_config/Radio_Icon_Text_Link_RoleSTRING_for_webURLs.xlsx")
                Handle_a_Radio_Menu_Item(apps_df, myradio, my_login_user)

            elif myradio == "平台简介":
                page_n = 5
                Help_for_Using_Webapp_Integrator(page_n, my_login_user)

            elif myradio == "退出":
                st.write(":blue[TIPS: 暂停系统运行，可点击关闭浏览器窗口以退出。]")
                st.warning("⚠️ 确认后将终止该 Streamlit 应用进程。")
                if st.button("🔴 确认退出"):
                    pid = os.getpid()
                    time.sleep(2)
                    os.kill(pid, signal.SIGTERM)
    return


# **********************************************************************************************
if __name__ == "__main__":
    main()
# ==================== 程序结束！================================================================