import streamlit as st
import pandas as pd
import base64
import io

# -------------------- 全局配置：固定展示的 Keys --------------------
FIXED_KEYS = ["一", "二", "三"]

# -------------------- 步骤1：初始化会话状态（存储上传的 value） --------------------
if "excel_values" not in st.session_state:
    st.session_state.excel_values = ["", "", ""]  # 初始为空

# -------------------- 步骤2：自定义 HTML 上传组件（仅显示按钮） --------------------
upload_html = """
<style>
/* 美化上传按钮 */
.upload-btn {
    background-color: #4F46E5;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s;
}
.upload-btn:hover {
    background-color: #4338CA;
}
/* 隐藏原生文件选择框 */
#custom-upload {
    display: none;
}
</style>

<!-- 自定义上传按钮 -->
<button class="upload-btn" onclick="document.getElementById('custom-upload').click()">
    📤 点击上传Excel文件
</button>
<input type="file" id="custom-upload" accept=".xlsx,.xls" onchange="handleUpload(this.files)">

<script>
// 处理文件上传，转换为Base64传递给Streamlit
function handleUpload(files) {
    if (files.length > 0) {
        const file = files[0];
        const reader = new FileReader();
        reader.onload = function(e) {
            const base64 = e.target.result.split(',')[1];
            // 发送文件数据到Streamlit
            window.parent.postMessage({
                type: 'file_upload',
                data: {
                    name: file.name,
                    content: base64,
                    type: file.type
                }
            }, '*');
        };
        reader.readAsDataURL(file);
    }
}

// 接收Streamlit的消息回调
window.addEventListener('message', function(e) {
    if (e.data.type === 'upload_complete') {
        console.log('上传成功');
    }
});
</script>
"""

# 嵌入自定义上传按钮
st.markdown("<center>", unsafe_allow_html=True)
st.components.v1.html(upload_html, height=80)
st.markdown("</center>", unsafe_allow_html=True)


# -------------------- 步骤3：监听前端上传消息，解析Excel数据 --------------------
def parse_excel(file_content):
    """解析Excel：第一行key，第二行value，匹配固定keys"""
    try:
        # 读取Excel文件（默认读取第一个sheet）
        df = pd.read_excel(file_content, header=None)  # header=None 不把第一行当表头

        # 验证数据格式：至少2行（key行+value行），至少3列（对应一、二、三）
        if len(df) < 2 or len(df.columns) < 3:
            st.error("Excel格式错误！需满足：第一行是key（一、二、三），第二行是value（1、2、3）")
            return None

        # 提取第一行key和第二行value（转为列表）
        excel_keys = df.iloc[0].tolist()  # 第一行：key列表
        excel_values = df.iloc[1].tolist()  # 第二行：value列表

        # 匹配固定keys，按顺序提取value（忽略Excel中key的顺序，强制按"一、二、三"匹配）
        result_values = []
        for target_key in FIXED_KEYS:
            if target_key in excel_keys:
                # 找到对应index，提取value
                idx = excel_keys.index(target_key)
                result_values.append(str(excel_values[idx]) if pd.notna(excel_values[idx]) else "")
            else:
                result_values.append("")  # 若Excel中缺少某个key，value为空

        return result_values
    except Exception as e:
        st.error(f"解析Excel失败：{str(e)}")
        return None


# 接收前端传递的Base64文件数据
upload_data = st.components.v1.html("""
<script>
let uploadData = null;
// 监听文件上传消息
window.addEventListener('message', function(e) {
    if (e.data.type === 'file_upload') {
        uploadData = e.data.data;
        // 传递给Streamlit
        Streamlit.setComponentValue(uploadData);
    }
});
// 初始返回null
Streamlit.setComponentValue(null);
</script>
""", height=0)

# 处理上传的文件
if upload_data is not None:
    print(111111111111111111111111111111111)
    try:
        # 解码Base64为文件对象
        file_content = base64.b64decode(upload_data["content"])
        excel_file = io.BytesIO(file_content)
#
#         # 解析Excel数据
#         values = parse_excel(excel_file)
#         if values:
#             st.session_state.excel_values = values  # 更新会话状态
#             st.success(f"✅ 上传成功！文件：{upload_data['name']}")
    except Exception as e:
        st.error(f"文件处理失败：{str(e)}")
#
#
#
# # -------------------- 步骤4：展示固定Container（key固定，value动态填充） --------------------
# st.markdown("---")  # 分割线
# st.subheader("📊 数据展示容器")
#
# # 创建容器（固定布局：key左，value右）
# container = st.container(border=True)
# with container:
#     # 按"一、二、三"顺序展示，每行一个key-value对
#     for i, key in enumerate(FIXED_KEYS):
#         col1, col2 = st.columns([1, 3])
#         with col1:
#             st.markdown(f"**{key}**")  # 固定key
#         with col2:
#             # 展示对应的value（从会话状态读取，初始为空）
#             st.info(st.session_state.excel_values[i] if st.session_state.excel_values[i] else "未上传数据")
