# =============================================
# production_analysis.py — 영화 제작/출연진 분석
# 마케터 인사이트: 감독·배우 브랜드 파워 vs 박스오피스 흥행 기여도
# =============================================

import json
import os
import sys

import matplotlib.pyplot as plt
import koreanize_matplotlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from movie_analysis.config import DATA_DIR, MOVIES
OUTPUT_DIR = os.path.join(os.path.dirname(DATA_DIR), "images_analysis")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 수동 확장: 수집된 KOBIS 외 유명 흥행 기록 (참고용 마케터 데이터)
KNOWN_BOX_OFFICE = {
    "명량": {"audi_acc": 17615000, "rank_peak": 1, "screens": 1587},
    "기생충": {"audi_acc": 10270000, "rank_peak": 1, "screens": 2006},
    "사도": {"audi_acc": 6240000, "rank_peak": 1, "screens": 1094},
    "왕과 사는 남자": {"audi_acc": None, "rank_peak": None, "screens": None},  # 수집 데이터 사용
}


def load_kobis_data() -> list:
    path = os.path.join(DATA_DIR, "kobis_movies.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_production(kobis_data: list) -> dict:
    """제작/출연진 분석"""
    results = {}
    for movie in kobis_data:
        name = movie.get("movieNm", "")
        directors = movie.get("directors", [])
        actors = movie.get("actors", [])
        companies = movie.get("companies", [])
        genres = movie.get("genres", [])
        audit = [a.get("grade", "") for a in movie.get("audits", [])]

        # 박스오피스 (KOBIS + 알려진 데이터 병합)
        known = KNOWN_BOX_OFFICE.get(name, {})
        peak = movie.get("peak_boxoffice", {})
        audi_acc = (
            known.get("audi_acc")
            or (peak.get("daily_data", [{}])[-1].get("audiAcc") if peak.get("daily_data") else None)
            or 0
        )
        rank_peak = known.get("rank_peak") or peak.get("rank") or "-"
        screens = known.get("screens") or (peak.get("daily_data", [{}])[0].get("scrnCnt") if peak.get("daily_data") else None) or "-"

        results[name] = {
            "directors": directors,
            "actors": actors[:8],
            "companies": companies,
            "genres": genres,
            "watch_grade": audit,
            "audi_acc": audi_acc,
            "rank_peak": rank_peak,
            "screens": screens,
            "release_year": movie.get("release_year", ""),
            "era": movie.get("era", ""),
        }
    return results


def plot_boxoffice_comparison(results: dict):
    """영화별 누적 관객수 비교 막대 차트"""
    movies = [k for k, v in results.items() if v.get("audi_acc")]
    if not movies:
        print("  ⚠️ 시각화할 누적 관객수 데이터가 없습니다.")
        return None
    audis  = [results[m]["audi_acc"] / 10000 for m in movies]  # 만 명 단위
    colors = ["#FF6B9D", "#4D96FF", "#F9A03F", "#6BCB77"]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(movies, audis, color=colors[:len(movies)], alpha=0.85, width=0.5)

    for bar, val in zip(bars, audis):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20,
                f"{val:.0f}만", ha="center", va="bottom", fontsize=10,
                fontweight="bold")

    ax.set_ylabel("누적 관객수 (만 명)")
    ax.set_title("영화별 누적 관객수 비교", fontsize=13, fontweight="bold")
    ax.set_xticklabels(movies)
    ax.set_ylim(0, max(audis) * 1.2)
    plt.tight_layout()

    out = os.path.join(OUTPUT_DIR, "boxoffice_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  💾 저장: {out}")
    return out


