"""
Script khởi tạo Data Warehouse giả lập (Enterprise DW - SQLite)
Mô phỏng chuỗi bán lẻ Nova Mart toàn quốc với 4 vùng miền, 8 siêu thị.
Tích hợp sẵn dữ liệu bình thường, biến động nguyên nhân gốc rễ và dữ liệu bẩn (dirty data)
để kiểm thử quy trình 6 bước của AI Analytics Agent.
"""

import os
import sqlite3
import random
from datetime import datetime, timedelta

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "enterprise_dw.db")

def init_database():
    os.makedirs(DB_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. BẢNG DIM_STORES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_stores (
        store_id INTEGER PRIMARY KEY,
        store_name TEXT NOT NULL,
        region TEXT NOT NULL,
        city TEXT NOT NULL,
        manager_name TEXT,
        manager_phone TEXT,
        manager_email TEXT
    )
    """)

    stores_data = [
        (1, "Nova Mart Quận 1", "Miền Nam", "TP. Hồ Chí Minh", "Nguyễn Văn Hùng", "0908123456", "hung.nv@novamart.vn"),
        (2, "Nova Mart Bình Thạnh", "Miền Nam", "TP. Hồ Chí Minh", "Trần Thị Mai", "0912345678", "mai.tt@novamart.vn"),
        (3, "Nova Mart Cần Thơ", "Miền Nam", "Cần Thơ", "Lê Hoàng Phúc", "0934567890", "phuc.lh@novamart.vn"),
        (4, "Nova Mart Cầu Giấy", "Miền Bắc", "Hà Nội", "Phạm Quốc Tuấn", "0987654321", "tuan.pq@novamart.vn"),
        (5, "Nova Mart Hoàn Kiếm", "Miền Bắc", "Hà Nội", "Vũ Thị Hương", "0976543210", "huong.vt@novamart.vn"),
        (6, "Nova Mart Hải Phòng", "Miền Bắc", "Hải Phòng", "Đỗ Minh Đạt", "0965432109", "dat.dm@novamart.vn"),
        (7, "Nova Mart Hải Châu", "Miền Trung", "Đà Nẵng", "Ngô Thanh Thảo", "0945678901", "thao.nt@novamart.vn"),
        (8, "Nova Mart Buôn Ma Thuột", "Tây Nguyên", "Đắk Lắk", "H'Hen Niê", "0923456789", "hhen@novamart.vn")
    ]
    cursor.executemany("INSERT INTO dim_stores VALUES (?,?,?,?,?,?,?)", stores_data)

    # 2. BẢNG DIM_PRODUCTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_products (
        product_id INTEGER PRIMARY KEY,
        sku_code TEXT NOT NULL UNIQUE,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        unit_cost REAL NOT NULL,
        unit_price REAL NOT NULL
    )
    """)

    products_data = [
        (101, "SKU-BEV-001", "Sữa tươi organic 1L", "Đồ uống", 28000, 42000),
        (102, "SKU-BEV-002", "Nước ép cam nguyên chất 500ml", "Đồ uống", 18000, 32000),
        (103, "SKU-BEV-003", "Cà phê pha sẵn lon", "Đồ uống", 9000, 16000),
        (104, "SKU-FRH-001", "Thịt bò Úc cao cấp 500g", "Thực phẩm tươi sống", 140000, 210000),
        (105, "SKU-FRH-002", "Cá hồi phi lê Nauy 300g", "Thực phẩm tươi sống", 120000, 185000),
        (106, "SKU-FRH-003", "Rau bina hữu cơ 300g", "Thực phẩm tươi sống", 12000, 24000),
        (107, "SKU-FMCG-001", "Nước giặt xả sinh học 3.6kg", "Hàng tiêu dùng", 110000, 175000),
        (108, "SKU-FMCG-002", "Nước rửa chén tinh dầu quế 750ml", "Hàng tiêu dùng", 22000, 38000),
        (109, "SKU-SNK-001", "Bánh quy bơ hộp thiếc", "Bánh kẹo", 65000, 105000),
        (110, "SKU-SNK-002", "Hạt điều rang muối 250g", "Bánh kẹo", 55000, 89000)
    ]
    cursor.executemany("INSERT INTO dim_products VALUES (?,?,?,?,?,?)", products_data)

    # 3. BẢNG DIM_CUSTOMERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_customers (
        customer_id INTEGER PRIMARY KEY,
        customer_name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        email TEXT,
        membership_tier TEXT NOT NULL
    )
    """)

    customers_data = [
        (1001, "Nguyễn An Khang", "0901112233", "khang.na@gmail.com", "Gold"),
        (1002, "Trần Bảo Ngọc", "0912223344", "ngoc.tb@yahoo.com", "Platinum"),
        (1003, "Lê Văn Hào", "0933334455", "hao.lv@hotmail.com", "Silver"),
        (1004, "Phạm Diệu Linh", "0944445566", "linh.pd@gmail.com", "Standard"),
        (1005, "Võ Quốc Cường", "0955556677", "cuong.vq@outlook.com", "Gold"),
        (1006, "Đặng Thùy Trang", "0966667788", "trang.dt@gmail.com", "Platinum"),
        (1007, "Bùi Gia Huy", "0977778899", "huy.bg@gmail.com", "Standard"),
        (1008, "Hoàng Mỹ Duyên", "0988889900", "duyen.hm@gmail.com", "Silver")
    ]
    cursor.executemany("INSERT INTO dim_customers VALUES (?,?,?,?,?)", customers_data)

    # 4. BẢNG FACT_STORE_TRAFFIC_WEATHER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_store_traffic_weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        store_id INTEGER NOT NULL,
        foot_traffic INTEGER NOT NULL,
        weather_condition TEXT NOT NULL,
        rainy_hours REAL NOT NULL
    )
    """)

    # 5. BẢNG FACT_SALES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_sales (
        transaction_id TEXT,
        order_date TEXT,
        order_timestamp TEXT,
        store_id INTEGER,
        product_id INTEGER,
        customer_id INTEGER,
        quantity INTEGER,
        gross_sales REAL,
        discount_amount REAL,
        net_revenue REAL,
        cost_amount REAL,
        gross_profit REAL,
        is_return INTEGER DEFAULT 0,
        out_of_stock_event INTEGER DEFAULT 0
    )
    """)

    # TẠO DỮ LIỆU BÁN HÀNG VÀ THỜI TIẾT TRONG 14 NGÀY
    # Tuần 1: 2026-11-02 đến 2026-11-08 (Tuần chuẩn - Baseline)
    # Tuần 2: 2026-11-09 đến 2026-11-15 (Tuần phân tích - Current, Miền Nam sụt giảm mạnh)
    random.seed(42)
    start_date = datetime(2026, 11, 2)
    sales_rows = []
    traffic_rows = []
    trans_counter = 10000

    products_map = {p[0]: p for p in products_data}

    for day_offset in range(14):
        current_day = start_date + timedelta(days=day_offset)
        day_str = current_day.strftime("%Y-%m-%d")
        is_week2 = (day_offset >= 7)

        for store in stores_data:
            s_id = store[0]
            region = store[2]

            # Giả lập thời tiết và foot traffic
            weather = "Nắng ráo"
            rainy_hours = 0.0
            base_traffic = random.randint(450, 650)

            # Scenario: Ở Tuần 2 (từ ngày 2026-11-11 đến 2026-11-14), Miền Nam (Q1, Bình Thạnh) gặp bão lớn
            is_south_storm = is_week2 and (s_id in [1, 2]) and (day_offset in [9, 10, 11, 12])
            if is_south_storm:
                weather = "Mưa bão ngập lụt"
                rainy_hours = round(random.uniform(6.5, 9.5), 1)
                traffic = int(base_traffic * random.uniform(0.35, 0.45)) # Giảm ~60% traffic
            else:
                if random.random() < 0.2:
                    weather = "Mưa rào"
                    rainy_hours = round(random.uniform(1.0, 3.0), 1)
                    traffic = int(base_traffic * 0.85)
                else:
                    traffic = base_traffic

            traffic_rows.append((day_str, s_id, traffic, weather, rainy_hours))

            # Số lượng giao dịch trong ngày tỉ lệ thuận với traffic
            daily_transactions = int(traffic * 0.25)

            for _ in range(daily_transactions):
                trans_counter += 1
                trans_id = f"TRX-{trans_counter}"
                p_id = random.choice(list(products_map.keys()))
                c_id = random.choice(customers_data)[0]
                p_info = products_map[p_id]

                qty = random.randint(1, 4)
                unit_price = p_info[5]
                unit_cost = p_info[4]

                # Tình huống đứt hàng (Stock-out) sản phẩm chủ lực SKU-BEV-001 tại Miền Nam tuần 2
                is_stockout = 0
                if is_south_storm and p_id == 101:
                    is_stockout = 1
                    qty = 0 # Khách muốn mua nhưng hết hàng!

                if qty == 0:
                    gross = 0.0
                    discount = 0.0
                    net = 0.0
                    cost = 0.0
                    profit = 0.0
                else:
                    discount = round(gross_sales := (qty * unit_price) * (0.1 if random.random() < 0.25 else 0.0), 0)
                    gross = qty * unit_price
                    net = gross - discount
                    cost = qty * unit_cost
                    profit = net - cost

                # Giờ ngẫu nhiên trong ngày
                hour = random.randint(8, 21)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                timestamp_str = f"{day_str} {hour:02d}:{minute:02d}:{second:02d}"

                sales_rows.append((
                    trans_id, day_str, timestamp_str, s_id, p_id, c_id,
                    qty, gross, discount, net, cost, profit, 0, is_stockout
                ))

    # CỐ TÌNH CÀI CẮM DỮ LIỆU BẨN (DIRTY DATA INJECTION) ĐỂ DEMO BƯỚC 3 (DATA QUARANTINE)
    # 1. Doanh thu âm bất thường (Bug phần mềm POS ghi âm)
    dirty_rows = [
        ("TRX-DIRTY-001", "2026-11-10", "2026-11-10 14:20:00", 1, 101, 1001, 2, -84000.0, 0.0, -84000.0, 56000.0, -140000.0, 0, 0),
        ("TRX-DIRTY-002", "2026-11-12", "2026-11-12 18:30:00", 2, 104, 1002, 1, -210000.0, 0.0, -210000.0, 140000.0, -350000.0, 0, 0),
        ("TRX-DIRTY-003", "2026-11-13", "2026-11-13 09:15:00", 1, 107, 1003, 3, -525000.0, 0.0, -525000.0, 330000.0, -855000.0, 0, 0),
        
        # 2. Thiếu mã cửa hàng (NULL store_id)
        ("TRX-DIRTY-004", "2026-11-11", "2026-11-11 11:00:00", None, 102, 1004, 2, 64000.0, 0.0, 64000.0, 36000.0, 28000.0, 0, 0),
        ("TRX-DIRTY-005", "2026-11-14", "2026-11-14 16:45:00", None, 105, 1005, 1, 185000.0, 0.0, 185000.0, 120000.0, 65000.0, 0, 0),

        # 3. Trùng lặp Transaction ID (Duplicate transactions)
        ("TRX-10100", "2026-11-04", "2026-11-04 10:15:00", 3, 101, 1006, 2, 84000.0, 0.0, 84000.0, 56000.0, 28000.0, 0, 0),
        ("TRX-10100", "2026-11-04", "2026-11-04 10:15:00", 3, 101, 1006, 2, 84000.0, 0.0, 84000.0, 56000.0, 28000.0, 0, 0),

        # 4. Lỗi số lượng âm không phải trả hàng (Negative quantity without return flag)
        ("TRX-DIRTY-006", "2026-11-09", "2026-11-09 15:20:00", 4, 106, 1007, -5, 120000.0, 0.0, 120000.0, 60000.0, 60000.0, 0, 0)
    ]

    sales_rows.extend(dirty_rows)

    cursor.executemany("INSERT INTO fact_store_traffic_weather (date, store_id, foot_traffic, weather_condition, rainy_hours) VALUES (?,?,?,?,?)", traffic_rows)
    cursor.executemany("INSERT INTO fact_sales VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", sales_rows)

    conn.commit()
    conn.close()
    print(f"[OK] Kho dữ liệu Enterprise DW đã được khởi tạo thành công tại: {DB_PATH}")
    print(f"     - Số giao dịch fact_sales: {len(sales_rows)}")
    print(f"     - Số bản ghi fact_store_traffic_weather: {len(traffic_rows)}")

if __name__ == "__main__":
    init_database()

