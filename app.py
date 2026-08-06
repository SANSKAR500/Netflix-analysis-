"""
Quantium Chip Analytics — Customer Behaviour & Store Trial Dashboard
=====================================================================
A single-file Streamlit app combining:
  • Task 1: transaction + loyalty data cleaning, feature engineering,
    and customer-segment / brand / pack-size analysis.
  • Task 2: pre-trial control-store selection (correlation + magnitude
    similarity) and trial-vs-control statistical testing for stores
    77, 86 and 88.

Run locally:
    streamlit run app.py

Deploy on Streamlit Community Cloud:
    1. Push app.py + requirements.txt to a GitHub repo.
    2. (Optional) also commit QVI_transaction_data.xlsx and
       QVI_purchase_behaviour.csv to the repo root — the app will pick
       them up automatically. Otherwise, upload them via the sidebar
       once the app is live.
    3. Deploy at https://share.streamlit.io.
"""

import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from scipy.stats import ttest_ind

# ----------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Quantium Chip Analytics",
    page_icon="🥔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Visual identity — palette, plotly template, custom CSS
# ----------------------------------------------------------------------
PALETTE = ["#7C5CFC", "#00C9A7", "#FF9F1C", "#FF5D8F", "#3AAED8", "#F4D35E", "#845EC2", "#4B4453"]
BG = "#0F1117"
CARD_BG = "#171A23"
GRID = "rgba(255,255,255,0.08)"
TEXT = "#E8E8F0"
MUTED = "#9A9CB0"

