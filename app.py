import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Digital 강남서원",
    page_icon="📈",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 사이드바 (메뉴 구성)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Digital 강남서원 메뉴")
    menu = st.radio("이동하기", ["🏠 AI 시장 분석기", "✨ MMI (나만의 인덱스)"])
    
    st.markdown("---")
    st.caption("설정")
    ticker = st.text_input("분석할 티커 (예: SPY, AAPL)", value="SPY")
    period = st.selectbox("기간", ["1y", "2y", "5y", "10y"], index=0)

# -----------------------------------------------------------------------------
# 3. 메인 화면 UI (요청하신 디자인 적용)
# -----------------------------------------------------------------------------

# 헤드라인 (굵고 크게, 가운데 정렬)
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 30px; font-size: 3rem;'>
        Digital 강남서원
    </h1>
    """, unsafe_allow_html=True)

# 상단 2단 블록 레이아웃
col_info1, col_info2 = st.columns(2)

with col_info1:
    st.info(
        "**📊 AI시장 분석기**\n\n"
        "주식시장의 핵심 3대 지표와 미래 시뮬레이션에 집중합니다."
    )

with col_info2:
    st.success(
        "**✨ MMI**\n\n"
        "당신 자신의 아이디어로 인덱스를 만들어 드립니다.\n"
        "(좌측 상단 '✨ MMI' 메뉴 선택)"
    )

st.divider()

# -----------------------------------------------------------------------------
# 4. 기능 로직 구현
# -----------------------------------------------------------------------------

def get_stock_data(ticker, period):
    """주가 데이터 가져오기"""
    df = yf.download(ticker, period=period, progress=False)
    # 멀티인덱스 컬럼 처리 (yfinance 최신 버전 대응)
    if isinstance(df.columns, pd.MultiIndex):
         df.columns = df.columns.get_level_values(0)
    return df

if menu == "🏠 AI 시장 분석기":
    # 데이터 로딩
    with st.spinner(f'{ticker} 데이터를 분석 중입니다...'):
        df = get_stock_data(ticker, period)
    
    if not df.empty:
        # [섹션 1] 3대 기술적 지표 (이동평균선, 볼린저밴드 예시)
        st.subheader(f"📈 {ticker} 핵심 기술적 지표 분석")
        
        # 지표 계산
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_60'] = df['Close'].rolling(window=60).mean()
        
        # 차트 그리기
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index,
                        open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], name='캔들차트'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='orange', width=1), name='20일 이동평균'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_60'], line=dict(color='blue', width=1), name='60일 이동평균'))
        
        fig.update_layout(height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # [섹션 2] 몬테카를로 시뮬레이션
        st.subheader("🔮 몬테카를로 미래 예측 시뮬레이션")
        st.markdown("과거 변동성을 기반으로 **향후 6개월(126 거래일)**의 주가 흐름을 50가지 시나리오로 예측합니다.")

        # 시뮬레이션 로직
        days_forecast = 126 # 6개월
        simulations = 50
        last_price = df['Close'].iloc[-1]
        
        # 일간 수익률 및 변동성 계산
        returns = df['Close'].pct_change().dropna()
        daily_vol = returns.std()
        
        simulation_df = pd.DataFrame()

        for i in range(simulations):
            # 랜덤 변동성 생성
            daily_returns = np.random.normal(0, daily_vol, days_forecast)
            price_series = [last_price]
            
            for r in daily_returns:
                price_series.append(price_series[-1] * (1 + r))
            
            simulation_df[f'Sim_{i}'] = price_series

        # 시뮬레이션 차트
        fig_mc = go.Figure()
        for col in simulation_df.columns:
            fig_mc.add_trace(go.Scatter(y=simulation_df[col], mode='lines', 
                                        line=dict(width=1, color='rgba(100, 100, 255, 0.2)'),
                                        showlegend=False))
        
        # 평균 예측선
        fig_mc.add_trace(go.Scatter(y=simulation_df.mean(axis=1), mode='lines',
                                    line=dict(width=3, color='red'), name='평균 예상 경로'))

        fig_mc.update_layout(height=400, title=f"{ticker} 향후 시나리오", 
                             xaxis_title="미래 거래일 (Days)", yaxis_title="주가")
        st.plotly_chart(fig_mc, use_container_width=True)

    else:
        st.error("데이터를 불러오지 못했습니다. 티커를 확인해주세요.")

elif menu == "✨ MMI (나만의 인덱스)":
    st.subheader("✨ MMI (My Market Index) 생성기")
    st.write("관심 있는 종목들을 조합하여 당신만의 인덱스를 만들어보세요.")
    
    col_input, col_view = st.columns([1, 2])
    
    with col_input:
        st.markdown("### 포트폴리오 구성")
        input_tickers = st.text_area("종목 코드 입력 (쉼표로 구분)", "AAPL, MSFT, GOOGL, NVDA")
        st.button("인덱스 생성하기")
    
    with col_view:
        st.info("💡 예시: 반도체, AI, 바이오 등 테마별로 종목을 묶어서 성과를 비교해 볼 수 있습니다.")
        # (여기에 추후 인덱스 계산 로직을 추가하면 됩니다)
        st.markdown(f"**입력된 종목:** {input_tickers}")
        st.warning("이 기능은 현재 아이디어 스케치 단계입니다. (로직 추가 가능)")

# -----------------------------------------------------------------------------
# 5. 하단 푸터
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>© 2024 Digital 강남서원 | All Rights Reserved.</div>", unsafe_allow_html=True)
