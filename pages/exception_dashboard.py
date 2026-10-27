from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Demand Exception Report", layout="wide")


# ==========================================================
# CONFIG
# ==========================================================

DATA_DIR = Path(__file__).resolve().parents[1] / "data/raw"
K = 1.5          # band width in standard deviations
WINDOW = 6       # rolling window for the regression input and enquiry baseline (months)
MIN_HIST = 3     # minimum prior months needed for a prediction

C_ACTUAL = "#386FE5"
C_LR = "#8980DA"
C_FLAG = "#E5484D"
# ==========================================================
# PAGE DESIGN (matches regional_analytics.py)
# ==========================================================

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background: #f5f7fb !important;
        color: #253249 !important;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3,
    [data-testid="stMain"] p,
    [data-testid="stMain"] label { color: #253249; }
    [data-testid="stMain"] [data-testid="stCaptionContainer"] p {
        color: #718096 !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: transparent !important;
        border-color: #dce4ef !important;
        border-radius: 14px !important;
        box-shadow: none !important;
    }
    [data-testid="stMetric"] {
        background: transparent !important;
        border: 1px solid #dce4ef !important;
        border-radius: 14px !important;
        padding: 18px 14px !important;
        min-width: 0 !important;
    }
    [data-testid="stMetricLabel"] p {
        font-size: 13px !important;
        color: #69788e !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: clamp(20px, 2.1vw, 30px) !important;
        color: #253249 !important;
        line-height: 1.25 !important;
    }
    [data-baseweb="select"] > div {
        background: rgba(255,255,255,.7) !important;
        border: 1px solid #dce4ef !important;
        border-radius: 10px !important;
        color: #253249 !important;
    }
    [data-baseweb="select"] div,
    [data-baseweb="select"] span { color: #253249 !important; }
    .lf-table-wrap { width: 100%; overflow-x: auto; margin-top: 14px; }
    .lf-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        color: #253249;
    }
    .lf-table th {
        color: #66758c;
        text-align: left;
        padding: 13px 12px;
        border-bottom: 1px solid #cfd9e7;
        white-space: nowrap;
    }
    .lf-table td {
        color: #253249;
        padding: 12px;
        border-bottom: 1px solid #e0e8f1;
        white-space: nowrap;
    }
    .lf-table tr:hover td { background: rgba(56,111,229,.06) !important; }
    .lf-eyebrow {
        font-size: 12px;
        font-weight: 700;
        color: #386fe5;
        letter-spacing: 1.4px;
        margin-bottom: 6px;
    }
    .lf-title {
        color: #253249;
        font-size: 17px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .lf-subtitle {
        color: #718096;
        font-size: 13px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# HELPERS
# ==========================================================

def chart_style(fig, height=340):
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color="#253249", size=12),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#253249"),
            orientation="h",
            y=-0.25,
        ),
        margin=dict(l=10, r=35, t=20, b=60),
        autosize=True,
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="#66758c"),
        automargin=True,
    )
    fig.update_yaxes(
        gridcolor="rgba(102,117,140,.13)",
        zeroline=False,
        tickfont=dict(color="#66758c"),
        automargin=True,
    )
    return fig


def show_plot(fig, height=340):
    st.plotly_chart(
        chart_style(fig, height),
        use_container_width=True,
        config={"displayModeBar": False},
    )


