import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
import platform
import matplotlib
import matplotlib.pyplot as plt

st.set_page_config(page_title="독립표본 t-검정 프로그램 (최종)", layout="centered")

# Fonts
if platform.system() == "Windows":
    matplotlib.rcParams["font.family"] = "Malgun Gothic"
elif platform.system() == "Darwin":
    matplotlib.rcParams["font.family"] = "AppleGothic"
else:
    matplotlib.rcParams["font.family"] = "NanumGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

st.title("독립표본 t-검정 프로그램")

# Sidebar
st.sidebar.header("옵션")
tail = st.sidebar.radio("검정 방향", ["양측(two-tailed)", "단측(one-tailed, A > B)", "단측(one-tailed, A < B)"], index=0)
alpha = st.sidebar.number_input("유의수준 α", min_value=0.001, max_value=0.5, value=0.05, step=0.01, format="%.3f")
show_plots = st.sidebar.checkbox("요약 그래프(평균±95% CI) 표시", value=True)

# 1) Upload
st.subheader("1) 데이터 업로드")
uploaded = st.file_uploader("CSV 또는 Excel(.xlsx/.xls) 업로드 (열: group, value)", type=["csv","xlsx","xls"])

data = None
if uploaded is not None:
    name = uploaded.name.lower()
    try:
        if name.endswith(".csv"):
            data = pd.read_csv(uploaded)
        else:
            xls = pd.ExcelFile(uploaded)
            sheet_name = st.selectbox("엑셀 시트 선택", xls.sheet_names, index=0)
            data = pd.read_excel(xls, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        st.stop()

if data is None:
    st.info("업로드가 없으면 예시 데이터를 사용합니다.")
    data = pd.DataFrame({
        "group": ["남자"]*7 + ["여자"]*6,
        "value": [78,67,97,87,78,76,79, 56,76,56,45,65,55]
    })

# Column mapping
cols = list(data.columns)
if not {"group","value"}.issubset(cols):
    st.warning("열 이름이 'group'과 'value'가 아닙니다. 아래에서 매핑을 선택하세요.")
    group_col = st.selectbox("집단 열", cols, index=0)
    value_col = st.selectbox("값 열", cols, index=1 if len(cols)>1 else 0)
    data = data.rename(columns={group_col:"group", value_col:"value"})

# Clean & split
data = data.dropna(subset=["group","value"])
try:
    data["value"] = pd.to_numeric(data["value"])
except Exception:
    st.error("값(value) 열은 숫자여야 합니다.")
    st.stop()

groups = data["group"].unique()
if len(groups) != 2:
    st.error(f"두 개의 집단만 필요합니다. 현재 집단: {list(groups)}")
    st.stop()

g1, g2 = groups[0], groups[1]
x = data.loc[data["group"]==g1, "value"].to_numpy(dtype=float)
y = data.loc[data["group"]==g2, "value"].to_numpy(dtype=float)

# 2) Descriptives
st.subheader("2) 기술통계")

def descriptives(arr):
    n = len(arr)
    mean = float(np.mean(arr)) if n>0 else np.nan
    sd = float(np.std(arr, ddof=1)) if n>1 else np.nan
    var = float(np.var(arr, ddof=1)) if n>1 else np.nan
    return n, mean, sd, var

n1, m1, sd1, var1 = descriptives(x)
n2, m2, sd2, var2 = descriptives(y)

desc_df = pd.DataFrame({
    "집단": [g1, g2],
    "사례수(n)": [n1, n2],
    "평균": [m1, m2],
    "표준편차": [sd1, sd2],
    "분산": [var1, var2],
})

try:
    desc_df["사례수(n)"] = desc_df["사례수(n)"].astype(int)
except Exception:
    pass

styled_desc = (
    desc_df.style
        .set_properties(**{"text-align": "center"})
        .set_table_styles([{"selector": "th", "props": [("text-align", "center")]}])
        .format({"평균": "{:.2f}", "표준편차": "{:.2f}", "분산": "{:.2f}"})
)
st.markdown(styled_desc.to_html(), unsafe_allow_html=True)

# 3) t-test (equal variance assumed)
st.subheader("3) 검정 결과")
equal_var = True

tstat, p_two = stats.ttest_ind(x, y, equal_var=equal_var, alternative="two-sided")

if "단측" in tail:
    if "A > B" in tail:
        p_val = p_two/2.0 if tstat > 0 else 1 - (p_two/2.0)
    else:
        p_val = p_two/2.0 if tstat < 0 else 1 - (p_two/2.0)
else:
    p_val = p_two

df = n1 + n2 - 2

mean_diff = m1 - m2
sp2 = ((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2) if df>0 else np.nan
se1 = np.sqrt(var1/n1); se2 = np.sqrt(var2/n2)
se_diff = np.sqrt(sp2*(1/n1 + 1/n2)) if df>0 else np.nan
tcrit = stats.t.ppf(1 - alpha/2, df) if "양측" in tail else stats.t.ppf(1 - alpha, df)
ci_low = mean_diff - tcrit*se_diff
ci_high = mean_diff + tcrit*se_diff

c1, c2 = st.columns(2)
with c1:
    st.metric("t 통계량", f"{tstat:.4f}")
    st.metric("자유도 df", f"{df:.2f}")
with c2:
    st.metric("p 값", f"{p_val:.4f}")
    st.metric("평균차 (A-B)", f"{mean_diff:.2f}")

st.write(f"신뢰구간 (95%): [{ci_low:.2f}, {ci_high:.2f}]")

decision = "유의함(H0 기각)" if p_val < alpha else "유의하지 않음(H0 기각 불가)"
st.success(f"결론: {decision} (α={alpha}, p={p_val:.4f})")

# 4) Narrative
st.markdown("---")
st.subheader("4) 해석(리포트 문장)")
if "양측" in tail:
    tail_txt = "양측검정"
elif "A > B" in tail:
    tail_txt = "단측검정(H1: A>B)"
else:
    tail_txt = "단측검정(H1: A<B)"
report = (f"{tail_txt} 기준으로 {g1}의 평균({m1:.2f})과 {g2}의 평균({m2:.2f})을 비교한 결과, "
          f"t={tstat:.2f}, df={df:.0f}, p={p_val:.4f}로 "
          f"{'통계적으로 유의한 차이가 있었다' if p_val < alpha else '유의한 차이가 없었다'}. "
          f"평균차({g1}-{g2})={mean_diff:.2f}, 95% CI [{ci_low:.2f}, {ci_high:.2f}] 입니다.")
st.write(report)

# 5) Plot
if show_plots:
    st.subheader("5) 요약 그래프")
    fig, ax = plt.subplots()
    ax.bar([g1, g2], [m1, m2])
    ax.errorbar([g1, g2], [m1, m2], yerr=[tcrit*se1, tcrit*se2], fmt='none', capsize=6)
    ax.set_ylabel("값(평균)")
    ax.set_title("평균 ± 신뢰구간(95%)")
    st.pyplot(fig)
