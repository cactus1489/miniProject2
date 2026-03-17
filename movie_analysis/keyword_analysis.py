# =============================================
# keyword_analysis.py — 키워드 & 시대성 분석
# 마케터 인사이트: 흥행 핵심 키워드 도출 + 시대성 마케팅 앵글 발굴
# =============================================

import json
import os
import sys
import re
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import koreanize_matplotlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from movie_analysis.config import DATA_DIR, MOVIES, ERA_KEYWORDS

# 한글 불용어
STOPWORDS = set([
    "이", "가", "을", "를", "의", "에", "은", "는", "도", "로", "으로",
    "와", "과", "이나", "나", "에서", "에게", "그", "그리고", "하지만",
    "영화", "보고", "정말", "너무", "진짜", "되게", "좀", "더", "이런",
    "그런", "대한", "것", "수", "어", "이렇게", "않", "있", "없", "많이",
    "같이", "같은", "때", "다", "에서는", "적인", "하는", "그냥", "ㅠ",
    "ㅜ", "ㅋ", "ㅋㅋ", "ㄷ", "때문에", "하고", "했다", "했", "봤",
    "거", "거야", "거다", "만", "또", "정도", "저", "나", "우리",
])

OUTPUT_DIR = os.path.join(os.path.dirname(DATA_DIR), "images_analysis")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():
    naver_path = os.path.join(DATA_DIR, "naver_reviews.json")
    with open(naver_path, "r", encoding="utf-8") as f:
        naver = json.load(f)
    return naver


def extract_keywords(texts: list, top_n: int = 30) -> Counter:
    """간단한 형태소 기반 키워드 추출 (정규식 + 불용어 필터)"""
    counter = Counter()
    for text in texts:
        # 한글 2글자 이상 추출
        words = re.findall(r"[가-힣]{2,}", text)
        for w in words:
            if w not in STOPWORDS and len(w) >= 2:
                counter[w] += 1
    return counter


def compute_era_scores(all_texts: list) -> dict:
    """시대성 키워드 점수 계산"""
    era_scores = {}
    for era, keywords in ERA_KEYWORDS.items():
        score = sum(
            sum(text.count(kw) for kw in keywords)
            for text in all_texts
        )
        era_scores[era] = score
    return era_scores


def analyze_keywords(naver_data: dict) -> dict:
    """영화별 키워드 분석"""
    results = {}
    for movie_name, movie_data in naver_data.items():
        # 뉴스 + 블로그 텍스트 합치기
        all_texts = []
        for item in movie_data.get("news", []) + movie_data.get("blog", []):
            text = item.get("title", "") + " " + item.get("description", "")
            all_texts.append(text)

        # 키워드 추출
        keyword_counter = extract_keywords(all_texts, top_n=30)

        # 시대성 분석
        era_scores = compute_era_scores(all_texts)

        results[movie_name] = {
            "top_keywords": keyword_counter.most_common(30),
            "era_scores": era_scores,
            "total_texts": len(all_texts),
        }
        print(f"  [{movie_name}] 상위 키워드: {[kw for kw, _ in keyword_counter.most_common(10)]}")
    return results


def plot_keyword_bar(results: dict):
    """영화별 Top 15 키워드 막대 차트"""
    movies = list(results.keys())
    n = len(movies)
    colors = ["#FF6B9D", "#4D96FF", "#F9A03F", "#6BCB77"]

    fig, axes = plt.subplots(1, n, figsize=(5 * n, 7))
    if n == 1:
        axes = [axes]

    fig.suptitle("영화별 핵심 키워드 Top 15 (마케터 분석)", fontsize=14, fontweight="bold")

    for idx, (movie, data) in enumerate(results.items()):
        ax = axes[idx]
        top = data["top_keywords"][:15]
        kws = [kw for kw, _ in top]
        cnts = [cnt for _, cnt in top]

        ax.barh(range(len(kws)), cnts, color=colors[idx % len(colors)], alpha=0.85)
        ax.set_yticks(range(len(kws)))
        ax.set_yticklabels(kws, fontsize=9)
        ax.invert_yaxis()
        ax.set_title(movie, fontsize=11)
        ax.set_xlabel("빈도")

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, "keyword_top15.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  💾 저장: {out}")
    return out


def plot_era_radar(results: dict):
    """영화별 시대성 키워드 레이더 차트"""
    era_labels = list(ERA_KEYWORDS.keys())
    movies = list(results.keys())
    colors = ["#FF6B9D", "#4D96FF", "#F9A03F", "#6BCB77"]

    N = len(era_labels)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.set_title("영화별 시대성 분포 (레이더)", fontsize=13, pad=20)

    for idx, movie in enumerate(movies):
        era_scores = results[movie]["era_scores"]
        values = [era_scores.get(e, 0) for e in era_labels]
        max_val = max(values) or 1
        values_norm = [v / max_val for v in values]
        values_norm += values_norm[:1]

        ax.plot(angles, values_norm, "o-", linewidth=2, color=colors[idx], label=movie)
        ax.fill(angles, values_norm, alpha=0.15, color=colors[idx])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(era_labels, fontsize=10)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    out = os.path.join(OUTPUT_DIR, "era_radar.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  💾 저장: {out}")
    return out


def plot_era_bar(results: dict):
    """시대성 키워드 영화별 막대 비교"""
    era_labels = list(ERA_KEYWORDS.keys())
    movies = list(results.keys())
    x = np.arange(len(era_labels))
    width = 0.2
    colors = ["#FF6B9D", "#4D96FF", "#F9A03F", "#6BCB77"]

    fig, ax = plt.subplots(figsize=(12, 6))
    for i, movie in enumerate(movies):
        scores = [results[movie]["era_scores"].get(e, 0) for e in era_labels]
        ax.bar(x + i * width, scores, width, label=movie, color=colors[i], alpha=0.85)

    ax.set_xticks(x + width * (len(movies) - 1) / 2)
    ax.set_xticklabels(era_labels)
    ax.set_ylabel("시대성 키워드 점수")
    ax.set_title("영화별 시대성 키워드 비교", fontsize=13)
    ax.legend()
    plt.tight_layout()

    out = os.path.join(OUTPUT_DIR, "era_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  💾 저장: {out}")
    return out


def generate_keyword_report(results: dict) -> str:
    """마케터 관점 키워드 분석 보고서"""
    lines = ["## 🔑 키워드 & 시대성 분석 (마케터 관점)\n"]

    for movie, data in results.items():
        top10 = [kw for kw, _ in data["top_keywords"][:10]]
        era_scores = data["era_scores"]
        dominant_era = max(era_scores, key=era_scores.get)

        lines.append(f"### 🎬 {movie}")
        lines.append(f"**Top 10 키워드**: {', '.join(f'`{kw}`' for kw in top10)}")
        lines.append(f"\n**시대성 분석**:")
        for era, score in sorted(era_scores.items(), key=lambda x: -x[1]):
            lines.append(f"- {era}: {score}점")
        lines.append(f"\n> 🎯 **마케터 전략**: 지배적 시대성 = `{dominant_era}` →")

        if dominant_era == "현재성":
            lines.append(f"> '지금 우리 이야기' 프레임으로 마케팅 → 현대 이슈와 연계한 SNS 바이럴\n")
        elif dominant_era in ["조선시대", "임진왜란"]:
            lines.append(f"> '역사의 재해석' 프레임 → 역사 교육·문화재 연계 체험 마케팅 + 학생층 공략\n")
        else:
            lines.append(f"> 현대적 보편성 강조 → 글로벌 OTT 마케팅 연계 추천\n")

    return "\n".join(lines)


def run_keyword_analysis() -> tuple:
    print("\n" + "="*50)
    print("🔑 키워드 & 시대성 분석 시작")
    print("="*50)
    naver_data = load_data()
    results = analyze_keywords(naver_data)
    plot_keyword_bar(results)
    plot_era_radar(results)
    plot_era_bar(results)
    report = generate_keyword_report(results)
    print("\n✅ 키워드 분석 완료")
    return results, report


if __name__ == "__main__":
    run_keyword_analysis()
