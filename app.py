import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# ==========================================================
# 🔧 한글 폰트 설정 (나눔고딕 자동 다운로드)
# ==========================================================
def setup_korean_font():
    font_path = "NanumGothic.ttf"
    if not os.path.exists(font_path):
        import requests
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        response = requests.get(url)
        with open(font_path, "wb") as f:
            f.write(response.content)
    
    fm.fontManager.addfont(font_path)
    plt.rc('font', family='NanumGothic')
    plt.rc('axes', unicode_minus=False)

setup_korean_font()
# ==========================================================

# 1. 페이지 설정
st.set_page_config(page_title="디지털강남서원 시장 분석기", layout="wide")

# 2. 제목
st.title("📡 디지털강남서원 AI 시장 정밀 분석기")
st.markdown("### 4대 기술적 지표(RSI, MACD, 볼린저밴드, 스토캐스틱) 기반 진단")
st.success("왼쪽 사이드바에 **종목코드**만 입력하세요. 목록 분석 후 **개별 차트**를 확인할 수 있습니다.")
st.markdown("---")

# 3. 사이드바 설정
st.sidebar.header("🔍 종목 분석 요청")

st.sidebar.info("""
**💡 입력 예시**
* **코스피:** 숫자.KS (예: `005930.KS`)
* **코스닥:** 숫자.KQ (예: `086520.KQ`)
* **미국:** 영어약어 (예: `NVDA`)
""")

st.sidebar.subheader("⬇️ 종목코드 입력")
example_text = """005930.KS
000660.KS
AAPL
TSLA"""

paste_area = st.sidebar.text_area("목록 붙여넣기 (한 줄에 하나)", example_text, height=200)

stock_names = {
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "005380.KS": "현대차",
    "005490.KS": "POSCO홀딩스", "035420.KS": "NAVER", "035720.KS": "카카오",
    "105560.KS": "KB금융", "086520.KQ": "에코프로", "247540.KQ": "에코프로비엠",
    "AAPL": "애플", "TSLA": "테슬라", "NVDA": "엔비디아", 
    "MSFT": "마이크로소프트", "QQQ": "나스닥100", "SPY": "S&P500",
    "GOOGL": "구글"
}

# 4. 지표 계산 함수들
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

# 5. 실행 로직
if st.sidebar.button("🚀 AI 시장 진단 시작"):
    st.session_state['analyzed'] = True
    st.session_state['codes'] = [line.strip() for line in paste_area.split('\n') if line.strip()]

if st.session_state.get('analyzed'):
    with st.spinner('데이터 분석 및 차트 생성 중...'):
        codes = st.session_state['codes']
        if not codes:
            st.warning("입력된 코드가 없습니다.")
            st.stop()

        analysis_data = []
        chart_data_dict = {}
        
        progress_bar = st.progress(0)
        total_rows = len(codes)

        # 1단계: 전체 목록 분석
        for i, code in enumerate(codes):
            try:
                ticker = yf.Ticker(code)
                hist = ticker.history(period="6mo")
                if hist.empty: continue
                
                # 종목명 찾기
                name = stock_names.get(code, code)
                if name == code:
                    try: name = ticker.info.get('longName', code)
                    except: pass
                
                # 차트용 데이터 저장 (키값은 코드로 관리하여 중복 방지)
                chart_data_dict[code] = {'hist': hist, 'name': name}

                price = hist['Close'].iloc[-1]
                rsi = get_rsi(hist).iloc[-1]
                
                macd, signal = get_macd(hist)
                macd_val = macd.iloc[-1]
                sig_val = signal.iloc[-1]
                
                up, mid, low = get_bollinger(hist)
                bb_low = low.iloc[-1]
                bb_up = up.iloc[-1]
                
                stoch = get_stochastic(hist).iloc[-1]

                score = 0
                reasons = []
                
                if rsi < 30: score+=1; reasons.append("RSI 과매도")
                elif rsi > 70: score-=1; reasons.append("RSI 과열")
                
                if macd_val > sig_val: score+=0.5
                else: score-=0.5
                
                if price <= bb_low * 1.02: score+=1; reasons.append("밴드 하단")
                elif price >= bb_up * 0.98: score-=1; reasons.append("밴드 상단")
                
                if stoch < 20: score+=0.5; reasons.append("스토캐스틱 바닥")
                elif stoch > 80: score-=0.5

                if score >= 1.5: op = "🔥 강력 매수"
                elif score >= 0.5: op = "매수 우위"
                elif score <= -1.5: op = "❄️ 강력 매도"
                elif score <= -0.5: op = "매도 우위"
                else: op = "HOLD (관망)"
                
                p_str = f"{price:,.0f} 원" if code.endswith((".KS", ".KQ")) else f"{price:,.2f} $"
                
                analysis_data.append({
                    "종목명": name, # [요청반영] 종목명 분리
                    "코드": code,   # [요청반영] 코드 분리
                    "현재가": p_str,
                    "종합 의견": op,
                    "핵심 근거": ", ".join(reasons) if reasons else "-",
                    "RSI": f"{rsi:.0f}",
                    "점수": score
                })
            except:
                continue
            progress_bar.progress((i + 1) / total_rows)

        # 2단계: 표 출력 및 하단 설명
        if analysis_data:
            df = pd.DataFrame(analysis_data).sort_values(by='점수', ascending=False)
            st.subheader("📋 AI 투자 진단 리포트 (전체 요약)")
            
            # [요청반영] 종목명과 코드를 분리해서 표시
            st.dataframe(
                df[['종목명', '코드', '현재가', '종합 의견', '핵심 근거', 'RSI']], 
                use_container_width=True, 
                hide_index=True
            )
            
            # [요청반영] RSI 설명을 표 바로 아래로 이동
            with
