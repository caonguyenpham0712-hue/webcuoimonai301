"""
Hệ thống Điều phối Chính (Master Pipeline Orchestrator)
Kết nối liền mạch toàn bộ 6 bước từ nhận ý định đến phản hồi điều hành
"""

import uuid
import pandas as pd
import numpy as np
import unicodedata
import re
from typing import Dict, Any, Optional

from core.step1_intent_parser import IntentContextParser
from core.step2_secure_sql import SecureQueryEngine
from core.step3_data_quarantine import DataProfilerQuarantine
from core.step4_root_cause import DeepAnalyticsEngine
from core.step5_viz_summary import VisualizationSummaryEngine
from core.step6_delivery_feedback import DeliveryFeedbackEngine

class EnterpriseAnalyticsAgent:
    def __init__(self):
        self.step1_parser = IntentContextParser()
        self.step2_query = SecureQueryEngine()
        self.step3_profiler = DataProfilerQuarantine()
        self.step4_analytics = DeepAnalyticsEngine()
        self.step5_summary = VisualizationSummaryEngine()
        self.step6_delivery = DeliveryFeedbackEngine()

    def _parse_numeric_value(self, val) -> float:
        """Chuyển đổi chuỗi tiền tệ/số định dạng Việt Nam & Quốc tế sang float an toàn"""
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        import re
        s = str(val).strip()
        s = re.sub(r'[^\d.,\-+]', '', s)
        if not s:
            return 0.0
        if '.' in s and ',' in s:
            if s.rfind(',') > s.rfind('.'):
                s = s.replace('.', '').replace(',', '.')
            else:
                s = s.replace(',', '')
        elif ',' in s:
            parts = s.split(',')
            if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
                s = s.replace(',', '')
            else:
                s = s.replace(',', '.')
        elif '.' in s:
            parts = s.split('.')
            if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
                s = s.replace('.', '')
        try:
            return float(s)
        except Exception:
            return 0.0

    def _clean_text(self, s: str) -> str:
        """Chuẩn hóa chuỗi, loại bỏ dấu tiếng Việt để đối chiếu tên cột thông minh"""
        s = str(s).strip().lower()
        s = unicodedata.normalize('NFD', s)
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
        return s.replace('đ', 'd').replace('Đ', 'd')

    def _standardize_custom_df(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Chuẩn hóa bảng dữ liệu tải lên từ người dùng để khớp hoàn toàn với pipeline phân tích
        """
        df = raw_df.copy()
        col_map = {}
        for c in df.columns:
            cl = self._clean_text(c)
            if any(k in cl for k in ["doanh thu", "revenue", "thanh tien", "tong tien", "total_amount", "amount", "gia tri", "sales", "tien", "gia ban", "gia", "thanh toan"]):
                if "net_revenue" not in col_map.values():
                    col_map[c] = "net_revenue"
            elif any(k in cl for k in ["ma don", "transaction", "order_id", "order_code", "ma gd", "ma giao dich", "invoice", "ma hoa don", "id"]):
                if "transaction_id" not in col_map.values():
                    col_map[c] = "transaction_id"
            elif any(k in cl for k in ["ngay", "date", "thoi gian", "created", "order_time", "thang", "time"]):
                if "order_date" not in col_map.values():
                    col_map[c] = "order_date"
            elif any(k in cl for k in ["chi nhanh", "cua hang", "store", "branch", "shop", "diem ban", "kho", "don vi", "dia diem", "khu vuc"]):
                if "store_name" not in col_map.values():
                    col_map[c] = "store_name"
            elif any(k in cl for k in ["san pham", "ten hang", "mat hang", "product", "item", "sku", "ten sp", "hang hoa"]):
                if "product_name" not in col_map.values():
                    col_map[c] = "product_name"
            elif any(k in cl for k in ["so luong", "qty", "quantity", "sl"]):
                if "quantity" not in col_map.values():
                    col_map[c] = "quantity"
            elif any(k in cl for k in ["nganh hang", "danh muc", "category", "nhom hang", "loai hang", "phan loai"]):
                if "category" not in col_map.values():
                    col_map[c] = "category"
            elif any(k in cl for k in ["vung mien", "region", "area", "mien", "tinh", "thanh pho", "city"]):
                if "region" not in col_map.values():
                    col_map[c] = "region"
            elif any(k in cl for k in ["khach hang", "ten khach", "customer", "nguoi mua", "client"]):
                if "customer_name" not in col_map.values():
                    col_map[c] = "customer_name"

        df.rename(columns=col_map, inplace=True)

        n = len(df)
        if "transaction_id" not in df.columns:
            df["transaction_id"] = [f"TRX-CUS-{i+1:05d}" for i in range(n)]
        if "order_date" not in df.columns:
            df["order_date"] = "2026-11-15"

        # Nếu không có store_name, tự động chọn cột phân loại phù hợp nhất
        if "store_name" not in df.columns:
            if "product_name" in df.columns and df["product_name"].nunique() > 1:
                df["store_name"] = df["product_name"]
            else:
                cat_cols = [c for c in df.columns if df[c].dtype == object and 2 <= df[c].nunique() <= 30]
                if cat_cols:
                    df["store_name"] = df[cat_cols[0]].astype(str)
                else:
                    df["store_name"] = [f"Chi nhánh {(i % 3) + 1}" for i in range(n)]

        if "region" not in df.columns:
            df["region"] = "Toàn quốc"
        if "customer_name" not in df.columns:
            df["customer_name"] = "Khách hàng"
        if "phone_number" not in df.columns:
            df["phone_number"] = "0900000000"
        if "sku_code" not in df.columns:
            df["sku_code"] = [f"SKU-{(i % 5) + 1}" for i in range(n)]
        if "product_name" not in df.columns:
            df["product_name"] = "Sản phẩm"
        if "category" not in df.columns:
            df["category"] = "Tiêu dùng"
        if "quantity" not in df.columns:
            df["quantity"] = 1

        # Xử lý an toàn cột doanh thu net_revenue
        if "net_revenue" in df.columns:
            df["net_revenue"] = df["net_revenue"].apply(self._parse_numeric_value)
        else:
            num_cols = df.select_dtypes(include=["number"]).columns
            if len(num_cols) > 0:
                df["net_revenue"] = df[num_cols[0]].apply(self._parse_numeric_value)
            else:
                df["net_revenue"] = 100000.0

        # Nếu toàn bộ net_revenue đều = 0, gán giá trị mặc định tránh sập biểu đồ
        if (df["net_revenue"] == 0).all():
            df["net_revenue"] = 150000.0

        if "gross_sales" not in df.columns:
            df["gross_sales"] = df["net_revenue"]
        else:
            df["gross_sales"] = df["gross_sales"].apply(self._parse_numeric_value)

        df["quantity"] = df["quantity"].apply(self._parse_numeric_value).astype(int)
        df.loc[df["quantity"] <= 0, "quantity"] = 1

        if "is_return" not in df.columns:
            df["is_return"] = 0
        if "out_of_stock_event" not in df.columns:
            df["out_of_stock_event"] = 0
        if "store_id" not in df.columns:
            df["store_id"] = pd.factorize(df["store_name"])[0] + 1
        if "product_id" not in df.columns:
            df["product_id"] = pd.factorize(df["sku_code"])[0] + 1
        if "gross_profit" not in df.columns:
            df["gross_profit"] = df["net_revenue"] * 0.35

        # Phân kỳ BASELINE / CURRENT dựa trên ngày nếu có, hoặc chia theo tỷ lệ
        if "period_type" not in df.columns:
            assigned = False
            if "order_date" in df.columns:
                try:
                    dates = pd.to_datetime(df["order_date"], errors="coerce")
                    if dates.notna().sum() > len(df) * 0.5 and dates.nunique() > 1:
                        df = df.sort_values(by="order_date").reset_index(drop=True)
                        dates = pd.to_datetime(df["order_date"], errors="coerce")
                        med_date = dates.median()
                        df["period_type"] = np.where(dates < med_date, "BASELINE", "CURRENT")
                        assigned = True
                except Exception:
                    pass
            if not assigned:
                half = max(1, n // 2)
                df["period_type"] = "BASELINE"
                df.iloc[half:, df.columns.get_loc("period_type")] = "CURRENT"

        return df

    def run(self, user_query: str, user_role: str = "CEO", as_of_date: str = "2026-11-16", custom_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Thực thi quy trình 6 bước chuẩn BA Data Analytics Agent
        """
        conversation_id = str(uuid.uuid4())[:8]
        pipeline_log = []

        # ==========================================
        # BƯỚC 1: TIẾP NHẬN & HIỂU Ý ĐỊNH
        # ==========================================
        pipeline_log.append("▶ [BƯỚC 1] Bóc tách thực thể và ánh xạ Semantic Layer...")
        parsed_context = self.step1_parser.parse(user_query, user_role, as_of_date)

        # ==========================================
        # BƯỚC 2: LẬP KẾ HOẠCH & TRUY VẤN AN TOÀN
        # ==========================================
        pipeline_log.append("▶ [BƯỚC 2] Lập kế hoạch truy vấn, kiểm duyệt AST Guardrails và PII Masking...")
        plan_queries = self.step2_query.generate_plan_queries(parsed_context)
        
        if custom_df is not None and not custom_df.empty:
            df_raw_sales = self._standardize_custom_df(custom_df)
            sales_exec_logs = [f"✅ Đã tiếp nhận và chuẩn hóa {len(df_raw_sales):,} bản ghi từ tệp dữ liệu người dùng nạp."]
            df_external = pd.DataFrame()
            ext_exec_logs = ["ℹ️ Chế độ tải tệp người dùng: Tự động phân tích dữ liệu bán hàng."]
        else:
            # Thực thi lấy dữ liệu bán hàng
            df_raw_sales, sales_exec_logs = self.step2_query.execute_with_retry(
                plan_queries["sales_transactions"], user_role=user_role
            )
            # Thực thi lấy dữ liệu ngoại cảnh (Thời tiết & Foot Traffic)
            df_external, ext_exec_logs = self.step2_query.execute_with_retry(
                plan_queries["traffic_weather"], user_role=user_role
            )
        pipeline_log.extend(sales_exec_logs)

        # ==========================================
        # BƯỚC 3: LÀM SẠCH & KIỂM ĐỊNH CHẤT LƯỢNG
        # ==========================================
        pipeline_log.append("▶ [BƯỚC 3] Kiểm định chất lượng dữ liệu trong Sandbox và cách ly dữ liệu lỗi...")
        df_clean, df_quarantine, dq_metrics = self.step3_profiler.profile_and_quarantine(df_raw_sales)
        pipeline_log.append(f"   -> Kết quả: {dq_metrics['clean_records']:,} dòng sạch, {dq_metrics['dirty_records']} dòng cách ly. Điểm chất lượng: {dq_metrics['quality_score']}%")

        # ==========================================
        # BƯỚC 4: PHÂN TÍCH CHUYÊN SÂU & TÌM GỐC RỄ
        # ==========================================
        pipeline_log.append("▶ [BƯỚC 4] Chạy mô hình phân tích đóng góp, tương quan Pearson và Pareto...")
        analytics_results = self.step4_analytics.analyze(df_clean, df_external, parsed_context)

        # ==========================================
        # BƯỚC 5: TRỰC QUAN HÓA & TỔNG HỢP INSIGHT
        # ==========================================
        pipeline_log.append("▶ [BƯỚC 5] Khởi tạo biểu đồ tương tác Plotly và lập Executive Summary...")
        chart_waterfall = self.step5_summary.build_waterfall_chart(
            analytics_results["kpi_summary"],
            analytics_results["store_breakdown"]
        )
        chart_pareto = self.step5_summary.build_pareto_chart(
            analytics_results["pareto_stores"],
            analytics_results.get("store_breakdown", [])
        )
        chart_forecast = self.step5_summary.build_forecast_chart(
            df_clean,
            analytics_results["short_term_forecast"]
        )
        executive_summary = self.step5_summary.generate_executive_summary(
            analytics_results, dq_metrics, parsed_context
        )

        # ==========================================
        # BƯỚC 6: PHẢN HỒI & CẢNH BÁO CHỦ ĐỘNG
        # ==========================================
        pipeline_log.append("▶ [BƯỚC 6] Đánh giá ngưỡng cảnh báo rủi ro và đóng gói báo cáo...")
        active_alerts = self.step6_delivery.evaluate_proactive_alerts(analytics_results, dq_metrics)
        excel_bytes = self.step6_delivery.export_to_excel(df_clean, df_quarantine)

        return {
            "conversation_id": conversation_id,
            "pipeline_log": pipeline_log,
            "step1_parsed_context": parsed_context,
            "step2_queries": plan_queries,
            "step2_raw_count": len(df_raw_sales),
            "step3_clean_df": df_clean,
            "step3_quarantine_df": df_quarantine,
            "step3_dq_metrics": dq_metrics,
            "step4_analytics": analytics_results,
            "step5_waterfall": chart_waterfall,
            "step5_pareto": chart_pareto,
            "step5_forecast": chart_forecast,
            "step5_executive_summary": executive_summary,
            "step6_alerts": active_alerts,
            "step6_excel_bytes": excel_bytes
        }

