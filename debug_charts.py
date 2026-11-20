import pandas as pd
from core.agent_pipeline import EnterpriseAnalyticsAgent

agent = EnterpriseAnalyticsAgent()

# Case 1: Minimal 2-column CSV
df1 = pd.DataFrame({
    "Ngày": ["2026-11-01", "2026-11-02", "2026-11-03", "2026-11-04"],
    "Doanh thu": [1000000, 2000000, 1500000, 1200000]
})

try:
    res1 = agent.run("Phân tích", custom_df=df1)
    wf1 = res1.get("step5_waterfall")
    pr1 = res1.get("step5_pareto")
    fc1 = res1.get("step5_forecast")
    print("Case 1:")
    print("  Waterfall data len:", len(wf1.data[0].y) if wf1.data else 0, wf1.data[0].y if wf1.data else "None")
    print("  Pareto data len:", len(pr1.data))
    print("  Forecast data len:", len(fc1.data))
except Exception as e:
    print("Case 1 Error:", e)

# Case 2: Realistic retail CSV without region or store_id
df2 = pd.DataFrame({
    "Order_ID": [f"ORD-{i}" for i in range(10)],
    "Date": ["2026-11-01"]*5 + ["2026-11-02"]*5,
    "Store": ["Store A"]*5 + ["Store B"]*5,
    "Revenue": [50000, 60000, 70000, 80000, 90000, 40000, 30000, 20000, 10000, 5000]
})

try:
    res2 = agent.run("Phân tích", custom_df=df2)
    wf2 = res2.get("step5_waterfall")
    pr2 = res2.get("step5_pareto")
    fc2 = res2.get("step5_forecast")
    print("Case 2:")
    print("  Waterfall data len:", len(wf2.data[0].y) if wf2.data else 0, wf2.data[0].y if wf2.data else "None")
    print("  Pareto data len:", len(pr2.data))
    print("  Forecast data len:", len(fc2.data))
except Exception as e:
    print("Case 2 Error:", e)

