
    # 2025년까지의 자료 중 유효 관측일이 300일 이상인 해만 사용한다.
    valid = (grouped["연도"] <= 2025) & (grouped["count"] >= 300)
    return grouped.loc[valid].rename(columns={"mean": "연평균기온"})


try:
    yearly = load_yearly()
    if len(yearly) < 2:
        st.error("회귀 분석에 사용할 수 있는 연도가 충분하지 않습니다.")
        st.stop()
except Exception as e:
    st.error("서울 기온 데이터를 불러오거나 처리하는 중 문제가 발생했습니다.")
    st.exception(e)
    st.stop()

yearly = yearly.sort_values("연도").reset_index(drop=True)

# 전체 기간 회귀
a, b = np.polyfit(yearly["연도"], yearly["연평균기온"], 1)
rise_100_years = a * 100

# 최근 20년: 가장 최근 연도에서 20년 전까지의 연도 자료
last_year = int(yearly["연도"].max())
recent_start = last_year - 19
recent = yearly[yearly["연도"] >= recent_start].copy()

if len(recent) >= 2:
    recent_a, recent_b = np.polyfit(recent["연도"], recent["연평균기온"], 1)
    recent_rise_100_years = recent_a * 100
else:
    recent_a, recent_b = np.nan, np.nan
    recent_rise_100_years = np.nan

# 큰 숫자로 100년당 기온 변화량을 나란히 표시
st.subheader("100년당 기온 변화량")
left, right = st.columns(2)
with left:
    st.metric(
        "전체 기간",
        f"{rise_100_years:+.2f} °C",
        help=f"{int(yearly['연도'].min())}~{last_year}년 자료의 회귀 기울기를 100배한 값입니다.",
    )
    st.caption(
        f"분석 기간: {int(yearly['연도'].min())}~{last_year}년 "
        f"({len(yearly)}개 연도)"
    )
with right:
    if np.isfinite(recent_rise_100_years):
        st.metric(
            "최근 20년",
            f"{recent_rise_100_years:+.2f} °C",
            help=f"{recent_start}~{last_year}년 자료의 회귀 기울기를 100배한 값입니다.",
        )
        st.caption(
            f"분석 기간: {int(recent['연도'].min())}~{int(recent['연도'].max())}년 "
            f"({len(recent)}개 연도)"
        )
    else:
        st.warning("최근 20년 자료가 부족해 기울기를 계산할 수 없습니다.")

st.caption("양수는 기온 상승 추세, 음수는 하강 추세를 뜻합니다. 100년당 변화량은 관측된 추세를 환산한 값이며 미래를 보장하지 않습니다.")

# 산점도와 전체 기간 회귀 직선, 최근 20년 회귀 직선을 표시
fig = px.scatter(
    yearly,
    x="연도",
    y="연평균기온",
    opacity=0.6,
    title="서울 연평균기온과 회귀 직선 비교",
    labels={"연도": "연도", "연평균기온": "연평균기온 (℃)"},
)

line_years = np.linspace(yearly["연도"].min(), yearly["연도"].max(), 200)
fig.add_scatter(
    x=line_years,
    y=a * line_years + b,
    mode="lines",
    name="전체 기간 회귀 직선",
)
if len(recent) >= 2:
    recent_line_years = np.linspace(recent["연도"].min(), recent["연도"].max(), 100)
    fig.add_scatter(
        x=recent_line_years,
        y=recent_a * recent_line_years + recent_b,
        mode="lines",
        name="최근 20년 회귀 직선",
    )
st.plotly_chart(fig, use_container_width=True)

st.metric(
    "전체 기간 연도와 연평균기온의 상관계수",
    f"{yearly['연도'].corr(yearly['연평균기온']):.3f}",
)

year = st.slider("예측할 연도를 고르세요", 1900, 2100, 2045)
st.metric(f"{year}년 예상 연평균기온", f"{a * year + b:.1f}℃")

if year < yearly["연도"].min() or year > yearly["연도"].max():
    st.info("학습 범위 밖의 외삽값입니다. 실제 미래 기온을 보장하지 않습니다.")

with st.expander("연도별 데이터 보기"):
    shown = yearly.rename(columns={"count": "관측일수"}).copy()
    shown["연평균기온"] = shown["연평균기온"].round(2)
    st.dataframe(shown, use_container_width=True, hide_index=True)
