import requests
import csv
import json
from datetime import datetime, timedelta

"""
KOBIS 오픈API를 통해 '왕과 사는 남자' (영화코드: 20242837) 일별 박스오피스 수집
- 개봉일 추정: 2026년 2월 초
- 오늘날짜: 2026-03-11
"""

MOVIE_CD = "20242837"
API_KEY = "f5eef3421c3d6af8e85d6efc1c62c5fc"  # 공개 샘플 키 (없을시 직접 요청 방식 사용)
OUTPUT_FILE = "king_daily_data.csv"

def fetch_daily_boxoffice(target_dt: str) -> list:
    """특정 날짜의 일별 박스오피스 데이터 中 '왕과 사는 남자' 행 반환"""
    url = "https://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": API_KEY,
        "targetDt": target_dt,
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        movieList = data["boxOfficeResult"]["dailyBoxOfficeList"]
        for movie in movieList:
            if movie.get("movieCd") == MOVIE_CD or "왕과 사는 남자" in movie.get("movieNm", ""):
                return [{
                    "날짜": target_dt,
                    "순위": movie.get("rank"),
                    "영화명": movie.get("movieNm"),
                    "일별관객수": movie.get("audiCnt"),
                    "누적관객수": movie.get("audiAcc"),
                    "일별매출액": movie.get("salesAmt"),
                    "누적매출액": movie.get("salesAcc"),
                    "스크린수": movie.get("scrnCnt"),
                    "상영횟수": movie.get("showCnt"),
                }]
    except Exception as e:
        print(f"Error for {target_dt}: {e}")
    return []

def collect_all():
    """개봉일부터 오늘까지 순회"""
    # 개봉일을 2026-02-05로 추정 (포스터 날짜 기반)
    start_date = datetime(2026, 2, 5)
    end_date = datetime(2026, 3, 11)
    
    rows = []
    cur = start_date
    while cur <= end_date:
        dt_str = cur.strftime("%Y%m%d")
        result = fetch_daily_boxoffice(dt_str)
        if result:
            rows.extend(result)
            print(f"[OK] {dt_str}: 순위 {result[0]['순위']}, 관객 {result[0]['일별관객수']:,}")
        else:
            print(f"[SKIP] {dt_str}: 박스오피스 미진입")
        cur += timedelta(days=1)

    if rows:
        keys = rows[0].keys()
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
        print(f"\n저장 완료: {OUTPUT_FILE} ({len(rows)}개 행)")
    else:
        print("데이터를 수집하지 못했습니다.")

if __name__ == "__main__":
    collect_all()
