import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import numpy as np # 수학 연산용 라이브러리

# ==========================================================
# 🔧 한글 폰트 설정
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
st.markdown("### 4대 기술적 지표 & 🔮 몬테카를로 미래 예측")
st.success("증권사 HTS에는 없는 **'미래 시나리오 시뮬레이션'** 기능이 탑재되었습니다.")
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

# -----------------------------------------------------------
# [NEW] 🔮 몬테카를로 시뮬레이션 함수 (미래 예측)
# -----------------------------------------------------------
def run_monte_carlo(hist, days_forecast=60, simulations=100):
    # 1. 일일 수익률의 평균과 변동성(표준편차) 계산
    log_returns = np.log(1 + hist['Close'].pct_change())
    u = log_returns.mean()
    var = log_returns.var()
    drift = u - (0.5 * var)
    stdev = log_returns.std()
    
    # 2. 미래 예측을 위한 난수 생성 (닥터 스트레인지의 100가지 미래)
    # days_forecast일 뒤까지, simulations개의 시나리오를 만듦
    daily_returns = np.exp(drift + stdev * np.random.norm(0, 1, (days_forecast, simulations)))
    
    # 3. 현재 가격에서 시작
    last_price = hist['Close'].iloc[-1]
    price_list = np.zeros_like(daily_returns)
    price_list[0] = last_price
    
    # 4. 시뮬레이션 실행 (복리 계산)
    for t in range(1, days_forecast):
        price_list[t] = price_list[t - 1] * daily_returns[t]
        
    return price_list

# 5. 실행 로직
if st.sidebar.button("🚀 AI 시장 진단 시작"):
    st.session_state['analyzed'] = True
    st.session_state['codes'] = [line.strip() for line in paste_area.split('\n') if line.strip()]

