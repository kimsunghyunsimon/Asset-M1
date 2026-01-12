import streamlit as st
import pandas as pd
import yfinance as yf
import io

# 1. 페이지 설정
st.set_page_config(page_title="디지털강남서원 시장 분석기", layout="wide")

# 2. 제목
st.title("📡 디지털강남서원 AI 시장 정밀 분석기")
st.markdown("### 4대 기술적 지표(RSI, MACD, 볼린저밴드, 스토캐스틱) 기반 진단")
st.info("왼쪽 사이드바에 분석하고 싶은 **종목코드**만 입력하세요. AI가 매수/매도 타이밍을 진단합니다.")
st.markdown("---")

# 3. 사이드바 설정
st.sidebar.header("🔍 종목 분석 요청")

st.sidebar.subheader("종목코드 입력")
st.sidebar.caption("한 줄에 하나씩 코드만 입력하세요.")

# 예시 텍스트 (수량 없이 코드만)
example_text = """005930.KS
000660.KS
AAPL
TSLA
NVDA"""

# 입력창
paste_area = st.sidebar.text_area("여기에 붙여넣기 (Ctrl+V)", example_text, height=200)

# 종목 이름 사전
stock_names = {
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "005380.KS": "현대차",
    "005490.KS": "POSCO홀딩스", "035420.KS": "NAVER", "035720.KS": "카카오",
    "105560.KS": "KB금융", "AAPL": "애플", "TSLA": "테슬라",
    "NVDA": "엔비디아", "MSFT": "마이크로소프트", "QQQ": "나스닥100", "SPY": "S&P500"
}

# ==========================================================
# 📊 지표 계산 함수들
# ==========================================================

