# =============================================
# marketing_report.py — 종합 마케팅 전략 리포트 생성
# 페르소나: 영화 마케터 (마케팅 전략 수립)
# =============================================

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from movie_analysis.config import DATA_DIR, MOVIES
from movie_analysis.kobis_collector import KobisCollector
from movie_analysis.naver_collector import NaverCollector
from movie_analysis.gender_analysis import run_gender_analysis
from movie_analysis.keyword_analysis import run_keyword_analysis
from movie_analysis.production_analysis import run_production_analysis

OUTPUT_DIR = os.path.join(os.path.dirname(DATA_DIR), "images_analysis")
REPORT_PATH = os.path.join(os.path.dirname(DATA_DIR), "movie_marketing_report.md")


MARKETING_STRATEGIES = {
    "왕과 사는 남자": {
        "target": "20~40대 사극 팬, 역사 관심층, 주연 배우 팬덤",
        "channel": "유튜브 예고편 바이럴, 인스타그램 감성 스틸컷, 틱톡 OST 챌린지",
        "angle": "왕과의 비밀스러운 관계 — '역사 속 숨겨진 이야기' 미스터리 마케팅",
        "hooks": ["#왕과사는남자", "#사극로맨스", "#2026사극대작"],
        "risk": "동시기 경쟁작 대비 스크린 확보 전략 필요",
    },
    "사도": {
        "target": "30~50대 역사 관심층, 가족 단위, 드라마 팬",
        "channel": "TV·OTT 광고, 포털 메인 배너, 역사 교육 커뮤니티 마케팅",
        "angle": "부자(父子) 비극 — '이해받지 못한 왕세자' 감성 공명 마케팅",
        "hooks": ["#사도세자", "#조선비극", "#부자의이야기"],
        "risk": "관람등급(15세 이상) 대비 가족 타겟 다소 제한",
    },
    "명량": {
        "target": "전 연령대 (8~70대), 특히 40~60대 남성, 학생층",
        "channel": "공중파 TV 광고, 뉴스 기사 연계, 학교·공공기관 단체관람",
        "angle": "'불가능한 전쟁을 이긴 이순신' — 민족 자긍심·집단 감동 마케팅",
        "hooks": ["#명량대첩", "#이순신", "#한국역대흥행1위"],
        "risk": "이미 천만 클래식 → 재개봉·OTT 중심 마케팅 전환 고려",
    },
    "기생충": {
        "target": "20~40대 도시 직장인, 영화 마니아, 글로벌 시장",
        "channel": "OTT(Netflix) 연계, 해외 영화제 PR, SNS 밈·짤 바이럴",
        "angle": "'계층의 기생' — 아카데미 수상 IP + 봉준호 감독 브랜드 마케팅",
        "hooks": ["#기생충", "#봉준호", "#아카데미수상"],
        "risk": "국내보다 글로벌 시장 의존도 높음 → 로컬 재마케팅 전략 필요",
    },
}


def generate_executive_summary(gender_results, keyword_results, production_results) -> str:
    """Executive Summary — 핵심 인사이트 3가지"""
    lines = []
    lines.append("## 📋 Executive Summary\n")
    lines.append("> **분석 페르소나**: K-역사영화 전문 마케터 | **분석 일시**: " + datetime.now().strftime("%Y년 %m월 %d일") + "\n")
    lines.append("> 본 보고서는 KOBIS Open API(박스오피스·영화정보)와 네이버 검색 API(뉴스·블로그 리뷰)를 기반으로")
    lines.append("> 4개 영화의 마케팅 전략 수립을 위한 데이터 분석 결과를 정리합니다.\n")

    lines.append("### 💡 핵심 인사이트 3가지\n")

    # 인사이트 1: 성별 dominance
    dominant_female_films = [
        m for m, r in gender_results.items()
        if r["total_female_score"] > r["total_male_score"]
    ]
    dominant_male_films = [
        m for m, r in gender_results.items()
        if r["total_male_score"] >= r["total_female_score"]
    ]
    lines.append(f"**① 성별 반응 양극화**")
    lines.append(f"- 여성 중심 반응: {', '.join(dominant_female_films) or '없음'}")
    lines.append(f"- 남성 중심 반응: {', '.join(dominant_male_films) or '없음'}")
    lines.append(f"- → 단일 메시지 광고보다 **성별 맞춤 채널 분리 집행** 권장\n")

    # 인사이트 2: 시대성 공통 키워드
    all_top_kws = []
    for r in keyword_results.values():
        all_top_kws += [kw for kw, _ in r["top_keywords"][:5]]
    from collections import Counter
    common_kws = [kw for kw, cnt in Counter(all_top_kws).most_common(5) if cnt >= 2]
    lines.append(f"**② 사극 공통 마케팅 키워드**")
    lines.append(f"- 4개 영화 공통 상위어: {', '.join(f'`{kw}`' for kw in common_kws) or '개별 분석 참조'}")
    lines.append(f"- → '**역사의 재발견**' 통합 캠페인 가능성 — 사극 시리즈 브랜딩 고려\n")

    # 인사이트 3: 박스오피스 격차
    prod = {r: production_results[r]["audi_acc"] for r in production_results if production_results[r]["audi_acc"]}
    if prod:
        top_movie = max(prod, key=prod.get)
        lines.append(f"**③ 흥행 격차와 마케팅 투자 배분**")
        lines.append(f"- 최고 흥행작: `{top_movie}` ({prod[top_movie]:,}명)")
        lines.append(f"- → 흥행작 감독·배우 브랜드를 신작(`왕과 사는 남자`) 론칭에 연계하는 **레버리지 전략** 유효\n")

    return "\n".join(lines)


