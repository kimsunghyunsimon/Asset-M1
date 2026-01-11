import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

# 1. 페이지 설정
st.set_page_config(page_title="디지털강남서원 자산엔진", layout="wide")

# 한글 폰트 문제 해결 (스트림릿 클라우드용)
import platform
from matplotlib import font_manager, rc
plt.rcParams['axes.unicode_minus'] = False
if platform.system() == 'Linux':
    plt.rc('font', family='NanumGothic')

# 2. 제목
st.title("🏦 디지털강남서원 글로벌 자산 관리 엔진")
st.markdown("---")

# 3. 사이드바 입력
st.sidebar.header("📝 포트폴리오 입력")
st.sidebar.info("보유하신 주식의 코드와 수량을 입력해주세요.")

# 기본 데이터
default_data = pd.DataFrame([
    {"종목코드": "005930.KS", "수량": 100},
    {"종목코드": "AAPL", "수량": 10},
    {"종목코드": "TSLA", "수량": 15}
])
input_df = st.sidebar.data_editor(default_data, num_rows="dynamic")

# 4. 분석 실행 버튼
if st.sidebar.button("🚀 자산 분석 실행"):
    with st.spinner('AI가 전 세계 증시 데이터를 수집 중입니다...'):
        try:
            # 환율 조회
            fx_ticker = yf.Ticker("KRW=X")
            fx = fx_ticker.history(period="1d")['Close'].iloc[-1]
            
            total_val = 0
            portfolio_data = []

            for index, row in input_df.iterrows():
                code = str(row['종목코드']).strip()
                qty = int(row['수량'])
                
                # 주가 조회
                ticker = yf.Ticker(code)
                data = ticker.history(period="1d")
                
                if data.empty:
                    st.warning(f"⚠️ {code} 데이터를 찾을 수 없습니다.")
                    continue
                    
                price = data['Close'].iloc[-1]
                
                # 통화 변환
                if code.endswith(".KS") or code.endswith(".KQ"):
                    val_krw = price * qty
                    currency = "KRW"
                else:
                    val_krw = price * fx * qty
                    currency = "USD"
                
                portfolio_data.append({
                    "종목": code,
                    "수량": qty,
                    "현재가": f"{price:,.2f}",
                    "통화": currency,
                    "평가금액(원)": val_krw
                })
                total_val += val_krw

            # 결과 출력
            res_df = pd.DataFrame(portfolio_data)
            
            # 레이아웃 분할
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("💰 총 자산 평가액")
                st.metric(label="Total Asset", value=f"{total_val:,.0f} 원")
                st.write(f"ℹ️ 적용 환율: 1 USD = {fx:,.2f} KRW")
                
                st.subheader("📋 상세 내역")
                st.dataframe(res_df)

            with col2:
                st.subheader("📊 자산 구성 비율")
                fig, ax = plt.subplots()
                ax.pie(res_df['평가금액(원)'], labels=res_df['종목'], autopct='%1.1f%%', startangle=90)
                st.pyplot(fig)

            st.success("분석이 성공적으로 완료되었습니다!")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
