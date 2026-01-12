import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

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
    
    # [수정 1] 메뉴 아이콘을 상단 설명과 일치시킴 (📊, ✨)
    menu = st.radio("메뉴 선택", ["📊 AI 시장 분석기", "✨ MMI (나만의 인덱스)"])
    st.markdown("---")
    
    st.subheader("🔍 종목 검색")
    
    with st.expander("📌 국내 주식 입력 방법 (Click)"):
        st.markdown("""
        **종목코드 뒤에 국가 코드를 붙여주세요.**
        - **코스피**: `.KS` (예: 삼성전자 `005930.KS`)
        - **코스닥**: `.KQ` (예: 에코프로 `086520.KQ`)
        - **미국**: 티커 그대로 (예: `AAPL`)
        """)

    ticker = st.text_input("티커 입력", value="005930.KS").upper()
    period = st.selectbox("분석 기간", ["1y", "2y", "5y", "10y"], index=0)
    
    st.info("💡 티커 입력 후 엔터(Enter)를 누르세요.")

# -----------------------------------------------------------------------------
# 3. 메인 화면 - 상단 디자인
# -----------------------------------------------------------------------------

st.markdown("""
    <h1 style='text-align: center; margin-bottom: 30px; font-size: 3rem;'>
        Digital 강남서원
    </h1>
    """, unsafe_allow_html=True)

col_head1, col_head2 = st.columns(2)

with col_head1:
    st.info("**📊 AI시장 분석기**\n\n주식시장의 핵심 3대 지표와 미래 시뮬레이션에 집중합니다.")

with col_head2:
    st.success("**✨ MMI**\n\n당신 자신의 아이디어로 인덱스를 만들어 드립니다.\n(좌측 상단 '✨ MMI' 메뉴 선택)")

st.divider()

# -----------------------------------------------------------------------------
# 4. 데이터 처리 및 로직
# -----------------------------------------------------------------------------

def get_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        return pd.DataFrame()

# [수정 2] 기업 이름 가져오는 함수 추가
def get_stock_name(ticker):
    try:
        stock_info = yf.Ticker(ticker).info
        # 긴 이름(longName)이 없으면 짧은 이름(shortName), 그것도 없으면 티커 반환
        return stock_info.get('longName', stock_info.get('shortName', ticker))
    except:
        return ticker

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

