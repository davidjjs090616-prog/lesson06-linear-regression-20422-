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

st.caption(
    f"회귀 직선에 사용한 기간: {start_year}년~{end_year}년 "
    f"({year_count}개 연도, 연도별 유효 관측일 {MIN_OBSERVATION_DAYS}일 이상)"
)

# 산점도, 회귀 직선, 슬라이더로 선택한 연도의 예측 지점을 함께 표시합니다.
line_years = np.linspace(start_year, 2100, 300)
line_temps = slope * line_years + intercept

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["연평균기온"],
        mode="markers",
        name="관측 연평균기온",
        marker=dict(size=7, opacity=0.75),
        customdata=annual[["관측일수"]].to_numpy(),
        hovertemplate=(
            "연도: %{x:.0f}년<br>"
            "연평균기온: %{y:.2f} °C<br>"
            "관측일수: %{customdata[0]}일<extra></extra>"
        ),
    )
)
fig.add_trace(
    go.Scatter(
        x=line_years,
        y=line_temps,
        mode="lines",
        name="선형 회귀 직선",
        line=dict(width=3),
        hovertemplate="연도: %{x:.0f}년<br>회귀 기온: %{y:.2f} °C<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=[selected_year],
        y=[predicted_temp],
        mode="markers",
        name=f"{selected_year}년 예측",
        marker=dict(size=13, symbol="star"),
        hovertemplate="%{x:.0f}년 예상 기온: %{y:.2f} °C<extra></extra>",
    )
)
fig.update_layout(
    title="서울 연평균기온과 선형 회귀 직선",
    xaxis_title="연도",
    yaxis_title="연평균기온 (°C)",
    hovermode="closest",
    legend_title="범례",
    margin=dict(l=20, r=20, t=60, b=20),
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("연도별 평균기온 데이터 보기"):
    display_df = annual.rename(
        columns={"연도": "연도", "연평균기온": "연평균기온 (°C)", "관측일수": "관측일수"}
    ).copy()
    display_df["연평균기온 (°C)"] = display_df["연평균기온 (°C)"].round(2)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

with st.expander("분석 방법과 주의사항"):
    st.markdown(
        """
        - 날짜별 평균기온이 유효한 관측만 사용합니다.
        - 2025년 이후 자료는 제외하고, 연도별 유효 관측일이 300일 미만인 해도 제외합니다.
        - 연평균기온을 계산한 뒤, 연도와 연평균기온 사이의 피어슨 상관계수를 구합니다.
        - 회귀 직선은 최소제곱법으로 계산한 단순 선형 회귀입니다.
        - **예상 기온은 과거 추세를 직선으로 연장한 값**입니다. 기후 변화의 복잡한 원인이나 미래의 변동을 모두 반영하지 않으므로 실제 기온 예보로 해석하면 안 됩니다.
        """
    )

st.caption("데이터 출처: 제공된 서울 기온 CSV 파일")
