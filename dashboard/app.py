import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="IFRS 9 ECL Engine", layout="wide")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "ecl_scenario_results.csv"


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


df = load_data()
total_ead = df["EAD"].sum()

st.title("IFRS 9 Expected Credit Loss Engine")
st.caption("Synthetic retail loan portfolio of 10,000 loans. ECL = PD x LGD x EAD, with Stage 1/2/3 classification and macroeconomic scenarios.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Loans", f"{len(df):,}")
c2.metric("Total exposure (EAD)", f"${total_ead:,.0f}")
c3.metric("Weighted ECL", f"${df['ECL_weighted'].sum():,.0f}")
c4.metric("Coverage ratio", f"{df['ECL_weighted'].sum() / total_ead:.2%}")

st.subheader("ECL by stage")
stage_table = df.groupby("stage").agg(
    loans=("loan_id", "count"),
    exposure=("EAD", "sum"),
    ECL_Base=("ECL_Base", "sum"),
    ECL_Adverse=("ECL_Adverse", "sum"),
    ECL_Severe=("ECL_Severe", "sum"),
    ECL_weighted=("ECL_weighted", "sum"),
).round(0)
st.dataframe(stage_table, use_container_width=True)