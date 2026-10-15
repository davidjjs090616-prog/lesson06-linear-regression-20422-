import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"

st.set_page_config(page_title="기온 예측기", page_icon="🌡️", layout="wide")
st.title("기온 예측기")


@st.cache_data
def load_yearly():
    df = pd.read_csv(DATA_URL, encoding="utf-8")
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")
    df = df.dropna(subset=["날짜", "평균기온"]).copy()
    df["연도"] = df["날짜"].dt.year

    # 날짜별로 정리하여 관측일을 중복 계산하지 않는다.
    daily = (
        df.groupby(["연도", df["날짜"].dt.date])["평균기온"]
        .mean()
        .reset_index(name="평균기온")
    )

    grouped = (
        daily.groupby("연도")["평균기온"]
        .agg(["mean", "count"])
        .reset_index()
    )

    # 2025년까지, 유효 관측일이 300일 이상인 연도만 사용한다.
    valid = (grouped["연도"] <= 2025) & (grouped["count"] >= 300)
    yearly = grouped.loc[valid].rename(columns={"mean": "연평균기온"})
    return yearly.sort_values("연도").reset_index(drop=True)


try:
    yearly = load_yearly()
    if len(yearly) < 2:
        st.error("회귀 분석에 사용할 수 있는 연도가 충분하지 않습니다.")
        st.stop()
except Exception as e:
    st.error("서울 기온 데이터를 불러오거나 처리하는 중 문제가 발생했습니다.")
    st.exception(e)
    st.stop()

# 전체 기간 회귀 직선
a, b = np.polyfit(yearly["연도"], yearly["연평균기온"], 1)
full_rise = a * 100

# 가장 최근 유효 연도부터 20년 범위의 자료로 회귀 직선을 계산한다.
last_year = int(yearly["연도"].max())
recent_start = last_year - 19
recent = yearly[yearly["연도"] >= recent_start].copy()

if len(recent) >= 2:
    recent_a, recent_b = np.polyfit(recent["연도"], recent["연평균기온"], 1)
    recent_rise = recent_a * 100
else:
    recent_a, recent_b, recent_rise = np.nan, np.nan, np.nan

st.subheader("100년당 기온 변화량")
col1, col2 = st.columns(2)

with col1:
    st.metric("전체 기간", f"{full_rise:+.2f} °C")
    st.caption(
        f"{int(yearly['연도'].min())}~{last_year}년 "
        f"({len(yearly)}개 연도)"
    )

with col2:
    if np.isfinite(recent_rise):
        st.metric("최근 20년", f"{recent_rise:+.2f} °C")
        st.caption(
            f"{int(recent['연도'].min())}~{int(recent['연도'].max())}년 "
            f"({len(recent)}개 연도)"
        )
    else:
        st.warning("최근 20년 자료가 부족해 기울기를 계산할 수 없습니다.")

st.caption("양수는 상승 추세, 음수는 하강 추세를 뜻합니다. 과거 추세를 100년 기준으로 환산한 값이며 미래를 보장하지 않습니다.")

fig = px.scatter(
    yearly,
    x="연도",
    y="연평균기온",
    opacity=0.6,
    title="서울 연평균기온과 회귀 직선",
    labels={"연도": "연도", "연평균기온": "연평균기온 (°C)"},
)

line_years = np.linspace(yearly["연도"].min(), yearly["연도"].max(), 200)
fig.add_scatter(
