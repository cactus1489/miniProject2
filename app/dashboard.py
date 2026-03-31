import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os
import numpy as np
from datetime import datetime, timedelta

# --------------------------------------------------------------------------------
# 1. 페이지 초기 설정 및 스타일링
# --------------------------------------------------------------------------------
st.set_page_config(page_title="K-Movie 천만 흥행 예측 & 투자 전략 대시보드", layout="wide")

# 프리미엄 다크 테마 커스텀 CSS
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #3e4150;
    }
    .stAlert {
        border-radius: 10px;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 2. 데이터 로딩 및 전처리
# --------------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

@st.cache_data
def load_all_data():
    # 주요 파일들 로드
    df_box = pd.read_csv(os.path.join(DATA_DIR, "all_movies_processed_integrated.csv"))
    df_det = pd.read_csv(os.path.join(DATA_DIR, "movie_details_integrated.csv"))
    df_sent = pd.read_csv(os.path.join(DATA_DIR, "news_sentiment_integrated.csv"))
    df_dl = pd.read_csv(os.path.join(DATA_DIR, "naver_datalab_integrated.csv"))
    
    # 날짜 데이터 변환
    df_box['targetDt'] = pd.to_datetime(df_box['targetDt'])
    df_dl['period'] = pd.to_datetime(df_dl['period'])
    
    return df_box, df_det, df_sent, df_dl

try:
    df_box, df_det, df_sent, df_dl = load_all_data()
except Exception as e:
    st.error(f"데이터 로드 실패: {e}")
    st.stop()

# --------------------------------------------------------------------------------
# 3. 사이드바 컨트롤
# --------------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/wired/256/ffffff/movie-projector.png", width=100)
st.sidebar.title("K-Movie 흥행 공식 v1.0")
st.sidebar.markdown("---")

# 영화 선택 (ID 매핑 포함)
movie_list = df_box['movieNm'].unique()
selected_movie = st.sidebar.selectbox("🎯 대상 영화 선택", movie_list)

# 선택된 영화의 기본 정보 추출
movie_data = df_box[df_box['movieNm'] == selected_movie].sort_values('targetDt')
# movie_id_map (ID 보강)
id_map = {
    "명량": "myeongryang", "기생충": "parasite", "사도": "sado",
    "왕과 사는 남자": "the_kings_garden", "올빼미": "the_night_owl",
    "남산의 부장들": "the_man_standing_next", "헤어질 결심": "decision_to_leave"
}
selected_id = id_map.get(selected_movie, movie_data['movie_id'].iloc[0] if 'movie_id' in movie_data.columns else "")

st.sidebar.markdown("### 흥행 임계값(Thresholds)")
st.sidebar.info("""
- **유튜브**: 268만뷰
- **스크린**: 60% 점유율
- **상영 효율**: 80명/회 (초기)
""")

# --------------------------------------------------------------------------------
# 4. 메인 대시보드 - 상단 메트릭
# --------------------------------------------------------------------------------
st.title(f"📊 {selected_movie} 천만 흥행 예측 및 투자 전략 분석")
st.markdown(f"**기준일:** {movie_data['targetDt'].max().strftime('%Y-%m-%d')} | **분석 모드:** 1,000만 흥행 성공 공식 v1.0")

# KPI Summary
cols = st.columns(4)

# 1. ROI 계산
det_row = df_det[df_det['movieNm'] == selected_movie]
if not det_row.empty:
    det_row = det_row.iloc[0]
    budget_won = det_row.get('budget', 0) / 1e8 # 억 원 단위 (가정)
    revenue_won = det_row.get('revenue', 0) / 1e8
    roi = (revenue_won / budget_won * 100) if budget_won > 0 else 0
    total_audi = movie_data['audiAcc'].max() / 1e4 # 만 명 단위
    
    cols[0].metric("현재 ROI", f"{roi:,.0f}%", delta=f"{roi - 1456:,.0f}% (vs 천만 평균 1,456%)")
    cols[1].metric("누적 관객수", f"{total_audi:,.1f}만 명", delta="1,000만 목표")
    cols[2].metric("제작비 규모", f"{budget_won:,.0f}억 원", delta="안전: 100~150억")
    cols[3].metric("상영 유지력(Eff.)", f"{movie_data['aud_per_show'].mean():,.1f}명/회", delta="임계값: 40명")

# --------------------------------------------------------------------------------
# 5. EWS (72시간 조기 경보) 및 흥행 패턴
# --------------------------------------------------------------------------------
st.markdown("---")
c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("🚨 72시간 조기 경보 (EWS)")
    # 개봉 후 3일 데이터 추출
    first_3_days = movie_data.head(3)
    early_audi = first_3_days['audiAcc'].max() if not first_3_days.empty else 0
    
    if early_audi >= 1000000:
        st.success(f"**[성공 신호]**\n\n초기 3일 관객 {early_audi/1e4:,.0f}만 명 달성 (100만 돌파)")
    else:
        st.warning(f"**[주의 신호]**\n\n초기 관객 {early_audi/1e4:,.1f}만 명 (목표 미달)")
    
    st.markdown("**핵심 정밀 판정 구간**")
    st.write(f"- 스크린 점유율: {movie_data['salesShare'].iloc[0]:.1f}% (목표 60%)")
    st.write(f"- 1주차 드롭률: {((movie_data['audiCnt'].iloc[0] - movie_data['audiCnt'].iloc[6])/movie_data['audiCnt'].iloc[0]*100 if len(movie_data)>6 else 0):.1f}%")

with c2:
    st.subheader("📈 흥행 성장 패턴 매칭 (Benchmark)")
    # 시계열 데이터 시각화
    fig, ax = plt.subplots(figsize=(10, 4.5))
    
    # 실제 데이터
    days = np.arange(len(movie_data))
    ax.plot(days, movie_data['audiAcc']/1e4, label='실제 누적 관객(만)', color='gold', linewidth=3, marker='o', markersize=4)
    
    # 1,000만 표준 모델 (폭발형 vs 장기형)
    target_line = np.linspace(0, 1000, len(movie_data)) if len(movie_data) > 0 else []
    ax.plot(days, target_line, '--', color='gray', label='천만 성공 기준선', alpha=0.5)
    
    ax.set_facecolor('#0e1117')
    fig.patch.set_facecolor('#0e1117')
    ax.tick_params(colors='white')
    ax.set_ylabel("만 명", color='white')
    ax.legend()
    st.pyplot(fig)

# --------------------------------------------------------------------------------
# 6. 투자 수익성 및 리스크 분석
# --------------------------------------------------------------------------------
st.markdown("---")
st.subheader("💰 투자 수익성 및 리스크 매트릭스")

left, right = st.columns(2)

with left:
    # 예산 vs ROI 분산형 차트
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 전체 영화 리스트 표시 (배경)
    all_det = df_det.copy()
    all_det['roi'] = (all_det['revenue'] / all_det['budget'] * 100)
    all_det['budget_won'] = all_det['budget'] / 1e8
    
    ax.scatter(all_det['budget_won'], all_det['roi'], alpha=0.3, color='gray', label='타 영화')
    
    # 현재 영화 강조
    selected_det = all_det[all_det['movieNm'] == selected_movie]
    if not selected_det.empty:
        ax.scatter(selected_det['budget_won'], selected_det['roi'], s=200, color='red', marker='*', label='선택 영화')
    
    # 위험 구간 박스
    ax.axvspan(100, 150, color='green', alpha=0.1, label='안전 투자 구간')
    ax.axvspan(150, 233, color='orange', alpha=0.1, label='주의 구간')
    ax.axvspan(233, all_det['budget_won'].max()+50, color='red', alpha=0.1, label='위험 구간')
    
    ax.set_xlabel("제작비 (억 원)", color='white')
    ax.set_ylabel("ROI (%)", color='white')
    ax.legend()
    st.pyplot(fig)

with right:
    # 텍스트 분석 / 감성 지수
    st.markdown("#### 🎭 관객 정서 및 뉴스 감성 분석")
    sent_row = df_sent[df_sent['movie_name'] == selected_movie]
    if not sent_row.empty:
        neg = sent_row.iloc[0]['부정']
        neu = sent_row.iloc[0]['중립']
        pos = 100 - neg - neu
        
        # 도넛 차트
        fig, ax = plt.subplots()
        ax.pie([pos, neu, neg], labels=['긍정', '중립', '부정'], autopct='%1.1f%%', 
               colors=['#4CAF50', '#FFC107', '#F44336'], hole=0.5 if hasattr(ax, 'pie') else 0)
        ax.set_title("뉴스 타이틀 감성 분포", color='white')
        st.pyplot(fig)
    else:
        st.write("감성 분석 데이터가 존재하지 않습니다.")

# --------------------------------------------------------------------------------
# 7. 최종 투자 권고 및 전략
# --------------------------------------------------------------------------------
st.markdown("---")
st.subheader("💡 최종 분석 리포트 & 투자 제언")

# 로직에 기반한 의견 생성 (단순 자동 생성 예시)
if roi > 1000:
    conclusion = f"**{selected_movie}**은 현재 명량/기생충 모델과 유사한 '폭발형' 흥행을 보이고 있습니다. " \
                 "천만 관객 달성 가능성이 매우 높으며, 상영 효율 40명/회 지지를 위해 관객 참여형 이벤트를 확대할 것을 권장합니다."
elif roi > 100:
     conclusion = f"**{selected_movie}**은 중예산 안정형 구조를 보입니다. 80억~120억 원 사이의 효율적인 제작비 집행이 빛을 발하고 있으며, " \
                  "바이럴 버즈 확산 시 '역주행 장기형'으로 전환될 가능성이 있습니다."
else:
    conclusion = f"**{selected_movie}**은 타겟 미스매치로 인한 리스크를 안고 있습니다. " \
                 "초반 버즈량 대비 드롭률이 높으므로 OTT 홀드백 단축 전략 등을 통해 손실을 최소화하는 방안을 고려하십시오."

st.info(conclusion)

st.caption("Produced by Cinema Strategy Team | Data period: 2005~2026")