def generate_full_report(gender_results, keyword_results, production_results,
                          gender_report, keyword_report, production_report) -> str:
    """전체 마케팅 보고서 생성"""

    report_lines = []

    # ── 헤더
    report_lines.append("# 🎬 영화 마케터 관점 데이터 분석 보고서")
    report_lines.append(f"> 대상 영화: 왕과 사는 남자 · 사도 · 명량 · 기생충")
    report_lines.append(f"> 분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append(f"> 데이터 소스: KOBIS Open API + 네이버 검색 API\n")
    report_lines.append("---\n")

    # ── Executive Summary
    report_lines.append(generate_executive_summary(gender_results, keyword_results, production_results))
    report_lines.append("\n---\n")

    # ── 성별 분석
    report_lines.append(gender_report)
    if os.path.exists(os.path.join(OUTPUT_DIR, "gender_comparison.png")):
        report_lines.append("\n![성별 비교 차트](images_analysis/gender_comparison.png)\n")
    
    report_lines.append("\n---\n")

    # ── 키워드 분석
    report_lines.append(keyword_report)
    if os.path.exists(os.path.join(OUTPUT_DIR, "keyword_top15.png")):
        report_lines.append("\n![키워드 Top15](images_analysis/keyword_top15.png)\n")
    if os.path.exists(os.path.join(OUTPUT_DIR, "era_radar.png")):
        report_lines.append("\n![시대성 레이더](images_analysis/era_radar.png)\n")
    
    report_lines.append("\n---\n")

    # ── 제작/출연진 분석
    report_lines.append(production_report)
    if os.path.exists(os.path.join(OUTPUT_DIR, "boxoffice_comparison.png")):
        report_lines.append("\n![박스오피스 비교](images_analysis/boxoffice_comparison.png)\n")
    if os.path.exists(os.path.join(OUTPUT_DIR, "production_profile.png")):
        report_lines.append("\n![제작 프로파일](images_analysis/production_profile.png)\n")
    report_lines.append("\n---\n")

    # ── 영화별 마케팅 전략
    report_lines.append("## 🚀 영화별 마케팅 실행 전략\n")
    for movie_cfg in MOVIES:
        movie = movie_cfg["name"]
        strat = MARKETING_STRATEGIES.get(movie, {})
        report_lines.append(f"### 🎬 {movie} ({movie_cfg['release_year']})\n")
        report_lines.append(f"| 항목 | 내용 |")
        report_lines.append(f"|------|------|")
        report_lines.append(f"| 핵심 타겟 | {strat.get('target', '-')} |")
        report_lines.append(f"| 마케팅 채널 | {strat.get('channel', '-')} |")
        report_lines.append(f"| 마케팅 앵글 | {strat.get('angle', '-')} |")
        report_lines.append(f"| 해시태그 | {' '.join(strat.get('hooks', []))} |")
        report_lines.append(f"| 리스크 | {strat.get('risk', '-')} |\n")

    # ── 왕과 사는 남자 집중 실행 계획
    report_lines.append("---\n")
    report_lines.append("## 🏹 왕과 사는 남자 — 마케팅 집중 실행 계획\n")
    report_lines.append("*(사도·명량·기생충 데이터 기반 교훈 적용)*\n")
    report_lines.append("| 단계 | 시기 | 전략 | KPI |")
    report_lines.append("|------|------|------|-----|")
    report_lines.append("| 티저 런칭 | 개봉 D-60 | 미스터리 감성 티저 → 유튜브·인스타 공개 | 조회수 500만+ |")
    report_lines.append("| 성별 맞춤 광고 | 개봉 D-30 | 여성 → 감성·배우 중심 / 남성 → 역사·스케일 중심 | CTR 3%+ |")
    report_lines.append("| 개봉 폭격 | D-7 ~ D+7 | 스크린 최대 확보 + 공중파 CF | 1주차 100만 돌파 |")
    report_lines.append("| 롱테일 마케팅 | D+14 이후 | 블로거·유튜버 리뷰 활성화, OTT 선판매 협상 | 누적 300만+ |")
    report_lines.append("| IP 확장 | 종영 후 | 사극 브랜드 시리즈화, 굿즈·전시 기획 | 2차 수익 창출 |\n")

    report_lines.append("---\n")
    report_lines.append(
        "> 본 보고서는 KOBIS Open API 및 네이버 검색 API 실데이터 기반으로 자동 생성되었습니다.  \n"
        "> 마케팅 전략 실행 전 추가 소비자 조사(FGI, 설문) 병행을 권장합니다.\n"
    )

    return "\n".join(report_lines)


def run_all():
    print("\n" + "=" * 60)
    print("영화 마케터 데이터 분석 시스템 시작")
    print("=" * 60)

    # ── 1. 데이터 수집
    print("\n[STEP 1] KOBIS 데이터 수집...")
    kobis = KobisCollector()
    kobis.collect_all_movies()

    print("\n[STEP 2] 네이버 검색 데이터 수집...")
    naver = NaverCollector()
    naver.collect_all_movies()

    # ── 2. 분석
    print("\n[STEP 3] 성별 비교 분석...")
    gender_results, gender_report = run_gender_analysis()

    print("\n[STEP 4] 키워드 & 시대성 분석...")
    keyword_results, keyword_report = run_keyword_analysis()

    print("\n[STEP 5] 제작/출연진 분석...")
    production_results, production_report = run_production_analysis()

    # ── 3. 최종 보고서 생성
    print("\n[STEP 6] 마케팅 전략 보고서 생성...")
    report_md = generate_full_report(
        gender_results, keyword_results, production_results,
        gender_report, keyword_report, production_report
    )

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\n{'='*60}")
    print(f"분석 완료!")
    print(f"최종 보고서: {REPORT_PATH}")
    print(f"시각화 이미지: {OUTPUT_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_all()
