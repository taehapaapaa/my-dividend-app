import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
import math

# 테마 색상 설정
THEME_COLOR = "#2997ff"

st.set_page_config(page_title="Dividend Pro Dashboard", page_icon="🚀", layout="wide")

st.markdown(f"""
<style>
    .reportview-container {{ background-color: #0d1117; color: #e6edf3; }}
    .metric-card {{ background: linear-gradient(135deg, #161b22 0%, #1f242d 100%); border: 1px solid #30363d; border-radius: 14px; padding: 18px; margin-bottom: 12px; }}
    .metric-title {{ color: #8b949e; font-size: 0.85rem; font-weight: 500; margin-bottom: 6px; }}
    .metric-value-green {{ color: {THEME_COLOR}; font-size: 1.5rem; font-weight: 700; }}
    .stProgress > div > div > div > div {{ background-color: {THEME_COLOR}; }}
</style>
""", unsafe_allow_html=True)

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
            divs = ticker_obj.dividends
            recent_divs = divs[divs.index >= (pd.Timestamp.now() - pd.DateOffset(years=1))]
            div_yield_pct = round((recent_divs.sum() / price) * 100, 2) if price > 0 else 0.0
            ex_date_ts = ticker_obj.info.get('exDividendDate')
            ex_date_str = datetime.fromtimestamp(ex_date_ts).strftime('%Y-%m-%d') if ex_date_ts else "-"
            data[tkr] = {'price': price, 'yield': div_yield_pct, 'ex_date': ex_date_str}
        except: data[tkr] = {'price': 0, 'yield': 0, 'ex_date': '-'}
    return data

if 'portfolio_permanent' not in st.session_state:
    st.session_state['portfolio_permanent'] = pd.DataFrame([
        {"계좌": "내 계좌", "증권사": "카카오페이", "종목코드": "SCHD", "보유수량": 15.0, "평균매수가(USD)": 78.5, "매일모으기(KRW)": 10000, "배당주기": "분기(3,6,9,12월)"}
    ])
    st.session_state['goal_1'] = 500000
    st.session_state['goal_final'] = 3000000

raw_df = st.session_state['portfolio_permanent'].copy()
live_data = get_live_data(list(raw_df['종목코드'].unique()))
live_rate = live_data.get('USDKRW', 1350.0)

tab_dashboard, tab_settings = st.tabs(["📊 통합 대시보드", "⚙️ 포트폴리오 수정"])

with tab_dashboard:
    filtered_df = raw_df.copy()
    filtered_df['현재가(USD)'] = filtered_df['종목코드'].map(lambda x: live_data.get(str(x).strip(), {}).get('price', 0))
    filtered_df['연간세후배당(USD)'] = (filtered_df['보유수량'] * filtered_df['현재가(USD)']) * (filtered_df['종목코드'].map(lambda x: live_data.get(str(x).strip(), {}).get('yield', 0))/100) * (1 - 0.154)
    
    total_monthly_div_krw = (filtered_df['연간세후배당(USD)'].sum() * live_rate) / 12.0
    st.markdown(f"### 월 평균 배당금: {format_krw(total_monthly_div_krw)}")
    
    fig = px.bar(x=[f"{m}월" for m in range(1,13)], y=[total_monthly_div_krw]*12, marker_color=THEME_COLOR)
    st.plotly_chart(fig, use_container_width=True)

with tab_settings:
    edited_df = st.data_editor(st.session_state['portfolio_permanent'], num_rows="dynamic", use_container_width=True, hide_index=True,
        column_config={
            "계좌": st.column_config.SelectboxColumn("계좌", options=["내 계좌", "아내 계좌", "자녀 계좌", "공동 계좌", "기타"]),
            "증권사": st.column_config.SelectboxColumn("증권사", options=["카카오페이", "토스증권", "삼성증권", "키움증권", "미래에셋증권", "기타"]),
            "배당주기": st.column_config.SelectboxColumn("배당주기", options=["월배당", "분기(3,6,9,12월)", "분기(1,4,7,10월)", "분기(2,5,8,11월)", "연배당", "기타"])
        })
    if st.button("💾 데이터 저장"):
        st.session_state['portfolio_permanent'] = edited_df
        st.rerun()
