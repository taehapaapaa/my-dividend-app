import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
import math

st.set_page_config(page_title="Dividend Pro Dashboard", page_icon="🚀", layout="wide")

# CSS (통합)
st.markdown("""
<style>
    .metric-card { background: linear-gradient(135deg, #161b22 0%, #1f242d 100%); border: 1px solid #30363d; border-radius: 14px; padding: 18px; margin-bottom: 12px; }
    .metric-value-green { color: #00E396; font-size: 1.5rem; font-weight: 700; }
    .stProgress > div > div > div > div { background-color: #00E396; }
</style>
""", unsafe_allow_html=True)

# 데이터 함수는 이전과 동일하게 유지
def format_krw(val): return f"{val/10000:.1f}만원".replace(".0만원", "만원") if val >= 10000 else f"{int(val):,}원"

@st.cache_data(ttl=3600)
def get_live_data(tickers):
    data = {}
    try: data['USDKRW'] = round(yf.Ticker("USDKRW=X").fast_info['last_price'], 2)
    except: data['USDKRW'] = 1350.00 
    for t in tickers:
        if pd.isna(t) or str(t).strip() == "": continue
        tkr = str(t).strip()
        ticker_obj = yf.Ticker(tkr)
        try: 
            price = ticker_obj.fast_info['last_price']
            div_yield = ticker_obj.info.get('dividendYield') or ticker_obj.info.get('trailingAnnualDividendYield', 0.0)
            ex_date_ts = ticker_obj.info.get('exDividendDate')
            ex_date_str = datetime.fromtimestamp(ex_date_ts).strftime('%Y-%m-%d') if ex_date_ts else "-"
            data[tkr] = {'price': price, 'yield': round(div_yield*100, 2) if div_yield else 0.0, 'ex_date': ex_date_str}
        except: data[tkr] = {'price': 0, 'yield': 0, 'ex_date': '-'}
    return data

# 데이터 영구 저장소
if 'portfolio_permanent' not in st.session_state:
    st.session_state['portfolio_permanent'] = pd.DataFrame([
        {"계좌": "내 계좌", "증권사": "카카오페이", "종목코드": "SCHD", "보유수량": 15.0, "평균매수가(USD)": 78.5, "매일모으기(KRW)": 10000, "배당주기": "분기(3,6,9,12월)"}
    ])
    st.session_state['goal_1'] = 500000
    st.session_state['goal_final'] = 3000000

raw_df = st.session_state['portfolio_permanent'].copy()
live_data = get_live_data(list(raw_df['종목코드'].unique()))
live_rate = live_data.get('USDKRW', 1350.0)

# -----------------------------------------------------------------------------
# 대시보드 로직
# -----------------------------------------------------------------------------
tab_dashboard, tab_settings = st.tabs(["📊 통합 대시보드", "⚙️ 포트폴리오 수정"])

with tab_dashboard:
    # 필터링 및 계산 생략 (이전 버전과 동일)
    # ... (데이터 계산 로직) ...
    
    # 🌟 목표 달성률 및 예상 기간 계산 🌟
    total_monthly_div_krw = 350000 # 예시값 (계산된 값으로 대체)
    
    st.markdown("### 🎯 목표 달성 진행률")
    c1, c2 = st.columns(2)
    # 1차 목표
    prog_1 = min(total_monthly_div_krw / st.session_state['goal_1'], 1.0)
    c1.markdown(f"**1차 목표({format_krw(st.session_state['goal_1'])})**")
    c1.progress(prog_1)
    
    # 최종 목표
    prog_final = min(total_monthly_div_krw / st.session_state['goal_final'], 1.0)
    c2.markdown(f"**최종 목표({format_krw(st.session_state['goal_final'])})**")
    c2.progress(prog_final)
    
    # 예상 달성일 계산 (단순화된 시뮬레이션)
    gap = st.session_state['goal_final'] - total_monthly_div_krw
    if gap > 0:
        months_left = math.ceil(gap / (total_monthly_div_krw * 0.05 + 50000)) # 예시 로직
        st.info(f"💡 현재 속도라면 최종 목표 달성까지 약 **{months_left}개월** 예상됩니다.")

    # ... (차트 및 상세 표 렌더링) ...

with tab_settings:
    # ... (드롭다운 설정) ...
