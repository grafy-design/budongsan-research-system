"""matplotlib 차트 생성 패턴 — v3 부암동 보고서에서 추출.

모든 차트 공통 규칙:
1. 파이차트 절대 X — 가로 막대(barh) 또는 세로 막대(bar)
2. 한글 폰트: NanumGothic (번들) → fallback Noto CJK
3. 라벨에 약어 노출 0 (LOC→입지·접근성 등)
4. 라벨 겹침 0 (tight_layout + 폰트 크기 조절)
5. DPI 150, bbox_inches="tight", facecolor="white"
"""
from pathlib import Path

# ── 한글 폰트 설정 (최초 1회) ──
_KR_FONT_SETUP = False
def _mpl():
    global _KR_FONT_SETUP
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if not _KR_FONT_SETUP:
        from matplotlib import font_manager
        # 번들 폰트 → 시스템 fallback
        bundle = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts" / "NanumGothic.ttf"
        candidates = [
            str(bundle),
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        for fp in candidates:
            try:
                if fp and Path(fp).exists():
                    font_manager.fontManager.addfont(fp)
                    fam = font_manager.FontProperties(fname=fp).get_name()
                    plt.rcParams["font.family"] = fam
                    break
            except Exception:
                continue
        plt.rcParams["axes.unicode_minus"] = False
        _KR_FONT_SETUP = True
    return matplotlib, plt

def _save_chart(fig, name, cache_dir):
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / name
    fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
    return path


# ── 종합점수 게이지 (반원형) ──
def build_score_gauge_chart(cache_dir, total=77.1, grade="B+", percentile=10):
    import numpy as np
    _, plt = _mpl()
    fig, ax = plt.subplots(figsize=(7.5, 4.2), subplot_kw={"projection": "polar"})
    theta = np.linspace(np.pi, 0, 200)
    seg_colors = ["#C0392B", "#E67E22", "#F1C40F", "#2ECC71", "#27AE60", "#1E8449"]
    seg_bounds = [0, 50, 60, 70, 80, 90, 100]
    for i in range(len(seg_colors)):
        lo, hi = seg_bounds[i], seg_bounds[i + 1]
        t = np.linspace(np.pi * (1 - lo/100), np.pi * (1 - hi/100), 50)
        ax.fill_between(t, 0.8, 1.0, color=seg_colors[i], alpha=0.85)
    ang = np.pi * (1 - total/100)
    ax.plot([ang, ang], [0, 0.95], color="#1F294B", linewidth=3.5, zorder=5)
    ax.scatter([ang], [0], color="#1F294B", s=80, zorder=6)
    ax.set_ylim(0, 1.1)
    ax.set_theta_offset(0); ax.set_xticks([]); ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_title(f"종합 점수  {total:.1f} / 100   등급 {grade}   상위 {percentile}%",
                 fontsize=13, color="#1F294B", pad=14, weight="bold")
    out = _save_chart(fig, "score_gauge.png", cache_dir)
    plt.close(fig)
    return out

# ── 8차원 레이더 차트 ──
def build_radar_chart(cache_dir, dims_kr, vals):
    """dims_kr = ["입지·접근성", ...], vals = [70, 92, ...]"""
    import numpy as np
    _, plt = _mpl()
    angles = np.linspace(0, 2*np.pi, len(dims_kr), endpoint=False).tolist()
    vals_c = vals + vals[:1]; angles_c = angles + angles[:1]
    fig, ax = plt.subplots(figsize=(6.8, 5.2), subplot_kw={"polar": True})
    ax.plot(angles_c, vals_c, color="#1F294B", linewidth=2)
    ax.fill(angles_c, vals_c, color="#4A6FA5", alpha=0.35)
    ax.set_xticks(angles); ax.set_xticklabels(dims_kr, fontsize=8, color="#1F294B")
    ax.set_ylim(0, 100); ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=8, color="#666")
    ax.set_title("8차원 레이더", fontsize=11, color="#1F294B", pad=18)
    out = _save_chart(fig, "radar.png", cache_dir)
    plt.close(fig)
    return out

