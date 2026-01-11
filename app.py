import streamlit as st
import pandas as pd
import yfinance as yf
import platform
import io # 텍스트 변환용 도구

# 1. 페이지 설정
st.set_page_config(page_title="디지털강남서원 자산관리", layout="wide")

# 2. 제목
st.title("📈 디지털강남서원 실전 자산관리")
st.markdown("### 구글시트 연동형 포트폴리오")
st.info("왼쪽 사이드바에 엑셀이나 구글시트 내용을 **복사(Ctrl+C)해서 붙여넣기(Ctrl+V)** 하세요.")
st.markdown("---")

# 3. 사이드바 설정
st.sidebar.header("📝 데이터 입력")

# ---------------------------------------------------------
# 📌 [핵심 기능] 엑셀/구글시트 복붙 전용 입력창
# ---------------------------------------------------------
st.sidebar.subheader("1. 엑셀 데이터 붙여넣기")
st.sidebar.caption("종목코드와 수량(숫자)만 드래그해서 복사하세요.")

# 기본 예시 텍스트 (사용자가 지우고 붙여넣을 공간)
example_text = """005930.KS	100
AAPL	10
005380.KS	30"""

paste_area = st.sidebar.text_area("여기에 Ctrl+V 하세요", example_text, height=150)

# ---------------------------------------------------------

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

# 4. RSI 계산 함수
def calculate_rsi(data, window=14):
    delta = data.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 5. 실행 로직
if st.sidebar.button("🚀 자산 비중 분석하기"):
    with st.spinner('엑셀 데이터를 읽고 분석 중입니다...'):
        try:
            # 1단계: 붙여넣은 텍스트를 데이터프레임으로 변환
            if paste_area.strip():
                # 탭(Tab)이나 콤마, 공백 등으로 구분된 데이터를 읽음
                try:
                    # sep='\t'는 엑셀/구글시트 복사본이 탭으로 구분되기 때문
                    input_df = pd.read_csv(io.StringIO(paste_area), sep='\t', header=None, names=['종목코드', '수량'])
                except:
                    # 탭이 안 먹힐 경우 공백으로 시도
                    input_df = pd.read_csv(io.StringIO(paste_area), sep=r'\s+', header=None, names=['종목코드', '수량'])
            else:
                st.warning("입력된 데이터가 없습니다.")
                st.stop()

            # 환율 조회
            fx_ticker = yf.Ticker("KRW=X")
            fx_data = fx_ticker.history(period="1d")
            fx = fx_data['Close'].iloc[-1] if not fx_data.empty else 1400.0
            
            total_val = 0
            portfolio_data = []

            # 2단계: 데이터 수집 및 분석
            total_rows = len(input_df)
            progress_bar = st.progress(0)

            for i, (index, row) in enumerate(input_df.iterrows()):
                # 데이터 정제 (공백 제거 등)
                code = str(row['종목코드']).strip()
                
                # 수량에 콤마(,)가 섞여 있어도 처리 (예: "1,000")
                try:
                    qty = int(str(row['수량']).replace(',', ''))
                except:
                    continue # 숫자가 아니면 건너뜀
                
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

            # 3단계: 결과 출력
            if total_val > 0:
                res_df = pd.DataFrame(portfolio_data)
                res_df['자산비중(%)'] = (res_df['평가금액(원)'] / total_val) * 100
                res_df = res_df.sort_values(by='평가금액(원)', ascending=False)
                
                display_df = res_df.copy()
                display_df['자산비중(%)'] = display_df['자산비중(%)'].apply(lambda x: f"{x:.1f}%")
                display_df['평가금액(원)'] = display_df['평가금액(원)'].apply(lambda x: f"{x:,.0f} 원")

                st.subheader(f"💰 총 자산: {total_val:,.0f} 원")
                st.write(f"(적용 환율: {fx:,.2f} 원/$)")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # 하단 설명
                st.markdown("---")
                with st.expander("ℹ️ RSI(상대강도지수)란 무엇인가요?"):
                    st.markdown("""
                    **RSI (Relative Strength Index)**는 주식 시장의 체온계입니다.
                    * **70 이상:** 과열 (매도 검토)
                    * **30 이하:** 침체 (매수 검토)
                    """)
            else:
                st.warning("분석할 수 있는 유효한 종목이 없습니다. 코드를 확인해주세요.")

            st.success("분석 완료")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다. 붙여넣은 데이터를 확인해주세요: {e}")