# [메뉴 1] AI 시장 분석기
if menu == "📊 AI 시장 분석기":
    if ticker:
        with st.spinner('데이터를 분석 중입니다...'):
            df = get_data(ticker, period)
            # 기업 이름 가져오기
            stock_name = get_stock_name(ticker)
        
        if not df.empty:
            df = calculate_indicators(df)
            
            # --- [Part 1] 4대 핵심 그래프 (2x2) ---
            # [수정 2 적용] 제목에 티커 대신 기업 이름 표시
            st.subheader(f"📈 {stock_name} ({ticker}) 핵심 지표 분석")
            
            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)
            
            # 1. 주가 & 이동평균선
            with row1_col1:
                st.markdown("**1. 주가 및 이동평균선**")
                fig1 = go.Figure()
                fig1.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Candle'))
                fig1.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA 20'))
                fig1.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='blue', width=1), name='MA 60'))
                fig1.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig1, use_container_width=True)
            
            # 2. 거래량
            with row1_col2:
                st.markdown("**2. 거래량 추이**")
                fig2 = go.Figure()
                colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in df.iterrows()]
                fig2.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'))
                fig2.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig2, use_container_width=True)
                
            # 3. RSI
            with row2_col1:
                st.markdown("**3. RSI (상대강도지수)**")
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name='RSI'))
                fig3.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="과매수(70)")
                fig3.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="과매도(30)")
                fig3.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), yaxis_range=[0, 100])
                st.plotly_chart(fig3, use_container_width=True)

            # 4. MACD
            with row2_col2:
                st.markdown("**4. MACD & Signal**")
                fig4 = go.Figure()
                fig4.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='grey', width=1), name='MACD'))
                fig4.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='red', width=1), name='Signal'))
                fig4.add_bar(x=df.index, y=df['MACD']-df['Signal'], name='Oscillator', marker_color='lightgrey')
                fig4.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig4, use_container_width=True)

            st.markdown("---")

            # --- [Part 2] 종합 매수/매도 판단 ---
            st.subheader(f"🤖 {stock_name} 기술적 지표 종합 판단")
            
            last_row = df.iloc[-1]
            score = 0
            reasons = []

            # (1) RSI 판단
            if last_row['RSI'] < 30:
                score += 1
                reasons.append("✅ RSI가 과매도 구간(30이하)입니다. 반등 가능성이 있습니다.")
            elif last_row['RSI'] > 70:
                score -= 1
                reasons.append("🔻 RSI가 과매수 구간(70이상)입니다. 조정 가능성이 있습니다.")
            else:
                reasons.append("➖ RSI는 중립 구간입니다.")

            # (2) MACD 판단
            if last_row['MACD'] > last_row['Signal']:
                score += 1
                reasons.append("✅ MACD가 시그널 위(상승추세)에 있습니다.")
            else:
                score -= 1
                reasons.append("🔻 MACD가 시그널 아래(하락추세)에 있습니다.")

            # (3) 이동평균선 판단
            if last_row['Close'] > last_row['MA20']:
                score += 1
                reasons.append("✅ 주가가 20일 이동평균선 위에 위치합니다.")
            else:
                score -= 1
                reasons.append("🔻 주가가 20일 이동평균선 아래에 위치합니다.")

            # 종합 의견
            if score >= 2: final_decision = "강력 매수 (Strong Buy)"
            elif score == 1: final_decision = "매수 (Buy)"
            elif score == 0: final_decision = "중립 (Neutral)"
            elif score == -1: final_decision = "매도 (Sell)"
            else: final_decision = "강력 매도 (Strong Sell)"

            col_res1, col_res2 = st.columns([1, 2])
            with col_res1:
                st.metric(label="현재 투자의견", value=final_decision)
            with col_res2:
                for reason in reasons:
                    st.write(reason)

            st.markdown("---")

            # --- [Part 3] 몬테카를로 시뮬레이션 ---
            st.subheader(f"🔮 {stock_name} 미래 예측 (6개월)")
            
            days_forecast = 126
            simulations = 50
            last_price = df['Close'].iloc[-1]
            daily_vol = df['Close'].pct_change().std()
            
            sim_df = pd.DataFrame()

            for i in range(simulations):
                daily_returns = np.random.normal(0, daily_vol, days_forecast)
                price_series = [last_price]
                for r in daily_returns:
                    price_series.append(price_series[-1] * (1 + r))
                sim_df[f'Sim_{i}'] = price_series

            end_prices = sim_df.iloc[-1]
            mean_end_price = end_prices.mean()
            max_end_price = end_prices.max()
            min_end_price = end_prices.min()
            
            expected_return = ((mean_end_price - last_price) / last_price) * 100
            color_str = "red" if expected_return > 0 else "blue"
            direction_str = "상승" if expected_return > 0 else "하락"

            st.info(f"""
            📊 **시뮬레이션 요약 분석**
            
            **{stock_name}**의 현재 주가 (**{last_price:,.0f}**) 대비 6개월 후 평균적으로 약 **:{color_str}[{expected_return:.2f}% {direction_str}]** 할 것으로 예측됩니다.
            
            - **평균 예상가**: {mean_end_price:,.0f}
            - **최대 낙관가**: {max_end_price:,.0f} (Best Case)
            - **최대 비관가**: {min_end_price:,.0f} (Worst Case)
            """)

            fig_mc = go.Figure()
            for col in sim_df.columns:
                fig_mc.add_trace(go.Scatter(y=sim_df[col], mode='lines', 
                                            line=dict(width=1, color='rgba(100, 100, 255, 0.1)'),
                                            showlegend=False))
            
            fig_mc.add_trace(go.Scatter(y=sim_df.mean(axis=1), mode='lines',
                                        line=dict(width=3, color='red'), name='평균 예상 경로'))
            
            fig_mc.update_layout(height=400, title=f"{stock_name} 향후 6개월 시나리오", 
                                 xaxis_title="미래 거래일수 (Days)", yaxis_title="주가")
            st.plotly_chart(fig_mc, use_container_width=True)

        else:
            st.error("데이터 로드 실패. 티커를 확인해주세요. (예: 삼성전자 -> 005930.KS)")

elif menu == "✨ MMI (나만의 인덱스)":
    st.subheader("✨ MMI 생성기")
    st.info("준비 중인 기능입니다.")

st.markdown("---")
st.caption("© 2024 Digital 강남서원")
