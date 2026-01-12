import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# ==========================================================
# 🔧 [핵심] 한글 폰트 강제 설정 (도구 없이 직접 해결)
# ==========================================================
def setup_korean_font():
    # 폰트 파일이 없으면 구글에서 받아옴 (나눔고딕)
    font_path = "NanumGothic.ttf"
    if not os.path.exists(font_path):
        import requests
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        response = requests.get(url)
        with open(font_path, "wb") as f:
            f.write(response.content)
    
    # 폰트 등록
    fm.fontManager.addfont(font_path)
    plt.rc('font', family='NanumGothic')
    plt.rc('axes', unicode_minus=False) # 마이너스 기호 깨짐 방지

# 분석 시작 전에 폰트부터 설정
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
    with st.spinner('데이터 분석 및 한글 폰트 설정 중...'):
        codes = st.session_state['codes']
        if not codes:
            st.warning("입력된 코드가 없습니다.")
            st.stop()

        analysis_data = []
        chart_data_dict = {}
        
        progress_bar = st.progress(0)
        total_rows = len(codes)

        for i, code in enumerate(codes):
            try:
                # [수정됨] 들여쓰기 오류가 없도록 정렬했습니다.
                ticker = yf.Ticker(code)
                hist = ticker.history(period="6mo")
                if hist.empty: continue
                
                name = stock_names.get(code, code)
                if name == code:
                    try: name = ticker.info.get('longName', code)
                    except: pass
                
                chart_data_dict[f"{name} ({code})"] = {'hist': hist, 'code': code}

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
                    "종목명": f"{name} ({code})",
                    "현재가": p_str,
                    "종합 의견": op,
                    "핵심 근거": ", ".join(reasons) if reasons else "-",
                    "RSI": f"{rsi:.0f}",
                    "점수": score
                })
            except Exception as e:
                # 에러가 나면 그냥 건너뜀
                continue
            progress_bar.progress((i + 1) / total_rows)

        # 결과 출력
        if analysis_data:
            df = pd.DataFrame(analysis_data).sort_values(by='점수', ascending=False)
            st.subheader("📋 AI 투자 진단 리포트 (전체 요약)")
            st.dataframe(df[['종목명', '현재가', '종합 의견', '핵심 근거', 'RSI']], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("📈 종목별 상세 차트 분석")
            
            selected_stock = st.selectbox("분석하고 싶은 종목을 선택하세요:", df['종목명'].tolist())
            
            if selected_stock:
                stock_info = chart_data_dict[selected_stock]
                data = stock_info['hist']
                
                st.info(f"Checking: **{selected_stock}** 의 4대 지표 상세 그래프입니다.")
                
                # 그래프용 데이터 재계산
                data['RSI'] = get_rsi(data)
                data['MACD'], data['Signal'] = get_macd(data)
                data['Upper'], data['MA'], data['Lower'] = get_bollinger(data)
                data['Stoch'] = get_stochastic(data)
                
                # 그래프 그리기 (4단)
                fig, axes = plt.subplots(4, 1, figsize=(12, 16), sharex=True)
                
                axes[0].set_title("Price & Bollinger Bands")
                axes[0].plot(data.index, data['Close'], label='Price', color='black')
                axes[0].plot(data.index, data['Upper'], linestyle='--', color='red', alpha=0.5)
                axes[0].plot(data.index, data['Lower'], linestyle='--', color='blue', alpha=0.5)
                axes[0].fill_between(data.index, data['Upper'], data['Lower'], color='gray', alpha=0.1)
                
                axes[1].set_title("MACD")
                axes[1].plot(data.index, data['MACD'], color='red')
                axes[1].plot(data.index, data['Signal'], color='blue')
                axes[1].bar(data.index, data['MACD']-data['Signal'], color='gray', alpha=0.3)
                axes[1].axhline(0, color='black', linestyle='--')

                axes[2].set_title("RSI")
                axes[2].plot(data.index, data['RSI'], color='purple')
                axes[2].axhline(70, color='red', linestyle='--')
                axes[2].axhline(30, color='blue', linestyle='--')
                axes[2].set_ylim(0, 100)

                axes[3].set_title("Stochastic")
                axes[3].plot(data.index, data['Stoch'], color='green')
                axes[3].axhline(80, color='red', linestyle='--')
                axes[3].axhline(20, color='blue', linestyle='--')
                axes[3].set_ylim(0, 100)
                
                st.pyplot(fig)
        else:
            st.warning("분석 가능한 종목이 없습니다.")
