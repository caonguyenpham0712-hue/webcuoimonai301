"""
BƯỚC 6: PHẢN HỒI & CẢNH BÁO CHỦ ĐỘNG (Delivery & Human-in-the-loop)
- Xuất dữ liệu đa định dạng (Excel / CSV) cho Dữ liệu sạch và Báo cáo cách ly.
- Động cơ Cảnh báo chủ động (Proactive Alerting): Đối chiếu với config/alert_thresholds.json.
- Vòng lặp phản hồi người dùng (Feedback Loop): Ghi nhận phản hồi và cập nhật bộ nhớ dài hạn.
"""

import os
import io
import json
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

from database.memory_store import AgentMemoryStore

THRESHOLDS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "alert_thresholds.json")

class DeliveryFeedbackEngine:
    def __init__(self, thresholds_path: str = THRESHOLDS_PATH):
        with open(thresholds_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.kpi_thresholds = self.config.get("kpi_alerts", {})
        self.alert_channels = self.config.get("alert_channels", [])
        self.memory = AgentMemoryStore()

    def evaluate_proactive_alerts(self, analytics_results: Dict[str, Any], dq_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Kiểm tra các chỉ số so với ngưỡng rủi ro cấu hình sẵn
        """
        alerts = []
        kpi = analytics_results.get("kpi_summary", {})
        rev_drop_pct = kpi.get("growth_revenue_pct", 0.0)

        # 1. Cảnh báo sụt giảm doanh thu vượt ngưỡng
        threshold_rev = self.kpi_thresholds.get("revenue_drop_pct_threshold", -15.0)
        if rev_drop_pct <= threshold_rev:
            alerts.append({
                "level": "CRITICAL",
                "code": "ALERT_REVENUE_CRASH",
                "title": "CẢNH BÁO KHẨN CẤP: Doanh thu sụt giảm vượt ngưỡng rủi ro",
                "message": f"Doanh thu tuần giảm {rev_drop_pct:+,.2f}% (vượt ngưỡng cho phép {threshold_rev}%). Cần kích hoạt phản ứng nhanh.",
                "channels": ["SLACK_WEBHOOK", "EMAIL", "DASHBOARD_BANNER"],
                "timestamp": datetime.now().isoformat()
            })

        # 2. Cảnh báo dữ liệu bẩn vượt ngưỡng
        dirty_pct = dq_metrics.get("dirty_percentage", 0.0)
        threshold_dirty = self.kpi_thresholds.get("dirty_data_pct_threshold", 3.0)
        if dirty_pct >= threshold_dirty:
            alerts.append({
                "level": "WARNING",
                "code": "ALERT_DIRTY_DATA_HIGH",
                "title": "CẢNH BÁO CHẤT LƯỢNG DỮ LIỆU: Tỷ lệ bản ghi lỗi tăng cao",
                "message": f"Tỷ lệ dữ liệu cách ly đạt {dirty_pct}% (ngưỡng tối đa {threshold_dirty}%). Đề nghị kiểm tra cổng tích hợp POS.",
                "channels": ["DASHBOARD_BANNER"],
                "timestamp": datetime.now().isoformat()
            })

        # 3. Cảnh báo đứt hàng (Stock-out)
        stockout_items = analytics_results.get("stockout_impact", [])
        if stockout_items:
            total_stockout_events = sum(item.get("out_of_stock_event", 0) for item in stockout_items)
            alerts.append({
                "level": "WARNING",
                "code": "ALERT_SUPPLY_CHAIN_STOCKOUT",
                "title": "CẢNH BÁO CHUỖI CUNG ỨNG: Xuất hiện đứt hàng diện rộng",
                "message": f"Phát hiện {total_stockout_events} lượt giao dịch bị đứt hàng, tập trung vào sản phẩm {stockout_items[0].get('product_name')}.",
                "channels": ["SLACK_WEBHOOK", "DASHBOARD_BANNER"],
                "timestamp": datetime.now().isoformat()
            })

        return alerts

    def export_to_excel(self, df_clean: pd.DataFrame, df_quarantine: pd.DataFrame) -> bytes:
        """
        Xuất file Excel gồm 2 sheet: Dữ liệu sạch & Kho cách ly dữ liệu bẩn
        """
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_clean.to_excel(writer, sheet_name="Clean_Sales_Data", index=False)
            if not df_quarantine.empty:
                df_quarantine.to_excel(writer, sheet_name="Quarantine_Dirty_Log", index=False)
        return output.getvalue()

    def record_feedback(self, conversation_id: str, question: str, sql_query: str, summary: str, rating: int, comment: str = "") -> bool:
        """
        Lưu phản hồi người dùng vào Vector/Semantic Memory Store
        """
        return self.memory.save_feedback(
            conversation_id=conversation_id,
            question=question,
            generated_sql=sql_query,
            summary=summary,
            rating=rating,
            comment=comment
        )