def plot_production_summary(results: dict):
    """감독·배우·제작사 요약 인포그래픽"""
    movies = list(results.keys())
    n = len(movies)
    colors = ["#FF6B9D", "#4D96FF", "#F9A03F", "#6BCB77"]

    fig, axes = plt.subplots(1, n, figsize=(4 * n, 8))
    if n == 1:
        axes = [axes]

    fig.suptitle("영화별 제작/출연진 프로파일", fontsize=14, fontweight="bold")

    for idx, movie in enumerate(movies):
        ax = axes[idx]
        ax.axis("off")
        r = results[movie]

        lines = [
            f"🎬 {movie}",
            f"({r['release_year']}년 | {r['era']})",
            "",
            f"🎥 감독",
            "\n".join(f"  · {d}" for d in r["directors"]) or "  · 정보없음",
            "",
            f"⭐ 주연 배우",
        ]
        for a in r["actors"][:5]:
            lines.append(f"  · {a['name']} ({a['cast'] or '출연'})")
        lines += [
            "",
            f"🏢 제작사",
            "\n".join(
                f"  · {c['name']}" for c in r["companies"] if c["type"] in ["제작사", "배급사"]
            )[:3] or "  · 정보없음",
            "",
            f"🎭 장르: {', '.join(r['genres'])}",
            f"🔞 관람등급: {', '.join(r['watch_grade']) or '정보없음'}",
            "",
            f"📊 흥행 성과",
            f"  · 누적관객: {r['audi_acc']:,}명" if r['audi_acc'] else "  · 누적관객: 수집중",
            f"  · 최고순위: {r['rank_peak']}위",
            f"  · 최대스크린: {r['screens']}개",
        ]

        full_text = "\n".join(lines)
        ax.text(0.05, 0.95, full_text, transform=ax.transAxes,
                fontsize=9, va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.5", facecolor=colors[idx], alpha=0.12))

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, "production_profile.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  💾 저장: {out}")
    return out


def plot_genre_comparison(results: dict):
    """영화별 장르 분포 파이 차트"""
    from collections import Counter
    all_genres = Counter()
    movie_genre_map = {}
    for movie, r in results.items():
        movie_genre_map[movie] = r["genres"]
        for g in r["genres"]:
            all_genres[g] += 1

    movies = list(results.keys())
    n = len(movies)
    colors_ring = ["#FF6B9D", "#4D96FF", "#F9A03F", "#6BCB77",
                   "#A78BFA", "#34D399", "#F87171", "#FBBF24"]

    fig, axes = plt.subplots(1, n, figsize=(4 * n, 5))
    if n == 1:
        axes = [axes]
    fig.suptitle("영화별 장르 구성", fontsize=13, fontweight="bold")

    for idx, movie in enumerate(movies):
        genres = movie_genre_map[movie]
        if not genres:
            axes[idx].axis("off")
            continue
        axes[idx].pie(
            [1] * len(genres),
            labels=genres,
            colors=colors_ring[:len(genres)],
            autopct="%1.0f%%",
            textprops={"fontsize": 9},
            startangle=90,
        )
        axes[idx].set_title(movie)

    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, "genre_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  💾 저장: {out}")
    return out


def generate_production_report(results: dict) -> str:
    """마케터 관점 제작/출연진 분석 보고서"""
    lines = ["## 🎬 영화 제작/출연진 분석 (마케터 관점)\n"]

    lines.append("### 영화별 핵심 정보 비교\n")
    lines.append("| 영화 | 감독 | 주연 | 누적관객 | 관람등급 | 장르 |")
    lines.append("|------|------|------|---------|---------|------|")
    for movie, r in results.items():
        directors = ", ".join(r["directors"]) or "-"
        actors = ", ".join(a["name"] for a in r["actors"][:2]) or "-"
        audi = f"{r['audi_acc']:,}명" if r["audi_acc"] else "수집중"
        grade = ", ".join(r["watch_grade"]) or "-"
        genres = ", ".join(r["genres"][:2]) or "-"
        lines.append(f"| {movie} | {directors} | {actors} | {audi} | {grade} | {genres} |")

    lines.append("\n### 마케팅 전략 제언\n")
    for movie, r in results.items():
        directors = ", ".join(r["directors"]) or "미정"
        actors_top = [a["name"] for a in r["actors"][:3]]
        audi = r["audi_acc"]

        lines.append(f"#### 🎬 {movie}")
        if audi and audi > 10000000:
            strategy = f"'{movie}'는 천만 영화 IP — 리부트/2차 콘텐츠(굿즈, 전시) 마케팅 가능"
        elif audi and audi > 5000000:
            strategy = f"500만 이상 흥행작 — 감독 `{directors}` 브랜드 + 배우 팬덤({', '.join(actors_top)}) 활용"
        else:
            strategy = f"신작 — `{directors}` 감독 레거시 + 주연({', '.join(actors_top)}) SNS 팬 결집 전략 집중"

        lines.append(f"> 🎯 {strategy}\n")

    return "\n".join(lines)


def run_production_analysis() -> tuple:
    print("\n" + "="*50)
    print("🎬 제작/출연진 분석 시작")
    print("="*50)
    kobis_data = load_kobis_data()
    results = analyze_production(kobis_data)
    plot_boxoffice_comparison(results)
    plot_production_summary(results)
    plot_genre_comparison(results)
    report = generate_production_report(results)
    print("\n✅ 제작/출연진 분석 완료")
    return results, report


if __name__ == "__main__":
    run_production_analysis()
