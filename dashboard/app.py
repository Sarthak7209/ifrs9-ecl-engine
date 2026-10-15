import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from staging import apply_staging  # noqa: E402

DATA_PATH = ROOT / "data" / "processed" / "ecl_scenario_results.csv"
STAGES = ["Stage 1", "Stage 2", "Stage 3"]

st.set_page_config(page_title="IFRS 9 ECL Engine", layout="wide")


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


@st.cache_data
def stressed_stages(dpd_shock, score_shock):
    """Re-run the real staging rules after adding extra delinquency and score deterioration."""
    data = load_data().copy()
    data["days_past_due"] = data["days_past_due"] + dpd_shock
    data["credit_score_change"] = data["credit_score_change"] - score_shock
    return apply_staging(data)["stage"]


def segment_table(data, column):
    table = data.groupby(column).agg(
        loans=("loan_id", "count"),
        exposure=("EAD", "sum"),
        ECL=("ECL_selected", "sum"),
    )
    table["coverage_ratio"] = table["ECL"] / table["exposure"]
    return table


df = load_data()

# ---------- Sidebar: scenario selector ----------
st.sidebar.header("Macro scenario")
scenario = st.sidebar.radio(
    "Choose scenario",
    ["Weighted", "Base", "Adverse", "Severe", "Custom multiplier"],
)
custom_mult = 1.0
if scenario == "Custom multiplier":
    custom_mult = st.sidebar.slider("PD multiplier", 1.0, 4.0, 1.5, 0.1)

st.sidebar.caption(
    "Weighted = 60% Base, 30% Adverse, 10% Severe. "
    "Base = PD x1.0, Adverse = x1.5, Severe = x2.5. PD is capped at 100%."
)

if scenario == "Custom multiplier":
    df["ECL_selected"] = np.clip(df["PD_used"] * custom_mult, 0, 1) * df["LGD"] * df["EAD"]
elif scenario == "Weighted":
    df["ECL_selected"] = df["ECL_weighted"]
else:
    df["ECL_selected"] = df[f"ECL_{scenario}"]

total_ead = df["EAD"].sum()
total_ecl = df["ECL_selected"].sum()

# ---------- Header and KPIs ----------
st.title("IFRS 9 Expected Credit Loss Engine")
st.caption(
    "Synthetic retail loan portfolio of 10,000 loans. "
    "ECL = PD x LGD x EAD, with Stage 1/2/3 classification and macroeconomic scenarios."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Loans", f"{len(df):,}")
c2.metric("Total exposure (EAD)", f"${total_ead:,.0f}")
c3.metric(f"ECL ({scenario})", f"${total_ecl:,.0f}")
c4.metric("Coverage ratio", f"{total_ecl / total_ead:.2%}")

tab_overview, tab_segments, tab_stress = st.tabs(
    ["Overview by stage", "Segment drill-down", "Stress and stage migration"]
)

# ---------- Tab 1: overview ----------
with tab_overview:
    stage_table = df.groupby("stage").agg(
        loans=("loan_id", "count"),
        exposure=("EAD", "sum"),
        ECL_Base=("ECL_Base", "sum"),
        ECL_Adverse=("ECL_Adverse", "sum"),
        ECL_Severe=("ECL_Severe", "sum"),
        ECL_weighted=("ECL_weighted", "sum"),
        ECL_selected=("ECL_selected", "sum"),
    )
    stage_table["coverage_ratio"] = stage_table["ECL_selected"] / stage_table["exposure"]

    left, right = st.columns(2)
    with left:
        st.subheader(f"ECL by stage ({scenario})")
        st.bar_chart(stage_table["ECL_selected"])
    with right:
        st.subheader("Share of loans vs share of ECL")
        mix = pd.DataFrame(
            {
                "% of loans": stage_table["loans"] / stage_table["loans"].sum(),
                "% of ECL": stage_table["ECL_selected"] / stage_table["ECL_selected"].sum(),
            }
        )
        st.bar_chart(mix)

    st.subheader("Total ECL under each scenario")
    scen_totals = pd.Series(
        {
            "Base": df["ECL_Base"].sum(),
            "Adverse": df["ECL_Adverse"].sum(),
            "Severe": df["ECL_Severe"].sum(),
            "Weighted": df["ECL_weighted"].sum(),
        }
    )
    st.bar_chart(scen_totals)

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
                "ECL_selected": "${:,.0f}",
                "coverage_ratio": "{:.2%}",
            }
        ),
        use_container_width=True,
    )

# ---------- Tab 2: segments ----------
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
        st.subheader(f"ECL ($, {scenario})")
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

# ---------- Tab 3: stress and stage migration ----------
with tab_stress:
    st.subheader("What if borrowers deteriorate?")
    st.write(
        "Add extra days past due and extra credit score decline to every loan, then re-run the staging rules. "
        "This is a what-if on a single snapshot, not observed migration over time. "
        "Base-scenario PDs are used so you see the effect of staging on its own."
    )

    s1, s2 = st.columns(2)
    dpd_shock = s1.slider("Extra days past due on every loan", 0, 60, 15, 5)
    score_shock = s2.slider("Extra credit score drop on every loan (points)", 0, 40, 10, 5)

    new_stage = stressed_stages(dpd_shock, score_shock)

    migration = (
        pd.crosstab(df["stage"], new_stage)
        .reindex(index=STAGES, columns=STAGES, fill_value=0)
    )
    migration.index.name = "Current stage"
    migration.columns.name = "Stage after stress"

    row_totals = migration.sum(axis=1).replace(0, np.nan)
    migration_pct = migration.div(row_totals, axis=0).fillna(0)

    m1, m2 = st.columns(2)
    with m1:
        st.write("Number of loans")
        st.dataframe(migration, use_container_width=True)
    with m2:
        st.write("Share of each current stage")
        st.dataframe(migration_pct.style.format("{:.1%}"), use_container_width=True)

    # ECL after migration: stage decides 12-month vs lifetime PD
    pd_after = np.where(new_stage == "Stage 1", df["PD_12month"], df["PD_lifetime"])
    ecl_after_loans = pd_after * df["LGD"] * df["EAD"]
    ecl_before = df["ECL_Base"].sum()
    ecl_after = ecl_after_loans.sum()

    k1, k2, k3 = st.columns(3)
    k1.metric("Base ECL today", f"${ecl_before:,.0f}")
    k2.metric("Base ECL after stress", f"${ecl_after:,.0f}")
    k3.metric(
        "Change",
        f"${ecl_after - ecl_before:,.0f}",
        f"{(ecl_after / ecl_before - 1):+.1%}",
    )

    st.subheader("ECL by stage after stress")
    st.bar_chart(ecl_after_loans.groupby(new_stage).sum().reindex(STAGES).fillna(0))

    moved_up = int((new_stage != df["stage"]).sum())
    st.info(
        f"{moved_up:,} loans change stage. Each Stage 1 to Stage 2 move switches that loan from "
        "12-month PD to lifetime PD, which is why ECL can jump even though only a few loans cross a threshold."
    )