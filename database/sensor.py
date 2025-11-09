import sqlite3
import time
import random
from datetime import datetime, timedelta
import threading
import logging
import math


class WellDataSimulator:
    def __init__(self, db_path='well_production.db',decay_rate=0.01, focus_well=None):
        self.db_path = db_path
        self.wells = []  # 存储气井ID和名称
        self.running = False
        self.threads = []
        self.decay_rate = decay_rate  # 衰减率，控制递减速度
        self.start_time = datetime.now()  # 记录开始时间
        self.focus_well = focus_well

        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 初始化数据库
        self.init_database()

    def init_database(self):
        """初始化数据库和表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wells (
                    well_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    well_name VARCHAR(50) NOT NULL UNIQUE,
                    location VARCHAR(100),
                    depth REAL,
                    status VARCHAR(20) DEFAULT 'active',
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS well_production_data (
                    data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    well_id INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    oil_pressure REAL,
                    temperature REAL,
                    back_pressure REAL,
                    instant_flow REAL,
                    cumulative_flow REAL,
                    liquid_accumulation VARCHAR(20),
                    FOREIGN KEY (well_id) REFERENCES wells(well_id),
                    UNIQUE(well_id, timestamp)
                )
            ''')

            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_well_timestamp 
                ON well_production_data(well_id, timestamp)
            ''')

            # 插入或更新五口气井信息
            wells_info = [
                ('气井1', '区块A', 2500.0),
                ('气井2', '区块B', 2800.0),
                ('气井3', '区块A', 2300.0),
                ('气井4', '区块C', 3000.0),
                ('气井5', '区块B', 2600.0)
            ]

            for well_name, location, depth in wells_info:
                cursor.execute('''
                    INSERT OR REPLACE INTO wells (well_name, location, depth) 
                    VALUES (?, ?, ?)
                ''', (well_name, location, depth))

            conn.commit()
            self.logger.info("数据库初始化完成")

            # 获取气井ID
            cursor.execute("SELECT well_id, well_name FROM wells")
            self.wells = cursor.fetchall()

        except sqlite3.Error as e:
            self.logger.error(f"数据库初始化错误: {e}")
        finally:
            if conn:
                conn.close()

    def get_last_cumulative_flow(self, well_id):
        """获取指定气井的最后累计流量"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cumulative_flow FROM well_production_data 
                WHERE well_id = ? ORDER BY timestamp DESC LIMIT 1
            ''', (well_id,))
            result = cursor.fetchone()
            return result[0] if result else 0.0
        except sqlite3.Error as e:
            self.logger.error(f"获取累计流量错误: {e}")
            return 0.0
        finally:
            if conn:
                conn.close()

    def generate_well_data(self, well_id, well_name):
        """为单口气井生成模拟数据"""
        # 获取上次的累计流量作为基准
        last_cumulative = self.get_last_cumulative_flow(well_id)

        # 模拟数据范围（根据实际情况调整）
        data_ranges = {
            'oil_pressure': (1.0, 8.0),  # MPa
            'temperature': (25.0, 85.0),  # °C
            'back_pressure': (0.5, 3.0),  # MPa
            'instant_flow': (50.0, 300.0),  # m³/h
            'min_flow': 30.0  # 最小瞬时流量，防止衰减到过低
        }

        # 积液情况选项
        liquid_options = ['无积液', '积液正常', '积液严重']

        # 模拟每秒采10min
        sim_start_time = datetime(2024, 9, 26, 8, 0, 0)  # 自定义起始时间
        sample_interval = timedelta(minutes=10)  # 10分钟间隔
        sample_count = 0  # 采样计数器

        while self.running:
            try:


                # 生成随机数据（添加小幅波动模拟真实情况）
                # 计算运行时间（小时）作为衰减依据
                elapsed_time = (datetime.now() - self.start_time).total_seconds() / 3600

                # 生成基础瞬时流量
                base_flow = random.uniform(*data_ranges['instant_flow'])

                # 计算衰减系数 (随时间增加而减小)
                # 衰减公式: 基础流量 × e^(-衰减率 × 运行时间)
                decay_factor = math.exp(-self.decay_rate * elapsed_time)
                decayed_flow = base_flow * decay_factor

                # 确保流量不会低于最小值，添加随机波动
                instant_flow = round(max(decayed_flow + random.uniform(-5, 5),
                                         data_ranges['min_flow']), 1)

                oil_pressure = round(random.uniform(*data_ranges['oil_pressure']) +
                                     random.uniform(-0.1, 0.1), 2)
                temperature = round(random.uniform(*data_ranges['temperature']) +
                                    random.uniform(-0.5, 0.5), 1)
                back_pressure = round(random.uniform(*data_ranges['back_pressure']) +
                                      random.uniform(-0.05, 0.05), 2)

                # 计算累计流量（瞬时流量 × 时间间隔，5秒=5/3600小时）
                time_interval_hours = 10 / 60
                flow_increment = instant_flow * time_interval_hours
                cumulative_flow = round(last_cumulative + flow_increment, 3)
                last_cumulative = cumulative_flow

                # 随机选择积液情况
                liquid_accumulation = random.choice(liquid_options)

                #时间戳定义
                sample_count += 1  # 每次循环，计数器+1
                current_sim_time = sim_start_time + (sample_count * sample_interval)
                current_time = current_sim_time.strftime('%Y-%m-%d %H:%M:%S')  # 保持原格式

                # 当前时间戳
                # current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # 插入数据库
                self.insert_well_data(
                    well_id, current_time, oil_pressure, temperature,
                    back_pressure, instant_flow, cumulative_flow,
                    liquid_accumulation
                )


                # 修改为：只打印关注的气井，且用info级别（更明显）
                if self.focus_well == well_name:  # 只显示指定气井
                    self.logger.info(f"【{well_name}】实时数据 - 时间: {current_time}, "
                                     f"油压: {oil_pressure}MPa, 温度: {temperature}°C, "
                                     f"瞬时流量: {instant_flow}m³/h, 累计流量: {cumulative_flow}m³")
                else:
                    # 非关注气井仍用debug级别，不干扰显示
                    self.logger.debug(f"{well_name} - 时间: {current_time}, 瞬时流量: {instant_flow}m³/h")

            except Exception as e:
                self.logger.error(f"生成{well_name}数据错误: {e}")

            # 等待5秒
            time.sleep(1)

    def insert_well_data(self, well_id, timestamp, oil_pressure, temperature,
                         back_pressure, instant_flow, cumulative_flow, liquid_accumulation):
        """插入气井数据到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO well_production_data 
                (well_id, timestamp, oil_pressure, temperature, back_pressure, 
                 instant_flow, cumulative_flow, liquid_accumulation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (well_id, timestamp, oil_pressure, temperature, back_pressure,
                  instant_flow, cumulative_flow, liquid_accumulation))

            conn.commit()

        except sqlite3.IntegrityError:
            # 时间戳重复，忽略这次插入
            pass
        except sqlite3.Error as e:
            self.logger.error(f"插入数据错误: {e}")
        finally:
            if conn:
                conn.close()

    def start_simulation(self):
        """开始模拟数据采集"""
        self.running = True
        self.logger.info("开始模拟数据采集...")

        # 为每口气井创建独立的采集线程
        for well_id, well_name in self.wells:
            thread = threading.Thread(
                target=self.generate_well_data,
                args=(well_id, well_name)
            )
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            self.logger.info(f"启动{well_name}数据采集线程")

        self.logger.info(f"共启动{len(self.threads)}个数据采集线程")

    def stop_simulation(self):
        """停止模拟数据采集"""
        self.running = False
        self.logger.info("停止数据采集...")

        # 等待所有线程结束
        for thread in self.threads:
            thread.join(timeout=2)

        self.logger.info("数据采集已停止")


def main():
    """主函数"""
    focus_well = input("请输入要实时显示的气井名称（如'气井1'），直接回车默认显示气井1：") or "气井1"

    simulator = WellDataSimulator(focus_well=focus_well)

    try:
        # 启动模拟
        simulator.start_simulation()
        print(f"数据采集程序运行中...正在实时显示【{focus_well}】的数据，按Ctrl+C停止")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n接收到中断信号，正在停止程序...")
    finally:
        simulator.stop_simulation()
        print("程序已退出")


if __name__ == "__main__":
    main()