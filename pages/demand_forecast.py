from pathlib import Path
from html import escape

import lightgbm as lgb
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import xgboost as xgb
from sklearn.linear_model import LinearRegression


# ==========================================================
# LIVESFLOW — DEMAND FORECAST
# Two tabs: Backtest, Six-Month Forecast
# ==========================================================

DATA_DIR = Path(__file__).resolve().parents[1] / "data/raw"

WINDOW = 6      # moving-average window (company practice)
HORIZON = 6     # forward forecast months
N_TEST = 6      # walk-forward backtest months

MODELS = [
    "Moving average (6M)",
    "Linear regression",
    "XGBoost",
    "LightGBM",
]

MODEL_COLORS = {
    "Moving average (6M)": "#2BAFA9",
    "Linear regression": "#8980DA",
    "XGBoost": "#F5A623",
    "LightGBM": "#66758c",
}

C_ACTUAL = "#386FE5"


# ==========================================================
# PAGE DESIGN
# ==========================================================

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background: #f5f7fb !important;
        color: #253249 !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3,
    [data-testid="stMain"] p,
    [data-testid="stMain"] label {
        color: #253249;
    }

    [data-testid="stMain"] [data-testid="stCaptionContainer"] p {
        color: #718096 !important;
    }

    /* Navy sidebar */
    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"] {
        background: #14243b !important;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] label {
        color: #e9f0fa !important;
    }

    /* Transparent chart containers */
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: transparent !important;
        box-shadow: none !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-color: #dce4ef !important;
        border-radius: 14px !important;
    }

    /* Transparent KPI cards */
    [data-testid="stMetric"] {
        background: transparent !important;
        border: 1px solid #dce4ef !important;
        border-radius: 14px !important;
        padding: 17px 12px !important;
        min-width: 0 !important;
        box-shadow: none !important;
    }

    [data-testid="stMetricLabel"] p {
        font-size: 13px !important;
        color: #69788e !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"] {
        font-size: clamp(18px, 1.8vw, 27px) !important;
        color: #253249 !important;
        line-height: 1.25 !important;
        min-width: 0 !important;
    }

    [data-testid="stMetricValue"] > div {
        color: #253249 !important;
        font-size: inherit !important;
        white-space: nowrap !important;
    }

    /* Two clickable tabs */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: transparent !important;
        gap: 8px !important;
        border-bottom: 1px solid #dce4ef !important;
    }

    [data-testid="stTabs"] button[data-baseweb="tab"] {
        color: #66758c !important;
        background: transparent !important;
        padding: 12px 17px !important;
        border-radius: 8px 8px 0 0 !important;
        font-weight: 600 !important;
    }

    [data-testid="stTabs"] button[data-baseweb="tab"] *,
    [data-testid="stTabs"] button[data-baseweb="tab"] p {
        color: #66758c !important;
        opacity: 1 !important;
    }

    [data-testid="stTabs"]
    button[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(56,111,229,0.07) !important;
        color: #386fe5 !important;
    }

    [data-testid="stTabs"]
    button[data-baseweb="tab"][aria-selected="true"] *,
    [data-testid="stTabs"]
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #386fe5 !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        background: #386fe5 !important;
    }

    /* Simple dropdown filters */
    [data-baseweb="select"] > div {
        background: rgba(255,255,255,0.7) !important;
        border: 1px solid #dce4ef !important;
        border-radius: 10px !important;
    }

    [data-baseweb="select"] div,
    [data-baseweb="select"] span {
        color: #253249 !important;
    }

    /* Transparent HTML tables */
    .lf-table-wrap {
        width: 100%;
        overflow-x: auto;
        background: transparent !important;
        margin-top: 12px;
    }

    .lf-table {
        width: 100%;
        border-collapse: collapse;
        background: transparent !important;
        color: #253249;
        font-size: 13px;
    }

    .lf-table thead,
    .lf-table tbody,
    .lf-table tr,
    .lf-table th,
    .lf-table td {
        background: transparent !important;
    }

    .lf-table th {
        color: #66758c;
        text-align: left;
        font-weight: 650;
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

    .lf-table tbody tr:hover td {
        background: rgba(56,111,229,0.06) !important;
    }

    .lf-eyebrow {
        color: #386fe5;
        font-size: 12px;
        font-weight: 700;
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
# LOAD DATA
# ==========================================================

@st.cache_data(show_spinner=False)
def load_demand():

    md = pd.read_csv(DATA_DIR / "monthly_demand.csv")

    required = ["month", "country", "product_group", "confirmed_units"]
    missing = [c for c in required if c not in md.columns]
    if missing:
        raise ValueError("Missing demand columns: " + ", ".join(missing))

    md["month"] = (
        pd.to_datetime(md["month"], errors="coerce")
        .dt.to_period("M")
        .dt.to_timestamp()
    )
    md = md.dropna(subset=["month"])

    keys = [c for c in ["country", "business_entity", "product_group"] if c in md.columns]

    md = (
        md.groupby(keys + ["month"], as_index=False)["confirmed_units"]
        .sum()
        .sort_values(keys + ["month"])
        .reset_index(drop=True)
    )
    md["ym"] = md["month"].dt.strftime("%Y-%m")

    return md, keys


try:
    md, keys = load_demand()

except (
    FileNotFoundError,
    KeyError,
    ValueError,
    pd.errors.ParserError,
) as error:
    st.error(f"Error loading CSV files: {error}")
    st.stop()


# ==========================================================
# MODEL HELPERS
# ==========================================================

def build_features(df, keys):
    """Lags, a 6-month rolling mean, month dummies (Dec and Jan are not neighbours), and series dummies."""

    df = df.sort_values(keys + ["month"]).copy()
    g = df.groupby(keys)["confirmed_units"]

    df["lag1"] = g.shift(1)
    df["lag2"] = g.shift(2).fillna(df["lag1"])
    df["lag3"] = g.shift(3).fillna(df["lag2"])
    df["roll6"] = g.transform(
        lambda s: s.shift(1).rolling(WINDOW, min_periods=1).mean()
    )

    month_d = pd.get_dummies(df["month"].dt.month, prefix="m", dtype=int)
    month_d = month_d.reindex(
        columns=[f"m_{i}" for i in range(1, 13)], fill_value=0
    )
    series_d = pd.get_dummies(df[keys], dtype=int)

    X = pd.concat(
        [df[["lag1", "lag2", "lag3", "roll6"]], month_d, series_d],
        axis=1,
    )
    return df, X


def fit_model(name, X, y):
    if name == "Linear regression":
        return LinearRegression().fit(X, y)
    if name == "XGBoost":
        return xgb.XGBRegressor(
            n_estimators=100, max_depth=2, learning_rate=0.1,
            objective="reg:squarederror", random_state=42,
        ).fit(X, y)
    if name == "LightGBM":
        return lgb.LGBMRegressor(
            n_estimators=100, max_depth=2, learning_rate=0.1,
            min_child_samples=5, random_state=42, verbose=-1,
        ).fit(X, y)
    return None  # moving average needs no fitting


def predict(name, model, X, roll6):
    if name == "Moving average (6M)":
        return roll6.to_numpy()
    return np.clip(model.predict(X), 0, None)


@st.cache_data(show_spinner=False)
def run_backtest(md, keys):
    """Walk-forward backtest: each model is retrained before every test month."""

    test_months = sorted(md["ym"].unique())[-N_TEST:]
    df, X = build_features(md, keys)
    usable = df["lag1"].notna()
    rows = []

    for tm in test_months:
        train = usable & (df["ym"] < tm)
        test = usable & (df["ym"] == tm)
        if train.sum() == 0 or test.sum() == 0:
            continue

        for name in MODELS:
            model = fit_model(name, X.loc[train], df.loc[train, "confirmed_units"])
            pred = predict(name, model, X.loc[test], df.loc[test, "roll6"])

            out = (
                df.loc[test, keys + ["ym", "confirmed_units"]]
                .rename(columns={"ym": "forecast_month", "confirmed_units": "actual_units"})
                .copy()
            )
            out["model"] = name
            out["predicted_units"] = pred
            out["err"] = out["predicted_units"] - out["actual_units"]
            out["abs_err"] = out["err"].abs()
            rows.append(out)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def summarise(res):
    g = res.groupby("model")
    out = pd.DataFrame({
        "MAE (units)": g["abs_err"].mean(),
        "WAPE %": g["abs_err"].sum() / g["actual_units"].sum() * 100,
        "Bias (units)": g["err"].mean(),
        "Rows scored": g.size(),
    }).reset_index()
    return out.sort_values("WAPE %").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def forecast_forward(md, keys, model_name):
    """Recursive forecast: each predicted month feeds the next."""

    df_hist, X_hist = build_features(md, keys)
    usable = df_hist["lag1"].notna()
    cols = X_hist.columns
    model = fit_model(model_name, X_hist.loc[usable], df_hist.loc[usable, "confirmed_units"])

    last = md["month"].max()
    future = [last + pd.DateOffset(months=i) for i in range(1, HORIZON + 1)]

    series = md[keys].drop_duplicates()
    placeholders = series.merge(pd.DataFrame({"month": future}), how="cross")
    placeholders["confirmed_units"] = np.nan
    ext = pd.concat(
        [md[keys + ["month", "confirmed_units"]], placeholders],
        ignore_index=True,
    )

    for fm in future:
        df_e, X_e = build_features(ext, keys)
        X_e = X_e.reindex(columns=cols, fill_value=0)
        mask = df_e["month"] == fm
        pred = predict(model_name, model, X_e.loc[mask], df_e.loc[mask, "roll6"])
        ext.loc[df_e.index[mask], "confirmed_units"] = pred

    out = ext[ext["month"].isin(future)].copy()
    out["forecast_month"] = out["month"].dt.strftime("%Y-%m")
    out["predicted_units"] = out["confirmed_units"].round(1)
    out["model"] = model_name
    out["training_through"] = last.strftime("%Y-%m")

    return out[keys + ["forecast_month", "predicted_units", "model", "training_through"]]


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def compact_number(value):
    """Short numbers to fit neatly in KPI cards."""

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K"

    return f"{value:,.0f}"


def chart_style(fig, height=340):
    """Transparent Plotly chart with readable dark text."""

    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color="#253249", size=12),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#253249", size=12),
            orientation="h",
            y=-0.25,
        ),
        margin=dict(l=10, r=35, t=20, b=35),
        autosize=True,
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="#66758c"),
        title_font=dict(color="#66758c"),
        automargin=True,
    )

    fig.update_yaxes(
        gridcolor="rgba(102,117,140,0.13)",
        zeroline=False,
        tickfont=dict(color="#66758c"),
        title_font=dict(color="#66758c"),
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
            f'<div class="lf-subtitle">'
            f'{escape(subtitle)}'
            f'</div>',
            unsafe_allow_html=True,
        )