def get_rsi(data, window=14):
    delta = data['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_macd(data):
    exp12 = data['Close'].ewm(span=12, adjust=False).mean()
    exp26 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp12 - exp26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def get_bollinger(data, window=20):
    sma = data['Close'].rolling(window=window).mean()
    std = data['Close'].rolling(window=window).std()
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    return upper, sma, lower

def get_stochastic(data, n=14):
    low_min = data['Low'].rolling(window=n).min()
    high_max = data['High'].rolling(window=n).max()
    k = 100 * ((data['Close'] - low_min) / (high_max - low_min))
    return k

# ==========================================================

if st.sidebar.button("🚀 AI 시장 진단 시작"):
    with st.spinner('전 세계 증시 데이터를 수집하고 4대 지표를 분석 중입니다...'):
        try:
            # 입력 데이터 처리 (줄바꿈으로 분리)
            codes = [line.strip() for line in paste_area.split('\n') if line.strip()]
            
            if not codes:
                st.warning("입력된 종목코드가 없습니다.")
                st.stop()

            # 환율 (참고용)
            fx_ticker = yf.Ticker("KRW=X")
            fx_data = fx_ticker.history(period="1d")
            fx = fx_data['Close'].iloc[-1] if not fx_data.empty else 1400.0
            
            analysis_data = []
            progress_bar = st.progress(0)
            total_rows = len(codes)

            for i, code in enumerate(codes):
                # 데이터 수집
                ticker = yf.Ticker(code)
                hist = ticker.history(period="6mo")
                
                if hist.empty:
                    continue
                
                # 종목명 찾기
                name = stock_names.get(code, code)
                if name == code: # 사전에 없으면 인터넷 검색
                    try: name = ticker.info.get('longName', code)
                    except: pass
                
                price = hist['Close'].iloc[-1]
                
                # --- 지표 계산 ---
                rsi = get_rsi(hist).iloc[-1]
                
                macd_line, macd_signal = get_macd(hist)
                macd_val = macd_line.iloc[-1]
                signal_val = macd_signal.iloc[-1]
                
                upper, mid, lower = get_bollinger(hist)
                bb_lower = lower.iloc[-1]
                bb_upper = upper.iloc[-1]
                
                stoch_k = get_stochastic(hist).iloc[-1]

                # --- 종합 점수 채점 (Voting) ---
                score = 0
                reasons = []
                
                # 1. RSI
                if rsi < 30: 
                    score += 1
                    reasons.append("RSI 과매도")
                elif rsi > 70: 
                    score -= 1
                    reasons.append("RSI 과열")
                    
                # 2. MACD
                if macd_val > signal_val:
                    score += 0.5 
                else:
                    score -= 0.5
                    
                # 3. Bollinger
                if price <= bb_lower * 1.02:
                    score += 1
                    reasons.append("밴드 하단(저점)")
                elif price >= bb_upper * 0.98:
                    score -= 1
                    reasons.append("밴드 상단(고점)")
                    
                # 4. Stochastic
                if stoch_k < 20:
                    score += 0.5
                    reasons.append("스토캐스틱 바닥")
                elif stoch_k > 80:
                    score -= 0.5
                
                # 의견 도출
                if score >= 1.5: final_opinion = "🔥 강력 매수"
                elif score >= 0.5: final_opinion = "매수 우위"
                elif score <= -1.5: final_opinion = "❄️ 강력 매도"
                elif score <= -0.5: final_opinion = "매도 우위"
                else: final_opinion = "HOLD (관망)"
                
                # 화폐 단위 표시
                if code.endswith(".KS") or code.endswith(".KQ"):
                    price_display = f"{price:,.0f} 원"
                else:
                    price_display = f"{price:,.2f} $"
                
                analysis_data.append({
                    "종목명": name,
                    "코드": code,
                    "현재가": price_display,
                    "종합 의견": final_opinion,
                    "핵심 근거": ", ".join(reasons) if reasons else "-",
                    "RSI 지표": f"{rsi:.0f}",
                    "점수": score # 정렬용
                })
                progress_bar.progress((i + 1) / total_rows)

            # 결과 출력
            if analysis_data:
                res_df = pd.DataFrame(analysis_data)
                # 매수 의견이 강한 순서대로 정렬
                res_df = res_df.sort_values(by='점수', ascending=False)
                
                st.subheader("📋 AI 투자 진단 리포트")
                
                # 색상 입히기 (스타일링) - 데이터프레임 표시
                st.dataframe(
                    res_df[['종목명', '코드', '현재가', '종합 의견', '핵심 근거', 'RSI 지표']], 
                    use_container_width=True, 
                    hide_index=True
                )
                
                # ==========================================
                # 👇 [요청하신 부분] 하단 지표 설명 섹션
                # ==========================================
                st.markdown("---")
                st.subheader("📚 4대 투자 지표 간단 해설")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.info("🌡️ RSI (상대강도지수)")
                    st.markdown("""
                    **"시장 온도계"**
                    * **70 이상:** 너무 뜨거움 (과열/매도)
                    * **30 이하:** 너무 차가움 (침체/매수)
                    * 가장 기본이 되는 지표입니다.
                    """)

                with col2:
                    st.success("🌊 MACD (추세선)")
                    st.markdown("""
                    **"파도의 방향"**
                    * 주가의 큰 흐름(Trend)을 봅니다.
                    * 상승 기류인지 하락 기류인지 판단하여, 역추세 매매를 방지합니다.
                    """)

                with col3:
                    st.warning("b Bollinger Bands")
                    st.markdown("""
                    **"가격의 고무줄"**
                    * 통계적으로 주가가 움직이는 범위입니다.
                    * 밴드 하단을 건드리면 **'지나치게 싸다'**고 봅니다.
                    * 밴드 상단을 건드리면 **'지나치게 비싸다'**고 봅니다.
                    """)

                with col4:
                    st.error("⚡ Stochastic")
                    st.markdown("""
                    **"단기 타이밍"**
                    * RSI보다 더 민감합니다.
                    * 단기적인 **'치고 빠지기'** 타이밍을 잡을 때 유용한 보조 지표입니다.
                    """)
                
                st.caption("※ 본 분석 결과는 AI 알고리즘에 의한 참고용 자료이며, 최종 투자의 책임은 본인에게 있습니다.")

            else:
                st.warning("분석할 종목이 없습니다.")

            st.success("분석 완료!")
            
        except Exception as e:
            st.error(f"오류 발생: {e}")
