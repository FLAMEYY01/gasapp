import numpy as np
import pandas as pd




class GasPVT:
    """气体PVT性质管理类，支持查询μg、Z、Ct"""
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.p_values = self.df['p（MPa）'].values * 1e6  # 转换为Pa
        self.μg_values = self.df['μg（Pa·s）'].values
        self.Z_values = self.df['Z（-）'].values
        self.Ct_values = self.df['Ct（MPa^-1）'].values  # 新增Ct属性

    def get_properties(self, p):
        """根据压强p（Pa）插值获取对应的μg、Z、Ct"""
        if p < self.p_values.min() or p > self.p_values.max():
            print(f"警告：压强{p/1e6:.1f}MPa超出数据范围，结果可能不准确")
        μg = np.interp(p, self.p_values, self.μg_values)
        Z = np.interp(p, self.p_values, self.Z_values)
        Ct = np.interp(p, self.p_values, self.Ct_values)
        return μg, Z, Ct

    # 若需单独查询某一属性，可添加如下方法（示例）
    def get_μg(self, p):
        return np.interp(p, self.p_values, self.μg_values)

    def get_Z(self, p):
        return np.interp(p, self.p_values, self.Z_values)

    def get_Ct(self, p):
        return np.interp(p, self.p_values, self.Ct_values)



