import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

# 1. 페이지 설정
st.set_page_config(page_title="AI 전략 백테스팅", layout="wide")
st.title("🧪 AI 투자 전략 검증기 (Back-testing)")
st.info("과거 데이터로 돌아가 **'RSI 30에 사고, 70에 파는 전략'**을 시뮬레이션합니다.")

# 2. 사이드바 설정
st.sidebar.header("⚙️ 시뮬레이션 설정")
ticker = st.sidebar.text_input("종목 코드 입력", value="005930.KS") # 기본 삼성전자
start_date = st.sidebar.date_input("시작일", pd.to_datetime("2020-01-01"))
initial_capital = st.sidebar.number_input("초기 투자금 (원)", value=10000000) # 1천만원

# RSI 전략 설정 (나중에 슬라이더로 조절 가능하게)
rsi_buy = 30
rsi_sell = 70

# 3. 데이터 가져오기 및 지표 계산 함수
def get_data(ticker, start):
    df = yf.download(ticker, start=start, progress=False)
    # 수정 종가 사용 (배당/액면분할 반영)
    if 'Adj Close' in df.columns:
        df['Price'] = df['Adj Close']
    else:
        df['Price'] = df['Close']
    
    # RSI 계산
    delta = df['Price'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# 4. 백테스팅 로직 (핵심 엔진)
def run_backtest(df):
    cash = initial_capital
    position = 0 # 보유 주식 수
    
    # 기록용 리스트
    history = []     # 매매 일지
    equity_curve = [] # 자산 변동 그래프용
    
    buy_price = 0 # 수익률 계산용

    for i in range(len(df)):
        date = df.index[i]
        price = df['Price'].iloc[i]
        rsi = df['RSI'].iloc[i]
        
        # 첫 14일은 RSI가 없으므로 패스
        if pd.isna(rsi):
            equity_curve.append(initial_capital)
            continue
            
        action = "HOLD"
        
        # --- 매매 로직 ---
        # 1. 매수 조건: 현금 보유 중이고 & RSI가 30 미만일 때
        if position == 0 and rsi < rsi_buy:
            position = cash // price # 전액 매수
            cash = cash - (position * price)
            buy_price = price
            action = "BUY"
            history.append({"날짜": date, "구분": "🔴 매수", "가격": price, "RSI": rsi, "수량": position})
            
        # 2. 매도 조건: 주식 보유 중이고 & RSI가 70 초과일 때
        elif position > 0 and rsi > rsi_sell:
            cash = cash + (position * price)
            return_rate = (price - buy_price) / buy_price * 100
            history.append({"날짜": date, "구분": "🔵 매도", "가격": price, "RSI": rsi, "수익률(%)": return_rate})
            position = 0 # 전량 매도
            action = "SELL"
            
        # 매일의 총 자산 가치 기록 (현금 + 주식평가액)
        total_value = cash + (position * price)
        equity_curve.append(total_value)
        
    df['Strategy_Value'] = equity_curve
    return df, pd.DataFrame(history)

# 5. 실행 버튼 및 결과 출력
if st.sidebar.button("🚀 시뮬레이션 시작"):
    with st.spinner('타임머신 가동 중...'):
        try:
            # 데이터 로드
            df = get_data(ticker, start_date)
            
            # 백테스팅 실행
            df_result, trade_log = run_backtest(df)
            
            # --- 결과 분석 ---
            final_value = df_result['Strategy_Value'].iloc[-1]
            buy_hold_value = (initial_capital / df_result['Price'].iloc[0]) * df_result['Price'].iloc[-1]
            
            total_return = ((final_value - initial_capital) / initial_capital) * 100
            buy_hold_return = ((buy_hold_value - initial_capital) / initial_capital) * 100
            
            # 1. 상단 요약 지표
            col1, col2, col3 = st.columns(3)
            col1.metric("최종 자산 (AI 매매)", f"{final_value:,.0f} 원", f"{total_return:.1f}%")
            col2.metric("존버했을 때 (Buy & Hold)", f"{buy_hold_value:,.0f} 원", f"{buy_hold_return:.1f}%")
            col3.metric("매매 횟수", f"{len(trade_log)} 회")
            
            # 2. 수익률 그래프 비교 (스트림릿 내장 차트 사용)
            st.subheader("📈 자산 증식 곡선 (AI vs 존버)")
            
            # 비교를 위해 데이터프레임 정리
            chart_data = pd.DataFrame({
                'AI 전략': df_result['Strategy_Value'],
                '그냥 보유(Buy&Hold)': (df_result['Price'] / df_result['Price'].iloc[0]) * initial_capital
            })
            st.line_chart(chart_data)
            
            # 3. 매매 일지 상세
            st.subheader("📝 AI 매매 기록")
            if not trade_log.empty:
                # 날짜 포맷 정리
                trade_log['날짜'] = trade_log['날짜'].dt.strftime('%Y-%m-%d')
                trade_log['가격'] = trade_log['가격'].apply(lambda x: f"{x:,.0f}원")
                trade_log['RSI'] = trade_log['RSI'].round(1)
                st.dataframe(trade_log, hide_index=True)
            else:
                st.warning("조건에 맞는 매매가 한 번도 발생하지 않았습니다. (기간을 늘리거나 RSI 기준을 조정해보세요)")

        except Exception as e:
            st.error(f"오류 발생: {e}")
            st.write("종목 코드가 정확한지 확인해주세요 (예: 005930.KS)")
