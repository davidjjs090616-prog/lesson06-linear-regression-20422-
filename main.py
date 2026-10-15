import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
)
CUTOFF_YEAR = 2025
MIN_OBSERVATION_DAYS = 300


st.set_page_config(page_title="기온 예측기", page_icon="🌡️", layout="wide")
st.title("🌡️ 기온 예측기")
st.caption("서울의 연평균기온 데이터를 이용한 단순 선형 회귀 예측")


@st.cache_data
def load_annual_data():
    """CSV를 읽고, 유효한 평균기온 관측일이 300일 이상인 연도만 반환합니다."""
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    required_columns = {"날짜", "평균기온"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"CSV에 필요한 열이 없습니다: {', '.join(sorted(missing))}")

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")
    df = df.dropna(subset=["날짜", "평균기온"]).copy()

    # 수업 기준 기간인 2025년까지의 데이터만 사용합니다.
    df = df[df["날짜"].dt.year <= CUTOFF_YEAR].copy()
    df["연도"] = df["날짜"].dt.year

    # 같은 날짜에 중복 행이 있으면 날짜별 평균을 먼저 계산해 관측일을 중복 집계하지 않습니다.
    daily = (
        df.groupby(["연도", df["날짜"].dt.date], as_index=False)["평균기온"]
        .mean()
        .rename(columns={"날짜": "관측날짜"})
    )

    annual = (
        daily.groupby("연도")
        .agg(
            연평균기온=("평균기온", "mean"),
            관측일수=("평균기온", "count"),
        )
        .reset_index()
    )

    annual = annual[annual["관측일수"] >= MIN_OBSERVATION_DAYS]
    annual = annual.sort_values("연도").reset_index(drop=True)

    if len(annual) < 2:
        raise ValueError("회귀 분석을 하기에 충분한 연도가 없습니다.")

    return annual


try:
    annual = load_annual_data()
except Exception as exc:
    st.error("서울 기온 데이터를 불러오거나 처리하는 중 문제가 발생했습니다.")
    st.exception(exc)
    st.stop()

years = annual["연도"].to_numpy(dtype=float)
temps = annual["연평균기온"].to_numpy(dtype=float)

# 최소제곱법으로 직선 y = slope*x + intercept를 계산합니다.
slope, intercept = np.polyfit(years, temps, 1)
correlation = float(np.corrcoef(years, temps)[0, 1])

start_year = int(annual["연도"].min())
end_year = int(annual["연도"].max())
year_count = len(annual)

st.subheader("연도 선택")
selected_year = st.slider(
    "예측할 연도를 선택하세요",
    min_value=1900,
    max_value=2100,
    value=2026,
    step=1,
)
predicted_temp = slope * selected_year + intercept

metric_col1, metric_col2, metric_col3 = st.columns(3)
with metric_col1:
    st.metric(f"{selected_year}년 예상 연평균기온", f"{predicted_temp:.2f} °C")
with metric_col2:
    st.metric("상관계수", f"{correlation:.4f}")
with metric_col3:
    st.metric("회귀에 사용한 연도 수", f"{year_count}년")