def show_table(df, formats=None):
    """Display a transparent HTML table."""

    if df.empty:
        st.info("No matching records for this selection.")
        return

    view = df.copy()

    for column, formatter in (formats or {}).items():
        if column in view.columns:
            view[column] = view[column].map(
                lambda value: (
                    formatter(value)
                    if pd.notna(value)
                    else "—"
                )
            )

    header = "".join(
        f"<th>{escape(str(column))}</th>"
        for column in view.columns
    )

    rows = []

    for record in view.itertuples(index=False, name=None):
        cells = "".join(
            f"<td>{escape(str(value)) if pd.notna(value) else '—'}</td>"
            for value in record
        )
        rows.append(f"<tr>{cells}</tr>")

    st.markdown(
        '<div class="lf-table-wrap">'
        '<table class="lf-table">'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>",
        unsafe_allow_html=True,
    )


# ==========================================================
# PAGE HEADER
# ==========================================================

st.markdown(
    '<div class="lf-eyebrow">'
    'LIVESFLOW / DEMAND FORECAST'
    '</div>',
    unsafe_allow_html=True,
)

st.title("Demand Forecast")

st.caption(
    "Walk-forward backtest of four models, then a six-month forward "
    "forecast from the best performer."
)


# ==========================================================
# SHARED FILTERS
# ==========================================================

