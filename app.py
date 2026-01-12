import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import numpy as np
import urllib.parse 

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
st.set_page_config(page_title="디지털강남서원 플랫폼", layout="wide")

# ==========================================================
# 📌 사이드바 메뉴
# ==========================================================
st.sidebar.title("🗂️ 메뉴 선택")
menu = st.sidebar.radio(
    "이동할 페이지를 선택하세요:",
    ["📈 AI 시장 분석기", "✨ MMI (나만의 지표 만들기)"]
)
st.sidebar.markdown("---")

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
    
    st.success("**핵심 3대 지표**와 **미래 시뮬레이션**에 집중합니다.")
    st.info("💡 **당신 자신의 아이디어로 인덱스를 만들어 드립니다.** (좌측 상단 '✨ MMI' 메뉴 선택)")
    st.markdown("---")

    st.sidebar.header("🔍 종목 분석 요청")
    st.sidebar.info("입력 예시: `005930.KS` (삼성전자), `NVDA` (엔비디아)")
    
    example_text = """005930.KS\n000660.KS\nAAPL\nTSLA"""
    paste_area = st.sidebar.text_area("목록 붙여넣기", example_text, height=200)

    # --- 함수들 ---
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
    
    # ----------------------------------------------------
    # 🚨 [중요] 여기에 선생님의 이메일을 입력하세요!
    # ----------------------------------------------------
    host_email = "kingkim.sim@gmail.com" 
    # ----------------------------------------------------
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.info("**🔒 철저한 보안/비공개**\n\n고객님이 작성하신 전략은 서버에 저장되지 않고,\n오직 호스트(개발자)의 **이메일로만 직송**됩니다.")
    with col2:
        st.warning("**🚀 진행 절차**\n\n1. 지표 논리 작성\n2. [신청서 작성 완료] 클릭\n3. [메일 전송하기] 버튼 클릭")
        
    st.markdown("---")
    st.subheader("📝 나만의 지표 설계도 작성")
    
    with st.form("mmi_form"):
        customer_name = st.text_input("성함 / 닉네임", placeholder="홍길동")
        contact_info = st.text_input("연락처 (이메일/전화번호)", placeholder="010-1234-5678")
        st.markdown("#### 만들고 싶은 지표의 논리를 설명해 주세요.")
        user_logic = st.text_area("지표 설명", height=150, placeholder="예: 삼성전자가 3일 연속 오르고 외국인이 100억 이상 샀을 때 '매수' 신호를 주는 지표")
        
        submitted = st.form_submit_button("✅ 신청서 작성 완료 (클릭)")

    if submitted:
        if user_logic and contact_info:
            subject = f"[MMI 신청] {customer_name}님의 지표 제작 요청"
            body = f"""
            [MMI 지표 제작 신청서]
            1. 신청자: {customer_name}
            2. 연락처: {contact_info}
            3. 지표 논리 설명:
            {user_logic}
            """
            
            encoded_subject = urllib.parse.quote(subject)
            encoded_body = urllib.parse.quote(body)
            mailto_link = f"mailto:{host_email}?subject={encoded_subject}&body={encoded_body}"
            
            st.success("작성이 완료되었습니다! 아래 초록색 버튼을 눌러 메일을 보내주세요.")
            
            # [수정 1] 오타 수정: '눌어서' 삭제
            st.markdown(f"""
            <a href="{mailto_link}" target="_blank" style="
                display: inline-block;
                background-color: #4CAF50;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                border-radius: 8px;
                font-weight: bold;
            ">📧 메일 전송하기 (최종 단계)</a>
            """, unsafe_allow_html=True)
            
            # [수정 2] 전송 실패 시 대비책 (내용 복사 기능)
            st.markdown("---")
            st.warning("⚠️ 혹시 위 버튼을 눌러도 반응이 없나요?")
            st.info("사용하시는 컴퓨터에 메일 프로그램(Outlook 등)이 없어서 그렇습니다.\n**아래 내용을 복사(Ctrl+C)해서, 평소 쓰시는 메일로 직접 보내주세요.**")
            st.text_area("신청서 내용 복사하기", value=body, height=200)
            st.caption(f"보내실 곳: {host_email}")
            
        else:
            st.error("모든 내용을 입력해 주세요.")

    st.markdown("---")
    st.subheader("💡 MMI 작성 예시 (참고하세요)")
    with st.expander("예시: '강남서원 불기둥' 전략 보기", expanded=True):
        st.markdown("""
        **[요청 내용]**
        > "거래량이 3배 터지고 주가가 5% 이상 오르면 '강력 매수' 신호를 주세요."
        """)
