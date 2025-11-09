import sqlite3
from datetime import datetime
def get_date_range_from_db(gas_name):
    """从数据库获取指定气井的日期范围"""
    try:
        conn = sqlite3.connect('well_production.db')
        cursor = conn.cursor()

        query = """
        SELECT 
            MIN(d.timestamp) as min_date,
            MAX(d.timestamp) as max_date
        FROM well_production_data d
        JOIN wells w ON d.well_id = w.well_id
        WHERE w.well_name = ?
        """

        cursor.execute(query, (gas_name,))
        result = cursor.fetchone()

        if result and result[0] and result[1]:
            min_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S").date()
            max_date = datetime.strptime(result[1], "%Y-%m-%d %H:%M:%S").date()
            return min_date, max_date
        else:
            # 如果没有数据，返回默认日期范围
            return datetime.now().date(), datetime.now().date()

    except Exception as e:
        print(f"获取日期范围错误: {e}")
        return datetime.now().date(), datetime.now().date()
    finally:
        if conn:
            conn.close()

print(get_date_range_from_db('气井1'))