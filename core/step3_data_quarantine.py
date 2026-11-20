"""
BƯỚC 3: LÀM SẠCH & KIỂM ĐỊNH CHẤT LƯỢNG (Data Profiling & Quarantine)
- Môi trường Sandbox: Python Pandas
- Kiểm định các bất thường:
  + Doanh thu âm bất thường khi không phải đơn hoàn trả.
  + Thiếu khóa ngoại (store_id, product_id bị NULL).
  + Trùng lặp Transaction ID.
  + Số lượng bán âm/bằng 0 trái quy tắc nghiệp vụ.
- Tách biệt (Quarantine) dữ liệu lỗi ra khỏi tập phân tích và tạo Báo cáo Chất lượng Dữ liệu (DQ Report).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

class DataProfilerQuarantine:
    def __init__(self):
        pass

    def profile_and_quarantine(self, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Kiểm định chất lượng dữ liệu và cách ly dữ liệu bẩn
        Returns:
            df_clean: DataFrame dữ liệu chuẩn đã làm sạch
            df_quarantine: DataFrame chứa các dòng dữ liệu bị cách ly kèm lý do
            dq_metrics: Từ điển các chỉ số Data Quality
        """
        if df_raw.empty:
            return df_raw, pd.DataFrame(), {"total_records": 0, "dirty_count": 0, "quality_score": 100.0}

        df = df_raw.copy()
        total_initial = len(df)
        df["quarantine_reasons"] = ""

        # Quy tắc 1: Doanh thu âm bất thường (Negative Sales where is_return == 0)
        neg_sales_mask = (df["net_revenue"] < 0) & (df["is_return"] == 0)
        df.loc[neg_sales_mask, "quarantine_reasons"] += "ERR_NEGATIVE_REVENUE; "

        # Quy tắc 2: Thiếu khóa ngoại quan trọng (Null Store ID hoặc Product ID)
        null_fk_mask = df["store_id"].isna() | df["product_id"].isna()
        df.loc[null_fk_mask, "quarantine_reasons"] += "ERR_MISSING_FOREIGN_KEY; "

        # Quy tắc 3: Trùng lặp Transaction ID (Duplicate IDs)
        dup_mask = df.duplicated(subset=["transaction_id"], keep="first")
        df.loc[dup_mask, "quarantine_reasons"] += "ERR_DUPLICATE_TRANSACTION_ID; "

        # Quy tắc 4: Số lượng <= 0 khi không phải đơn hoàn (Invalid Quantity)
        invalid_qty_mask = (df["quantity"] <= 0) & (df["is_return"] == 0) & (df["out_of_stock_event"] == 0)
        df.loc[invalid_qty_mask, "quarantine_reasons"] += "ERR_INVALID_QUANTITY; "

        # Tách dữ liệu
        is_dirty = df["quarantine_reasons"] != ""
        df_quarantine = df[is_dirty].copy()
        df_clean = df[~is_dirty].copy().drop(columns=["quarantine_reasons"])

        # Thống kê phân loại lỗi
        error_breakdown = {
            "ERR_NEGATIVE_REVENUE": int(neg_sales_mask.sum()),
            "ERR_MISSING_FOREIGN_KEY": int(null_fk_mask.sum()),
            "ERR_DUPLICATE_TRANSACTION_ID": int(dup_mask.sum()),
            "ERR_INVALID_QUANTITY": int(invalid_qty_mask.sum())
        }

        dirty_count = len(df_quarantine)
        clean_count = len(df_clean)
        dirty_pct = round((dirty_count / total_initial) * 100.0, 2)
        quality_score = round(100.0 - dirty_pct, 2)

        dq_metrics = {
            "total_records": total_initial,
            "clean_records": clean_count,
            "dirty_records": dirty_count,
            "dirty_percentage": dirty_pct,
            "quality_score": quality_score,
            "status": "PASSED" if dirty_pct < 5.0 else "WARNING_HIGH_DIRTY_DATA",
            "error_breakdown": error_breakdown
        }

        return df_clean, df_quarantine, dq_metrics