quantium_template = go.layout.Template()
quantium_template.layout = go.Layout(
    colorway=PALETTE,
    font=dict(family="Poppins, sans-serif", color=TEXT, size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    title=dict(font=dict(size=18, color=TEXT), x=0.02, xanchor="left"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)"),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED)),
    margin=dict(t=60, l=10, r=10, b=10),
    hoverlabel=dict(bgcolor=CARD_BG, font=dict(color=TEXT, family="Poppins, sans-serif")),
)
pio.templates["quantium"] = quantium_template
pio.templates.default = "quantium"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Poppins', sans-serif;
}}
.stApp {{
    background: radial-gradient(circle at 15% 0%, #1b1f2e 0%, {BG} 45%) fixed;
}}
section[data-testid="stSidebar"] {{
    background: {CARD_BG};
    border-right: 1px solid rgba(255,255,255,0.06);
}}
h1, h2, h3 {{
    color: {TEXT} !important;
    font-weight: 600 !important;
}}
p, span, label, .stMarkdown {{
    color: {TEXT};
}}
.kpi-row {{
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}}
.kpi-card {{
    flex: 1;
    min-width: 170px;
    border-radius: 16px;
    padding: 18px 20px;
    background: linear-gradient(135deg, var(--c1) 0%, var(--c2) 100%);
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
}}
.kpi-icon {{ font-size: 22px; opacity: 0.9; }}
.kpi-label {{ font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; opacity: 0.85; margin-top: 6px; }}
.kpi-value {{ font-size: 26px; font-weight: 700; margin-top: 2px; }}

.section-tag {{
    display: inline-block;
    padding: 3px 12px;
    border-radius: 999px;
    background: rgba(124,92,252,0.15);
    color: #B9A6FF;
    font-size: 12px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 6px;
}}
div[data-testid="stMetricValue"] {{ color: {TEXT}; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
.stTabs [data-baseweb="tab"] {{
    background-color: {CARD_BG};
    border-radius: 10px 10px 0 0;
    padding: 8px 16px;
    color: {MUTED};
}}
.stTabs [aria-selected="true"] {{
    color: {TEXT} !important;
    background-color: #232838 !important;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def kpi_card(icon: str, label: str, value: str, c1: str, c2: str) -> str:
    return f"""
    <div class="kpi-card" style="--c1:{c1};--c2:{c2};">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """


def kpi_row(cards: list) -> None:
    st.markdown(f'<div class="kpi-row">{"".join(cards)}</div>', unsafe_allow_html=True)


def section_tag(text: str) -> None:
    st.markdown(f'<div class="section-tag">{text}</div>', unsafe_allow_html=True)


def style(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(template="quantium", height=height)
    return fig


# ----------------------------------------------------------------------
# Data loading (Task 1 pipeline)
# ----------------------------------------------------------------------
DEFAULT_TXN_PATH = "QVI_transaction_data.xlsx"
DEFAULT_PB_PATH = "QVI_purchase_behaviour.csv"

BRAND_REPLACE = {
    "RED": "RRD",
    "SNBTS": "SUNBITES",
    "INFZNS": "INFUZIONS",
    "WW": "WOOLWORTHS",
    "SMITH": "SMITHS",
}


@st.cache_data(show_spinner="Cleaning & merging transaction data...")
def build_master_data(txn_bytes: bytes, pb_bytes: bytes) -> pd.DataFrame:
    import io

    transactions = pd.read_excel(io.BytesIO(txn_bytes))
    purchase = pd.read_csv(io.BytesIO(pb_bytes))

    # Excel serial date -> datetime
    transactions["DATE"] = pd.to_datetime(
        transactions["DATE"], unit="D", origin="1899-12-30"
    )
    transactions["YEAR"] = transactions["DATE"].dt.year
    transactions["MONTH"] = transactions["DATE"].dt.month
    transactions["YEARMONTH"] = transactions["DATE"].dt.strftime("%Y%m").astype(int)

    # Drop bulk/commercial outlier purchases
    transactions = transactions[transactions["PROD_QTY"] < 10].copy()

    # Feature engineering
    transactions["PACK_SIZE"] = transactions["PROD_NAME"].str.extract(r"(\d+)").astype(int)
    transactions["BRAND"] = transactions["PROD_NAME"].str.split().str[0].str.upper()
    transactions["BRAND"] = transactions["BRAND"].replace(BRAND_REPLACE)

    data = transactions.merge(purchase, on="LYLTY_CARD_NBR", how="left")
    data["PRICE_PER_UNIT"] = data["TOT_SALES"] / data["PROD_QTY"]
    return data


@st.cache_data(show_spinner=False)
def build_store_month(data: pd.DataFrame) -> pd.DataFrame:
    store_month = (
        data.groupby(["STORE_NBR", "YEARMONTH"])
        .agg(
            TOT_SALES=("TOT_SALES", "sum"),
            N_CUSTOMERS=("LYLTY_CARD_NBR", "nunique"),
            TXNS=("TXN_ID", "nunique"),
        )
        .reset_index()
    )
    store_month["AVG_TXN_PER_CUSTOMER"] = store_month["TXNS"] / store_month["N_CUSTOMERS"]
    return store_month


def magnitude_similarity(distance: pd.Series) -> pd.Series:
    """Normalize a distance series into a 0-1 similarity score (1 = most similar)."""
    d = distance.astype(float)
    span = d.max() - d.min()
    if span == 0:
        return pd.Series(1.0, index=d.index)
    return 1 - (d - d.min()) / (span + 1e-9)


@st.cache_data(show_spinner=False)
def score_trial(pretrial: pd.DataFrame, trial_store: int, metric: str) -> pd.DataFrame:
    trial = pretrial[pretrial.STORE_NBR == trial_store][["YEARMONTH", metric]]
    results = []
    for store in pretrial.STORE_NBR.unique():
        if store == trial_store:
            continue
        ctrl = pretrial[pretrial.STORE_NBR == store][["YEARMONTH", metric]]
        merged = trial.merge(ctrl, on="YEARMONTH", suffixes=("_trial", "_ctrl"))
        if len(merged) < 2:
            continue
        corr = merged[f"{metric}_trial"].corr(merged[f"{metric}_ctrl"])
        dist = ((merged[f"{metric}_trial"] - merged[f"{metric}_ctrl"]) ** 2).mean()
        results.append([store, corr, dist])

    res = pd.DataFrame(results, columns=["STORE", "CORRELATION", "DISTANCE"])
    res["MAG_SCORE"] = magnitude_similarity(res["DISTANCE"])
    res["FINAL_SCORE"] = (res["CORRELATION"].fillna(0) + res["MAG_SCORE"]) / 2
    return res.sort_values("FINAL_SCORE", ascending=False).reset_index(drop=True)


# ----------------------------------------------------------------------
# Sidebar — data source
# ----------------------------------------------------------------------
st.sidebar.markdown("## 🥔 Quantium Chips")
st.sidebar.caption("Customer behaviour & store-trial analytics")
st.sidebar.markdown("---")

txn_bytes = pb_bytes = None
if os.path.exists(DEFAULT_TXN_PATH) and os.path.exists(DEFAULT_PB_PATH):
    with open(DEFAULT_TXN_PATH, "rb") as f:
        txn_bytes = f.read()
    with open(DEFAULT_PB_PATH, "rb") as f:
        pb_bytes = f.read()
    st.sidebar.success("Loaded bundled QVI data files ✅")
else:
    txn_file = st.sidebar.file_uploader("QVI_transaction_data.xlsx", type=["xlsx"])
    pb_file = st.sidebar.file_uploader("QVI_purchase_behaviour.csv", type=["csv"])
    if txn_file and pb_file:
        txn_bytes, pb_bytes = txn_file.getvalue(), pb_file.getvalue()

if not (txn_bytes and pb_bytes):
    st.title("🥔 Quantium Chip Analytics")
    st.info(
        "Upload **QVI_transaction_data.xlsx** and **QVI_purchase_behaviour.csv** "
        "in the sidebar to launch the dashboard."
    )
    st.stop()

data = build_master_data(txn_bytes, pb_bytes)
store_month = build_store_month(data)

# ----------------------------------------------------------------------
# Header + KPIs
# ----------------------------------------------------------------------
st.title("🥔 Quantium Chip Analytics")
st.caption("Customer purchasing behaviour & store trial uplift dashboard")

total_sales = data["TOT_SALES"].sum()
total_txns = data["TXN_ID"].nunique()
total_customers = data["LYLTY_CARD_NBR"].nunique()
avg_txn_value = data.groupby("TXN_ID")["TOT_SALES"].sum().mean()
avg_qty = data["PROD_QTY"].mean()

kpi_row([
    kpi_card("💰", "Total Sales", f"${total_sales:,.0f}", "#7C5CFC", "#4A2FCF"),
    kpi_card("🧾", "Transactions", f"{total_txns:,}", "#00C9A7", "#00897B"),
    kpi_card("👥", "Customers", f"{total_customers:,}", "#FF9F1C", "#E07A00"),
    kpi_card("💵", "Avg Txn Value", f"${avg_txn_value:,.2f}", "#FF5D8F", "#C82C60"),
    kpi_card("📦", "Avg Qty / Txn", f"{avg_qty:.2f}", "#3AAED8", "#1E7FA8"),
])

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------
tab_customers, tab_brands, tab_trial, tab_insights = st.tabs(
    ["👥 Customer Behaviour", "🏷️ Brand & Pack", "🧪 Store Trial Analysis", "💡 Insights"]
)

# ---- Customer Behaviour -------------------------------------------------
with tab_customers:
    section_tag("Segmentation")
    st.subheader("Who's buying, and how much?")

    c1, c2 = st.columns([1, 1])

    with c1:
        sales_life = (
            data.groupby("LIFESTAGE")["TOT_SALES"].sum().sort_values(ascending=True).reset_index()
        )
        fig = px.bar(
            sales_life, x="TOT_SALES", y="LIFESTAGE", orientation="h",
            color="TOT_SALES", color_continuous_scale=[PALETTE[7], PALETTE[0]],
            title="Sales by Lifestage",
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style(fig), use_container_width=True)

    with c2:
        sales_premium = data.groupby("PREMIUM_CUSTOMER")["TOT_SALES"].sum().reset_index()
        fig = px.pie(
            sales_premium, names="PREMIUM_CUSTOMER", values="TOT_SALES", hole=0.55,
            title="Sales by Premium Tier", color_discrete_sequence=PALETTE,
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(style(fig), use_container_width=True)

    segment = (
        data.groupby(["LIFESTAGE", "PREMIUM_CUSTOMER"])
        .agg(
            Total_Sales=("TOT_SALES", "sum"),
            Transactions=("TXN_ID", "nunique"),
            Customers=("LYLTY_CARD_NBR", "nunique"),
            Avg_Spend=("TOT_SALES", "mean"),
            Avg_Qty=("PROD_QTY", "mean"),
            Avg_Price=("PRICE_PER_UNIT", "mean"),
        )
        .reset_index()
    )

    section_tag("Segment Explorer")
    fig = px.scatter(
        segment, x="Avg_Qty", y="Avg_Price", size="Total_Sales", color="LIFESTAGE",
        symbol="PREMIUM_CUSTOMER", size_max=48, color_discrete_sequence=PALETTE,
        hover_name="LIFESTAGE",
        title="Segment Landscape — Avg Qty vs Avg Price (bubble = total sales)",
        labels={"Avg_Qty": "Avg Quantity per Transaction", "Avg_Price": "Avg Price per Unit ($)"},
    )
    st.plotly_chart(style(fig, height=520), use_container_width=True)

    pivot = segment.pivot(index="LIFESTAGE", columns="PREMIUM_CUSTOMER", values="Total_Sales")
    fig = px.imshow(
        pivot, text_auto=".0f", aspect="auto",
        color_continuous_scale=[CARD_BG, PALETTE[1], PALETTE[0]],
        title="Sales Heatmap — Lifestage × Premium Tier",
    )
    st.plotly_chart(style(fig, height=460), use_container_width=True)

    with st.expander("📋 Full segment table"):
        st.dataframe(segment.style.format({
            "Total_Sales": "${:,.0f}", "Avg_Spend": "${:,.2f}",
            "Avg_Qty": "{:.2f}", "Avg_Price": "${:,.2f}",
        }), use_container_width=True)

# ---- Brand & Pack ---------------------------------------------------------
with tab_brands:
    section_tag("Products")
    st.subheader("Brands & pack sizes that drive revenue")

    brand_sales = data.groupby("BRAND")["TOT_SALES"].sum().sort_values(ascending=False)
    pack_sales = data.groupby("PACK_SIZE")["TOT_SALES"].sum().sort_values(ascending=False)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        top_brand = brand_sales.head(12).sort_values(ascending=True).reset_index()
        fig = px.bar(
            top_brand, x="TOT_SALES", y="BRAND", orientation="h",
            color="TOT_SALES", color_continuous_scale=[PALETTE[6], PALETTE[2]],
            title="Top 12 Brands by Sales",
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style(fig, height=480), use_container_width=True)

    with c2:
        pack_df = pack_sales.reset_index()
        pack_df.columns = ["PACK_SIZE", "TOT_SALES"]
        pack_df["PACK_SIZE"] = pack_df["PACK_SIZE"].astype(str) + "g"
        fig = px.treemap(
            pack_df, path=["PACK_SIZE"], values="TOT_SALES",
            color="TOT_SALES", color_continuous_scale=[CARD_BG, PALETTE[3], PALETTE[0]],
            title="Pack Size Revenue Mix",
        )
        st.plotly_chart(style(fig, height=480), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section_tag("Price vs Volume")
    price_by_pack = data.groupby("PACK_SIZE").agg(
        Avg_Price=("PRICE_PER_UNIT", "mean"), Units_Sold=("PROD_QTY", "sum")
    ).reset_index()
    fig = px.scatter(
        price_by_pack, x="PACK_SIZE", y="Avg_Price", size="Units_Sold",
        color="Avg_Price", color_continuous_scale=[PALETTE[4], PALETTE[0]],
        title="Average Price per Unit by Pack Size (bubble = units sold)",
        labels={"PACK_SIZE": "Pack Size (g)", "Avg_Price": "Avg Price ($)"},
    )
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(style(fig), use_container_width=True)

# ---- Store Trial Analysis --------------------------------------------------
with tab_trial:
    section_tag("Trial Design")
    st.subheader("Which stores best match each trial store?")

    all_stores = sorted(store_month["STORE_NBR"].unique())
    default_trials = [s for s in [77, 86, 88] if s in all_stores] or all_stores[:3]

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        trial_stores = st.multiselect("Trial store(s)", all_stores, default=default_trials)
    with sc2:
        yearmonths = sorted(store_month["YEARMONTH"].unique())
        trial_start = st.selectbox(
            "Trial period start (YEARMONTH)", yearmonths,
            index=yearmonths.index(201902) if 201902 in yearmonths else len(yearmonths) // 2,
        )
    with sc3:
        metric = st.selectbox("Similarity metric", ["TOT_SALES", "N_CUSTOMERS", "AVG_TXN_PER_CUSTOMER"])

    pretrial = store_month[store_month["YEARMONTH"] < trial_start].copy()
    trial_period = store_month[store_month["YEARMONTH"] >= trial_start].copy()

    if not trial_stores:
        st.warning("Select at least one trial store to run the analysis.")
    else:
        for trial in trial_stores:
            st.markdown(f"#### 🏪 Trial Store {trial}")
            result = score_trial(pretrial, trial, metric)

            if result.empty:
                st.warning(f"Not enough pre-trial overlap to score control stores for store {trial}.")
                continue

            top5 = result.head(5)
            cc1, cc2 = st.columns([1, 1.4])

            with cc1:
                fig = px.bar(
                    top5.sort_values("FINAL_SCORE"), x="FINAL_SCORE", y="STORE", orientation="h",
                    color="FINAL_SCORE", color_continuous_scale=[PALETTE[5], PALETTE[0]],
                    title=f"Top Control Candidates for Store {trial}",
                    labels={"STORE": "Candidate Store", "FINAL_SCORE": "Similarity Score"},
                )
                fig.update_layout(coloraxis_showscale=False)
                st.plotly_chart(style(fig, height=340), use_container_width=True)

            with cc2:
                st.dataframe(
                    top5.style.format({"CORRELATION": "{:.3f}", "DISTANCE": "{:.1f}",
                                        "MAG_SCORE": "{:.3f}", "FINAL_SCORE": "{:.3f}"}),
                    use_container_width=True, height=220,
                )
                control_store = st.selectbox(
                    f"Control store for {trial}", top5["STORE"].astype(int).tolist(),
                    key=f"ctrl_{trial}",
                )

            # Trend comparison chart
            combo = store_month[store_month["STORE_NBR"].isin([trial, control_store])].copy()
            combo["Store Role"] = combo["STORE_NBR"].map(
                {trial: f"Trial ({trial})", control_store: f"Control ({control_store})"}
            )
            fig = px.line(
                combo.sort_values("YEARMONTH"), x="YEARMONTH", y=metric, color="Store Role",
                markers=True, color_discrete_sequence=[PALETTE[0], PALETTE[1]],
                title=f"{metric} — Trial {trial} vs Control {control_store}",
            )
            fig.add_vline(x=trial_start, line_dash="dash", line_color=MUTED,
                           annotation_text="Trial start", annotation_font_color=MUTED)
            st.plotly_chart(style(fig, height=380), use_container_width=True)

            # Statistical test on trial-period sales
            trial_sales = trial_period[trial_period.STORE_NBR == trial]["TOT_SALES"]
            control_sales = trial_period[trial_period.STORE_NBR == control_store]["TOT_SALES"]

            if len(trial_sales) >= 2 and len(control_sales) >= 2:
                stat, p = ttest_ind(trial_sales, control_sales, equal_var=False)
                uplift = (trial_sales.mean() - control_sales.mean()) / control_sales.mean() * 100
                sig = "✅ statistically significant" if p < 0.05 else "⚠️ not statistically significant"
                st.markdown(
                    f"**Trial-period sales uplift vs control:** "
                    f"`{uplift:+.1f}%` &nbsp;|&nbsp; t = `{stat:.2f}`, p = `{p:.3f}` → {sig}"
                )
            else:
                st.info("Not enough trial-period months to run a t-test yet.")

            st.markdown("---")

# ---- Insights ---------------------------------------------------------
with tab_insights:
    section_tag("Auto-generated")
    st.subheader("Headline takeaways")

    top_segment = data.groupby(["LIFESTAGE", "PREMIUM_CUSTOMER"])["TOT_SALES"].sum().idxmax()
    top_freq_segment = (
        data.groupby(["LIFESTAGE", "PREMIUM_CUSTOMER"])["TXN_ID"].nunique().idxmax()
    )
    top_brand_name = data.groupby("BRAND")["TOT_SALES"].sum().idxmax()
    top_pack = int(data.groupby("PACK_SIZE")["TOT_SALES"].sum().idxmax())
    premium_price = data[data["PREMIUM_CUSTOMER"] == "Premium"]["PRICE_PER_UNIT"].mean()
    other_price = data[data["PREMIUM_CUSTOMER"] != "Premium"]["PRICE_PER_UNIT"].mean()
    price_note = "higher" if premium_price > other_price else "lower"

    st.markdown(f"""
- 🏆 **Highest-spending segment:** {top_segment[0].title()} — {top_segment[1]}
- 🔁 **Highest purchase frequency:** {top_freq_segment[0].title()} — {top_freq_segment[1]}
- 🏷️ **Most popular brand:** {top_brand_name}
- 📦 **Most popular pack size:** {top_pack}g
- 💲 **Premium customers pay a {price_note} price per unit** (${premium_price:.2f} vs ${other_price:.2f})
    """)

    st.markdown("#### 🧪 Store trial recap")
    st.caption(
        "Select control stores in the **Store Trial Analysis** tab — uplift and "
        "significance for each trial/control pair will be summarized there as you configure them."
    )

    st.markdown("#### 🎯 Strategic recommendations")
    st.markdown("""
- Focus promotions and shelf placement on the top-value customer segment identified above.
- Prioritise inventory and end-cap space for best-selling brands and pack sizes.
- Tailor campaign messaging by lifestage and premium tier rather than a one-size-fits-all approach.
- If a trial store shows a significant, positive uplift over its control, recommend
  rolling out the trial initiative chain-wide; if not significant, extend the trial
  period or refine the control-store match before deciding.
""")

st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit + Plotly · Quantium Chip Analytics")