def section_title(title, subtitle=None):
    st.markdown(
        f'<div class="lf-title">{escape(title)}</div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<div class="lf-subtitle">{escape(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def show_table(df, formats=None):
    if df.empty:
        st.info("No matching records for this selection.")
        return

    view = df.copy()
    for column, fmt in (formats or {}).items():
        if column in view.columns:
            view[column] = view[column].map(
                lambda x: fmt(x) if pd.notna(x) else "—"
            )

    header = "".join(f"<th>{escape(str(c))}</th>" for c in view.columns)
    rows = []
    for record in view.itertuples(index=False, name=None):
        cells = "".join(
            f"<td>{escape(str(v)) if pd.notna(v) else '—'}</td>"
            for v in record
        )
        rows.append(f"<tr>{cells}</tr>")

    st.markdown(
        '<div class="lf-table-wrap"><table class="lf-table">'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>",
        unsafe_allow_html=True,
    )


# ==========================================================
# DATA AND FORECASTS
# ==========================================================

@st.cache_data(show_spinner="Building forecasts...")
def build_dataset():
    md = pd.read_csv(DATA_DIR / "monthly_demand.csv")
    md["month"] = pd.to_datetime(md["month"]).dt.strftime("%Y-%m")
    osm = pd.read_csv(DATA_DIR / "order_status_monthly.csv")
    osm["month"] = pd.to_datetime(osm["month"]).dt.strftime("%Y-%m")

    keys = ["country", "product_group"]
    if "business_entity" in md.columns:
        keys.insert(1, "business_entity")

    md = md.sort_values(keys + ["month"]).reset_index(drop=True)
    g = md.groupby(keys)["confirmed_units"]
    md["lag1"] = g.shift(1)
    md["lag2"] = g.shift(2)
    md["lag3"] = g.shift(3)
    # Rolling mean used only as a regression input
    md["roll6"] = g.transform(
        lambda s: s.shift(1).rolling(WINDOW, min_periods=MIN_HIST).mean()
    )
    md["month_num"] = pd.to_datetime(md["month"]).dt.month

    # Linear regression: walk-forward, trained only on earlier months.
    # Month dummies replace month_num so December and January are not neighbours.
    feat = md.dropna(subset=["lag1", "lag2", "lag3"]).copy()
    series_d = pd.get_dummies(feat[keys], dtype=int)
    month_d = pd.get_dummies(feat["month_num"], prefix="m", dtype=int).reindex(
        columns=[f"m_{i}" for i in range(1, 13)], fill_value=0
    )
    X = pd.concat(
        [feat[["lag1", "lag2", "lag3", "roll6"]], month_d, series_d],
        axis=1,
    )
    y = feat["confirmed_units"]
    feat["lr_pred"] = np.nan
    for m in sorted(feat["month"].unique()):
        train = feat["month"] < m
        test = feat["month"] == m
        if not train.any():
            continue
        model = LinearRegression().fit(X[train], y[train])
        feat.loc[test, "lr_pred"] = model.predict(X[test])
    md["lr_pred"] = feat["lr_pred"]

    # Bands: sigma from residuals of PRIOR months only
    md["lr_resid"] = md["confirmed_units"] - md["lr_pred"]
    md["lr_sigma"] = md.groupby(keys)["lr_resid"].transform(
        lambda s: s.shift(1).expanding(min_periods=MIN_HIST).std()
    )
    md["lr_lower"] = md["lr_pred"] - K * md["lr_sigma"]
    md["lr_upper"] = md["lr_pred"] + K * md["lr_sigma"]

    # Enquiry spikes on a full monthly grid (zeros where none)
    enq = (
        osm[osm["order_status"] == "Enquiry"]
        .groupby(["month"] + keys)["units"].sum()
        .reset_index()
    )
    grid = md[keys].drop_duplicates().merge(
        pd.DataFrame({"month": sorted(md["month"].unique())}),
        how="cross",
    )
    enq = grid.merge(enq, on=["month"] + keys, how="left")
    enq["units"] = enq["units"].fillna(0)
    enq = enq.sort_values(keys + ["month"])
    ge = enq.groupby(keys)["units"]
    enq["enq_mean"] = ge.transform(
        lambda s: s.shift(1).rolling(WINDOW, min_periods=MIN_HIST).mean()
    )
    enq["enq_std"] = ge.transform(
        lambda s: s.shift(1).rolling(WINDOW, min_periods=MIN_HIST).std()
    )
    enq["enq_flag"] = (
        (enq["units"] - enq["enq_mean"]) / enq["enq_std"]
    ).abs() > K

    md = md.merge(
        enq[["month"] + keys + ["units", "enq_flag"]]
        .rename(columns={"units": "enquiry_units"}),
        on=["month"] + keys,
        how="left",
    )
    md["enq_flag"] = md["enq_flag"].fillna(False).astype(bool)

    # Exception flag: outside LR band OR enquiry spike
    md["lr_breach"] = (
        (md["confirmed_units"] < md["lr_lower"])
        | (md["confirmed_units"] > md["lr_upper"])
    )
    md["lr_flag"] = md["lr_breach"] | md["enq_flag"]

    return md, keys
md, keys = build_dataset()

def series_label(frame):
    return frame[keys].astype(str).agg(" | ".join, axis=1)

COUNTRY_CODES = {
    "Singapore": "SG",
    "Indonesia": "IND",
    "Malaysia": "MY",
    "Thailand": "TH",
    "Vietnam": "VN",
}


def short_label(frame):
    code = frame["country"].astype(str).map(
        lambda c: COUNTRY_CODES.get(c, c[:3].upper())
    )
    product = frame["product_group"].astype(str).str.replace(
        "Product ", "", regex=False
    )
    return code + "-" + product

# ==========================================================
# HEADER
# ==========================================================

st.markdown(
    '<div class="lf-eyebrow">LIVESFLOW / DEMAND EXCEPTION REPORT</div>',
    unsafe_allow_html=True,
)
st.title("Demand Exception Report")
st.caption(
    f"Historical backtest. A series is flagged when actual units fall "
    f"outside ±{K}σ of its forecast, or when enquiries spike."
)


# ==========================================================
# FILTERS (top of page)
# ==========================================================

months = sorted(md["month"].unique().tolist())

f1, f2, f3, f4 = st.columns(4)

with f1:
    country = st.selectbox(
        "Country",
        ["All Countries"] + md["country"].unique().tolist(),
    )

with f2:
    product = st.selectbox(
        "Product",
        ["All Products"] + md["product_group"].unique().tolist(),
    )

with f3:
    month = st.selectbox("Month", months, index=len(months) - 1)

with f4:
    hide_flagged = st.toggle(
        "Remove flagged series",
        value=False,
        help="Hides series flagged for the selected month from the charts.",
    )

df = md.copy()
if country != "All Countries":
    df = df[df["country"] == country]
if product != "All Products":
    df = df[df["product_group"] == product]

month_df = df[df["month"] == month].copy()
month_df["label"] = short_label(month_df)

if month_df.empty:
    st.info("No data for this month with the current filters.")
    st.stop()


# ==========================================================
# KPI CARDS
# ==========================================================

scored = month_df[month_df["lr_pred"].notna()]
lr_mae = (
    (scored["confirmed_units"] - scored["lr_pred"]).abs().mean()
    if len(scored) else np.nan
)

k1, k2, k3 = st.columns(3)
k1.metric("Series", len(month_df))
k2.metric("Flagged", int(month_df["lr_flag"].sum()))
k3.metric("Enquiry spikes", int(month_df["enq_flag"].sum()))


# ==========================================================
# FORECAST CHART
# ==========================================================

def forecast_bars():
    view = month_df[month_df["lr_pred"].notna()].copy()
    if hide_flagged:
        view = view[~view["lr_flag"]]
    if view.empty:
        st.info("No series to show after removing flagged series.")
        return

    view = view.sort_values("label")
    x = view["label"] + np.where(view["lr_flag"], "*", "")
    err = (K * view["lr_sigma"]).fillna(0).tolist()

    fig = go.Figure()
    fig.add_bar(
        x=x, y=view["confirmed_units"],
        name="Actual", marker_color=C_ACTUAL,
    )
    fig.add_bar(
        x=x, y=view["lr_pred"],
        name="Linear regression forecast", marker_color=C_LR,
        error_y=dict(type="data", array=err, color=C_FLAG, thickness=1.2),
    )
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Units")
    fig.update_xaxes(tickangle=45)
    show_plot(fig, height=420)


with st.container(border=True):
    section_title(
        "Linear Regression",
        f"Actual vs forecast for {month}. * = flagged. Red bars show ±{K}σ.",
    )
    forecast_bars()


# ==========================================================
# FLAGGED SERIES TABLE
# ==========================================================

with st.container(border=True):
    section_title(f"Flagged Series, {month}")

    flagged = month_df[month_df["lr_flag"]].copy()

    if flagged.empty:
        st.info("No series flagged for this month.")
    else:
        table = pd.DataFrame({
            "Series": flagged["label"],
            "Actual Units": flagged["confirmed_units"],
            "LR Forecast": flagged["lr_pred"],
            "Outside Band": np.where(flagged["lr_breach"], "Yes", "No"),
            "Enquiry Spike": np.where(flagged["enq_flag"], "Yes", "No"),
        })
        show_table(
            table,
            formats={
                "Actual Units": lambda x: f"{x:,.0f}",
                "LR Forecast": lambda x: f"{x:,.1f}",
            },
        )

# ==========================================================
# TREND FOR ONE SERIES
# ==========================================================
with st.container(border=True):
    section_title(
        "Trend for One Series",
        "Actual units against the linear regression forecast across all months.",
    )

    ts_df = df.copy()
    ts_df["label"] = series_label(ts_df)
    options = sorted(ts_df["label"].unique().tolist())

    if not options:
        st.info("No series match the filters.")
    else:
        choice = st.selectbox("Series", options)
        ts = ts_df[ts_df["label"] == choice].sort_values("month")

        fig = go.Figure()

        # Band: upper line first, then lower line filled up to it
        fig.add_scatter(
            x=ts["month"], y=ts["lr_upper"], mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        )
        fig.add_scatter(
            x=ts["month"], y=ts["lr_lower"], mode="lines",
            line=dict(width=0), fill="tonexty",
            fillcolor="rgba(137,128,218,0.15)",
            name=f"±{K}σ band",
        )

        fig.add_scatter(
            x=ts["month"], y=ts["confirmed_units"], mode="lines+markers",
            name="Actual", line=dict(color=C_ACTUAL, width=2.5),
        )
        fig.add_scatter(
            x=ts["month"], y=ts["lr_pred"], mode="lines+markers",
            name="Linear Regression", line=dict(color=C_LR, dash="dash"),
        )

        breach = ts[ts["lr_breach"]]
        fig.add_scatter(
            x=breach["month"], y=breach["confirmed_units"],
            mode="markers", name="Outside band (LR)",
            marker=dict(color=C_FLAG, size=11, symbol="x"),
        )

        spike = ts[ts["enq_flag"]]
        fig.add_scatter(
            x=spike["month"], y=spike["confirmed_units"],
            mode="markers", name="Enquiry spike",
            marker=dict(color="#F5A623", size=11, symbol="diamond"),
        )
        show_plot(fig, height=340)

# ==========================================================
# FLAGGED SERIES TABLE
# ==========================================================

with st.container(border=True):
    section_title(f"Flagged Series, {month}")

    flagged = month_df[month_df["lr_flag"]].copy()

    if flagged.empty:
        st.info("No series flagged for this month.")
    else:
        table = pd.DataFrame({
            "Series": flagged["label"],
            "Actual Units": flagged["confirmed_units"],
            "LR Forecast": flagged["lr_pred"],
            "Outside Band": np.where(flagged["lr_breach"], "Yes", "No"),
            "Enquiry Spike": np.where(flagged["enq_flag"], "Yes", "No"),
        })
        show_table(
            table,
            formats={
                "Actual Units": lambda x: f"{x:,.0f}",
                "LR Forecast": lambda x: f"{x:,.1f}",
            },
        )

st.caption(
    "Synthetic competition dataset. Not actual Lives Group data."
)
