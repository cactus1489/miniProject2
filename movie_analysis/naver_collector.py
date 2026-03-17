# =============================================
# naver_collector.py — 네이버 검색 API 수집
# =============================================

import requests
import json
import time
import re
import os
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from movie_analysis.config import (
    NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, NAVER_BASE_URL,
    MOVIES, DATA_DIR, GENDER_KEYWORDS
)


class NaverCollector:
    def __init__(self):
        self.headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def search(self, endpoint: str, query: str, display: int = 100, start: int = 1, sort: str = "sim") -> list:
        """네이버 검색 API 공통 호출"""
        url = f"{NAVER_BASE_URL}/{endpoint}.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort,
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("items", [])
            else:
                print(f"[NAVER] API 오류 {resp.status_code}: {resp.text[:200]}")
                return []
        except Exception as e:
            print(f"[NAVER] 요청 오류: {e}")
            return []

    def collect_news(self, movie_name: str, query: str, max_items: int = 100) -> list:
        """뉴스 수집 (최대 100건)"""
        items = self.search("news", query, display=100, sort="date")
        # HTML 태그 제거
        cleaned = []
        for item in items[:max_items]:
            cleaned.append({
                "type": "news",
                "movie": movie_name,
                "title": re.sub(r"<[^>]+>", "", item.get("title", "")),
                "description": re.sub(r"<[^>]+>", "", item.get("description", "")),
                "pubDate": item.get("pubDate", ""),
                "link": item.get("link", ""),
            })
        return cleaned

    def collect_blog(self, movie_name: str, query: str, max_items: int = 100) -> list:
        """블로그 리뷰 수집 (최대 100건)"""
        items = self.search("blog", query, display=100, sort="sim")
        cleaned = []
        for item in items[:max_items]:
            text = re.sub(r"<[^>]+>", "", item.get("description", ""))
            author_gender = self._estimate_gender(text)
            cleaned.append({
                "type": "blog",
                "movie": movie_name,
                "title": re.sub(r"<[^>]+>", "", item.get("title", "")),
                "description": text,
                "blogger": item.get("bloggername", ""),
                "pubDate": item.get("postdate", ""),
                "link": item.get("link", ""),
                "estimated_gender": author_gender,
                "gender_score": self._gender_score(text),
            })
        return cleaned

    def _gender_score(self, text: str) -> dict:
        """텍스트에서 성별 키워드 점수 계산"""
        text_lower = text.lower()
        female_score = sum(1 for kw in GENDER_KEYWORDS["female"] if kw in text)
        male_score = sum(1 for kw in GENDER_KEYWORDS["male"] if kw in text)
        return {"female": female_score, "male": male_score}

    def _estimate_gender(self, text: str) -> str:
        """성별 추정 (female / male / unknown)"""
        scores = self._gender_score(text)
        if scores["female"] > scores["male"]:
            return "female"
        elif scores["male"] > scores["female"]:
            return "male"
        return "unknown"

    def collect_all_movies(self) -> dict:
        """모든 영화에 대해 뉴스 + 블로그 수집"""
        all_data = {}

        for movie_cfg in MOVIES:
            name = movie_cfg["name"]
            query = movie_cfg["naver_query"]
            print(f"\n네이버 수집 중: {name}")

            news = self.collect_news(name, query + " 리뷰")
            time.sleep(0.5)  # API 호출 간격
            blog = self.collect_blog(name, query + " 후기 리뷰")
            time.sleep(0.5)

            all_data[name] = {
                "news": news,
                "blog": blog,
                "total_news": len(news),
                "total_blog": len(blog),
            }

            # 성별 분포 요약
            female_cnt = sum(1 for b in blog if b["estimated_gender"] == "female")
            male_cnt = sum(1 for b in blog if b["estimated_gender"] == "male")
            unknown_cnt = len(blog) - female_cnt - male_cnt

            print(f"   뉴스: {len(news)}건 | 블로그: {len(blog)}건")
            print(f"   성별 추정 -> 여성: {female_cnt} | 남성: {male_cnt} | 미분류: {unknown_cnt}")

        # JSON 저장
        out_path = os.path.join(DATA_DIR, "naver_reviews.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 저장 완료: {out_path}")

        return all_data


if __name__ == "__main__":
    collector = NaverCollector()
    data = collector.collect_all_movies()
    print("\n=== 수집 결과 요약 ===")
    for movie, d in data.items():
        print(f"  {movie}: 뉴스 {d['total_news']}건, 블로그 {d['total_blog']}건")
