import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
import platform
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
    
st.set_page_config(page_title="독립표본 t-검증증 프로그램 (최종)", layout="centered")

# --- 폰트 설정: 함수로 캡슐화 (전역에 primary/candidates 남기지 않기) ---
def ensure_korean_font():
    from matplotlib import font_manager as fm
    from pathlib import Path
    import platform
    import matplotlib

    # 1) 레포 내 폰트 파일(있으면) 등록 시도
    base = Path(__file__).resolve().parent
    font_paths = [
        base / "fonts" / "NanumGothic.ttf",
        base / "NanumGothic.ttf",
        base / "fonts" / "NotoSansKR-Regular.otf",
        base / "NotoSansKR-Regular.otf",
    ]
    for p in font_paths:
        if p.exists() and p.suffix.lower() in {".ttf", ".otf", ".ttc"} and p.stat().st_size > 10_000:
            try:
                fm.fontManager.addfont(str(p))
                break
            except Exception:
                pass  # 손상/비정상 파일은 스킵

    # 2) OS별 기본 후보
    if platform.system() == "Windows":
        primary = "Malgun Gothic"
    elif platform.system() == "Darwin":
        primary = "AppleGothic"
    else:
        primary = "NanumGothic"

    # 3) 설치된 폰트 중에서 한글 지원 후보 탐색
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
        matplotlib.rcParams["font.family"] = matplotlib.rcParams.get("font.family", "DejaVu Sans")

    matplotlib.rcParams["axes.unicode_minus"] = False

# Fonts
ensure_korean_font()

st.title("DW SEO] 독립표본 t-검증 프로그램")


# Sidebar
st.markdown("""
<style>
/* 1. 버튼 컨테이너 (정사각형 크기 및 오버플로우 방지) */
[data-testid="stSidebar"] button {
    width: 35px !important; 
    height: 5px !important; 
    padding: 0; 
    line-height: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    font-weight: bold;
    /* 텍스트가 잘리는 것을 방지 */
    overflow: visible !important; 
}

/* 2. 버튼 내부의 텍스트 요소 (p 및 span)를 타겟팅하여 가시성 확보 및 수직 위치 조정 */
/* 중복되는 p와 span 선택자를 통합하고 불필요한 opacity/visibility를 제거하여 코드를 간결하게 정리했습니다. */
[data-testid="stSidebar"] button > div > p,
[data-testid="stSidebar"] button span {
    color: red !important;
    font-size: 20px !important; 
    line-height: 1 !important;
    margin: 0 !important; 
    padding: 0 !important;
    display: block !important;
    /* 텍스트를 위로 살짝 이동시켜 수직 중앙에 맞춤 */
    transform: translateY(3px) !important; 
}


/* 유의수준 숫자를 버튼과 같은 높이에 중앙 정렬합니다. */
[data-testid="stSidebar"] [data-testid="stColumn"] > div {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
}

</style>
""", unsafe_allow_html=True)

# --- Sidebar Content ---
st.sidebar.header("옵션")
tail = st.sidebar.radio("검증 방향", ["양측(two-tailed)", "단측(one-tailed, A > B)", "단측(one-tailed, A < B)"], index=0)

# 유의수준 선택 관련 로직
alpha_options = [0.05, 0.01, 0.001]
if 'alpha_index' not in st.session_state:
    st.session_state.alpha_index = 0

st.sidebar.write("유의수준 $\\alpha$")
col1, col2, col3 = st.sidebar.columns([1, 2, 1])

# "<" 버튼 로직 (왼쪽)
with col1:
    # 텍스트 대신 HTML 엔티티를 사용하여 Streamlit의 텍스트 숨김 문제를 우회합니다.
    # &lt;는 < 기호를 나타냅니다.
    if st.button(" &lt; ", key="alpha_minus"):
        if st.session_state.alpha_index > 0:
            st.session_state.alpha_index -= 1

# 유의수준 값 표시
with col2:
    st.write(f"<div style='text-align: center; font-weight: 600; font-size: 1.1rem;'>{alpha_options[st.session_state.alpha_index]}</div>", unsafe_allow_html=True)

