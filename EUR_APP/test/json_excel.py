import json
import pandas as pd


def json_to_excel(json_data, output_excel_path):
    """
    将JSON数据保存为Excel文件
    :param json_data: JSON数据（字典格式）
    :param output_excel_path: 输出Excel文件路径（如"output.xlsx"）
    """
    # 提取keys（第一行）和values（第二行）
    keys = list(json_data.keys())
    values = list(json_data.values())

    # 创建DataFrame，按"一行keys+一行values"组织
    df = pd.DataFrame([keys, values])

    # 保存为Excel（不保留索引和表头）
    df.to_excel(output_excel_path, index=False, header=False)
    print(f"✅ JSON数据已成功保存到：{output_excel_path}")


if __name__ == "__main__":
    # -------------------------- 配置部分（根据需求修改）--------------------------
    # 1. JSON数据来源：可选"直接写字典"或"读取JSON文件"，二选一即可
    # 方式1：直接在脚本中定义JSON字典（适合少量数据）
    json_data = {
          "μgi" : 1.8,
  "Zi": 1.0,
  "pi": 20,
  "Cti": 0.064,
  "G": 7999257418,
  "K": 20,
  "Φ":0.12,
  "Ti": 220,
  "h": 20,
    }

    # 方式2：从JSON文件读取（适合大量数据，取消下面两行注释并修改文件路径）
    # json_file_path = "input.json"  # 你的JSON文件路径
    # with open(json_file_path, "r", encoding="utf-8") as f:
    #     json_data = json.load(f)

    # 2. 输出Excel文件路径
    output_excel = "json_to_excel_result.xlsx"
    # -----------------------------------------------------------------------------

    # 执行转换
    json_to_excel(json_data, output_excel)