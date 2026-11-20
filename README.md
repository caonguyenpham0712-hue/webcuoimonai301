# ĐỒ ÁN AI301: ENTERPRISE DATA BUSINESS ANALYST & ANALYTICS AGENT
> **Hệ Thống Trợ Lý Phân Tích Dữ Liệu Nghiệp Vụ & Tìm Nguyên Nhân Gốc Rễ Đa Chiều Chuẩn Doanh Nghiệp**

---

## 🌟 Giới Thiệu Tổng Quan
Hệ thống được phát triển nhằm đóng vai trò như một **Senior Data Business Analyst (BA) AI Agent**, hỗ trợ Ban Giám Đốc (BOD), các Quản lý Khối Vận hành và Chuỗi cung ứng giải quyết các bài toán hóc búa:
- Tự động bóc tách và phân tích ý định ngôn ngữ tự nhiên.
- Sinh SQL an toàn với các chốt chặn bảo mật cứng (**Guardrails**), chống SQL Injection và che dữ liệu cá nhân (**PII Masking**).
- Tự động kiểm định và cách ly dữ liệu bẩn (**Data Profiling & Quarantine**) trong Python Sandbox.
- Thực hiện thống kê chuyên sâu: Phân rã đóng góp (**Contribution Decomposition**), quy luật Pareto 80/20, tương quan Pearson với yếu tố ngoại cảnh (Mưa bão, Đứt hàng, Khách đến).
- Trực quan hóa tương tác (**Plotly Waterfall, Pareto, Trend Forecast**) và xuất báo cáo điều hành chuẩn Minto Pyramid.
- Đóng gói xuất file Excel đa sheet, kích hoạt cảnh báo chủ động và lưu trữ phản hồi vào bộ nhớ dài hạn (**Human-in-the-loop Memory Loop**).

---

## 🏗️ Cấu Trúc Thư Mục Dự Án

```text
BÀI CUỐI MÔN AI301/
├── config/
│   ├── semantic_catalog.yaml     # Từ điển dữ liệu doanh nghiệp & công thức KPI chuẩn
│   ├── rbac_policies.json        # Phân quyền vai trò (RBAC) & quy tắc che PII
│   └── alert_thresholds.json     # Ngưỡng kích hoạt cảnh báo rủi ro tự động
├── database/
│   ├── init_mock_dw.py           # Khởi tạo Data Warehouse mô phỏng (SQLite)
│   ├── enterprise_dw.db          # Cơ sở dữ liệu DW với >14,000 giao dịch
│   ├── memory_store.py           # Bộ nhớ dài hạn lưu Golden SQL & phản hồi chuyên gia
│   └── agent_memory.db           # SQLite Memory Store
├── core/
│   ├── __init__.py
│   ├── step1_intent_parser.py    # BƯỚC 1: Tiếp nhận ý định & Semantic Layer
│   ├── step2_secure_sql.py       # BƯỚC 2: AST Guardrail, PII Masking & Auto-retry SQL
│   ├── step3_data_quarantine.py  # BƯỚC 3: Python Sandbox Data Profiling & Quarantine
│   ├── step4_root_cause.py       # BƯỚC 4: Phân rã đóng góp, tương quan & dự báo
│   ├── step5_viz_summary.py      # BƯỚC 5: Biểu đồ Plotly & Báo cáo Minto Pyramid
│   ├── step6_delivery_feedback.py# BƯỚC 6: Cảnh báo, Xuất Excel & Human-in-the-loop
│   └── agent_pipeline.py         # Pipeline điều phối tổng hợp 6 bước
├── app.py                        # Giao diện Web tương tác hoàn chỉnh (Streamlit Localhost)
├── run_cli.py                    # Script kiểm thử trọn vẹn 6 bước qua dòng lệnh CLI
└── README.md                     # Tài liệu đồ án
```

---

## 🚀 Hướng Dẫn Khởi Chạy Trên Localhost