f1, f2 = st.columns(2)

with f1:
    selected_country = st.selectbox(
        "Country",
        ["All Countries"] + sorted(md["country"].dropna().unique().tolist()),
    )

with f2:
    selected_product = st.selectbox(
        "Product",
        ["All Products"] + sorted(md["product_group"].dropna().unique().tolist()),
    )


def scoped(frame):
    out = frame
    if selected_country != "All Countries":
        out = out[out["country"] == selected_country]
    if selected_product != "All Products":
        out = out[out["product_group"] == selected_product]
    return out


# ==========================================================
# RUN MODELS AND KPI CARDS
# ==========================================================

res_all = run_backtest(md, keys)

if res_all.empty:
    st.error(
        "Not enough history to run a backtest. "
        "Each series needs at least two months of data."
    )
    st.stop()

summary_all = summarise(res_all)
best_model = summary_all.iloc[0]["model"]
best_wape = summary_all.iloc[0]["WAPE %"]
last_actual = md["ym"].max()
test_months = sorted(res_all["forecast_month"].unique())

k1, k2, k3, k4 = st.columns(4)
k1.metric("Best model", best_model)
k2.metric("Best WAPE", f"{best_wape:.1f}%")
k3.metric("Last actual month", last_actual)
k4.metric("Forecast horizon", f"{HORIZON} months")


# ==========================================================
# TABS
# ==========================================================

tab1, tab2 = st.tabs(["Backtest", "Six-Month Forecast"])


# ----------------------------------------------------------
# TAB 1 — BACKTEST
# ----------------------------------------------------------

