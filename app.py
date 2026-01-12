import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import numpy as np

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

# 1. 페이지 기본 설정
st.set_page_config(page_title="디지털강남서원 플랫폼", layout="wide")

# ==========================================================
# 📌 사이드바 메뉴 구성
# ==========================================================
st.sidebar.title("🗂️ 메뉴 선택")
menu = st.sidebar.radio(
    "이동할 페이지를 선택하세요:",
    ["📈 AI 시장 분석기", "✨ MMI (나만의 지표 만들기)"]
)
st.sidebar.markdown("---")

# 종목 이름 사전
stock_names = {
    "005930.KS": "삼성전자", "000660.KS": "SK하이닉스", "005380.KS": "현대차",
    "005490.KS": "POSCO홀딩스", "035420.KS": "NAVER", "035720.KS": "카카오",
    "105560.KS": "KB금융", "086520.KQ": "에코프로", "AAPL": "애플", 
    "TSLA": "테슬라", "NVDA": "엔비디아", "MSFT": "마이크로소프트", 
    "QQQ": "나스닥100", "SPY": "S&P500"
}

# ==========================================================
# 🅰️ 첫 번째 메뉴: AI 시장 분석기
# ==========================================================
if menu == "📈 AI 시장 분석기":
    st.title("📡 디지털강남서원 AI 시장 정밀 분석기")
    st.markdown("### 3대 기술적 지표 & 🔮 몬테카를로 미래 예측")
    
    # -----------------------------------------------------------
    # [수정된 부분] 문구 변경 및 MMI 안내 추가
    # -----------------------------------------------------------
    st.success("**핵심 3대 지표**와 **미래 시뮬레이션**에 집중합니다.")
    st.info("💡 **당신 자신의 아이디어로 인덱스를 만들어 드립니다.** (좌측 상단 '✨ MMI' 메뉴 선택)")
    # -----------------------------------------------------------
    
    st.markdown("---")

    # --- 분석기 사이드바 ---
    st.sidebar.header("🔍 종목 분석 요청")
    st.sidebar.info("입력 예시: `005930.KS` (삼성전자), `NVDA` (엔비디아)")
    
    example_text = """005930.KS\n000660.KS\nAAPL\nTSLA"""
    paste_area = st.sidebar.text_area("목록 붙여넣기", example_text, height=200)

    # --- 함수 정의 ---
    def get_rsi(data, window=14):
        delta = data['Close'].diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

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

    def run_monte_carlo(hist, days_forecast=60, simulations=100):
        log_returns = np.log(1 + hist['Close'].pct_change())
        u = log_returns.mean()
        var = log_returns.var()
        drift = u - (0.5 * var)
        stdev = log_returns.std()
        # 정규분포 함수 사용 (에러 수정됨)
        daily_returns = np.exp(drift + stdev * np.random.normal(0, 1, (days_forecast, simulations)))
        
        last_price = hist['Close'].iloc[-1]
        price_list = np.zeros_like(daily_returns)
        price_list[0] = last_price
        
        for t in range(1, days_forecast):
            price_list[t] = price_list[t - 1] * daily_returns[t]
        return price_list

    # --- 실행 로직 ---
    if st.sidebar.button("🚀 AI 시장 진단 시작"):
        st.session_state['analyzed'] = True
        st.session_state['codes'] = [line.strip() for line in paste_area.split('\n') if line.strip()]

    if st.session_state.get('analyzed'):
        with st.spinner('데이터 분석 중...'):
            codes = st.session_state['codes']
            if not codes:
                st.warning("코드를 입력해주세요.")
                st.stop()

            analysis_data = []
            chart_data_dict = {}
            progress_bar = st.progress(0)
            
            for i, code in enumerate(codes):
                try:
                    ticker = yf.Ticker(code)
                    hist = ticker.history(period="1y")
                    if hist.empty: continue
                    
                    name = stock_names.get(code, code)
                    if name == code:
                        try: name = ticker.info.get('longName', code)
                        except: pass
                    
                    chart_data_dict[code] = {'hist': hist, 'name': name}
                    price = hist['Close'].iloc[-1]
                    rsi = get_rsi(hist).iloc[-1]
                    up, mid, low = get_bollinger(hist)
                    stoch = get_stochastic(hist).iloc[-1]

                    score = 0
                    reasons = []
                    if rsi < 30: score+=1; reasons.append("RSI 과매도")
                    elif rsi > 70: score-=1; reasons.append("RSI 과열")
                    if price <= low.iloc[-1] * 1.02: score+=1; reasons.append("밴드 하단")
                    elif price >= up.iloc[-1] * 0.98: score-=1; reasons.append("밴드 상단")
                    if stoch < 20: score+=0.5; reasons.append("스토캐스틱 바닥")
                    elif stoch > 80: score-=0.5

                    if score >= 1.5: op = "🔥 강력 매수"
                    elif score >= 0.5: op = "매수 우위"
                    elif score <= -1.5: op = "❄️ 강력 매도"
                    elif score <= -0.5: op = "매도 우위"
                    else: op = "HOLD"
                    
                    p_str = f"{price:,.0f} 원" if code.endswith((".KS", ".KQ")) else f"{price:,.2f} $"
                    analysis_data.append({
                        "종목명": name, "코드": code, "현재가": p_str,
                        "종합 의견": op, "핵심 근거": ", ".join(reasons) if reasons else "-",
                        "RSI": f"{rsi:.0f}", "점수": score
                    })
                except: continue
                progress_bar.progress((i + 1) / len(codes))

            if analysis_data:
                df = pd.DataFrame(analysis_data).sort_values(by='점수', ascending=False)
                st.subheader("📋 AI 투자 진단 리포트")
                st.dataframe(df[['종목명', '코드', '현재가', '종합 의견', '핵심 근거', 'RSI']], use_container_width=True, hide_index=True)
                
                with st.expander("ℹ️ 지표 해설", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1: st.info("RSI: 30이하 매수 / 70이상 매도")
                    with c2: st.warning("볼린저: 하단 매수 / 상단 매도")
                    with c3: st.error("스토캐스틱: 20이하 매수 / 80이상 매도")

                st.markdown("---")
                st.subheader("📈 종목별 상세 차트 & 미래 시뮬레이션")
                select_options = [f"{row['종목명']} ({row['코드']})" for index, row in df.iterrows()]
                selected_option = st.selectbox("종목 선택:", select_options)
                
                if selected_option:
                    sel_code = selected_option.split('(')[-1].replace(')', '')
                    stock_info = chart_data_dict[sel_code]
                    data = stock_info['hist']
                    
                    data['RSI'] = get_rsi(data)
                    data['Upper'], _, data['Lower'] = get_bollinger(data)
                    data['Stoch'] = get_stochastic(data)
                    
                    fig, axes = plt.subplots(4, 1, figsize=(12, 16))
                    
                    axes[0].set_title("1. RSI")
                    axes[0].plot(data.index, data['RSI'], color='purple')
                    axes[0].axhline(70, color='red', ls='--'); axes[0].axhline(30, color='blue', ls='--')
                    
                    axes[1].set_title("2. Bollinger Bands")
                    axes[1].plot(data.index, data['Close'], 'k'); axes[1].plot(data.index, data['Upper'], 'r--'); axes[1].plot(data.index, data['Lower'], 'b--')
                    
                    axes[2].set_title("3. Stochastic")
                    axes[2].plot(data.index, data['Stoch'], 'g'); axes[2].axhline(80, color='red', ls='--'); axes[2].axhline(20, color='blue', ls='--')
                    
                    axes[3].set_title("4. 🔮 몬테카를로 시뮬레이션 (60일 예측)")
                    sim_data = run_monte_carlo(data, 60, 50)
                    last = data['Close'].iloc[-1]
                    axes[3].plot(sim_data, color='gray', alpha=0.1)
                    axes[3].plot(sim_data.mean(axis=1), 'b', lw=2)
                    axes[3].axhline(last, color='black', ls='--')
                    
                    up_prob = np.sum(sim_data[-1] > last) / 50 * 100
                    st.pyplot(fig)
                    st.success(f"**{stock_info['name']}** 60일 후 상승 확률: **{up_prob:.1f}%**")

# ==========================================================
# 🅱️ 두 번째 메뉴: MMI (나만의 지표 만들기)
# ==========================================================
elif menu == "✨ MMI (나만의 지표 만들기)":
    st.title("✨ MMI (Make My Index)")
    st.markdown("### 당신만의 '비밀 투자 공식'을 현실로 만들어 드립니다.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.info("""
        **MMI 서비스란?**
        
        시중에 있는 평범한 지표(RSI, MACD)로는 만족하지 못하시나요?
        고객님이 생각하시는 **독창적인 매매 논리**를 알려주세요.
        
        디지털강남서원의 금융 공학 팀이
        **세상에 하나뿐인 알고리즘**으로 코딩해 드립니다.
        """)
    
    with col2:
        st.warning("""
        **진행 절차**
        1. 아래 양식에 생각하시는 지표의 논리를 적어주세요.
        2. [지표 제작 신청] 버튼을 누릅니다.
        3. 전문가가 검토 후 상담 연락을 드립니다.
        4. 완성된 코드를 앱에 탑재해 드립니다.
        """)
        
    st.markdown("---")
    
    st.subheader("📝 나만의 지표 설계도 작성")
    
    with st.form("mmi_form"):
        customer_name = st.text_input("성함 / 닉네임", placeholder="홍길동")
        contact_info = st.text_input("연락처 (이메일 또는 전화번호)", placeholder="email@example.com")
        
        st.markdown("#### 만들고 싶은 지표의 논리를 설명해 주세요.")
        user_logic = st.text_area("지표 설명", height=150, placeholder="예: 삼성전자가 3일 연속 오르고 외국인이 100억 이상 샀을 때 '매수' 신호를 주는 지표를 만들어주세요.")
        
        submitted = st.form_submit_button("📩 지표 제작 신청하기")
        
        if submitted:
            if user_logic and contact_info:
                st.success(f"✅ 접수되었습니다! {customer_name}님만의 지표를 분석하여 곧 연락드리겠습니다.")
                st.balloons()
            else:
                st.error("연락처와 지표 내용을 모두 입력해 주세요.")

    st.markdown("---")
    st.subheader("💡 MMI 작성 예시 (참고하세요)")
    
    with st.expander("예시 1: '강남서원 불기둥' 전략 보기", expanded=True):
        st.markdown("""
        **[고객 요청 내용]**
        > "저는 **거래량이 터지면서 가격이 급등할 때**만 사고 싶습니다.
        > 아래 조건 3개가 모두 맞으면 **'강력 매수'**라고 뜨게 해주세요."
        
        **[구체적인 조건식]**
        1. **오늘 거래량**이 어제 거래량의 **300% (3배)** 이상일 것.
        2. **오늘 주가**가 **5% 이상 상승** 마감할 것.
        3. RSI 지표는 아직 70을 넘지 않을 것 (너무 과열되지 않은 상태).
        
        ---
        **👉 이렇게 적어주시면, 저희가 '강남서원 불기둥'이라는 이름의 지표로 만들어 앱에 추가해 드립니다.**
        """)
