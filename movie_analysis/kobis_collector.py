# =============================================
# kobis_collector.py — KOBIS Open API 데이터 수집
# =============================================

import requests
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from movie_analysis.config import KOBIS_API_KEY, KOBIS_BASE_URL, MOVIES, DATA_DIR


class KobisCollector:
    def __init__(self):
        self.api_key = KOBIS_API_KEY
        self.base_url = KOBIS_BASE_URL
        self.session = requests.Session()

    def get_movie_info(self, movie_code: str) -> dict:
        """영화 상세 정보 조회 (감독, 배우, 장르, 등급 등)"""
        url = f"{self.base_url}/movie/searchMovieInfo.json"
        params = {"key": self.api_key, "movieCd": movie_code}
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            info = data.get("movieInfoResult", {}).get("movieInfo", {})
            return {
                "movieCd": info.get("movieCd", ""),
                "movieNm": info.get("movieNm", ""),
                "movieNmEn": info.get("movieNmEn", ""),
                "prdtYear": info.get("prdtYear", ""),
                "openDt": info.get("openDt", ""),
                "typeNm": info.get("typeNm", ""),
                "showTm": info.get("showTm", ""),
                "nations": [n.get("nationNm", "") for n in info.get("nations", [])],
                "genres": [g.get("genreNm", "") for g in info.get("genres", [])],
                "directors": [d.get("peopleNm", "") for d in info.get("directors", [])],
                "actors": [
                    {"name": a.get("peopleNm", ""), "cast": a.get("cast", "")}
                    for a in info.get("actors", [])[:10]
                ],
                "companies": [
                    {"name": c.get("companyNm", ""), "type": c.get("companyPartNm", "")}
                    for c in info.get("companys", [])
                ],
                "audits": [
                    {"grade": a.get("watchGradeNm", ""), "number": a.get("auditNo", "")}
                    for a in info.get("audits", [])
                ],
            }
        except Exception as e:
            print(f"[KOBIS] 영화정보 조회 오류 ({movie_code}): {e}")
            return {}

    def get_daily_boxoffice(self, target_dt: str, movie_code: str = None) -> list:
        """일별 박스오피스 전체 or 특정 영화 조회"""
        url = f"{self.base_url}/boxoffice/searchDailyBoxOfficeList.json"
        params = {"key": self.api_key, "targetDt": target_dt}
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            movie_list = data.get("boxOfficeResult", {}).get("dailyBoxOfficeList", [])
            if movie_code:
                return [m for m in movie_list if m.get("movieCd") == movie_code]
            return movie_list
        except Exception as e:
            print(f"[KOBIS] 박스오피스 조회 오류 ({target_dt}): {e}")
            return []

    def get_weekly_boxoffice(self, target_dt: str, week_gb: str = "0") -> list:
        """주간 박스오피스 (week_gb: 0=주간, 1=주말)"""
        url = f"{self.base_url}/boxoffice/searchWeeklyBoxOfficeList.json"
        params = {"key": self.api_key, "targetDt": target_dt, "weekGb": week_gb}
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            return data.get("boxOfficeResult", {}).get("weeklyBoxOfficeList", [])
        except Exception as e:
            print(f"[KOBIS] 주간 박스오피스 오류: {e}")
            return []

    def get_peak_boxoffice(self, movie: dict) -> dict:
        """영화 개봉 첫 주 박스오피스 성적 조회"""
        from datetime import datetime, timedelta

        open_dt = movie.get("openDt", "")
        if not open_dt or len(open_dt) < 8:
            return {}

        # 개봉일 기준 7일치 수집
        peak = {"rank": 999, "max_daily_audi": 0, "total_audi_first_week": 0, "daily_data": []}
        try:
            start = datetime.strptime(open_dt, "%Y%m%d")
            for i in range(7):
                dt = start + timedelta(days=i)
                dt_str = dt.strftime("%Y%m%d")
                results = self.get_daily_boxoffice(dt_str, movie.get("movieCd", ""))
                if results:
                    r = results[0]
                    audi = int(r.get("audiCnt", 0))
                    rank = int(r.get("rank", 999))
                    peak["daily_data"].append({
                        "date": dt_str,
                        "rank": rank,
                        "audiCnt": audi,
                        "audiAcc": int(r.get("audiAcc", 0)),
                        "salesAmt": int(r.get("salesAmt", 0)),
                        "scrnCnt": int(r.get("scrnCnt", 0)),
                    })
                    if rank < peak["rank"]:
                        peak["rank"] = rank
                    if audi > peak["max_daily_audi"]:
                        peak["max_daily_audi"] = audi
                    peak["total_audi_first_week"] += audi
        except Exception as e:
            print(f"[KOBIS] 개봉 첫주 조회 오류: {e}")
        return peak

    def collect_all_movies(self) -> list:
        """MOVIES 설정의 모든 영화 데이터 수집"""
        results = []
        for movie_cfg in MOVIES:
            print(f"\n수집 중: {movie_cfg['name']} ({movie_cfg['kobis_code']})")
            info = self.get_movie_info(movie_cfg["kobis_code"])
            if info:
                # 설정 정보 병합
                info["genre_custom"] = movie_cfg["genre"]
                info["era"] = movie_cfg["era"]
                info["release_year"] = movie_cfg["release_year"]

                # 개봉 첫 주 박스오피스
                print(f"   → 개봉 첫주 박스오피스 조회...")
                peak = self.get_peak_boxoffice(info)
                info["peak_boxoffice"] = peak

                results.append(info)
                print(f"   완료: {info.get('movieNm')} | 감독: {', '.join(info.get('directors', []))} | 관람등급: {[a['grade'] for a in info.get('audits', [])]}")
            else:
                print(f"   데이터 없음")

        # JSON 저장
        out_path = os.path.join(DATA_DIR, "kobis_movies.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 저장 완료: {out_path} ({len(results)}개 영화)")
        return results


if __name__ == "__main__":
    collector = KobisCollector()
    data = collector.collect_all_movies()
    print("\n=== 수집 결과 요약 ===")
    for movie in data:
        print(f"  {movie['movieNm']}: 감독={movie.get('directors')}, 배우={[a['name'] for a in movie.get('actors', [])[:3]]}")
