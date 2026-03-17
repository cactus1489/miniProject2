# =============================================
# config.py — API 키 및 영화 기본 설정
# =============================================

# KOBIS Open API
KOBIS_API_KEY = "f5eef3421c3d6af8e85d6efc1c62c5fc"
KOBIS_BASE_URL = "https://kobis.or.kr/kobisopenapi/webservice/rest"

# 네이버 검색 API
NAVER_CLIENT_ID = "T6a3xK5XXPYpKNNrw7k4"
NAVER_CLIENT_SECRET = "b0rwJWmVyf"
NAVER_BASE_URL = "https://openapi.naver.com/v1/search"

# 분석 대상 영화 목록
MOVIES = [
    {
        "name": "왕과 사는 남자",
        "kobis_code": "20242837",
        "release_year": 2026,
        "genre": "사극",
        "era": "조선시대",
        "naver_query": "왕과 사는 남자 영화",
    },
    {
        "name": "사도",
        "kobis_code": "20154352",
        "release_year": 2015,
        "genre": "사극",
        "era": "조선시대",
        "naver_query": "사도 영화",
    },
    {
        "name": "명량",
        "kobis_code": "20131138",
        "release_year": 2014,
        "genre": "사극/전쟁",
        "era": "조선시대/임진왜란",
        "naver_query": "명량 영화",
    },
    {
        "name": "기생충",
        "kobis_code": "20183939",
        "release_year": 2019,
        "genre": "드라마/스릴러",
        "era": "현대",
        "naver_query": "기생충 영화 봉준호",
    },
]

# 데이터 저장 경로
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 성별 분류 키워드 사전
GENDER_KEYWORDS = {
    "female": [
        "감동", "눈물", "울었", "울컥", "설레", "배우", "잘생", "멋있",
        "OST", "음악", "사랑", "로맨스", "감성", "힐링", "공감", "여운",
        "아름답", "섬세", "디테일", "의상", "아련", "슬프", "따뜻",
    ],
    "male": [
        "전투씬", "역사", "고증", "연출", "CG", "스케일", "스펙터클",
        "액션", "전략", "전술", "통쾌", "웅장", "장군", "전쟁", "박진감",
        "현실적", "냉정", "분석", "몰입", "긴장감", "반전",
    ],
}

# 시대성 키워드
ERA_KEYWORDS = {
    "조선시대": ["왕", "신하", "사대부", "궁궐", "임금", "백성", "양반", "한복"],
    "임진왜란": ["이순신", "왜군", "전쟁", "해전", "거북선", "의병"],
    "현대": ["계층", "빈부격차", "반지하", "취업", "사회", "불평등"],
    "현재성": ["공감", "지금", "현실", "오늘날", "요즘", "우리", "사회적"],
}
