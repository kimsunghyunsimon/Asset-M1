
import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import platform
from matplotlib import font_manager, rc

# 1. 페이지 설정
st.set_page_config(page_title="디지털강남서원 AI 어드바이저", layout="wide")

# 한글 폰트 설정 (스트림릿 클라우드 리눅스 환경 대응)
plt.rcParams['axes.unicode_minus'] = False
if platform.system() == 'Linux':
    plt.rc('font', family='NanumGothic')
else:
    # 윈도우/맥 등 로컬 환경용 (필요시 폰트명 변경)
    plt.rc('font', family='Malgun Gothic')

# 2. 제목 및 소개
st.title("🤖 디지털강남서원 AI 로보어드바이저")
st.markdown("### 30년 금융 전문가의 Insight & AI 기술의 결합")
st.info("보유하신 우량주 10종목의 **자산 가치**와 **AI 매매 신호(RSI)**를 실시간으로 분석합니다.")
st.markdown("---")

# 3. 사이드바: 포트폴리오 구성
st.sidebar.header("📝 포트폴리오 구성")

# 10개 우량주 기본 세팅 (한국 + 미국)
default_data = pd.DataFrame([
    {"종목코드": "005930.KS", "수량": 100},  # 삼성전자
    {"종목코드": "000660.KS", "수량": 50},   # SK하이닉스
    {"종목코드": "005380.KS", "수량": 30},   # 현대차
    {"종목코드": "005490.KS", "수량": 20},   # POSCO홀딩스
    {"종목코드": "035420.KS", "수량": 15},   # NAVER
    {"종목코드": "AAPL", "수량": 10},        # 애플 (미국)
    {"종목코드": "TSLA", "수량": 10},        # 테슬라 (미국)
    {"종목코드": "NVDA", "수량": 5},         # 엔비디아 (미국)
    {"종목코드": "MSFT", "수량": 5},         # 마이크로소프트 (미국)
    {"종목코드": "QQQ", "수량": 20}          # QQQ (나스닥 ETF)
])
input_df = st.sidebar.data_editor(default_data, num_rows="dynamic")

# 4. 핵심 로직: RSI 계산 함수
def calculate_rsi(data, window=14):
    delta = data.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 5. 실행 버튼 및 분석
if st.sidebar.button("🚀 AI 정밀 분석 시작"):
    with st.spinner('AI가 전 세계 증시 데이터를 수집하고 분석 중입니다...'):
        try:
            # 실시간 환율 조회
            fx_ticker = yf.Ticker("KRW=X")
            fx = fx_ticker.history(period="1d")['Close'].iloc[-1]
            
            total_val = 0
            portfolio_data = []

            # 진행률 바
            progress_bar = st.progress(0)
            total_rows = len(input_df)

            for i, (index, row) in enumerate(input_df.iterrows()):
                code = str(row['종목코드']).strip()
                qty = int(row['수량'])
                
                # 데이터 가져오기 (RSI 계산을 위해 3달치)
                ticker = yf.Ticker(code)
                hist = ticker.history(period="3mo")
                
                if hist.empty:
                    continue
                    
                price = hist['Close'].iloc[-1]
                
                # RSI 지표 계산
                rsi_series = calculate_rsi(hist['Close'])
                rsi = rsi_series.iloc[-1]
                
                # 매매 의견 도출 알고리즘
                opinion = "HOLD (관망)"
                if rsi < 30:
                    opinion = "🔥 STRONG BUY (과매도)"
                elif rsi > 70:
                    opinion = "❄️ SELL (과열)"
                elif rsi < 40:
                    opinion = "BUY (저점 매수)"
                
                # 통화 변환 (한국 주식은 원화, 미국 주식은 달러 -> 원화 환산)
                if code.endswith(".KS") or code.endswith(".KQ"):
                    val_krw = price * qty
                    price_display = f"{price:,.0f} 원"
                else:
                    val_krw = price * fx * qty
                    price_display = f"{price:,.2f} $"
                
                portfolio_data.append({
                    "종목": code,
                    "수량": qty,
                    "현재가": price_display,
                    "RSI": round(rsi, 1),
                    "AI 의견": opinion,
                    "평가금액(원)": val_krw
                })
                total_val += val_krw
                
                # 진행률 업데이트
                progress_bar.progress((i + 1) / total_rows)

            # 결과 데이터프레임 생성
            res_df = pd.DataFrame(portfolio_data)
            
            # 레이아웃 분할 (좌측: 표 / 우측: 그래프)
            col1, col2 = st.columns([1.5, 1])
            
            with col1:
                st.subheader("📋 종목별 AI 진단 리포트")
                # 숫자 포맷팅 (보기 좋게)
                display_df = res_df.copy()
                display_df['평가금액(원)'] = display_df['평가금액(원)'].apply(lambda x: f"{x:,.0f} 원")
                st.dataframe(display_df, hide_index=True)

            with col2:
                st.subheader("💰 총 자산 포트폴리오")
                st.metric(label="총 평가 금액 (KRW)", value=f"{total_val:,.0f} 원", delta=f"환율: {fx:,.2f}원/$")
                
                # 파이 차트
                fig, ax = plt.subplots()
                # 색상 팔레트 적용
                colors = plt.cm.Pastel1(range(len(res_df)))
                ax.pie(res_df['평가금액(원)'], labels=res_df['종목'], autopct='%1.1f%%', startangle=90, colors=colors)
                st.pyplot(fig)
            
            st.success("✅ 분석 완료! 'AI 의견'은 참고용 보조지표입니다.")
            
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