# ">" 버튼 로직 (오른쪽)
with col3:
    # 텍스트 대신 HTML 엔티티를 사용하여 Streamlit의 텍스트 숨김 문제를 우회합니다.
    # &gt;는 > 기호를 나타냅니다.
    if st.button(" &gt; ", key="alpha_plus"):
        if st.session_state.alpha_index < len(alpha_options) - 1:
            st.session_state.alpha_index += 1

alpha = alpha_options[st.session_state.alpha_index]

show_plots = st.sidebar.checkbox("요약 그래프(평균±CI)", value=True)



# 1) Upload
st.markdown("""
<style>
/* 1. "유의사항" 텍스트를 감싸는 div를 타겟팅하여 리스트와의 간격 조정 */
/* st.markdown으로 생성된 마크다운 텍스트를 감싸는 div를 타겟팅합니다. */
div.stMarkdown:has(p > strong:contains("유의사항")) {
    margin-bottom: -10px; /* 음수 마진을 주어 다음 요소(리스트)와의 간격을 줄입니다. */
}

/* 2. 유의사항 리스트 (ul/ol) 자체의 상단 마진을 제거하여 "유의사항" 제목과 밀착시킵니다. */
div.stMarkdown ul {
    margin-top: 0px; /* 리스트와 유의사항 제목 사이의 간격을 최소화합니다. */
}

/* 3. 유의사항 텍스트 (***유의사항**) 바로 밑의 마진을 제거합니다. */
/* st.markdown 내부의 <p> 태그를 타겟팅합니다. */
div.stMarkdown p {
    margin-bottom: 0px; /* 단락 아래의 기본 여백을 제거하여 리스트와 더욱 밀착 */
}
</style>
""", unsafe_allow_html=True)


st.subheader("1) 데이터 업로드")
uploaded = st.file_uploader("Excel(.xlsx/.xls) 업로드", type=["xlsx","xls"])
st.markdown("""
***유의사항**
1. 1번 행(header) > A열 'group' / B열 'value'로 header 정의
2. A열 'group'명 [예: 남,여] 기입 + B열 데이터 입력
3. B열의 모든 데이터는 반드시 숫자(numeric value)
""")

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
st.subheader("2) 독립변수(집단) 기술통계")

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
confidence_level = int((1 - alpha) * 100)
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

st.write(f"신뢰구간 ({confidence_level}%): [{ci_low:.2f}, {ci_high:.2f}]")

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
    f" 평균차({g1}-{g2})={mean_diff:.2f}, {confidence_level}% CI [{ci_low:.2f}, {ci_high:.2f}] 이다.</b>"
)
st.markdown(report, unsafe_allow_html=True)


# 5) Plot
if show_plots:
    st.subheader("5) 요약 그래프")
    
    import matplotlib.font_manager as fm
    from pathlib import Path
    
    base = Path(__file__).resolve().parent
    font_paths = [
        base / "fonts" / "NanumGothic.ttf",
        base / "NanumGothic.ttf",
        base / "fonts" / "NotoSansKR-Regular.otf",
        base / "NotoSansKR-Regular.otf",
    ]
    
    font_loaded = False
    for font_path in font_paths:
        if font_path.exists():
            try:
                fm.fontManager.addfont(str(font_path))
                font_name = fm.FontProperties(fname=str(font_path)).get_name()
                plt.rcParams['font.family'] = font_name
                font_loaded = True
                break
            except Exception:
                pass
    
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(figsize=(2.5, 1.8), dpi=240)
    
    ax.bar([g1, g2], [m1, m2], width=0.7, color="#1f77b4", edgecolor="black", linewidth=0.8, antialiased=True)
    ax.errorbar([g1, g2], [m1, m2], yerr=[tcrit*se1, tcrit*se2], fmt='none', capsize=4, color='black', elinewidth=1.2, antialiased=True)
    
    ax.set_ylabel("값(평균)", fontsize=8)
    ax.set_title(f"평균 ± 신뢰구간({confidence_level}%)", fontsize=8)
    ax.tick_params(axis='x', labelsize=8)
    ax.tick_params(axis='y', labelsize=8)
    
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)
    
    plt.tight_layout(pad=0.05)
    st.pyplot(fig, use_container_width=False)
