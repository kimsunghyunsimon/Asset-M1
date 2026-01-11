
import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import platform

# 1. 페이지 설정
st.set_page_config(page_title="디지털강남서원 AI 어드바이저", layout="wide")

# 한글 폰트 설정 (리눅스/윈도우 호환)
plt.rcParams['axes.unicode_minus'] = False
if platform.system() == 'Linux':
    plt.rc('font', family='NanumGothic')
else:
    plt.rc('font', family='Malgun Gothic')

# 2. 제목
st.title("🤖 디지털강남서원 AI 로보어드바이저")
st.markdown("### 30년 금융 전문가의 Insight & AI 기술의 결합")
st.info("보유하신 종목의 **종목명**, **자산 가치**, **AI 매매 신호(RSI)**를 분석합니다.")
st.markdown("---")

# 3. 사이드바: 포트폴리오 구성
st.sidebar.header("📝 포트폴리오 구성")

# 📌 [핵심] 자주 쓰는 종목 이름 사전 (속도 향상을 위해 미리 지정)
# 여기에 없는 종목은 AI가 인터넷에서 자동으로 이름을 찾아옵니다.
stock_names = {
    "395270.KS": "hanaro반도체",
    "396500.KS": "tiger반도체",
    "0080G0.KS": "방산ETF",
    "466920.KS": "조선ETF",
    "012450.KS": "한화에어로",
    "141080.KQ": "리가켐",
    "475830.KQ": "오름테라",
    "468530.KQ": "프로티나",
    "376900.KQ": "로켓헬스",
    "475960.KQ": "토모큐브",
    "CRML": "크리티널 메탈스"
}

# 기본 데이터 세팅
default_data = pd.DataFrame([
    {"종목코드": "395270.KS", "수량": 3260},
    {"종목코드": "396500.KS", "수량": 4416},
    {"종목코드": "0080G0.KS", "수량": 13000},
    {"종목코드": "466920.KS", "수량": 4440},
    {"종목코드": "012450.KS", "수량": 5},
    {"종목코드": "141080.KQ", "수량": 160},
    {"종목코드": "475830.KQ", "수량": 600},
    {"종목코드": "468530.KQ", "수량": 1400},
    {"종목코드": "376900.KQ", "수량": 1031},
    {"종목코드": "475960.KQ", "수량": 5},
    {"종목코드": "CRML", "수량": 20}
])
input_df = st.sidebar.data_editor(default_data, num_rows="dynamic")

# 4. RSI 계산 함수
def calculate_rsi(data, window=14):
    delta = data.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 5. 실행 버튼 및 분석 로직
if st.sidebar.button("🚀 AI 정밀 분석 시작"):
    with st.spinner('AI가 종목명을 확인하고 데이터를 분석 중입니다...'):
        try:
            # 실시간 환율 조회
            fx_ticker = yf.Ticker("KRW=X")
            fx_data = fx_ticker.history(period="1d")
            fx = fx_data['Close'].iloc[-1] if not fx_data.empty else 1400.0
            
            total_val = 0
            portfolio_data = []

            progress_bar = st.progress(0)
            total_rows = len(input_df)

            for i, (index, row) in enumerate(input_df.iterrows()):
                code = str(row['종목코드']).strip()
                qty = int(row['수량'])
                
                # 데이터 가져오기
                ticker = yf.Ticker(code)
                hist = ticker.history(period="3mo")
                
                if hist.empty:
                    continue
                
                # 📌 [추가된 기능] 종목명 가져오기
                # 1. 내 사전에 있으면 그거 쓰고, 2. 없으면 인터넷에서 검색
                if code in stock_names:
                    name = stock_names[code]
                else:
                    try:
                        # yfinance 정보에서 긴 이름 가져오기 (시간이 좀 걸릴 수 있음)
                        name = ticker.info.get('longName', code)
                    except:
                        name = code # 실패하면 그냥 코드명 사용
                
                price = hist['Close'].iloc[-1]
                
                # RSI 계산
                rsi_series = calculate_rsi(hist['Close'])
                rsi = rsi_series.iloc[-1]
                
                # 매매 의견
                opinion = "HOLD (관망)"
                if rsi < 30:
                    opinion = "🔥 STRONG BUY (과매도)"
                elif rsi > 70:
                    opinion = "❄️ SELL (과열)"
                elif rsi < 40:
                    opinion = "BUY (저점 매수)"
                
                # 통화 변환 및 포맷
                if code.endswith(".KS") or code.endswith(".KQ"):
                    val_krw = price * qty
                    price_display = f"{price:,.0f} 원"
                else:
                    val_krw = price * fx * qty
                    price_display = f"{price:,.2f} $"
                
                portfolio_data.append({
                    "종목명": name,       # <--- 여기에 종목명 추가!
                    "코드": code,
                    "수량": qty,
                    "현재가": price_display,
                    "RSI": round(rsi, 1),
                    "AI 의견": opinion,
                    "평가금액(원)": val_krw
                })
                total_val += val_krw
                
                progress_bar.progress((i + 1) / total_rows)

            # 결과 처리
            res_df = pd.DataFrame(portfolio_data)
            
            col1, col2 = st.columns([1.8, 1])
            
            with col1:
                st.subheader("📋 포트폴리오 상세 분석")
                display_df = res_df.copy()
                display_df['평가금액(원)'] = display_df['평가금액(원)'].apply(lambda x: f"{x:,.0f} 원")
                # 종목명이 맨 앞에 오도록 컬럼 순서 지정 가능하지만, 기본적으로 딕셔너리 순서 따름
                st.dataframe(display_df, hide_index=True)

            with col2:
                st.subheader("💰 자산 구성")
                st.metric(label="총 평가 금액 (KRW)", value=f"{total_val:,.0f} 원", delta=f"환율: {fx:,.2f}원/$")
                
                fig, ax = plt.subplots()
                colors = plt.cm.Pastel1(range(len(res_df)))
                # 파이 차트 라벨도 '종목명'으로 변경
                ax.pie(res_df['평가금액(원)'], labels=res_df['종목명'], autopct='%1.1f%%', startangle=90, colors=colors)
                st.pyplot(fig)
            
            st.success("✅ 분석 완료! 종목명과 함께 확인하세요.")
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