### 1. Cài đặt các thư viện cần thiết
```bash
pip install streamlit plotly pyyaml sqlglot pandas openpyxl
```

### 2. Khởi tạo Cơ sở Dữ liệu Data Warehouse mô phỏng
```bash
python database/init_mock_dw.py
```

### 3. Chạy kiểm thử nhanh qua Command Line (CLI)
```bash
python run_cli.py
```

### 4. Khởi chạy Giao Diện Web Dashboard Streamlit trên Localhost
```bash
streamlit run app.py
```
Sau khi chạy, trình duyệt web sẽ tự động mở tại địa chỉ:
👉 **`http://localhost:8501`**

---

## 📋 Chi Tiết 6 Bước Vận Hành Trong Hệ Thống

| Bước | Tên Module | Chức Năng Chính | Công Nghệ Sử Dụng |
|:---:|:---|:---|:---|
| **1** | **Intent & Context Parsing** | Bóc tách thực thể (thời gian, vùng miền, KPI mục tiêu), tra cứu từ điển dữ liệu Semantic Catalog, tìm kiếm Few-shot memory tương tự. | Python, PyYAML, Vector Token Matcher |
| **2** | **Planning & Secure Retrieval** | Lập kế hoạch truy vấn 3 tầng, kiểm duyệt AST chặn lệnh ghi/xóa (INSERT/UPDATE/DELETE/DROP), tự động che PII, ép điều kiện RBAC, cơ chế Auto-Retry. | SQLGlot AST, SQLite, PII Masker |
| **3** | **Data Profiling & Quarantine** | Đưa dữ liệu thô qua Sandbox để bắt lỗi doanh thu âm, null ID, trùng lặp hóa đơn; cách ly dữ liệu lỗi ra bảng riêng và tính điểm chất lượng DQ Score. | Python Pandas Sandbox |
| **4** | **Deep Analytics & Root-Cause** | Phân rã đóng góp (Contribution), kiểm định tương quan Pearson với yếu tố ngoại cảnh (Mưa ngập, lưu lượng khách), phân tích Pareto 80/20, dự báo 7 ngày. | Numpy, Scipy Thống kê |
| **5** | **Visualization & Summary** | Sinh biểu đồ động Waterfall (thác nước), Pareto, Line chart dự phóng phục hồi; sinh báo cáo điều hành chuẩn Minto Pyramid (Hiện trạng - Nguyên nhân - Đề xuất). | Plotly Graph Objects, Markdown Engine |
| **6** | **Delivery & Feedback Loop** | Đánh giá ngưỡng cảnh báo rủi ro tự động (Slack/Email/Banner), xuất file Excel đa sheet, thu thập đánh giá chuyên gia để cập nhật bộ nhớ dài hạn. | OpenPyXL, Memory Database |

---

## 🎯 Tình Huống Nghiệp Vụ Mẫu Đã Cài Đặt Sẵn
- **Câu hỏi:** *"Tại sao doanh thu Miền Nam tuần qua sụt giảm mạnh?"*
- **Hiện trạng:** Doanh thu Miền Nam giảm -23.76% (từ 642.6M xuống 489.9M VNĐ).
- **Nguyên nhân cốt lõi phát hiện:**
  1. Hai chi nhánh **Nova Mart Bình Thạnh** và **Nova Mart Quận 1** đóng góp hơn 84% vào tổng mức giảm.
  2. Thời tiết mưa bão ngập lụt 4 ngày liên tiếp kéo giảm 55% lưu lượng khách ghé cửa hàng ($r = -0.92$).
  3. Đứt hàng (Stock-out) sản phẩm chủ lực sữa tươi organic do chậm xe giao vận.
  4. Đã phát hiện và cách ly an toàn 5 dòng giao dịch bẩn (doanh thu âm và trùng mã hóa đơn).
- **Giải pháp:** Đề xuất 4 hành động chia theo cấp độ khẩn cấp (24h, 48h, 1 tuần) gắn trách nhiệm cho từng phòng ban.

