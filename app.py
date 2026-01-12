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
# 2. 사이드바 (메뉴 및 입력창)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Digital 강남서원")
    
    # 메뉴 선택
    menu = st.radio("메뉴 선택", ["📊 AI 시장 분석기", "✨ MMI (나만의 인덱스)"])
    st.markdown("---")
    
    # [메뉴 1] AI 시장 분석기일 때만 종목 검색창 표시
    if menu == "📊 AI 시장 분석기":
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
        
    else: # [메뉴 2] MMI일 때는 안내 메시지 표시
        st.subheader("✨ 인덱스 주문")
        st.info("우측 화면에서 당신만의 투자 아이디어를 주문해주세요.")

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
    st.success("**✨ MMI (Make My Index)**\n\n당신 자신의 아이디어로 인덱스를 만들어 드립니다.\n(좌측 상단 '✨ MMI' 메뉴 선택)")

st.divider()

# -----------------------------------------------------------------------------
# 4. 공통 함수 (데이터 및 이름 처리)
# -----------------------------------------------------------------------------

def get_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        return pd.DataFrame()

def get_stock_name(ticker):
    manual_names = {
        "005930.KS": "Samsung Electronics (삼성전자)",
        "000660.KS": "SK Hynix (SK하이닉스)",
        "373220.KS": "LG Energy Solution (LG엔솔)",
        "207940.KS": "Samsung Biologics (삼바)",
        "005380.KS": "Hyundai Motor (현대차)",
        "000270.KS": "Kia (기아)",
        "005490.KS": "POSCO Holdings (포스코홀딩스)",
        "035420.KS": "NAVER (네이버)",
        "068270.KS": "Celltrion (셀트리온)",
        "086520.KQ": "Ecopro (에코프로)",
        "247540.KQ": "Ecopro BM (에코프로비엠)"
    }
    if ticker in manual_names: return manual_names[ticker]
    try:
        stock_info = yf.Ticker(ticker).info
        name = stock_info.get('longName') or stock_info.get('shortName')
        if name: return name
    except: pass
    return ticker

# -----------------------------------------------------------------------------
# 5. 기능 로직 구현
# -----------------------------------------------------------------------------

# ==========================================
# [메뉴 1] AI 시장 분석기 (기존 기능 유지)
# ==========================================
if menu == "📊 AI 시장 분석기":
    
    def calculate_indicators(df):
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        return df

    if ticker:
        with st.spinner('데이터를 분석 중입니다...'):
            df = get_data(ticker, period)
            stock_name = get_stock_name(ticker)
        
        if not df.empty:
            df = calculate_indicators(df)
            
            display_title = f"📈 {stock_name} 핵심 지표 분석" if stock_name == ticker else f"📈 {stock_name} ({ticker}) 핵심 지표 분석"
            st.subheader(display_title)
            
            # 1. 4대 그래프
            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)
            
            with row1_col1:
                st.markdown("**1. 주가 및 이동평균선**")
                fig1 = go.Figure()
                fig1.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Candle'))
                fig1.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA 20'))
                fig1.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='blue', width=1), name='MA 60'))
                fig1.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig1, use_container_width=True)
            
            with row1_col2:
                st.markdown("**2. 거래량 추이**")
                fig2 = go.Figure()
                colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in df.iterrows()]
                fig2.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'))
                fig2.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig2, use_container_width=True)
                
            with row2_col1:
                st.markdown("**3. RSI (상대강도지수)**")
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name='RSI'))
                fig3.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="과매수")
                fig3.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="과매도")
                fig3.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), yaxis_range=[0, 100])
                st.plotly_chart(fig3, use_container_width=True)

            with row2_col2:
                st.markdown("**4. MACD & Signal**")
                fig4 = go.Figure()
                fig4.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='grey', width=1), name='MACD'))
                fig4.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='red', width=1), name='Signal'))
                fig4.add_bar(x=df.index, y=df['MACD']-df['Signal'], name='Oscillator', marker_color='lightgrey')
                fig4.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig4, use_container_width=True)

            st.markdown("---")

            # 2. 종합 판단
            st.subheader(f"🤖 {stock_name} 기술적 지표 종합 판단")
            last_row = df.iloc[-1]
            score = 0
            reasons = []

            if last_row['RSI'] < 30:
                score += 1; reasons.append("✅ RSI 과매도 구간 (반등 가능성)")
            elif last_row['RSI'] > 70:
                score -= 1; reasons.append("🔻 RSI 과매수 구간 (조정 가능성)")
            
            if last_row['MACD'] > last_row['Signal']:
                score += 1; reasons.append("✅ MACD 상승 추세")
            else:
                score -= 1; reasons.append("🔻 MACD 하락 추세")

            if last_row['Close'] > last_row['MA20']:
                score += 1; reasons.append("✅ 20일 이동평균선 상회")
            else:
                score -= 1; reasons.append("🔻 20일 이동평균선 하회")

            decision_map = {3:"강력 매수", 2:"강력 매수", 1:"매수", 0:"중립", -1:"매도", -2:"강력 매도", -3:"강력 매도"}
            final_decision = decision_map.get(score, "중립")

            c1, c2 = st.columns([1, 2])
            with c1: st.metric("투자의견", final_decision)
            with c2: 
                for r in reasons: st.write(r)
                if not reasons: st.write("특이 사항 없음 (중립)")

            st.markdown("---")

            # 3. 몬테카를로
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

            end_mean = sim_df.iloc[-1].mean()
            ret = ((end_mean - last_price)/last_price)*100
            color_str = "red" if ret > 0 else "blue"
            direction = "상승" if ret > 0 else "하락"

            st.info(f"📊 현재가 대비 6개월 후 약 **:{color_str}[{ret:.1f}% {direction}]** 예상 (평균가: {end_mean:,.0f})")

            fig_mc = go.Figure()
            for col in sim_df.columns:
                fig_mc.add_trace(go.Scatter(y=sim_df[col], mode='lines', line=dict(width=1, color='rgba(100,100,255,0.1)'), showlegend=False))
            fig_mc.add_trace(go.Scatter(y=sim_df.mean(axis=1), mode='lines', line=dict(width=3, color='red'), name='평균 예상'))
            fig_mc.update_layout(height=400, xaxis_title="일수", yaxis_title="주가")
            st.plotly_chart(fig_mc, use_container_width=True)
        else:
            st.error("데이터를 불러오지 못했습니다. 티커를 확인해주세요.")

