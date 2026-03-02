import streamlit as st
import pandas as pd
import plotly.express as px
import io

from data.loader import load_data
from data.preprocessing import create_features
from models.predictor import forecast_per_location
from config import (
    DEFAULT_SCENARIOS,
    STAFF_AVAILABILITY_PCT,
    FORECAST_HORIZON,
    STAFF_COST_PER_DAY,
)

# PDF
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet


# PAGE CONFIG
st.set_page_config(layout="wide", page_title="UAC Operational Dashboard")
st.title("UAC Operational Dashboard – Scenario Comparison")



# SIDEBAR SETTINGS
st.sidebar.header("Forecast Settings")

forecast_horizon = st.sidebar.slider(
    "Forecast Horizon (days)", 7, 30, FORECAST_HORIZON
)

staff_availability_pct = st.sidebar.slider(
    "Staff Availability (%)", 50, 150, STAFF_AVAILABILITY_PCT
)

staff_cost = st.sidebar.number_input(
    "Cost per Staff per Day", value=STAFF_COST_PER_DAY
)

upload_file = st.sidebar.file_uploader(
    "Upload CSV with daily UAC data", type="csv"
)


# LOAD DATA (ROBUST MODE)
df = load_data(upload_file)

if df is None or df.empty:
    st.error("No data loaded. Please upload a valid CSV.")
    st.stop()

# Clean column names
df.columns = df.columns.str.strip()

# Required base columns
required_columns = ["Date", "Location"]

# Auto-detect care load column
possible_load_columns = [
    "HHS Care Load",
    "Care Load",
    "HHS_Load",
    "Children",
    "Daily Load",
]

care_load_col = None
for col in possible_load_columns:
    if col in df.columns:
        care_load_col = col
        break

if care_load_col is None:
    st.error(
        "Care Load column not found. CSV must contain one of: "
        + ", ".join(possible_load_columns)
    )
    st.stop()

# Standardize name
df = df.rename(columns={care_load_col: "HHS Care Load"})

# Convert Date column
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

missing_required = [col for col in required_columns if col not in df.columns]
if missing_required:
    st.error(f"Missing required columns: {missing_required}")
    st.stop()

# Feature engineering
try:
    df_features = create_features(df)
except Exception as e:
    st.error(f"Feature engineering failed: {e}")
    st.stop()

# Forecasting
try:
    forecast_all = forecast_per_location(
        df_features,
        DEFAULT_SCENARIOS,
        staff_pct=staff_availability_pct,
        forecast_horizon=forecast_horizon,
        staff_cost=staff_cost,
    )
except Exception as e:
    st.error(f"Forecasting failed: {e}")
    st.stop()

if forecast_all.empty:
    st.error("Forecast could not be generated.")
    st.stop()


# KPI PANEL
st.subheader("📊 Forecast KPIs")

metrics = [
    "Forecast Accuracy (%)",
    "Forecast Stability Index (%)",
    "Capacity Breach Probability (%)",
    "Model Robustness",
]

kpi_cols = st.columns(len(metrics))

for i, metric in enumerate(metrics):
    value = forecast_all[metric].mean() if metric in forecast_all.columns else 0
    kpi_cols[i].metric(metric, f"{value:.2f}")



# REAL-TIME ALERTS
st.subheader("⚠️ Real-Time Capacity Alerts")

if "Status" in forecast_all.columns:
    alerts = forecast_all[forecast_all["Status"] == "SHORTAGE"]

    if not alerts.empty:
        for scenario in alerts["Scenario"].unique():
            scenario_alerts = alerts[alerts["Scenario"] == scenario]
            for loc in scenario_alerts["Location"].unique():
                loc_alerts = scenario_alerts[
                    scenario_alerts["Location"] == loc
                ]
                dates = ", ".join(
                    loc_alerts["Date"].dt.strftime("%Y-%m-%d")
                )
                st.warning(f"{loc} ({scenario}) exceeds capacity on {dates}")
    else:
        st.success("No projected capacity shortages.")


# LOAD FORECAST CHART
st.subheader("Scenario – HHS Care Load Forecast")

if "Forecasted HHS Care Load" in forecast_all.columns:
    fig_load = px.line(
        forecast_all,
        x="Date",
        y="Forecasted HHS Care Load",
        color="Location",
        line_dash="Scenario",
        title="Forecasted Children in HHS Care by Scenario",
    )
    st.plotly_chart(fig_load, use_container_width=True)



