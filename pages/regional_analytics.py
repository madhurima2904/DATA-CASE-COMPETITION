
from pathlib import Path
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st


# ==========================================================
# LIVESFLOW — REGIONAL ANALYTICS
# Three tabs: Summary Data, Sales Opportunities, Cross-Entity
# ==========================================================

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

BLUE = "#386FE5"

PRODUCT_COLORS = {
    "Product A": "#386FE5",
    "Product B": "#8980DA",
    "Product C": "#2BAFA9",
}

ENTITY_COLORS = {
    "SPD": "#386FE5",
    "QTS": "#8980DA",
    "QTG": "#2BAFA9",
}


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

    /* Three clickable tabs */
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
def load_data():

    orders = pd.read_csv(DATA_DIR / "purchase_orders.csv")
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    items = pd.read_csv(DATA_DIR / "items.csv")

    required_columns = [
        "order_id",
        "order_date",
        "customer_id",
        "country",
        "product_group",
        "business_entity",
        "quantity",
        "order_value_sgd",
        "order_status",
    ]

    missing = [
        column for column in required_columns
        if column not in orders.columns
    ]

    if missing:
        raise ValueError(
            "Missing purchase order columns: "
            + ", ".join(missing)
        )

    orders["order_date"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce",
    )

    orders = orders.dropna(
        subset=["order_date"]
    ).copy()

    orders["month"] = (
        orders["order_date"]
        .dt.to_period("M")
        .astype(str)
    )

    for column in ["quantity", "order_value_sgd"]:
        orders[column] = pd.to_numeric(
            orders[column],
            errors="coerce",
        ).fillna(0)

    for column in [
        "country",
        "product_group",
        "business_entity",
        "order_status",
    ]:
        orders[column] = (
            orders[column]
            .astype(str)
            .str.strip()
        )

    # Deduplicate customer master records
    master = customers.drop_duplicates(
        "customer_id"
    ).copy()

    if "canonical_customer_id" in master.columns:

        canonical_map = master.set_index(
            "customer_id"
        )["canonical_customer_id"]

        orders["customer_key"] = (
            orders["customer_id"]
            .map(canonical_map)
            .fillna(orders["customer_id"])
        )

    else:
        orders["customer_key"] = orders["customer_id"]

    if "customer_name" in master.columns:

        name_map = master.set_index(
            "customer_id"
        )["customer_name"]

        orders["customer_name"] = (
            orders["customer_id"]
            .map(name_map)
            .fillna(orders["customer_id"].astype(str))
        )

    else:
        orders["customer_name"] = (
            orders["customer_id"].astype(str)
        )

    return orders, customers, items


try:
    orders, customers, items = load_data()