with tab1:

    st.write("")

    res_scope = scoped(res_all)
    summary = summarise(res_scope) if not res_scope.empty else pd.DataFrame()

    with st.container(border=True):

        section_title(
            "Model Comparison",
            f"Walk-forward backtest, {test_months[0]} to {test_months[-1]}. "
            f"Lowest WAPE ranks first. Best model across all data: {best_model}.",
        )

        left, right = st.columns(2, gap="large")

        with left:

            show_table(
                summary,
                formats={
                    "MAE (units)": lambda x: f"{x:,.1f}",
                    "WAPE %": lambda x: f"{x:,.1f}",
                    "Bias (units)": lambda x: f"{x:+,.1f}",
                    "Rows scored": lambda x: f"{x:,.0f}",
                },
            )

        with right:

            if not summary.empty:

                fig = go.Figure(
                    go.Bar(
                        x=summary["model"],
                        y=summary["WAPE %"],
                        marker_color=[MODEL_COLORS[m] for m in summary["model"]],
                        text=summary["WAPE %"].round(1),
                        textposition="outside",
                    )
                )
                fig.update_yaxes(title_text="WAPE %")
                show_plot(fig, height=320)

            else:

                st.info("No backtest rows for this selection.")

    with st.container(border=True):

        section_title(
            "Monthly Error by Model",
            "Mean absolute error per test month. Lower is better.",
        )

        monthly = (
            res_scope.groupby(["forecast_month", "model"], as_index=False)["abs_err"]
            .mean()
        )

        if not monthly.empty:

            fig = go.Figure()

            for name in MODELS:
                part = monthly[monthly["model"] == name]
                if part.empty:
                    continue
                fig.add_scatter(
                    x=part["forecast_month"],
                    y=part["abs_err"],
                    mode="lines+markers",
                    name=name,
                    line=dict(color=MODEL_COLORS[name], width=2.5),
                )

            fig.update_yaxes(title_text="MAE (units)")
            show_plot(fig, height=320)

        else:

            st.info("No backtest rows for this selection.")

        st.download_button(
            "Download Backtest (CSV)",
            data=res_all.round(2).to_csv(index=False).encode("utf-8"),
            file_name="livesflow_backtest_all_models.csv",
            mime="text/csv",
        )

    st.caption(
        "Backtest uses only data available before each test month. "
        "Country and product filters change the tables and charts, "
        "not the choice of best model."
    )


# ----------------------------------------------------------
# TAB 2 — SIX-MONTH FORECAST
# ----------------------------------------------------------

with tab2:

    st.write("")

    with st.container(border=True):

        section_title(
            "Six-Month Forward Forecast",
            f"Trained on data through {last_actual}. "
            "Each predicted month feeds the next.",
        )

        fc_model = st.selectbox(
            "Forecast model",
            MODELS,
            index=MODELS.index(best_model),
            help="Defaults to the best model in the backtest.",
        )

        fc_all = forecast_forward(md, keys, fc_model)
        fc = scoped(fc_all)

        hist = (
            scoped(md)
            .groupby("ym", as_index=False)["confirmed_units"]
            .sum()
            .tail(12)
            .rename(columns={"ym": "month", "confirmed_units": "units"})
        )
        fcs = (
            fc.groupby("forecast_month", as_index=False)["predicted_units"]
            .sum()
            .rename(columns={"forecast_month": "month", "predicted_units": "units"})
        )

        fig = go.Figure()
        fig.add_scatter(
            x=hist["month"],
            y=hist["units"],
            mode="lines+markers",
            name="Actual",
            line=dict(color=C_ACTUAL, width=2.5),
        )
        fig.add_scatter(
            x=fcs["month"],
            y=fcs["units"],
            mode="lines+markers",
            name=f"{fc_model} forecast",
            line=dict(color=MODEL_COLORS[fc_model], dash="dash", width=2.5),
        )
        fig.update_yaxes(title_text="Units")
        show_plot(fig, height=340)

    with st.container(border=True):

        section_title(
            "Forecast Units by Series",
            "Predicted confirmed units per country and product",
        )

        if not fc.empty:

            wide = (
                fc.assign(series=fc[keys].astype(str).agg(" | ".join, axis=1))
                .pivot_table(
                    index="series",
                    columns="forecast_month",
                    values="predicted_units",
                    aggfunc="sum",
                )
                .reset_index()
                .rename(columns={"series": "Series"})
            )

            show_table(
                wide,
                formats={
                    c: (lambda x: f"{x:,.1f}")
                    for c in wide.columns if c != "Series"
                },
            )

        else:

            st.info("No forecast rows for this selection.")

        st.download_button(
            "Download Forecast (CSV, all countries)",
            data=fc_all.to_csv(index=False).encode("utf-8"),
            file_name=f"livesflow_forecast_6m_{fc_model.split()[0].lower()}.csv",
            mime="text/csv",
        )

    st.caption(
        "Forecasts are recursive, so errors can compound over the horizon. "
        "Seasonality comes from month dummies."
    )


# ==========================================================
# FOOTER
# ==========================================================

st.write("")
st.divider()

st.caption(
    "Synthetic competition dataset. "
    "Not actual Lives Group performance."
)