# CAPACITY GAP
st.subheader("Scenario – Capacity Gap Alerts")

if "Capacity Gap" in forecast_all.columns:
    fig_gap = px.bar(
        forecast_all,
        x="Date",
        y="Capacity Gap",
        color="Status",
        facet_col="Location",
        barmode="group",
        pattern_shape="Scenario",
        title="Capacity Gaps per Shelter",
    )
    st.plotly_chart(fig_gap, use_container_width=True)



# STAFFING FORECAST
st.subheader("Scenario – Staffing Recommendations")

if "Staff Required" in forecast_all.columns:
    fig_staff = px.line(
        forecast_all,
        x="Date",
        y=[
            "Staff Required",
            "Medical Staff Required",
            "Caseworkers Required",
        ],
        color="Location",
        line_dash="Scenario",
        title="Staffing Needs Forecast",
    )
    st.plotly_chart(fig_staff, use_container_width=True)



# RISK HEATMAP
st.subheader("🔥 Risk Heatmap – Capacity Stress")

if "Capacity Gap" in forecast_all.columns:
    fig_heatmap = px.density_heatmap(
        forecast_all,
        x="Date",
        y="Location",
        z="Capacity Gap",
        facet_col="Scenario",
        color_continuous_scale="Reds",
        title="Capacity Stress Heatmap",
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)


# COST ANALYSIS
st.subheader("💰 Cost Impact Analysis")

if "Staff Required" in forecast_all.columns:

    cost_df = forecast_all.copy()
    cost_df["Projected Staff Cost"] = (
        cost_df["Staff Required"] * staff_cost
    )

    cost_summary = (
        cost_df.groupby("Scenario")["Projected Staff Cost"]
        .sum()
        .reset_index()
    )

    st.dataframe(cost_summary)

    fig_cost = px.bar(
        cost_summary,
        x="Scenario",
        y="Projected Staff Cost",
        text_auto=True,
        title="Total Staffing Cost per Scenario",
    )
    st.plotly_chart(fig_cost, use_container_width=True)


# RISK SCORE INDEX
st.subheader("📈 Composite Risk Score Index")

if "Capacity Gap" in forecast_all.columns:

    risk_df = forecast_all.copy()

    risk_df["Gap Score"] = risk_df["Capacity Gap"].clip(lower=0)
    risk_df["Breach Score"] = risk_df.get(
        "Capacity Breach Probability (%)", 0
    )
    risk_df["Stability Risk"] = 100 - risk_df.get(
        "Forecast Stability Index (%)", 100
    )

    risk_df["Risk Score Index"] = (
        risk_df["Gap Score"] * 0.5
        + risk_df["Breach Score"] * 0.3
        + risk_df["Stability Risk"] * 0.2
    )

    risk_summary = (
        risk_df.groupby("Scenario")["Risk Score Index"]
        .mean()
        .reset_index()
    )

    st.dataframe(risk_summary)

    fig_risk = px.bar(
        risk_summary,
        x="Scenario",
        y="Risk Score Index",
        text_auto=True,
        title="Average Risk Score by Scenario",
    )
    st.plotly_chart(fig_risk, use_container_width=True)


# EXECUTIVE PDF
st.subheader("📄 Download Executive Summary PDF")


def generate_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(
        Paragraph("UAC Operational Executive Summary", styles["Title"])
    )
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("Key KPIs", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    for metric in metrics:
        value = (
            forecast_all[metric].mean()
            if metric in forecast_all.columns
            else 0
        )
        elements.append(
            Paragraph(f"{metric}: {value:.2f}", styles["Normal"])
        )

    doc.build(elements)
    buffer.seek(0)
    return buffer


pdf_file = generate_pdf()

st.download_button(
    label="Download Executive PDF",
    data=pdf_file,
    file_name="UAC_Executive_Summary.pdf",
    mime="application/pdf",
)


# DOWNLOAD FORECAST CSV
st.download_button(
    label="Download Scenario Forecast CSV",
    data=forecast_all.to_csv(index=False),
    file_name="uac_scenario_comparison_forecast.csv",
    mime="text/csv",
)