import pandas as pd
from datetime import datetime
import os

# ------------ Load Data ------------
def load_data():
    try:
        df = pd.read_csv("brand_sentiment_predictions.csv")
        sent_col = "predicted_sentiment"
    except:
        df = pd.read_csv("brand_sentiment_1000_clean.csv")
        sent_col = "sentiment"

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df, sent_col

df, sent_col = load_data()

# ------------ Basic Metrics ------------
total = len(df)
neg = int((df[sent_col] == "negative").sum())
neu = int((df[sent_col] == "neutral").sum())
pos = int((df[sent_col] == "positive").sum())

# Region worst
worst_region_html = "<p>No region column</p>"
if "region" in df.columns:
    region_tbl = df.groupby(["region", sent_col]).size().unstack(fill_value=0)
    region_tbl["negative_percent"] = (region_tbl.get("negative", 0) / region_tbl.sum(axis=1)) * 100
    worst = region_tbl.sort_values("negative_percent", ascending=False).head(5)
    worst_region_html = worst.to_html()

# Aspect worst
worst_aspect_html = "<p>No aspect column</p>"
if "aspect" in df.columns:
    asp_tbl = df.groupby(["aspect", sent_col]).size().unstack(fill_value=0)
    asp_tbl["negative_percent"] = (asp_tbl.get("negative", 0) / asp_tbl.sum(axis=1)) * 100
    worst_a = asp_tbl.sort_values("negative_percent", ascending=False).head(5)
    worst_aspect_html = worst_a.to_html()

# Trend (last 7 vs prev 7)
trend_html = "<p>No valid date</p>"
if "date" in df.columns and df["date"].notna().any():
    last_date = df["date"].max()
    last_7 = df[df["date"] >= last_date - pd.Timedelta(days=7)]
    prev_7 = df[(df["date"] < last_date - pd.Timedelta(days=7)) & (df["date"] >= last_date - pd.Timedelta(days=14))]

    last_7_neg = last_7[sent_col].value_counts(normalize=True).get("negative", 0) * 100
    prev_7_neg = prev_7[sent_col].value_counts(normalize=True).get("negative", 0) * 100
    change = last_7_neg - prev_7_neg

    trend_html = f"""
    <ul>
      <li>Last 7 days Negative %: <b>{last_7_neg:.2f}%</b></li>
      <li>Previous 7 days Negative %: <b>{prev_7_neg:.2f}%</b></li>
      <li>Change: <b>{change:.2f}%</b></li>
    </ul>
    """

# ------------ Build HTML ------------
today = datetime.now().strftime("%Y-%m-%d")
os.makedirs("reports", exist_ok=True)

report_html = f"""
<html>
<head>
  <meta charset="utf-8">
  <title>Daily Sentiment Report - {today}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    h1 {{ color: #222; }}
    .kpi {{ display: flex; gap: 15px; }}
    .box {{ padding: 12px; border: 1px solid #ddd; border-radius: 8px; width: 180px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; }}
    th {{ background: #f5f5f5; }}
  </style>
</head>
<body>
  <h1>📌 Daily Brand Sentiment Report - {today}</h1>

  <h2>1) KPI Summary</h2>
  <div class="kpi">
    <div class="box"><b>Total Records</b><br>{total}</div>
    <div class="box"><b>Negative</b><br>{neg}</div>
    <div class="box"><b>Neutral</b><br>{neu}</div>
    <div class="box"><b>Positive</b><br>{pos}</div>
  </div>

  <h2>2) Trend Summary</h2>
  {trend_html}

  <h2>3) Top Problem Regions</h2>
  {worst_region_html}

  <h2>4) Top Problem Aspects</h2>
  {worst_aspect_html}

  <p style="margin-top:30px;color:#666;">
    Generated automatically by Brand Sentiment Monitoring System.
  </p>
</body>
</html>
"""

out_path = f"reports/daily_report_{today}.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(report_html)

print("✅ Report generated:", out_path)