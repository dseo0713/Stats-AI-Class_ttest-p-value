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
                st.success(f"폰트 로드 성공: {font_path.name}")
                break
            except Exception:
                pass
    
    if not font_loaded:
        st.warning("한글 폰트를 찾을 수 없습니다.")
    
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(figsize=(2.5, 1.8), dpi=240)
    
    ax.bar([g1, g2], [m1, m2], width=0.7, color="#1f77b4", edgecolor="black", linewidth=0.8, antialiased=True)
    ax.errorbar([g1, g2], [m1, m2], yerr=[tcrit*se1, tcrit*se2], fmt='none', capsize=4, color='black', elinewidth=1.2, antialiased=True)
    
    ax.set_ylabel("값(평균)", fontsize=9)
    ax.set_title("평균 ± 신뢰구간(95%)", fontsize=10)
    ax.tick_params(axis='x', labelsize=9)
    ax.tick_params(axis='y', labelsize=8)
    
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)
    
    plt.tight_layout(pad=0.05)
    st.pyplot(fig, use_container_width=False)
