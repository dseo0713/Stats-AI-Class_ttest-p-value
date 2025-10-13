import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
import platform
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
    
st.set_page_config(page_title="독립표본 t-검증증 프로그램 (최종)", layout="centered")

from matplotlib import font_manager as fm
from pathlib import Path

# 폰트 파일 탐색: fonts/ 또는 레포 루트에 있으면 자동 등록
base = Path(__file__).resolve().parent
font_paths = [
    base / "fonts" / "NanumGothic.ttf",
    base / "NanumGothic.ttf",
    base / "fonts" / "NotoSansKR-Regular.otf",
    base / "NotoSansKR-Regular.otf",
]

added = False
for p in font_paths:
    if p.exists() and p.suffix.lower() in {".ttf", ".otf", ".ttc"} and p.stat().st_size > 10_000:
        try:
            fm.fontManager.addfont(str(p))
            added = True
            break
        except Exception:
            # 손상/비정상 파일은 스킵
            pass
# added=False여도 이후 OS별 후보/설치 폰트 탐색 로직으로 계속 진행


    # 2) 보조 후보 목록 (설치 환경별 차이를 흡수)
    candidates = [
        primary,
        "NanumGothic",
        "Noto Sans CJK KR",
        "Noto Sans KR",
        "Noto Sans CJK",
        "Noto Sans",
        "AppleGothic",
        "Malgun Gothic",
        "NanumBarunGothic",
    ]

    installed = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in installed:
            matplotlib.rcParams["font.family"] = name
            break
    else:
        # 최후의 보루(영문 기본) — 한글 미지원일 수 있으나 그대로 둠
        matplotlib.rcParams["font.family"] = matplotlib.rcParams.get("font.family", "DejaVu Sans")

    matplotlib.rcParams["axes.unicode_minus"] = False

# Fonts
ensure_korean_font()

st.title("DW SEO] 독립표본 t-검증 프로그램")

# Sidebar
st.sidebar.header("옵션")
tail = st.sidebar.radio("검증 방향", ["양측(two-tailed)", "단측(one-tailed, A > B)", "단측(one-tailed, A < B)"], index=0)
alpha = st.sidebar.number_input("유의수준 α", min_value=0.001, max_value=0.5, value=0.05, step=0.01, format="%.3f")
show_plots = st.sidebar.checkbox("요약 그래프(평균±95% CI)", value=True)

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
    st.info("업로드된 파일이 없으면 아래의 예시 데이터를 사용합니다.")
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
st.subheader("2) 독립변수(집단) 통계")

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
st.subheader("3) 검증 결과")
equal_var = True

tstat, p_two = stats.ttest_ind(x, y, equal_var=equal_var, alternative="two-sided")

if "단측" in tail:
    if "A > B" in tail:
        p_val = p_two/2.0 if tstat > 0 else 1 - (p_two/2.0)
    else:
        p_val = p_two/2.0 if tstat < 0 else 1 - (p_two/2.0)
else:
    p_val = p_two

def sig_stars(p):
    if p < 0.001:
        return "(***)"
    elif p < 0.01:
        return "(**)"
    elif p < 0.05:
        return "(*)"
    else:
        return ""

stars = sig_stars(p_val)

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
    st.metric("t-값", f"{tstat:.4f}")
    st.metric("자유도(df)", f"{df:.2f}")
with c2:
    st.metric(f"p-값 {stars}", f"{p_val:.4f}")
    st.metric("평균차 (A-B)", f"{mean_diff:.2f}")

st.write(f"신뢰구간 (95%): [{ci_low:.2f}, {ci_high:.2f}]")

decision = "유의함(H0 기각)" if p_val < alpha else "유의하지 않음(H0 기각 불가)"
st.success(f"결론: {decision} (α={alpha}, p={p_val:.4f})")

# 4) Narrative
st.markdown("---")
st.subheader("4) 해석")

if "양측" in tail:
    tail_txt = "양측검증"
elif "A > B" in tail:
    tail_txt = "단측검증(H1: A>B)"
else:
    tail_txt = "단측검증(H1: A<B)"

report = (
    f"<b style='color:red;'>{tail_txt} 기준으로 {g1}의 평균({m1:.2f})과 "
    f"{g2}의 평균({m2:.2f})을 비교한 결과, "
    f"t={tstat:.2f}, df={df:.0f}, p={p_val:.4f}로 "
    f"{'통계적으로 유의미한 차이가 있었다' if p_val < alpha else '유의미한 차이가 없었다'}."
    f" 평균차({g1}-{g2})={mean_diff:.2f}, 95% CI [{ci_low:.2f}, {ci_high:.2f}] 이다.</b>"
)
st.markdown(report, unsafe_allow_html=True)

# 5) Plot
if show_plots:
    st.subheader("5) 요약 그래프")

    fig, ax = plt.subplots(figsize=(2.5, 1.8), dpi=240)

    ax.bar([g1, g2], [m1, m2], width=0.7, color="#1f77b4", edgecolor="black", linewidth=0.8, antialiased=True)
    ax.errorbar([g1, g2], [m1, m2],
                yerr=[tcrit*se1, tcrit*se2],
                fmt='none', capsize=4, color='black', elinewidth=1.2, antialiased=True)

    ax.set_ylabel("값(평균)", fontsize=5)
    ax.set_title("평균 ± 신뢰구간(95%)", fontsize=5)
    ax.tick_params(axis='x', labelsize=5)
    ax.tick_params(axis='y', labelsize=5)

    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

    plt.tight_layout(pad=0.05)
    st.pyplot(fig, use_container_width=False)
