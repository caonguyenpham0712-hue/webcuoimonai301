"""
BƯỚC 1: TIẾP NHẬN & HIỂU Ý ĐỊNH (Intent & Context Parsing)
- Tách thực thể (Thời gian, Vùng miền, Cửa hàng, Ngành hàng, Chỉ số KPI).
- Đối chiếu với Data Catalog / Semantic Layer (config/semantic_catalog.yaml).
- Tra cứu các mẫu câu hỏi tương tự từ Vector/Semantic Memory Store.
"""

import os
import re
import yaml
from typing import Dict, Any, List
from datetime import datetime, timedelta

from database.memory_store import AgentMemoryStore

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "semantic_catalog.yaml")

class IntentContextParser:
    def __init__(self, catalog_path: str = CATALOG_PATH):
        with open(catalog_path, "r", encoding="utf-8") as f:
            self.catalog = yaml.safe_load(f)
        self.memory = AgentMemoryStore()
        self.metrics_def = self.catalog.get("metrics", {})
        self.tables_def = self.catalog.get("tables", {})

    def parse(self, user_query: str, user_role: str = "CEO", as_of_date: str = "2026-11-16") -> Dict[str, Any]:
        """
        Phân tách ý định người dùng và đối chiếu với Semantic Layer
        """
        query_lower = user_query.lower()

        # 1. Xác định Intent Type (Loại ý định)
        if any(w in query_lower for w in ["tại sao", "nguyên nhân", "lý do", "giảm do", "sụt giảm", "sao lại", "gốc rễ"]):
            intent_type = "DIAGNOSTIC_ROOT_CAUSE"
        elif any(w in query_lower for w in ["dự báo", "xu hướng", "sắp tới", "tuần sau", "tương lai"]):
            intent_type = "PREDICTIVE"
        else:
            intent_type = "DESCRIPTIVE"

        # 2. Bóc tách Vùng miền (Region)
        region = None
        if "miền nam" in query_lower or "phía nam" in query_lower:
            region = "Miền Nam"
        elif "miền bắc" in query_lower or "phía bắc" in query_lower:
            region = "Miền Bắc"
        elif "miền trung" in query_lower:
            region = "Miền Trung"
        elif "tây nguyên" in query_lower:
            region = "Tây Nguyên"

        # 3. Bóc tách Cửa hàng (Store)
        store_keyword = None
        for s in ["quận 1", "bình thạnh", "cần thơ", "cầu giấy", "hoàn kiếm", "hải phòng", "hải châu", "buôn ma thuột"]:
            if s in query_lower:
                store_keyword = s
                break

        # 4. Bóc tách Chỉ số KPI mục tiêu (Metrics mapping)
        target_metric = "net_revenue" # Mặc định
        if any(w in query_lower for w in ["lợi nhuận", "gross profit", "lãi"]):
            target_metric = "gross_profit"
        elif any(w in query_lower for w in ["đứt hàng", "hết hàng", "stockout", "stock out"]):
            target_metric = "out_of_stock_rate"
        elif any(w in query_lower for w in ["đơn hàng", "số đơn", "order count"]):
            target_metric = "order_count"
        elif any(w in query_lower for w in ["aov", "giá trị đơn trung bình"]):
            target_metric = "aov"
        elif any(w in query_lower for w in ["doanh thu", "sales", "revenue", "tiền"]):
            target_metric = "net_revenue"

        metric_info = self.metrics_def.get(target_metric, {
            "display_name": target_metric,
            "formula_sql": f"SUM({target_metric})",
            "unit": ""
        })

        # 5. Phân tách Khoảng thời gian (Time Range) & Kỳ đối chiếu (Baseline comparison)
        # Giả lập thời điểm hiện tại là 2026-11-16 (Đầu tuần 3)
        # Tuần qua (Current period): 2026-11-09 đến 2026-11-15
        # Tuần trước đó (Baseline period): 2026-11-02 đến 2026-11-08
        current_period = {
            "name": "Tuần phân tích (09/11 - 15/11/2026)",
            "start_date": "2026-11-09",
            "end_date": "2026-11-15"
        }
        baseline_period = {
            "name": "Tuần đối chiếu (02/11 - 08/11/2026)",
            "start_date": "2026-11-02",
            "end_date": "2026-11-08"
        }

        # 6. Tìm kiếm Few-shot memory tương tự
        similar_examples = self.memory.search_similar_queries(user_query, top_k=2)

        parsed_context = {
            "original_query": user_query,
            "user_role": user_role,
            "intent_type": intent_type,
            "target_metric": target_metric,
            "metric_info": metric_info,
            "region": region,
            "store_keyword": store_keyword,
            "current_period": current_period,
            "baseline_period": baseline_period,
            "similar_examples": [
                {"question": ex[1], "sql": ex[3]} for ex in similar_examples
            ],
            "relevant_tables": ["fact_sales", "dim_stores", "dim_products", "fact_store_traffic_weather"]
        }

        return parsed_context

