"""
Tầng lưu trữ bộ nhớ dài hạn (Vector & Semantic Memory Store)
Lưu trữ các mẫu truy vấn đã được chuyên gia thẩm định (Golden SQL Examples),
lịch sử hội thoại và ghi nhận phản hồi (Human-in-the-loop Feedback Loop)
để tối ưu hóa độ chính xác theo thời gian.
"""

import os
import sqlite3
import json
from datetime import datetime

MEM_DIR = os.path.dirname(os.path.abspath(__file__))
MEM_DB_PATH = os.path.join(MEM_DIR, "agent_memory.db")

class AgentMemoryStore:
    def __init__(self, db_path=MEM_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bảng lưu trữ Golden SQL / Few-shot examples
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS golden_sql_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_question TEXT NOT NULL,
            parsed_intent TEXT NOT NULL,
            sql_query TEXT NOT NULL,
            verified_by TEXT DEFAULT 'EXPERT_BA',
            score REAL DEFAULT 1.0,
            created_at TEXT
        )
        """)

        # Bảng ghi nhận phản hồi người dùng (Feedback Loop)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            question TEXT,
            generated_sql TEXT,
            executive_summary TEXT,
            user_rating INTEGER, -- +1: Thumbs Up, -1: Thumbs Down
            user_comment TEXT,
            created_at TEXT
        )
        """)
        conn.commit()

        # Seed initial golden examples nếu chưa có
        cursor.execute("SELECT COUNT(*) FROM golden_sql_store")
        count = cursor.fetchone()[0]
        if count == 0:
            initial_examples = [
                (
                    "Doanh thu thuần của các vùng miền trong tuần qua như thế nào?",
                    json.dumps({"metric": "net_revenue", "dimension": "region", "time_range": "last_week"}),
                    """SELECT s.region, 
                              SUM(f.net_revenue) AS total_net_revenue,
                              COUNT(DISTINCT f.transaction_id) AS order_count
                       FROM fact_sales f
                       JOIN dim_stores s ON f.store_id = s.store_id
                       WHERE f.order_date >= '2026-11-09' AND f.order_date <= '2026-11-15'
                       GROUP BY s.region
                       ORDER BY total_net_revenue DESC;""",
                    "EXPERT_BA", 1.0, datetime.now().isoformat()
                ),
                (
                    "Top 5 sản phẩm bán chạy nhất tháng này",
                    json.dumps({"metric": "net_revenue", "dimension": "product", "limit": 5}),
                    """SELECT p.sku_code, p.product_name, p.category,
                              SUM(f.quantity) AS total_quantity,
                              SUM(f.net_revenue) AS total_net_revenue
                       FROM fact_sales f
                       JOIN dim_products p ON f.product_id = p.product_id
                       WHERE f.order_date >= '2026-11-01'
                       GROUP BY p.sku_code, p.product_name, p.category
                       ORDER BY total_net_revenue DESC
                       LIMIT 5;""",
                    "EXPERT_BA", 1.0, datetime.now().isoformat()
                ),
                (
                    "Tỷ lệ đứt hàng theo từng cửa hàng tại Miền Nam",
                    json.dumps({"metric": "out_of_stock_rate", "region": "Miền Nam"}),
                    """SELECT s.store_name,
                              COUNT(*) AS total_events,
                              SUM(f.out_of_stock_event) AS stockout_count,
                              ROUND(SUM(f.out_of_stock_event) * 100.0 / COUNT(*), 2) AS stockout_rate_pct
                       FROM fact_sales f
                       JOIN dim_stores s ON f.store_id = s.store_id
                       WHERE s.region = 'Miền Nam'
                       GROUP BY s.store_name
                       ORDER BY stockout_rate_pct DESC;""",
                    "EXPERT_BA", 1.0, datetime.now().isoformat()
                )
            ]
            cursor.executemany("""
            INSERT INTO golden_sql_store (user_question, parsed_intent, sql_query, verified_by, score, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, initial_examples)
            conn.commit()

        conn.close()

    def search_similar_queries(self, query_text: str, top_k: int = 2):
        """
        Tìm kiếm các mẫu SQL tương tự trong bộ nhớ dài hạn
        dựa trên độ tương đồng từ khóa (Jaccard & N-gram Token Similarity)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_question, parsed_intent, sql_query, score FROM golden_sql_store")
        rows = cursor.fetchall()
        conn.close()

        def tokenize(text):
            return set(text.lower().replace("?", "").replace(",", "").split())

        query_tokens = tokenize(query_text)
        scored = []
        for r in rows:
            example_tokens = tokenize(r[1])
            intersection = query_tokens.intersection(example_tokens)
            union = query_tokens.union(example_tokens)
            similarity = len(intersection) / len(union) if union else 0.0
            scored.append((similarity * r[4], r))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored[:top_k] if item[0] > 0.05]
        return results

    def save_feedback(self, conversation_id: str, question: str, generated_sql: str, summary: str, rating: int, comment: str = ""):
        """Ghi nhận phản hồi Human-in-the-loop vào bộ nhớ dài hạn"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO feedback_log (conversation_id, question, generated_sql, executive_summary, user_rating, user_comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (conversation_id, question, generated_sql, summary, rating, comment, datetime.now().isoformat()))
        
        # Nếu người dùng đánh giá tốt (+1), cân nhắc lưu vào Golden SQL
        if rating > 0:
            cursor.execute("""
            INSERT INTO golden_sql_store (user_question, parsed_intent, sql_query, verified_by, score, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (question, "USER_APPROVED_FEEDBACK", generated_sql, "USER_FEEDBACK", 1.0, datetime.now().isoformat()))

        conn.commit()
        conn.close()
        return True

