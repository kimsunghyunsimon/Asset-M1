import streamlit as st

# 1. 헤드라인 (굵고 크게 표현)
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 30px;'>
        Digital 강남서원
    </h1>
    """, unsafe_allow_html=True)

# 2. 두 개의 블록 레이아웃 구성
col1, col2 = st.columns(2)

# 첫 번째 블록: AI시장 분석기
with col1:
    st.info(
        "**📊 AI시장 분석기**\n\n"
        "주식시장의 핵심 3대 지표와 미래 시뮬레이션에 집중합니다."
    )

# 두 번째 블록: MMI
with col2:
    st.success(
        "**✨ MMI**\n\n"
        "당신 자신의 아이디어로 인덱스를 만들어 드립니다.\n"
        "(좌측 상단 '✨ MMI' 메뉴 선택)"
    )

# --- (이 아래에 기존 그래프나 데이터 로직이 이어지면 됩니다) ---
st.divider()