except (
    FileNotFoundError,
    KeyError,
    ValueError,
    pd.errors.ParserError,
) as error:
    st.error(f"Error loading CSV files: {error}")
    st.stop()


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
        font=dict(
            family="Arial",
            color="#253249",
            size=12,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="#253249",
                size=12,
            ),
            orientation="h",
            y=-0.25,
        ),
        margin=dict(
            l=10,
            r=35,
            t=20,
            b=35,
        ),
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

    for record in view.itertuples(
        index=False,
        name=None,
    ):

        cells = "".join(
            f"<td>{escape(str(value)) if pd.notna(value) else '—'}</td>"
            for value in record
        )

        rows.append(f"<tr>{cells}</tr>")

    html = (
        '<div class="lf-table-wrap">'
        '<table class="lf-table">'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def growth_analysis(df, months):
    """Compare two equal-length halves of the selected period."""

    if len(months) < 2:
        return pd.DataFrame()

    half = len(months) // 2

    earlier_months = months[:half]
    later_months = months[-half:]

    earlier = (
        df[df["month"].isin(earlier_months)]
        .groupby(
            ["country", "product_group"]
        )["quantity"]
        .sum()
    )

    later = (
        df[df["month"].isin(later_months)]
        .groupby(
            ["country", "product_group"]
        )["quantity"]
        .sum()
    )

    result = pd.concat(
        [
            earlier.rename("Earlier Units"),
            later.rename("Later Units"),
        ],
        axis=1,
    ).fillna(0).reset_index()

    result["Change (Units)"] = (
        result["Later Units"]
        - result["Earlier Units"]
    )

    result["Growth (%)"] = result.apply(
        lambda row: (
            (
                row["Later Units"]
                / row["Earlier Units"]
                - 1
            ) * 100
            if row["Earlier Units"] > 0
            else float("nan")
        ),
        axis=1,
    )

    return result.rename(
        columns={
            "country": "Country",
            "product_group": "Product",
        }
    )




# ==========================================================
# PAGE HEADER
# ==========================================================

st.markdown(
    '<div class="lf-eyebrow">'
    'LIVESFLOW / REGIONAL ANALYTICS'
    '</div>',
    unsafe_allow_html=True,
)

st.title("Regional Performance")

st.caption(
    "Monitor purchasing performance, discover sales "
    "opportunities and compare business entities."
)


# ==========================================================
# SHARED FILTERS
# ==========================================================

f1, f2, f3 = st.columns(3)

with f1:

    selected_country = st.selectbox(
        "Country",
        ["All Countries"]
        + sorted(
            orders["country"]
            .dropna()
            .unique()
            .tolist()
        ),
    )

with f2:

    selected_product = st.selectbox(
        "Product",
        ["All Products"]
        + sorted(
            orders["product_group"]
            .dropna()
            .unique()
            .tolist()
        ),
    )

with f3:

    selected_entity = st.selectbox(
        "Business Entity",
        ["All Entities"]
        + sorted(
            orders["business_entity"]
            .dropna()
            .unique()
            .tolist()
        ),
    )


months = sorted(
    orders["month"].unique().tolist()
)

if not months:
    st.warning("No valid monthly data found.")
    st.stop()

start_month, end_month = st.select_slider(
    "Analysis Period",
    options=months,
    value=(months[0], months[-1]),
)

selected_months = [
    month for month in months
    if start_month <= month <= end_month
]

filtered = orders[
    orders["month"].between(
        start_month,
        end_month,
    )
].copy()

if selected_country != "All Countries":

    filtered = filtered[
        filtered["country"] == selected_country
    ]

if selected_product != "All Products":

    filtered = filtered[
        filtered["product_group"] == selected_product
    ]

if selected_entity != "All Entities":

    filtered = filtered[
        filtered["business_entity"] == selected_entity
    ]


# Separate confirmed orders and enquiries
confirmed = filtered[
    filtered["order_status"].str.casefold() == "confirmed"
].copy()

enquiries = filtered[
    filtered["order_status"].str.casefold() == "enquiry"
].copy()


# ==========================================================
# THREE MAIN TABS
# ==========================================================

tab1, tab2, tab3 = st.tabs(
    [
        "Summary Data",
        "Sales Opportunities",
        "Cross-Entity",
    ]
)


# ==========================================================
# TAB 1 — SUMMARY DATA
# ==========================================================

with tab1:

    st.write("")

    # ------------------------------------------------------
    # FIVE KPI CARDS — INCLUDING NEW ENQUIRIES CARD
    # ------------------------------------------------------

    total_units = confirmed["quantity"].sum()
    total_value = confirmed["order_value_sgd"].sum()

    confirmed_order_count = confirmed["order_id"].nunique()
    customer_count = confirmed["customer_key"].nunique()

    # Enquiries are counted as unique order IDs
    enquiry_count = enquiries["order_id"].nunique()

    k1, k2, k3, k4, k5 = st.columns(
        5,
        gap="small",
    )

    with k1:
        st.metric(
            "Confirmed Units",
            compact_number(total_units),
        )

    with k2:
        st.metric(
            "Order Value",
            "S$" + compact_number(total_value),
        )

    with k3:
        st.metric(
            "Confirmed Orders",
            f"{confirmed_order_count:,}",
        )

    with k4:
        st.metric(
            "Customers",
            f"{customer_count:,}",
        )

    with k5:
        st.metric(
            "Enquiries",
            f"{enquiry_count:,}",
        )

    st.write("")

    # ------------------------------------------------------
    # MONTHLY TRENDS AND COUNTRY VOLUME
    # ------------------------------------------------------

    left, right = st.columns(
        [1.6, 1],
        gap="large",
    )

    with left:

        with st.container(border=True):

            section_title(
                "Monthly Purchasing Trends",
                "Confirmed order units by product",
            )

            monthly = (
                confirmed.groupby(
                    ["month", "product_group"],
                    as_index=False,
                )["quantity"]
                .sum()
            )

            if not monthly.empty:

                fig = px.line(
                    monthly,
                    x="month",
                    y="quantity",
                    color="product_group",
                    markers=True,
                    color_discrete_map=PRODUCT_COLORS,
                    labels={
                        "month": "",
                        "quantity": "Units Ordered",
                        "product_group": "Product",
                    },
                )

                show_plot(fig)

            else:

                st.info("No confirmed orders.")


    with right:

        with st.container(border=True):

            section_title(
                "Volume by Country",
                "Confirmed purchasing volume",
            )

            country_data = (
                confirmed.groupby(
                    "country",
                    as_index=False,
                )["quantity"]
                .sum()
                .sort_values("quantity")
            )

            if not country_data.empty:

                fig = px.bar(
                    country_data,
                    x="quantity",
                    y="country",
                    orientation="h",
                    color_discrete_sequence=[BLUE],
                    labels={
                        "quantity": "Units",
                        "country": "",
                    },
                )

                fig.update_traces(
                    hovertemplate=(
                        "%{y}: %{x:,.0f} units"
                        "<extra></extra>"
                    )
                )

                show_plot(fig)

            else:

                st.info("No confirmed orders.")


    # ------------------------------------------------------
    # COUNTRY × PRODUCT COMPARISON
    # ------------------------------------------------------

    with st.container(border=True):

        section_title(
            "Country × Product Comparison",
            "Compare order quantities by product group",
        )

        compare = (
            confirmed.groupby(
                ["country", "product_group"],
                as_index=False,
            )["quantity"]
            .sum()
        )

        if not compare.empty:

            fig = px.bar(
                compare,
                x="country",
                y="quantity",
                color="product_group",
                barmode="group",
                color_discrete_map=PRODUCT_COLORS,
                labels={
                    "country": "",
                    "quantity": "Units Ordered",
                    "product_group": "Product",
                },
            )

            show_plot(fig)

        else:
            st.info("No confirmed orders.")


    # ------------------------------------------------------
    # COUNTRY × PRODUCT × BUSINESS ENTITY SUMMARY
    # ------------------------------------------------------

    with st.container(border=True):

        section_title(
            "Country × Product × Business Entity",
            "Confirmed orders by market, product and entity",
        )

        summary = (
            confirmed.groupby(
                [
                    "country",
                    "product_group",
                    "business_entity",
                ],
                as_index=False,
            )
            .agg(
                Units=("quantity", "sum"),
                Orders=("order_id", "nunique"),
                Value=("order_value_sgd", "sum"),
            )
        )

        summary = summary.rename(
            columns={
                "country": "Country",
                "product_group": "Product",
                "business_entity": "Entity",
                "Value": "Order Value (SGD)",
            }
        )

        show_table(
            summary.sort_values(
                ["Country", "Product", "Entity"]
            ),
            formats={
                "Units": lambda x: f"{x:,.0f}",
                "Order Value (SGD)": lambda x: f"{x:,.0f}",
            },
        )


    # ------------------------------------------------------
    # PURCHASING GROWTH ANALYSIS
    # ------------------------------------------------------

    with st.container(border=True):

        section_title(
            "Purchasing Growth Analysis",
            "Earlier vs later confirmed purchasing volumes",
        )

        growth = growth_analysis(
            confirmed,
            selected_months,
        )

        if growth.empty:

            st.info(
                "Select at least two months for growth analysis."
            )

        else:

            growth_country = st.selectbox(
                "Select Country",
                ["All Countries"]
                + sorted(
                    growth["Country"].unique().tolist()
                ),
                key="growth_country",
            )

            if growth_country != "All Countries":

                growth = growth[
                    growth["Country"] == growth_country
                ]

            show_table(
                growth.sort_values(
                    ["Country", "Product"]
                ),
                formats={
                    "Earlier Units": lambda x: f"{x:,.0f}",
                    "Later Units": lambda x: f"{x:,.0f}",
                    "Change (Units)": lambda x: f"{x:+,.0f}",
                    "Growth (%)": lambda x: f"{x:+.1f}%",
                },
            )


# ==========================================================
# TAB 2 — SALES OPPORTUNITIES
# ==========================================================

with tab2:

    st.write("")

    section_title(
        "Sales Opportunities",
        "Potential opportunities based on confirmed purchases",
    )

    # ------------------------------------------------------
    # CROSS-SELLING CANDIDATES
    # ------------------------------------------------------

    with st.container(border=True):

        section_title(
            "Cross-Selling Candidates",
            "Customers who have not purchased all product groups",
        )

        product_list = sorted(
            orders["product_group"]
            .dropna()
            .unique()
            .tolist()
        )

        profiles = (
            confirmed.groupby(
                "customer_key"
            )
            .agg(
                Customer=("customer_name", "first"),
                Country=("country", "first"),
                Purchased=(
                    "product_group",
                    lambda values: set(values),
                ),
            )
            .reset_index()
        )

        leads = []

        for _, row in profiles.iterrows():

            gaps = [
                product
                for product in product_list
                if product not in row["Purchased"]
            ]

            if gaps:

                leads.append(
                    {
                        "Customer": row["Customer"],
                        "Country": row["Country"],
                        "Currently Buys": ", ".join(
                            sorted(row["Purchased"])
                        ),
                        "Potential Products": ", ".join(gaps),
                        "Action": "Review product fit",
                    }
                )

        if leads:

            show_table(
                pd.DataFrame(leads).head(30)
            )

        else:

            st.info(
                "No cross-selling candidates found."
            )


    # ------------------------------------------------------
    # CUSTOMERS WITH DECLINING PURCHASES
    # ------------------------------------------------------

    with st.container(border=True):

        section_title(
            "Customers with Declining Purchases",
            "Latest three months vs previous three months",
        )

        if len(selected_months) < 6:

            st.info(
                "Select at least six months to calculate "
                "customer purchase decline."
            )

        else:

            older = selected_months[-6:-3]
            newer = selected_months[-3:]

            previous = (
                confirmed[
                    confirmed["month"].isin(older)
                ]
                .groupby("customer_key")["quantity"]
                .sum()
            )

            recent = (
                confirmed[
                    confirmed["month"].isin(newer)
                ]
                .groupby("customer_key")["quantity"]
                .sum()
            )

            change = pd.concat(
                [
                    previous.rename("Previous Units"),
                    recent.rename("Recent Units"),
                ],
                axis=1,
            ).fillna(0)

            change = change[
                (change["Previous Units"] > 0)
                &
                (
                    change["Recent Units"]
                    < change["Previous Units"]
                )
            ].copy()

            change["Change (%)"] = (
                change["Recent Units"]
                / change["Previous Units"]
                - 1
            ) * 100

            details = (
                confirmed
                .drop_duplicates("customer_key")
                .set_index("customer_key")[
                    ["customer_name", "country"]
                ]
            )

            change = (
                change.join(details)
                .reset_index()
                .rename(
                    columns={
                        "customer_name": "Customer",
                        "country": "Country",
                    }
                )
            )

            columns = [
                "Customer",
                "Country",
                "Previous Units",
                "Recent Units",
                "Change (%)",
            ]

            show_table(
                change[columns]
                .sort_values("Change (%)")
                .head(20),
                formats={
                    "Previous Units": lambda x: f"{x:,.0f}",
                    "Recent Units": lambda x: f"{x:,.0f}",
                    "Change (%)": lambda x: f"{x:+.1f}%",
                },
            )


    # ------------------------------------------------------
    # GROWING MARKETS AND PRODUCTS
    # ------------------------------------------------------

    with st.container(border=True):

        section_title(
            "Growing Markets and Products",
            "Segments with increasing confirmed order volume",
        )

        growth = growth_analysis(
            confirmed,
            selected_months,
        )

        if not growth.empty:

            growing = growth[
                growth["Growth (%)"] > 0
            ].sort_values(
                "Growth (%)",
                ascending=False,
            )

            show_table(
                growing,
                formats={
                    "Earlier Units": lambda x: f"{x:,.0f}",
                    "Later Units": lambda x: f"{x:,.0f}",
                    "Change (Units)": lambda x: f"{x:+,.0f}",
                    "Growth (%)": lambda x: f"{x:+.1f}%",
                },
            )

        else:

            st.info(
                "Select at least two months."
            )

    st.caption(
        "Sales opportunities are analytical suggestions, "
        "not confirmed future demand."
    )


# ==========================================================
# TAB 3 — CROSS-ENTITY
# ==========================================================

with tab3:

    st.write("")

    section_title(
        "Cross-Entity Analysis",
        "Compare business entities across countries and products",
    )

    if selected_entity != "All Entities":

        st.info(
            "Choose 'All Entities' in the filter above "
            "to compare all business entities."
        )

    left, right = st.columns(
        2,
        gap="large",
    )


    # ------------------------------------------------------
    # ORDER VOLUME BY ENTITY
    # ------------------------------------------------------

    with left:

        with st.container(border=True):

            section_title(
                "Order Volume by Entity",
                "Confirmed order quantities",
            )

            entity_data = (
                confirmed.groupby(
                    "business_entity",
                    as_index=False,
                )["quantity"]
                .sum()
            )

            if not entity_data.empty:

                fig = px.bar(
                    entity_data,
                    x="business_entity",
                    y="quantity",
                    color="business_entity",
                    color_discrete_map=ENTITY_COLORS,
                    labels={
                        "business_entity": "Entity",
                        "quantity": "Units",
                    },
                )

                fig.update_layout(
                    showlegend=False
                )

                show_plot(fig)

            else:

                st.info("No confirmed orders.")


    # ------------------------------------------------------
    # ENTITY × COUNTRY COMPARISON
    # ------------------------------------------------------

    with right:

        with st.container(border=True):

            section_title(
                "Entity × Country Comparison",
                "Purchasing volume across markets",
            )

            entity_country = (
                confirmed.groupby(
                    [
                        "country",
                        "business_entity",
                    ],
                    as_index=False,
                )["quantity"]
                .sum()
            )

            if not entity_country.empty:

                fig = px.bar(
                    entity_country,
                    x="country",
                    y="quantity",
                    color="business_entity",
                    barmode="group",
                    color_discrete_map=ENTITY_COLORS,
                    labels={
                        "country": "",
                        "quantity": "Units",
                        "business_entity": "Entity",
                    },
                )

                show_plot(fig)

            else:

                st.info("No confirmed orders.")


    # ------------------------------------------------------
    # PRODUCT PERFORMANCE BY ENTITY
    # ------------------------------------------------------

    with st.container(border=True):

        section_title(
            "Product Performance by Entity",
            "Product demand across business entities",
        )

        entity_product = (
            confirmed.groupby(
                [
                    "business_entity",
                    "product_group",
                ],
                as_index=False,
            )["quantity"]
            .sum()
        )

        if not entity_product.empty:

            fig = px.bar(
                entity_product,
                x="business_entity",
                y="quantity",
                color="product_group",
                barmode="group",
                color_discrete_map=PRODUCT_COLORS,
                labels={
                    "business_entity": "Entity",
                    "quantity": "Units",
                    "product_group": "Product",
                },
            )

            show_plot(fig)

        else:

            st.info("No confirmed orders.")


    # ------------------------------------------------------
    # ENTITY × PRODUCT SUMMARY
    # ------------------------------------------------------

    with st.container(border=True):

        section_title(
            "Entity × Product Summary",
            "Confirmed order performance",
        )

        entity_summary = (
            confirmed.groupby(
                [
                    "business_entity",
                    "product_group",
                ],
                as_index=False,
            )
            .agg(
                Units=("quantity", "sum"),
                Orders=("order_id", "nunique"),
                Customers=("customer_key", "nunique"),
                Value=("order_value_sgd", "sum"),
            )
        )

        entity_summary = entity_summary.rename(
            columns={
                "business_entity": "Entity",
                "product_group": "Product",
                "Value": "Order Value (SGD)",
            }
        )

        show_table(
            entity_summary,
            formats={
                "Units": lambda x: f"{x:,.0f}",
                "Order Value (SGD)": lambda x: f"{x:,.0f}",
            },
        )


    # ------------------------------------------------------
    # CUSTOMERS ACROSS MULTIPLE ENTITIES
    # ------------------------------------------------------

    with st.container(border=True):

        section_title(
            "Customers Across Multiple Entities",
            "Customers purchasing through more than one entity",
        )

        overlaps = (
            confirmed.groupby(
                "customer_key"
            )
            .agg(
                Customer=("customer_name", "first"),
                Entity_Count=(
                    "business_entity",
                    "nunique",
                ),
                Entities=(
                    "business_entity",
                    lambda values: ", ".join(
                        sorted(values.unique())
                    ),
                ),
            )
            .reset_index()
        )

        overlaps = overlaps[
            overlaps["Entity_Count"] > 1
        ]

        if overlaps.empty:

            st.info(
                "No cross-entity customer overlap detected "
                "in the current selection."
            )

        else:

            show_table(
                overlaps[
                    [
                        "Customer",
                        "Entity_Count",
                        "Entities",
                    ]
                ].rename(
                    columns={
                        "Entity_Count": "Number of Entities",
                    }
                )
            )


# ==========================================================
# EXPORT
# ==========================================================

st.write("")
st.divider()

st.download_button(
    "Download Filtered Confirmed Orders (CSV)",
    data=confirmed.to_csv(
        index=False
    ).encode("utf-8"),
    file_name="livesflow_regional_analytics.csv",
    mime="text/csv",
)

st.caption(
    "Synthetic competition dataset. "
    "Not actual Lives Group performance."
)
