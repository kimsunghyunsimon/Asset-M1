import streamlit as st
import pandas as pd
import yfinance as yf
import io

# 1. 페이지 설정
st.set_page_config(page_title="디지털강남서원 시장 분석기", layout="wide")

# 2. 제목
st.title("📡 디지털강남서원 AI 시장 정밀 분석기")
st.markdown("### 4대 기술적 지표(RSI, MACD, 볼린저밴드, 스토캐스틱) 기반 진단")
st.success("왼쪽 사이드바에 **종목코드**만 입력하세요. AI가 복잡한 차트를 분석해 드립니다.")
st.markdown("---")

# 3. 사이드바 설정
st.sidebar.header("🔍 종목 분석 요청")

# 📌 [추가된 부분] 친절한 입력 가이드
st.sidebar.info("""
**💡 입력 예시 (중요)**
입력창에 종목코드를 아래 규칙대로 적어주세요.

* **코스피 (삼성전자 등):** 숫자.KS  
  (예: `005930.KS`)
* **코스닥 (에코프로 등):** 숫자.KQ  
  (예: `086520.KQ`)
* **미국 (엔비디아 등):** 영어약어  
  (예: `NVDA`)
""")

st.sidebar.subheader("⬇️ 여기에 붙여넣으세요")

# 예시 텍스트 (입력창에 미리 보여줄 내용)
example_text = """005930.KS
000660.KS
AAPL
TSLA
NVDA"""

# 입력창
paste_area = st.sidebar.text_area("종목코드 목록 (한 줄에 하나씩)", example_text, height=200)

# 종목 이름 사전 (빠른 매칭용)
stock_names = {
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "005380.KS": "현대차",
    "005490.KS": "POSCO홀딩스", "035420.KS": "NAVER", "035720.KS": "카카오",
    "105560.KS": "KB금융", "086520.KQ": "에코프로", "247540.KQ": "에코프로비엠",
    "AAPL": "애플", "TSLA": "테슬라", "NVDA": "엔비디아", 
    "MSFT": "마이크로소프트", "QQQ": "나스닥100", "SPY": "S&P500",
    "GOOGL": "구글(Alphabet)"
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

            analysis_data = []
            progress_bar = st.progress(0)
            total_rows = len(codes)

            for i, code in enumerate(codes):
                # 데이터 수집 (최근 6개월)
                ticker = yf.Ticker(code)
                hist = ticker.history(period="6mo")
                
                if hist.empty:
                    continue
                
                # 종목명 찾기 (사전 -> 인터넷 검색)
                name = stock_names.get(code, code)
                if name == code: 
                    try:
