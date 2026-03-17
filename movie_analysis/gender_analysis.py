# =============================================
# gender_analysis.py — 성별 비교 분석
# 마케터 인사이트: 남녀 타겟별 반응 차이 파악 → SNS 광고 전략 도출
# =============================================

import json
import os
import sys
import re
from collections import Counter, defaultdict

import matplotlib.pyplot as plt
import koreanize_matplotlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from movie_analysis.config import DATA_DIR, MOVIES, GENDER_KEYWORDS
OUTPUT_DIR = os.path.join(os.path.dirname(DATA_DIR), "images_analysis")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_naver_data() -> dict:
    path = os.path.join(DATA_DIR, "naver_reviews.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_gender_keyword_scores(data: dict) -> dict:
    """영화별 성별 키워드 점수 합산"""
    results = {}
    for movie_name, movie_data in data.items():
        blogs = movie_data.get("blog", [])
        total_female = 0
        total_male = 0
        female_keywords = Counter()
        male_keywords = Counter()

        for blog in blogs:
            text = blog.get("title", "") + " " + blog.get("description", "")
            for kw in GENDER_KEYWORDS["female"]:
                cnt = text.count(kw)
                if cnt:
                    female_keywords[kw] += cnt
                    total_female += cnt
            for kw in GENDER_KEYWORDS["male"]:
                cnt = text.count(kw)
                if cnt:
                    male_keywords[kw] += cnt
                    total_male += cnt

        # 성별 분포
        female_blogs = sum(1 for b in blogs if b.get("estimated_gender") == "female")
        male_blogs = sum(1 for b in blogs if b.get("estimated_gender") == "male")
        unknown_blogs = len(blogs) - female_blogs - male_blogs

        results[movie_name] = {
            "total_female_score": total_female,
            "total_male_score": total_male,
            "female_ratio": total_female / (total_female + total_male + 0.001),
            "top_female_keywords": female_keywords.most_common(10),
            "top_male_keywords": male_keywords.most_common(10),
            "female_blogs": female_blogs,
            "male_blogs": male_blogs,
            "unknown_blogs": unknown_blogs,
        }
    return results


def plot_gender_comparison(results: dict):
    """영화별 성별 반응 비교 바 차트"""
    movies = list(results.keys())
    female_scores = [results[m]["total_female_score"] for m in movies]
    male_scores   = [results[m]["total_male_score"]   for m in movies]

    x = np.arange(len(movies))
    width = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("영화별 성별 키워드 반응 비교 (마케터 분석)", fontsize=15, fontweight="bold")

    # ─ 왼쪽: 키워드 점수 비교
    ax = axes[0]
    bars_f = ax.bar(x - width/2, female_scores, width, label="여성 키워드", color="#FF6B9D", alpha=0.85)
    bars_m = ax.bar(x + width/2, male_scores,   width, label="남성 키워드", color="#4D96FF", alpha=0.85)
    ax.set_title("성별 키워드 점수 합계", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(movies)
    ax.legend()
    ax.set_ylabel("키워드 빈도 합계")
    for bar in bars_f:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                str(int(bar.get_height())), ha="center", va="bottom", fontsize=9)
    for bar in bars_m:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                str(int(bar.get_height())), ha="center", va="bottom", fontsize=9)

    # ─ 오른쪽: 여성비율 수평 막대
    ax2 = axes[1]
    female_ratios = [results[m]["female_ratio"] * 100 for m in movies]
    male_ratios   = [100 - r for r in female_ratios]
    y = np.arange(len(movies))
    ax2.barh(y, female_ratios, color="#FF6B9D", alpha=0.85, label="여성")
    ax2.barh(y, male_ratios, left=female_ratios, color="#4D96FF", alpha=0.85, label="남성")
    ax2.set_yticks(y)
    ax2.set_yticklabels(movies)
    ax2.set_xlabel("비율 (%)")
    ax2.set_title("성별 키워드 비율", fontsize=12)
    ax2.axvline(50, color="white", linestyle="--", linewidth=1.5)
    ax2.legend(loc="lower right")

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, "gender_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  💾 저장: {out}")
    return out


def plot_keyword_heatmap(results: dict):
    """영화별 상위 여성/남성 키워드 히트맵"""
    all_female_kws = set()
    all_male_kws   = set()
    for r in results.values():
        all_female_kws.update(kw for kw, _ in r["top_female_keywords"])
        all_male_kws.update(kw for kw, _ in r["top_male_keywords"])

    movies = list(results.keys())

    def draw_heatmap(kw_set, label, filename, color):
        kws = sorted(list(kw_set))
        if not kws:
            return
        matrix = np.zeros((len(kws), len(movies)))
        for j, movie in enumerate(movies):
            score_dict = dict(results[movie][f"top_{label}_keywords"])
            for i, kw in enumerate(kws):
                matrix[i, j] = score_dict.get(kw, 0)

        fig, ax = plt.subplots(figsize=(10, max(4, len(kws) * 0.45)))
        im = ax.imshow(matrix, cmap=color, aspect="auto")
        ax.set_xticks(range(len(movies)))
        ax.set_xticklabels(movies)
        ax.set_yticks(range(len(kws)))
        ax.set_yticklabels(kws)
        ax.set_title(f"{'여성' if label == 'female' else '남성'} 키워드 히트맵 (영화별)", fontsize=12)
        plt.colorbar(im, ax=ax, label="빈도")
        plt.tight_layout()
        out = os.path.join(OUTPUT_DIR, filename)
        plt.savefig(out, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  💾 저장: {out}")

    draw_heatmap(all_female_kws, "female", "gender_heatmap_female.png", "RdPu")
    draw_heatmap(all_male_kws,   "male",   "gender_heatmap_male.png",   "Blues")


def generate_gender_report(results: dict) -> str:
    """마케터 관점 성별 분석 보고서 텍스트 생성"""
    lines = ["## 📊 성별 비교 분석 (마케터 관점)\n"]
    lines.append("**분석 방법**: 네이버 블로그 리뷰에서 성별 연관 키워드 빈도를 집계하여 남녀 반응 차이를 분석합니다.\n")

    for movie, r in results.items():
        f = r["total_female_score"]
        m = r["total_male_score"]
        total = f + m + 0.001
        dominant = "여성" if f > m else "남성"
        top_f_kws = ", ".join(f"`{kw}`({cnt})" for kw, cnt in r["top_female_keywords"][:5])
        top_m_kws = ", ".join(f"`{kw}`({cnt})" for kw, cnt in r["top_male_keywords"][:5])

        lines.append(f"### 🎬 {movie}")
        lines.append(f"| 항목 | 여성 | 남성 |")
        lines.append(f"|------|------|------|")
        lines.append(f"| 키워드 점수 합계 | **{f}점** | **{m}점** |")
        lines.append(f"| 비율 | {f/total*100:.1f}% | {m/total*100:.1f}% |")
        lines.append(f"| 블로그 리뷰 수 | {r['female_blogs']}건 | {r['male_blogs']}건 |")
        lines.append(f"\n**주요 여성 키워드**: {top_f_kws}")
        lines.append(f"**주요 남성 키워드**: {top_m_kws}")
        lines.append(f"\n> 🎯 **마케터 전략**: `{movie}`는 **{dominant}** 중심 반응 → {dominant} 타겟 SNS/온라인 광고 우선 집행 권장\n")

    return "\n".join(lines)


def run_gender_analysis() -> tuple:
    print("\n" + "="*50)
    print("📊 성별 비교 분석 시작")
    print("="*50)
    data = load_naver_data()
    results = compute_gender_keyword_scores(data)
    plot_gender_comparison(results)
    plot_keyword_heatmap(results)
    report = generate_gender_report(results)
    print("\n✅ 성별 분석 완료")
    return results, report


if __name__ == "__main__":
    run_gender_analysis()
