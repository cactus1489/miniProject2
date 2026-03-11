# -*- coding: utf-8 -*-
"""
KOBIS moviePrompt.md 방식 응용 — 영화 상세 통계 페이지 스크래핑
실제 KOBIS 사이트의 영화별 일별 박스오피스 테이블 수집
"""

import requests
from bs4 import BeautifulSoup
import csv, json, re

SESSION = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.kobis.or.kr",
}
MOVIE_CD = "20242837"

# moviePrompt.md에서 확인한 실제 KOBIS 모바일 패턴 활용
# 좌석 점유율(일별) URL 탐색
print("=== 1) KOBIS 모바일 좌석 점유율 (일별) ===")
url = "https://www.kobis.or.kr/kobis/mobile/main/findDailySeatTicketList.do"
r = SESSION.get(url, headers=HEADERS)
soup = BeautifulSoup(r.text, 'html.parser')
# 첫번째 날짜 확인
dates = [a.text.strip() for a in soup.select('.date_area a')]
print(f"날짜 탭: {dates[:5]}")

# AJAX URL 파악 (스크립트에서 추출)
scripts = soup.find_all('script')
for s in scripts:
    text = s.string or ""
    if 'Ajax' in text or 'findDailySeat' in text:
        print("Script found:", text[:400])

print("\n=== 2) 영화 상세 정보 API (Fetch 방식) ===")
# moviePrompt.md에서 사용한 KOBIS 모바일 API
ajax_url2 = "https://www.kobis.or.kr/kobis/mobile/mast/mvie/searchMovieDtl.do"
r2 = SESSION.get(ajax_url2, params={"movieCd": MOVIE_CD}, headers=HEADERS)
r2.encoding = 'utf-8'
print(f"Status: {r2.status_code}")
print(r2.text[:500])

print("\n=== 3) KOBIS API 직접 호출 (일별 통계) ===")
# 공식 REST API (키 없이 시도 가능한 public 엔드포인트)
from datetime import datetime, timedelta

start_dt = datetime(2026, 2, 5)
end_dt = datetime(2026, 3, 11)
results = []
cur = start_dt
while cur <= end_dt:
    dt_str = cur.strftime("%Y%m%d")
    try:
        r3 = SESSION.get(
            "https://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json",
            params={"key": "430156241533f1d058c603178cc3ca0e", "targetDt": dt_str},
            headers=HEADERS, timeout=5
        )
        data = r3.json()
        if 'boxOfficeResult' in data:
            for m in data['boxOfficeResult']['dailyBoxOfficeList']:
                if '왕과' in m.get('movieNm', ''):
                    results.append({
                        "날짜": dt_str,
                        "순위": m.get("rank"),
                        "영화명": m.get("movieNm"),
                        "일별관객수": int(m.get("audiCnt", 0)),
                        "누적관객수": int(m.get("audiAcc", 0)),
                        "일별매출": int(m.get("salesAmt", 0)),
                        "스크린수": int(m.get("scrnCnt", 0)),
                        "상영횟수": int(m.get("showCnt", 0)),
                    })
                    print(f"[{dt_str}] 순위:{m['rank']} 관객:{int(m['audiCnt']):,} 누적:{int(m['audiAcc']):,}")
    except Exception as e:
        pass
    cur += timedelta(days=1)

if results:
    with open("king_daily_data.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"\n저장 완료: king_daily_data.csv ({len(results)}행)")
else:
    print("\n데이터 없음 - API 키 문제 또는 해당 영화 미진입")
    # HTML 파싱 방식으로 폴백 시도
    print("\n=== FALLBACK: HTML 파싱 ===")
    fallback = "https://www.kobis.or.kr/kobis/business/mast/mvie/searchMovieDtlList.do"
    r4 = SESSION.get(fallback, params={"movieCd": MOVIE_CD}, headers={
        **HEADERS, "Accept": "text/html"
    })
    r4.encoding = 'utf-8'
    s4 = BeautifulSoup(r4.text, 'html.parser')
    tables = s4.find_all('table')
    print(f"테이블 수: {len(tables)}")
    for t in tables[:3]:
        print(t.prettify()[:400])