# ── 시나리오 비교 막대 ──
def build_scenario_bars_chart(cache_dir, scenarios):
    """scenarios = [("A 라이프스타일", 79.9), ("B 카페", 73.3), ("C 재건축", 72.4)]"""
    _, plt = _mpl()
    labels = [f"{name}\n({score})" for name, score in scenarios]
    values = [s for _, s in scenarios]
    colors = ["#27AE60", "#C0392B", "#8E44AD"][:len(scenarios)]
    fig, ax = plt.subplots(figsize=(8.0, 3.6))
    bars = ax.bar(labels, values, color=colors, edgecolor="#1F294B", linewidth=0.6, width=0.6)
    for b, v in zip(bars, values):
        ax.text(b.get_x()+b.get_width()/2, v+0.6, f"{v:.1f}", ha="center",
                fontsize=10, weight="bold", color="#1F294B")
    ax.axhline(80, color="#2ECC71", linestyle="--", linewidth=0.7, alpha=0.7)
    ax.axhline(70, color="#F1C40F", linestyle="--", linewidth=0.7, alpha=0.7)
    ax.set_ylim(min(values)-10, max(values)+10)
    ax.set_ylabel("종합 점수", fontsize=10)
    ax.set_title("시나리오 비교", fontsize=11, color="#1F294B", pad=10)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    out = _save_chart(fig, "scenario_bars.png", cache_dir)
    plt.close(fig)
    return out

# ── 간트 차트 ──
def build_gantt_chart(cache_dir, scenario_name, phases, fname):
    """phases = [("단계명", 시작월, 기간월), ...]"""
    _, plt = _mpl()
    fig, ax = plt.subplots(figsize=(8.5, 3.2 + 0.35*len(phases)))
    palette = ["#4A6FA5", "#27AE60", "#E67E22", "#8E44AD", "#C0392B",
               "#16A085", "#D4AC0D", "#7F8C8D"]
    ys = list(range(len(phases)))[::-1]
    for i, (label, start, dur) in enumerate(phases):
        ax.barh(ys[i], dur, left=start, color=palette[i % len(palette)],
                edgecolor="#1F294B", linewidth=0.6, height=0.55)
        ax.text(start + dur/2, ys[i], f"{dur}개월", ha="center", va="center",
                fontsize=8, color="white", weight="bold")
    ax.set_yticks(ys)
    ax.set_yticklabels([p[0] for p in phases], fontsize=9)
    total = max((s+d) for _, s, d in phases)
    ax.set_xlim(0, total + 0.5)
    ax.set_xlabel("개월", fontsize=9)
    ax.set_title(f"Scenario {scenario_name}", fontsize=11, color="#1F294B", pad=10, weight="bold")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.3, linestyle="--")
    out = _save_chart(fig, fname, cache_dir)
    plt.close(fig)
    return out

# ── 평당가 비교 막대 ──
def build_price_comparison_chart(cache_dir, labels, values, subject_idx=0):
    """subject_idx = 본 매물 인덱스 (빨간색 강조)."""
    _, plt = _mpl()
    colors = ["#4A6FA5"] * len(labels)
    colors[subject_idx] = "#C0392B"
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    bars = ax.bar(labels, values, color=colors, edgecolor="#1F294B", linewidth=0.6)
    ax.set_ylabel("평당 토지가 (만원)", fontsize=10)
    ax.set_title("단독주택 평당 토지가 비교", fontsize=11, color="#1F294B", pad=10)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + 80, f"{v:,}",
                ha="center", fontsize=8, color="#1F294B")
    ax.set_ylim(0, max(values) * 1.18)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    out = _save_chart(fig, "chart_price.png", cache_dir)
    plt.close(fig)
    return out

# ── 취득비용 구성 가로 막대 (파이차트 대체) ──
def build_acquisition_bar_chart(cache_dir, labels, values_eok):
    _, plt = _mpl()
    total = sum(values_eok)
    colors = ["#2D4A3E", "#C9A24B", "#D8C8A8", "#B65D3A", "#1F294B"][:len(labels)]
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    y_pos = list(range(len(labels)))[::-1]
    bars = ax.barh(y_pos, values_eok, color=colors,
                   edgecolor="#1F294B", linewidth=0.6, height=0.62)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10, color="#1F294B")
    ax.set_xlabel("금액 (억원)", fontsize=10, color="#1F294B")
    ax.set_xlim(0, max(values_eok) * 1.22)
    ax.set_title(f"총 초기투자 구성  ·  합계 약 {total:.2f}억원",
                 fontsize=12, color="#1F294B", pad=10, weight="bold")
    for b, v in zip(bars, values_eok):
        pct = v / total * 100
        label = f"  {v:,.2f}억  ({pct:.1f}%)"
        ax.text(v, b.get_y() + b.get_height() / 2,
                label, va="center", ha="left",
                fontsize=10, color="#1F294B", weight="bold")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.25, linestyle="--")
    ax.invert_yaxis()
    out = _save_chart(fig, "chart_acquisition_bar.png", cache_dir)
    plt.close(fig)
    return out
