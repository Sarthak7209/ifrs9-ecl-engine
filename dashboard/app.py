import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="IFRS 9 ECL Engine", layout="wide")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "ecl_scenario_results.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)

    # Rebuild readable segment columns from the one-hot columns (dropped category = all zeros)
    df["loan_type"] = np.where(df["loan_type_term"].astype(int) == 1, "term", "revolving")
    df["region"] = np.select(
        [df["region_North"].astype(int) == 1, df["region_South"].astype(int) == 1, df["region_West"].astype(int) == 1],
        ["North", "South", "West"],
        default="East",
    )
    df["loan_purpose"] = np.select(
        [
            df["loan_purpose_debt_consolidation"].astype(int) == 1,
            df["loan_purpose_home_improvement"].astype(int) == 1,
            df["loan_purpose_personal"].astype(int) == 1,
        ],
        ["debt_consolidation", "home_improvement", "personal"],
        default="auto",
    )
    df["credit_score_band"] = pd.cut(
        df["orig_credit_score"],
        bins=[300, 580, 650, 700, 750, 850],
        labels=["Poor", "Fair", "Good", "Very Good", "Excellent"],
        include_lowest=True,
    ).astype(str)
    return df


def segment_table(data, column):
    table = data.groupby(column).agg(
        loans=("loan_id", "count"),
        exposure=("EAD", "sum"),
        ECL=("ECL_weighted", "sum"),
    )
    table["coverage_ratio"] = table["ECL"] / table["exposure"]
    return table


df = load_data()
total_ead = df["EAD"].sum()
total_ecl = df["ECL_weighted"].sum()

st.title("IFRS 9 Expected Credit Loss Engine")
st.caption(
    "Synthetic retail loan portfolio of 10,000 loans. "
    "ECL = PD x LGD x EAD, with Stage 1/2/3 classification and macroeconomic scenarios."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Loans", f"{len(df):,}")
c2.metric("Total exposure (EAD)", f"${total_ead:,.0f}")
c3.metric("Weighted ECL", f"${total_ecl:,.0f}")
c4.metric("Coverage ratio", f"{total_ecl / total_ead:.2%}")

tab_overview, tab_segments = st.tabs(["Overview by stage", "Segment drill-down"])

with tab_overview:
    stage_table = df.groupby("stage").agg(
        loans=("loan_id", "count"),
        exposure=("EAD", "sum"),
        ECL_Base=("ECL_Base", "sum"),
        ECL_Adverse=("ECL_Adverse", "sum"),
        ECL_Severe=("ECL_Severe", "sum"),
        ECL_weighted=("ECL_weighted", "sum"),
    )
    stage_table["coverage_ratio"] = stage_table["ECL_weighted"] / stage_table["exposure"]

    left, right = st.columns(2)
    with left:
        st.subheader("Weighted ECL by stage")
        st.bar_chart(stage_table["ECL_weighted"])
    with right:
        st.subheader("Share of loans vs share of ECL")
        mix = pd.DataFrame(
            {
                "% of loans": stage_table["loans"] / stage_table["loans"].sum(),
                "% of ECL": stage_table["ECL_weighted"] / stage_table["ECL_weighted"].sum(),
            }
        )
        st.bar_chart(mix)

    st.subheader("Stage summary")
    st.dataframe(
        stage_table.style.format(
            {
                "loans": "{:,.0f}",
                "exposure": "${:,.0f}",
                "ECL_Base": "${:,.0f}",
                "ECL_Adverse": "${:,.0f}",
                "ECL_Severe": "${:,.0f}",
                "ECL_weighted": "${:,.0f}",
                "coverage_ratio": "{:.2%}",
            }
        ),
        use_container_width=True,
    )

with tab_segments:
    labels = {
        "Loan type": "loan_type",
        "Loan purpose": "loan_purpose",
        "Region": "region",
        "Credit score band": "credit_score_band",
    }
    choice = st.selectbox("Break the portfolio down by", list(labels.keys()))
    seg = segment_table(df, labels[choice])

    left, right = st.columns(2)
    with left:
        st.subheader("Weighted ECL ($)")
        st.bar_chart(seg["ECL"])
    with right:
        st.subheader("Coverage ratio (ECL / exposure)")
        st.bar_chart(seg["coverage_ratio"])

    st.dataframe(
        seg.style.format(
            {"loans": "{:,.0f}", "exposure": "${:,.0f}", "ECL": "${:,.0f}", "coverage_ratio": "{:.2%}"}
        ),
        use_container_width=True,
    )