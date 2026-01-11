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

# 종목 이름 사전 (빠른 검색용)
stock_names = {
    "005930.KS": "삼성전자",
    "000660.KS": "SK하이닉스",
    "005380.KS": "현대차",
    "AAPL": "애플",
    "TSLA": "테슬라",
    "NVDA": "엔비디아",
    "QQQ": "나스닥100 ETF"
}

# 기본 데이터는 최소화 (사용자가 직접 입력하도록 유도)
# 빈 줄을 추가하려면 표 아래의 '+' 버튼을 누르면 됩니다.
default_data = pd.DataFrame([
    {"종목코드": "005930.KS", "수량": 10},
    {"종목코드": "AAPL", "수량": 5},
])

# num_rows="dynamic" 옵션이 있어서 사용자가 줄을 추가/삭제 가능
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

            # 1단계: 개별 종목 데이터 수집
            total_rows = len(input_df)
            progress_bar = st.progress(0)

            for i, (index, row) in enumerate(input_df.iterrows()):
                code = str(row['종목코드']).strip()
                qty = int(row['수량'])
                
                # 코드가 비어있으면 건너뛰기
                if not code: continue

                ticker = yf.Ticker(code)
                hist = ticker.history(period="3mo")
                
                if hist.empty: continue
                
                # 종목명 찾기
                if code in stock_names:
                    name = stock_names[code]
                else:
                    try:
                        name = ticker.info.get('longName', code)
                    except:
                        name = code
                
                price = hist['Close'].iloc[-1]
                rsi = calculate_rsi(hist['Close']).iloc[-1]
                
                # AI 의견
                opinion = "HOLD"
                if rsi < 30: opinion = "🔥 매수 (과매도)"
                elif rsi > 70: opinion = "❄️ 매도 (과열)"
                elif rsi < 40: opinion = "매수 관점"
                
                # 평가금액 계산
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
                    "평가금액(원)": val_krw  # 나중에 비중 계산용 (숫자)
                })
                total_val += val_krw
                progress_bar.progress((i + 1) / total_rows)

            # 2단계: 자산 비중 계산 및 결과 정리
            if total_val > 0:
                res_df = pd.DataFrame(portfolio_data)
                
                # 비중 컬럼 추가 (핵심 요청 사항)
                res_df['자산비중(%)'] = (res_df['평가금액(원)'] / total_val) * 100
                
                # 보기 좋게 정렬 (비중 높은 순서대로)
                res_df = res_df.sort_values(by='평가금액(원)', ascending=False)
                
                # 포맷팅 (숫자를 문자열로 변환하여 표에 표시)
                display_df = res_df.copy()
                display_df['자산비중(%)'] = display_df['자산비중(%)'].apply(lambda x: f"{x:.1f}%")
                display_df['평가금액(원)'] = display_df['평가금액(원)'].apply(lambda x: f"{x:,.0f} 원")

                # 결과 출력
                st.subheader(f"💰 총 자산: {total_val:,.0f} 원")
                st.write(f"(적용 환율: {fx:,.2f} 원/$)")
                
                # 그래프 없이 표만 넓게 보여주기
                st.dataframe(
                    display_df, 
                    use_container_width=True, # 화면 꽉 차게
                    hide_index=True
                )
            else:
                st.warning("입력된 종목이 없거나 데이터를 가져오지 못했습니다.")

            st.success("분석 완료")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
