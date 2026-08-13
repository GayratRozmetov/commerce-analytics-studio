"""Streamlit entry point for Commerce Analytics Studio."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import (
    calculate_metrics,
    dimension_revenue,
    low_stock_products,
    prepare_data,
    product_performance,
    revenue_by_month,
)


APP_DIR = Path(__file__).parent

st.set_page_config(page_title="Commerce Analytics Studio", page_icon="📊", layout="wide")
st.markdown(
    """
    <style>
    .stApp {background:#f5f2ea; color:#171916;}
    [data-testid="stSidebar"] {background:#171916;}
    [data-testid="stSidebar"] * {color:#f5f2ea;}
    [data-testid="stMetric"] {background:#fff; border:1px solid #dedbd2; padding:18px; border-radius:16px;}
    h1,h2,h3 {letter-spacing:-.035em;}
    .hero {background:#171916;color:#fff;padding:32px;border-radius:22px;margin-bottom:22px;}
    .hero b {color:#c9ff36;letter-spacing:.12em;font-size:.76rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="hero"><b>PYTHON • DATA • COMMERCE</b>
    <h1>Commerce Analytics Studio</h1>
    <p>Turn raw sales files into clear decisions, performance signals and exportable reports.</p></div>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Data source")
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    st.caption("Your file is processed only for the current session.")
    threshold = st.slider("Low-stock threshold", 1, 100, 15)

try:
    if uploaded:
        raw = pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)
        source_label = uploaded.name
    else:
        raw = pd.read_csv(APP_DIR / "data" / "sample_sales.csv")
        source_label = "Built-in demo dataset"
    data = prepare_data(raw)
except Exception as exc:
    st.error(f"The dataset could not be analyzed: {exc}")
    st.stop()

st.caption(f"Source: {source_label} · {len(data):,} valid rows")

metrics = calculate_metrics(data)
columns = st.columns(4)
columns[0].metric("Revenue", f"${metrics.revenue:,.0f}")
columns[1].metric("Orders", f"{metrics.orders:,}")
columns[2].metric("Units sold", f"{metrics.units:,}")
columns[3].metric("Average order", f"${metrics.average_order_value:,.2f}")

st.subheader("Revenue performance")
trend = revenue_by_month(data)
st.plotly_chart(
    px.area(trend, x="month", y="revenue", markers=True, color_discrete_sequence=["#91b900"])
    .update_layout(xaxis_title=None, yaxis_title="Revenue ($)"),
    use_container_width=True,
)

left, right = st.columns(2)
with left:
    st.subheader("Top products")
    products = product_performance(data)
    st.plotly_chart(
        px.bar(products.head(10), x="revenue", y="product", orientation="h", color="revenue", color_continuous_scale="Greens")
        .update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False),
        use_container_width=True,
    )
with right:
    st.subheader("Revenue by country")
    countries = dimension_revenue(data, "country")
    st.plotly_chart(
        px.pie(countries, names="country", values="revenue", hole=.58, color_discrete_sequence=px.colors.sequential.Greens_r),
        use_container_width=True,
    )

tab1, tab2, tab3 = st.tabs(["Product intelligence", "Customers", "Data quality"])
with tab1:
    st.dataframe(products, use_container_width=True, hide_index=True)
    alerts = low_stock_products(data, threshold)
    if alerts.empty:
        st.success("No products are below the selected stock threshold.")
    else:
        st.warning(f"{len(alerts)} product(s) need inventory attention.")
        st.dataframe(alerts, use_container_width=True, hide_index=True)
with tab2:
    st.dataframe(dimension_revenue(data, "customer"), use_container_width=True, hide_index=True)
with tab3:
    st.write({"Original rows": len(raw), "Valid rows": len(data), "Rejected rows": len(raw) - len(data)})
    st.dataframe(data.tail(50), use_container_width=True, hide_index=True)

output = BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    data.to_excel(writer, sheet_name="Clean Data", index=False)
    products.to_excel(writer, sheet_name="Product Performance", index=False)
    countries.to_excel(writer, sheet_name="Country Revenue", index=False)

st.download_button(
    "Download Excel analysis",
    output.getvalue(),
    file_name="commerce-analytics-report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
)

st.caption("Portfolio demonstration · All built-in data is fictional.")
