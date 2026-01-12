import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Digital 강남서원",
    page_icon="📈",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. 사이드바 (종목 입력기 및 메뉴)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Digital 강남서원")
    
    # 메뉴 선택
    menu = st.radio("메뉴 선택", ["🏠 AI 시장 분석기", "✨ MMI (나만의 인덱스)"])
    st.markdown("---")
    
    # 종목 입력기
    st.subheader("🔍 종목 검색")
    ticker = st.text_input("티커 입력 (예: SPY, AAPL, NVDA)", value="SPY").upper()
    period = st.selectbox("분석 기간", ["1y", "2y", "5y", "10y"], index=0)
    
    st.info("💡 티커를 입력하고 엔터를 누르면 우측 화면이 갱신됩니다.")

# -----------------------------------------------------------------------------
# 3. 메인 화면 - 상단 디자인
# -----------------------------------------------------------------------------

# 헤드라인
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 30px; font-size: 3rem;'>
        Digital 강남서원
    </h1>
    """, unsafe_allow_html=True)

# 상단 2단 블록 레이아웃
col_head1, col_head2 = st.columns(2)

with col_head1:
    st.info(
        "**📊 AI시장 분석기**\n\n"
        "주식시장의 핵심 3대 지표와 미래 시뮬레이션에 집중합니다."
    )

with col_head2:
    st.success(
        "**✨ MMI**\n\n"
        "당신 자신의 아이디어로 인덱스를 만들어 드립니다.\n"
        "(좌측 상단 '✨ MMI' 메뉴 선택)"
    )

st.divider()

# -----------------------------------------------------------------------------
# 4. 메인 화면 - 하단 콘텐츠 (그래프 4개 배치)
# -----------------------------------------------------------------------------

# 데이터 가져오기 함수
def get_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:  # <--- 여기에 띄어쓰기를 수정했습니다!
        return pd.DataFrame()

# 지표 계산 함수
def calculate_indicators(df):
    # 이동평균
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

# [메뉴 1] AI 시장 분석기 로직
if menu == "🏠 AI 시장 분석기":
    if ticker:
        df = get_data(ticker, period)
        
        if not df.empty:
            df = calculate_indicators(df)
            
            st.subheader(f"📈 {ticker} 종합 분석 대시보드")
            
            # --- 그래프 4개 배치 (2x2 그리드) ---
            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)
            
            # 1. 주가 & 이동평균선
            with row1_col1:
                st.markdown("**1. 주가 및 이동평균선**")
                fig1 = go.Figure()
                fig1.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Candle'))
                fig1.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA 20'))
                fig1.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='blue', width=1), name='MA 60'))
                fig1.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig1, use_container_width=True)
            
            # 2. 거래량
            with row1_col2:
                st.markdown("**2. 거래량 추이**")
                fig2 = go.Figure()
                colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in df.iterrows()]
                fig2.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'))
                fig2.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig2, use_container_width=True)
                
            # 3. RSI
            with row2_col1:
                st.markdown("**3. RSI (상대강도지수)**")
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name='RSI'))
                fig3.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="과매수")
                fig3.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="과매도")
                fig3.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20), yaxis_range=[0, 100])
                st.plotly_chart(fig3, use_container_width=True)

            # 4. MACD
            with row2_col2:
                st.markdown("**4. MACD & Signal**")
                fig4 = go.Figure()
                fig4.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='grey', width=1), name='MACD'))
                fig4.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='red', width=1), name='Signal'))
                fig4.add_bar(x=df.index, y=df['MACD']-df['Signal'], name='Oscillator', marker_color='lightgrey')
                fig4.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig4, use_container_width=True)

        else:
            st.error("데이터를 불러올 수 없습니다. 티커를 확인해주세요.")

elif menu == "✨ MMI (나만의 인덱스)":
    st.subheader("✨ MMI 생성기")
    st.info("준비 중인 기능입니다.")

st.markdown("---")
st.caption("© 2024 Digital 강남서원")