# ==========================================
# [메뉴 2] MMI (나만의 인덱스) - 주문형으로 변경
# ==========================================
elif menu == "✨ MMI (나만의 인덱스)":
    st.subheader("✨ MMI 인덱스 개발 의뢰")
    st.markdown("""
    당신의 독창적인 투자 아이디어를 적어주세요.  
    **Digital 강남서원**의 퀀트 전문가가 당신만의 인덱스 산식으로 구현해 드립니다.
    """)
    
    # 주문 폼 UI
    with st.container(border=True):
        st.markdown("### 📝 아이디어 명세서")
        
        # 입력 폼
        client_name = st.text_input("의뢰자 성명 (또는 닉네임)")
        index_name = st.text_input("인덱스 이름 (예: K-반도체 저평가 3선)")
        
        idea_desc = st.text_area(
            "아이디어 및 산식 설명", 
            placeholder="예시: \n코스피 시가총액 상위 50위 중,\nPER이 10 이하이고 최근 1달간 거래량이 급증한 종목 5개를 뽑아서 \n동일 가중치로 인덱스를 만들어주세요.",
            height=200
        )
        
        contact_info = st.text_input("연락받을 이메일 (결과 리포트 발송용)")
        
        # 전송 버튼
        submitted = st.button("📨 인덱스 개발 의뢰하기", use_container_width=True)

        if submitted:
            if client_name and idea_desc:
                st.success(f"✅ **{client_name}**님의 주문이 정상적으로 접수되었습니다!")
                st.balloons() # 축하 효과
                st.info("담당자가 내용을 검토한 후, 입력하신 이메일로 인덱스 분석 리포트를 보내드립니다.")
            else:
                st.error("성명과 아이디어 설명을 입력해주세요.")

    # 하단 예시 이미지 등 (꾸밈 요소)
    st.divider()
    st.markdown("#### 💡 이런 인덱스들이 만들어지고 있습니다.")
    st.info("🔹 **'강남 3구 부동산 연동 리츠 지수'** (김**수 회원님)")
    st.info("🔹 **'AI 전력 설비 관련주 모멘텀 지수'** (Park** 회원님)")
    st.info("🔹 **'외국인 순매수 지속 바이오 Top 3'** (이**영 회원님)")


# -----------------------------------------------------------------------------
# 6. 푸터
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption("© 2024 Digital 강남서원")
