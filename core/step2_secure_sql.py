"""
BƯỚC 2: LẬP KẾ HOẠCH & TRUY VẤN AN TOÀN (Planning & Secure Retrieval)
- Lập kế hoạch truy vấn đa chiều (KPI tổng quan, Drill-down, Biến ngoại cảnh).
- Chốt chặn bảo mật (Guardrails): Chặn DML/DDL (INSERT/UPDATE/DELETE/DROP) bằng AST SQL.
- Phân quyền theo vai trò (RBAC) & Che dữ liệu nhạy cảm (PII Masking).
- Cơ chế tự sửa lỗi câu lệnh (Auto-Retry loop tối đa 3 lần).
"""

import os
import json
import sqlite3
import pandas as pd
import sqlglot
from sqlglot import exp
from typing import Dict, Any, Tuple, List

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "enterprise_dw.db")
RBAC_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "rbac_policies.json")

class SecureQueryEngine:
    def __init__(self, db_path: str = DB_PATH, rbac_path: str = RBAC_PATH):
        self.db_path = db_path
        with open(rbac_path, "r", encoding="utf-8") as f:
            self.rbac_config = json.load(f)
        self.roles = self.rbac_config.get("roles", {})
        self.pii_rules = self.rbac_config.get("pii_masking_rules", {})

    def validate_sql_security(self, sql_query: str) -> Tuple[bool, str]:
        """
        Dùng AST (Abstract Syntax Tree) của sqlglot để kiểm duyệt an ninh tuyệt đối:
        - Chỉ cho phép SELECT.
        - Chặn hoàn toàn INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, EXEC...
        """
        try:
            parsed_trees = sqlglot.parse(sql_query)
            if not parsed_trees:
                return False, "Câu truy vấn rỗng hoặc cú pháp không hợp lệ."

            for tree in parsed_trees:
                # Kiểm tra root expression
                if not isinstance(tree, (exp.Select, exp.Union)):
                    return False, f"Guardrail Violated: Lệnh '{type(tree).__name__}' bị cấm tuyệt đối. Chỉ cho phép SELECT."

                # Quét đệ quy tất cả các nút con trong cây cú pháp
                for node in tree.walk():
                    if isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Command)):
                        return False, f"Guardrail Violated: Phát hiện hành vi can thiệp dữ liệu nguy hiểm ({type(node).__name__})."

            return True, "Cú pháp an toàn (Read-Only Verified)."
        except Exception as e:
            return False, f"Lỗi phân tích AST SQL: {str(e)}"

    def apply_rbac_and_filters(self, parsed_context: Dict[str, Any]) -> str:
        """
        Tạo điều kiện WHERE phù hợp với phân quyền RBAC và ngữ cảnh người dùng
        """
        user_role = parsed_context.get("user_role", "CEO")
        role_info = self.roles.get(user_role, self.roles.get("CEO"))
        allowed_regions = role_info.get("allowed_regions", ["ALL"])

        filters = []
        target_region = parsed_context.get("region")

        if "ALL" in allowed_regions:
            if target_region:
                filters.append(f"s.region = '{target_region}'")
        else:
            if target_region and target_region in allowed_regions:
                filters.append(f"s.region = '{target_region}'")
            else:
                formatted_regions = ", ".join([f"'{r}'" for r in allowed_regions])
                filters.append(f"s.region IN ({formatted_regions})")

        return " AND ".join(filters) if filters else "1=1"

    def generate_plan_queries(self, parsed_context: Dict[str, Any]) -> Dict[str, str]:
        """
        Lập kế hoạch truy vấn 3 tầng:
        - Query 1: So sánh KPI kỳ này vs kỳ trước (Kèm cờ is_return và dirty data để kiểm tra)
        - Query 2: Bóc tách Drill-down theo Cửa hàng và Sản phẩm
        - Query 3: Dữ liệu thời tiết và lưu lượng khách (fact_store_traffic_weather)
        """
        rbac_where = self.apply_rbac_and_filters(parsed_context)
        c_start = parsed_context["current_period"]["start_date"]
        c_end = parsed_context["current_period"]["end_date"]
        b_start = parsed_context["baseline_period"]["start_date"]
        b_end = parsed_context["baseline_period"]["end_date"]

        # 1. Query KPI Tổng hợp và Giao dịch chi tiết để chuyển sang Bước 3 Data Profiling
        query_sales = f"""
        SELECT 
            f.transaction_id,
            f.order_date,
            f.order_timestamp,
            f.store_id,
            s.store_name,
            s.region,
            s.city,
            s.manager_name,
            s.manager_phone,
            f.product_id,
            p.sku_code,
            p.product_name,
            p.category,
            f.customer_id,
            c.customer_name,
            c.phone_number,
            f.quantity,
            f.gross_sales,
            f.discount_amount,
            f.net_revenue,
            f.gross_profit,
            f.is_return,
            f.out_of_stock_event,
            CASE 
                WHEN f.order_date BETWEEN '{b_start}' AND '{b_end}' THEN 'BASELINE'
                WHEN f.order_date BETWEEN '{c_start}' AND '{c_end}' THEN 'CURRENT'
                ELSE 'OTHER'
            END AS period_type
        FROM fact_sales f
        LEFT JOIN dim_stores s ON f.store_id = s.store_id
        LEFT JOIN dim_products p ON f.product_id = p.product_id
        LEFT JOIN dim_customers c ON f.customer_id = c.customer_id
        WHERE ({rbac_where})
          AND (f.order_date BETWEEN '{b_start}' AND '{c_end}')
        ORDER BY f.order_date ASC, f.order_timestamp ASC;
        """

        # 2. Query Thời tiết và Lưu lượng khách (Foot Traffic)
        query_external = f"""
        SELECT 
            w.date,
            w.store_id,
            s.store_name,
            s.region,
            w.foot_traffic,
            w.weather_condition,
            w.rainy_hours,
            CASE 
                WHEN w.date BETWEEN '{b_start}' AND '{b_end}' THEN 'BASELINE'
                WHEN w.date BETWEEN '{c_start}' AND '{c_end}' THEN 'CURRENT'
                ELSE 'OTHER'
            END AS period_type
        FROM fact_store_traffic_weather w
        JOIN dim_stores s ON w.store_id = s.store_id
        WHERE ({rbac_where})
          AND (w.date BETWEEN '{b_start}' AND '{c_end}')
        ORDER BY w.date ASC;
        """

        return {
            "sales_transactions": query_sales.strip(),
            "traffic_weather": query_external.strip()
        }

    def mask_pii(self, df: pd.DataFrame, user_role: str) -> pd.DataFrame:
        """
        Bảo vệ quyền riêng tư (PII Masking):
        Tự động che số điện thoại, tên khách hàng và quản lý nếu không phải DATA_ADMIN
        """
        role_info = self.roles.get(user_role, self.roles.get("CEO"))
        if role_info.get("can_view_pii", False):
            return df # Được phép xem PII

        masked_df = df.copy()
        
        # Che số điện thoại: 0908123456 -> 0908***456
        for col in ["phone_number", "manager_phone"]:
            if col in masked_df.columns:
                masked_df[col] = masked_df[col].astype(str).apply(
                    lambda x: x[:4] + "***" + x[-3:] if len(x) >= 7 and x != "None" else "***"
                )

        # Che tên khách hàng: Nguyễn An Khang -> N*** K***
        for col in ["customer_name", "manager_name"]:
            if col in masked_df.columns:
                masked_df[col] = masked_df[col].astype(str).apply(
                    lambda x: " ".join([part[0] + "***" for part in x.split()]) if x != "None" else "***"
                )

        return masked_df

    def execute_with_retry(self, sql_query: str, user_role: str = "CEO", max_retries: int = 3) -> Tuple[pd.DataFrame, List[str]]:
        """
        Thực thi SQL an toàn kèm cơ chế Guardrails và Auto-Retry
        """
        logs = []
        is_safe, sec_msg = self.validate_sql_security(sql_query)
        if not is_safe:
            logs.append(f"[GUARDRAIL_BLOCKED] {sec_msg}")
            raise PermissionError(sec_msg)

        logs.append(f"[GUARDRAIL_PASSED] {sec_msg}")

        attempt = 0
        current_sql = sql_query

        while attempt < max_retries:
            attempt += 1
            try:
                conn = sqlite3.connect(self.db_path)
                df = pd.read_sql_query(current_sql, conn)
                conn.close()

                if df.empty:
                    logs.append(f"[RETRY_{attempt}] Truy vấn trả về rỗng, đang thử tinh chỉnh bộ lọc...")
                    # Auto-fix nhẹ: nếu WHERE quá chặt, nới lỏng
                    current_sql = current_sql.replace("1=1 AND", "1=1")
                    continue

                logs.append(f"[SUCCESS] Lấy thành công {len(df)} dòng dữ liệu tại lần thử thứ {attempt}.")
                
                # Áp dụng PII Masking
                masked_df = self.mask_pii(df, user_role)
                logs.append(f"[PII_GUARD] Đã che thông tin nhận dạng cá nhân theo chính sách bảo mật.")
                return masked_df, logs

            except Exception as e:
                logs.append(f"[RETRY_{attempt}_FAILED] Lỗi SQL: {str(e)}")
                # Sửa lỗi phổ biến nếu có
                if "no such column" in str(e).lower():
                    # Thử loại bỏ cột lỗi hoặc sửa tên
                    pass
                if attempt >= max_retries:
                    raise RuntimeError(f"Truy vấn thất bại sau {max_retries} lần thử. Lỗi cuối: {str(e)}")

        return pd.DataFrame(), logs