if st.session_state.get('analyzed'):
    with st.spinner('미래 시나리오(Monte Carlo) 시뮬레이션 중...'):
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
                hist = ticker.history(period="1y") # 몬테카를로를 위해 1년치 데이터 확보
                if hist.empty: continue
                
                name = stock_names.get(code, code)
                if name == code:
                    try: name = ticker.info.get('longName', code)
                    except: pass
                
                chart_data_dict[code] = {'hist': hist, 'name': name}

                # 최신 데이터만 사용
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
                    "종목명": name,
                    "코드": code,
                    "현재가": p_str,
                    "종합 의견": op,
                    "핵심 근거": ", ".join(reasons) if reasons else "-",
                    "RSI": f"{rsi:.0f}",
                    "점수": score
                })
            except:
                continue
            progress_bar.progress((i + 1) / total_rows)

        # 2단계: 표 및 설명 출력
        if analysis_data:
            df = pd.DataFrame(analysis_data).sort_values(by='점수', ascending=False)
            st.subheader("📋 AI 투자 진단 리포트")
            
            st.dataframe(
                df[['종목명', '코드', '현재가', '종합 의견', '핵심 근거', 'RSI']], 
                use_container_width=True, 
                hide_index=True
            )
            
            with st.expander("ℹ️ RSI 및 4대 지표 보는 법", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.info("**🌡️ RSI**\n30이하: 매수\n70이상: 매도");
                with c2: st.warning("**b 볼린저**\n하단: 쌈\n상단: 비쌈");
                with c3: st.success("**🌊 MACD**\n상승추세 확인\n골든크로스 매수");
                with c4: st.error("**⚡ 스토캐스틱**\n20바닥\n80과열");
            
            # 3단계: 상세 차트 + 몬테카를로
            st.markdown("---")
            st.subheader("📈 종목별 상세 차트 & 미래 시뮬레이션")
            
            select_options = [f"{row['종목명']} ({row['코드']})" for index, row in df.iterrows()]
            selected_option = st.selectbox("분석할 종목 선택:", select_options)
            
            if selected_option:
                selected_code = selected_option.split('(')[-1].replace(')', '')
                stock_info = chart_data_dict[selected_code]
                data = stock_info['hist']
                
                st.info(f"Checking: **{stock_info['name']}** 의 4대 지표 및 미래 예측 시나리오입니다.")
                
                # 지표 재계산
                data['RSI'] = get_rsi(data)
                data['MACD'], data['Signal'] = get_macd(data)
                data['Upper'], data['MA'], data['Lower'] = get_bollinger(data)
                data['Stoch'] = get_stochastic(data)
                
                # -------------------------------------------------------
                # [그래프] 4대 지표 + 몬테카를로 (총 5단)
                # -------------------------------------------------------
                fig, axes = plt.subplots(5, 1, figsize=(12, 20)) # 높이를 좀 더 키움
                
                # 1. RSI (맨 위)
                axes[0].set_title("1. RSI (핵심)")
                axes[0].plot(data.index, data['RSI'], color='purple')
                axes[0].axhline(70, color='red', linestyle='--')
                axes[0].axhline(30, color='blue', linestyle='--')
                axes[0].fill_between(data.index, data['RSI'], 70, where=(data['RSI']>=70), color='red', alpha=0.3)
                axes[0].fill_between(data.index, data['RSI'], 30, where=(data['RSI']<=30), color='blue', alpha=0.3)
                axes[0].set_ylim(0, 100)

                # 2. Bollinger
                axes[1].set_title("2. Bollinger Bands")
                axes[1].plot(data.index, data['Close'], color='black', label='Price')
                axes[1].plot(data.index, data['Upper'], linestyle='--', color='red', alpha=0.5)
                axes[1].plot(data.index, data['Lower'], linestyle='--', color='blue', alpha=0.5)
                axes[1].fill_between(data.index, data['Upper'], data['Lower'], color='gray', alpha=0.1)
                
                # 3. MACD
                axes[2].set_title("3. MACD")
                axes[2].plot(data.index, data['MACD'], color='red')
                axes[2].plot(data.index, data['Signal'], color='blue')
                axes[2].bar(data.index, data['MACD']-data['Signal'], color='gray', alpha=0.3)
                axes[2].axhline(0, color='black', linestyle='--')

                # 4. Stochastic
                axes[3].set_title("4. Stochastic")
                axes[3].plot(data.index, data['Stoch'], color='green')
                axes[3].axhline(80, color='red', linestyle='--')
                axes[3].axhline(20, color='blue', linestyle='--')
                axes[3].set_ylim(0, 100)
                
                # -------------------------------------------------------
                # 5. [NEW] 🔮 몬테카를로 미래 시뮬레이션
                # -------------------------------------------------------
                axes[4].set_title("5. 🔮 AI 몬테카를로 시뮬레이션 (향후 60일 예측)")
                
                # 시뮬레이션 실행 (100가지 시나리오)
                sim_data = run_monte_carlo(data, days_forecast=60, simulations=50)
                
                # 결과 그리기
                last_close = data['Close'].iloc[-1]
                
                # 50개의 흐릿한 선 그리기 (가능한 미래들)
                axes[4].plot(sim_data, color='gray', alpha=0.1)
                
                # 평균 예측선 (굵은 파란선)
                mean_path = sim_data.mean(axis=1)
                axes[4].plot(mean_path, color='blue', linewidth=2, label='평균 예측 경로')
                
                # 시작점 표시
                axes[4].axhline(last_close, color='black', linestyle='--', label='현재 주가')
                
                # 상승/하락 확률 계산
                final_prices = sim_data[-1] # 60일 뒤 가격들
                up_chance = np.sum(final_prices > last_close) / len(final_prices) * 100
                
                axes[4].legend(loc='upper left')
                
                # 확률 텍스트 표시
                st.pyplot(fig)
                
                # 몬테카를로 결과 해석 텍스트
                st.success(f"""
                **🔮 AI 미래 예측 결과 ({stock_info['name']})**
                과거의 변동성을 기반으로 100번의 모의투자를 진행했을 때:
                * **60일 뒤 주가가 상승할 확률:** **{up_chance:.1f}%**
                * **평균 예상 주가:** {mean_path[-1]:,.0f} (현재가 대비 {((mean_path[-1]-last_close)/last_close)*100:.1f}%)
                
                (※ 이는 통계적 확률이며, 실제 미래를 보장하지 않습니다.)
                """)

        else:
            st.warning("분석 가능한 종목이 없습니다.")
