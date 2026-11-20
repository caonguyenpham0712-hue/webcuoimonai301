"""
CLI Runner để kiểm thử trọn vẹn 6 bước của AI Analytics Agent
"""

import sys
from core.agent_pipeline import EnterpriseAnalyticsAgent

def main():
    print("=" * 70)
    print("🚀 KHỞI ĐỘNG KIỂM THỬ ENTERPRISE BA DATA ANALYTICS AGENT")
    print("=" * 70)

    agent = EnterpriseAnalyticsAgent()
    query = "Tại sao doanh thu Miền Nam tuần qua sụt giảm mạnh?"
    role = "CEO"

    print(f"\n[USER QUERY]: {query}")
    print(f"[USER ROLE] : {role}\n")

    result = agent.run(user_query=query, user_role=role)

    print("\n--- NHẬT KÝ THỰC THI (PIPELINE LOGS) ---")
    for log in result["pipeline_log"]:
        print(log)

    print("\n--- BƯỚC 1: PARSED INTENT ---")
    p1 = result["step1_parsed_context"]
    print(f"Target Metric : {p1['target_metric']} ({p1['metric_info']['display_name']})")
    print(f"Region        : {p1['region']}")
    print(f"Current Period: {p1['current_period']['name']}")
    print(f"Baseline      : {p1['baseline_period']['name']}")

    print("\n--- BƯỚC 3: DATA PROFILING & QUARANTINE ---")
    dq = result["step3_dq_metrics"]
    print(f"Total Rows : {dq['total_records']:,}")
    print(f"Clean Rows : {dq['clean_records']:,}")
    print(f"Dirty Rows : {dq['dirty_records']:,} ({dq['dirty_percentage']}%)")
    print(f"DQ Score   : {dq['quality_score']}%")
    print(f"Breakdown  : {dq['error_breakdown']}")

    print("\n--- BƯỚC 4: DEEP ANALYTICS SUMMARY ---")
    kpi = result["step4_analytics"]["kpi_summary"]
    print(f"Baseline Revenue: {kpi['baseline_revenue']:,.0f} VND")
    print(f"Current Revenue : {kpi['current_revenue']:,.0f} VND")
    print(f"Growth Revenue  : {kpi['growth_revenue_pct']:+,.2f}%")
    print(f"Order Count     : {kpi['current_orders']} (Growth: {kpi['growth_orders_pct']:+,.2f}%)")

    print("\n--- BƯỚC 5: EXECUTIVE SUMMARY ---")
    print(result["step5_executive_summary"])

    print("\n--- BƯỚC 6: CẢNH BÁO CHỦ ĐỘNG (ALERTS) ---")
    for a in result["step6_alerts"]:
        print(f"[{a['level']}] {a['title']} -> {a['message']}")

    print("\n[SUCCESS] KIỂM THỬ THÀNH CÔNG TRỌN VẸN 6 BƯỚC!")

if __name__ == "__main__":
    main()

