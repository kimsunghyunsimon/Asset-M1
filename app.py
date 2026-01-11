
import streamlit as st
import pandas as pd
import yfinance as yf
import platform

# 1. 페이지 설정
st.set_page_config(page_title="디지털강남서원 자산관리", layout="wide")

# 2. 제목
st.title("📈 디지털강남서원 실전 자산관리")
st.markdown("### 내가 직접 만드는 포트폴리오 (비중 분석)")
st.info("왼쪽 사이드바에 **종목코드**와 **수량**을 직접 입력하세요.")
st.markdown("---")

# 3. 사이드바: 직접 입력하는 표
st.sidebar.header("📝 종목 입력 (직접 추가)")

# 종목 이름 사전
stock_names = {
    "005930.KS": "삼성전자",
    "000660.KS": "SK하이닉스",
    "005380.KS": "현대차",
    "005490.KS": "POSCO홀딩스",
    "035420.KS": "NAVER",
    "035720.KS": "카카오",
    "105560.KS": "KB금융",
    "AAPL": "애플",
    "TSLA": "테슬라",
    "NVDA": "엔비디아",
    "MSFT": "마이크로소프트",
    "QQQ": "나스닥100 ETF",
    "SPY": "S&P500 ETF"
}

# 기본 데이터 (빈 줄 추가는 표 아래 + 버튼)
default_data = pd.DataFrame([
    {"종목코드": "005930.KS", "수량": 10},
    {"종목코드": "AAPL", "수량": 5},
])

input_df = st.sidebar.data_editor(default_data, num_rows="dynamic")

# 4. RSI 계산 함수
def calculate_rsi(data, window=14):
    delta = data.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 5. 실행 로직
if st.sidebar.button("🚀 자산 비중 분석하기"):
    with st.spinner('현재가 및 자산 비중 계산 중...'):
        try:
            # 환율 조회
            fx_ticker = yf.Ticker("KRW=X")
            fx_data = fx_ticker.history(period="1d")
            fx = fx_data['Close'].iloc[-1] if not fx_data.empty else 1400.0
            
            total_val = 0
            portfolio_data = []

            # 1단계: 데이터 수집
            total_rows = len(input_df)
            progress_bar = st.progress(0)

            for i, (index, row) in enumerate(input_df.iterrows()):
                code = str(row['종목코드']).strip()
                qty = int(row['수량'])
                
                if not code: continue

                ticker = yf.Ticker(code)
                hist = ticker.history(period="3mo")
                
                if hist.empty: continue
                
                if code in stock_names:
                    name = stock_names[code]
                else:
                    try:
                        name = ticker.info.get('longName', code)
                    except:
                        name = code
                
                price = hist['Close'].iloc[-1]
                rsi = calculate_rsi(hist['Close']).iloc[-1]
                
                opinion = "HOLD"
                if rsi < 30: opinion = "🔥 매수 (과매도)"
                elif rsi > 70: opinion = "❄️ 매도 (과열)"
                elif rsi < 40: opinion = "매수 관점"
                
                if code.endswith(".KS") or code.endswith(".KQ"):
                    val_krw = price * qty
                    price_display = f"{price:,.0f} 원"
                else:
                    val_krw = price * fx * qty
                    price_display = f"{price:,.2f} $"
                
                portfolio_data.append({
                    "종목명": name,
                    "코드": code,
                    "수량": qty,
                    "현재가": price_display,
                    "RSI": round(rsi, 1),
                    "AI의견": opinion,
                    "평가금액(원)": val_krw
                })
                total_val += val_krw
                progress_bar.progress((i + 1) / total_rows)

            # 2단계: 결과 출력
            if total_val > 0:
                res_df = pd.DataFrame(portfolio_data)
                
                # 비중 계산
                res_df['자산비중(%)'] = (res_df['평가금액(원)'] / total_val) * 100
                res_df = res_df.sort_values(by='평가금액(원)', ascending=False)
                
                # 표 포맷팅
                display_df = res_df.copy()
                display_df['자산비중(%)'] = display_df['자산비중(%)'].apply(lambda x: f"{x:.1f}%")
                display_df['평가금액(원)'] = display_df['평가금액(원)'].apply(lambda x: f"{x:,.0f} 원")

                st.subheader(f"💰 총 자산: {total_val:,.0f} 원")
                st.write(f"(적용 환율: {fx:,.2f} 원/$)")
                
                st.dataframe(
                    display_df, 
                    use_container_width=True,
                    hide_index=True
                )
                
                # ==========================================
                # 👇 [추가됨] 하단 RSI 설명 섹션
                # ==========================================
                st.markdown("---")
                with st.expander("ℹ️ RSI(상대강도지수)란 무엇인가요? (클릭해서 보기)"):
                    st.markdown("""
                    **RSI (Relative Strength Index)**는 주식 시장의 **'체온계'**와 같습니다.
                    주가가 얼마나 과열되었는지(비싼지), 혹은 얼마나 침체되었는지(싼지)를 **0부터 100까지의 숫자**로 알려줍니다.
                    
                    * **70 이상 (❄️ 과열 구간):** * 사람들이 너무 많이 사서 가격이 비정상적으로 올랐습니다. 
                        * 조만간 떨어질 가능성이 높으니 **'매도'**를 고민하세요.
                    
                    * **30 이하 (🔥 침체 구간):** * 사람들이 공포에 질려 너무 많이 팔았습니다. 
                        * 가격이 쌀 때이니 **'매수'**를 고민할 좋은 기회입니다.
                        
                    * **40 ~ 60 (관망):** * 특별한 과열이나 침체 없이 평범하게 흘러가는 구간입니다.
                    """)
                    st.caption("※ 본 지표는 보조 수단이며, 투자의 책임은 본인에게 있습니다.")
                # ==========================================
                
            else:
                st.warning("데이터를 가져오지 못했습니다.")

            st.success("분석 완료")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
