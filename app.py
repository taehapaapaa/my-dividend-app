import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 다크 핀테크 CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Dividend Pro Dashboard", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    .reportview-container { background-color: #0d1117; color: #e6edf3; }
    .metric-card { background: linear-gradient(135deg, #161b22 0%, #1f242d 100%); border: 1px solid #30363d; border-radius: 14px; padding: 18px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); }
    .metric-title { color: #8b949e; font-size: 0.85rem; font-weight: 500; margin-bottom: 6px; }
    .metric-value-green { color: #2ea043; font-size: 1.5rem; font-weight: 700; }
    .metric-value-cyan { color: #58a6ff; font-size: 1.5rem; font-weight: 700; }
    .metric-value-white { color: #ffffff; font-size: 1.5rem; font-weight: 700; }
    .alert-card { background-color: rgba(248, 81, 73, 0.1); border: 1px solid #f85149; border-radius: 10px; padding: 12px; margin-bottom: 15px; color: #ff7b72; font-weight: 600; }
    .stProgress > div > div > div > div { background-color: #2ea043; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 실시간 데이터 수집 (빈칸 방어 적용)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_live_data(tickers):
    data = {}
    try: data['USDKRW'] = round(yf.Ticker("USDKRW=X").fast_info['last_price'], 2)
    except: data['USDKRW'] = 1350.00 
    
    for t in tickers:
        if pd.isna(t) or str(t).strip() == "":
            continue
            
        ticker_obj = yf.Ticker(str(t).strip())
        
        try: price = ticker_obj.fast_info['last_price']
        except: price = 0.0
        
        try: 
            div_yield = ticker_obj.info.get('dividendYield') or ticker_obj.info.get('trailingAnnualDividendYield', 0.0)
            div_yield_pct = round(div_yield * 100, 2) if div_yield else 0.0
        except: div_yield_pct = 0.0
        
        try:
            ex_date_ts = ticker_obj.info.get('exDividendDate')
            if ex_date_ts:
                ex_date_str = datetime.fromtimestamp(ex_date_ts).strftime('%Y-%m-%d')
            else:
                ex_date_str = "-"
        except: ex_date_str = "-"
        
        data[str(t).strip()] = {'price': price, 'yield': div_yield_pct, 'ex_date': ex_date_str}
    return data

# -----------------------------------------------------------------------------
# 3. 데이터 초기화 (저장소 이름 v3로 변경하여 메모리 충돌 해결)
# -----------------------------------------------------------------------------
if 'portfolio_v3' not in st.session_state:
    st.session_state['portfolio_v3'] = pd.DataFrame([
        {"계좌": "내 계좌", "증권사": "카카오페이", "종목코드": "SCHD", "보유수량": 15.0, "평균매수가(USD)": 78.5, "매일모으기(KRW)": 10000, "배당주기": "분기(3,6,9,12월)"},
        {"계좌": "내 계좌", "증권사": "삼성증권", "종목코드": "SCHD", "보유수량": 30.5, "평균매수가(USD)": 80.2, "매일모으기(KRW)": 0, "배당주기": "분기(3,6,9,12월)"},
        {"계좌": "내 계좌", "증권사": "카카오페이", "종목코드": "JEPI", "보유수량": 30.0, "평균매수가(USD)": 56.2, "매일모으기(KRW)": 15000, "배당주기": "월배당"},
        {"계좌": "아내 계좌", "증권사": "토스증권", "종목코드": "JEPQ", "보유수량": 25.0, "평균매수가(USD)": 54.0, "매일모으기(KRW)": 10000, "배당주기": "월배당"},
        {"계좌": "아내 계좌", "증권사": "카카오페이", "종목코드": "O", "보유수량": 20.0, "평균매수가(USD)": 55.0, "매일모으기(KRW)": 10000, "배당주기": "월배당"},
    ])
    st.session_state['goal_1'] = 500000
    st.session_state['goal_final'] = 3000000

raw_df = st.session_state['portfolio_v3'].copy()
live_data = get_live_data(list(raw_df['종목코드'].unique()))
live_rate = live_data['USDKRW']

# -----------------------------------------------------------------------------
# 4. 헤더 및 배당락일 알림
# -----------------------------------------------------------------------------
col_h1, col_h2 = st.columns([2, 1])
with col_h1: st.markdown("### 📈 실시간 배당주 포트폴리오 대시보드")
with col_h2: st.markdown(f"<div style='text-align: right; color: #58a6ff; font-weight: 600;'>● LIVE 환율: {live_rate:,.2f} 원</div>", unsafe_allow_html=True)

upcoming_ex_dates = []
for t in raw_df['종목코드'].dropna().unique():
    if str(t).strip() == "": continue
    d = live_data.get(str(t).strip(), {}).get('ex_date', '-')
    if d != '-' and d >= datetime.now().strftime('%Y-%m-%d'):
        upcoming_ex_dates.append(f"{t} ({d})")

if upcoming_ex_dates:
    alert_text = " | ".join(upcoming_ex_dates)
    st.markdown(f"<div class='alert-card'>🔔 다가오는 배당락일: {alert_text}</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 탭 구성
# -----------------------------------------------------------------------------
tab_dashboard, tab_settings = st.tabs(["📊 통합 대시보드", "⚙️ 포트폴리오 수정"])

with tab_dashboard:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_account = st.selectbox("👤 계좌 필터", ["전체 합산"] + list(raw_df["계좌"].dropna().unique()))
    with col_f2:
        selected_broker = st.selectbox("🏛️ 증권사 필터", ["전체 증권사"] + list(raw_df["증권사"].dropna().unique()))
    
    filtered_df = raw_df.copy()
    if selected_account != "전체 합산": filtered_df = filtered_df[filtered_df["계좌"] == selected_account]
    if selected_broker != "전체 증권사": filtered_df = filtered_df[filtered_df["증권사"] == selected_broker]

    filtered_df['현재가(USD)'] = filtered_df['종목코드'].map(lambda x: live_data.get(str(x).strip(), {}).get('price', 0) if pd.notna(x) else 0)
    filtered_df['실시간배당률(%)'] = filtered_df['종목코드'].map(lambda x: live_data.get(str(x).strip(), {}).get('yield', 0) if pd.notna(x) else 0)
    filtered_df['배당락일'] = filtered_df['종목코드'].map(lambda x: live_data.get(str(x).strip(), {}).get('ex_date', '-') if pd.notna(x) else '-')
    
    filtered_df['평가금액(USD)'] = pd.to_numeric(filtered_df['보유수량'], errors='coerce').fillna(0) * filtered_df['현재가(USD)']
    
    avg_price = pd.to_numeric(filtered_df['평균매수가(USD)'], errors='coerce').fillna(1)
    avg_price = avg_price.replace(0, 1) 
    filtered_df['수익률(%)'] = ((filtered_df['현재가(USD)'] - avg_price) / avg_price) * 100
    
    filtered_df['연간세전배당(USD)'] = filtered_df['평가금액(USD)'] * (pd.to_numeric(filtered_df['실시간배당률(%)'], errors='coerce').fillna(0) / 100.0)
    filtered_df['연간세후배당(USD)'] = filtered_df['연간세전배당(USD)'] * (1 - 0.154)

    total_assets_krw = filtered_df['평가금액(USD)'].sum() * live_rate
    total_monthly_div_krw = (filtered_df['연간세후배당(USD)'].sum() * live_rate) / 12.0
    
    # 🌟 이 부분이 문제없이 작동하도록 메모리 충돌을 해결했습니다 🌟
    total_daily_dca_krw = pd.to_numeric(filtered_df['매일모으기(KRW)'], errors='coerce').fillna(0).sum()
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="metric-card"><div class="metric-title">실수령 월 평균 배당금 (세후)</div><div class="metric-value-green">약 {int(total_monthly_div_krw):,} 원</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-card"><div class="metric-title">총 포트폴리오 평가 자산</div><div class="metric-value-cyan">{int(total_assets_krw):,} 원</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-card"><div class="metric-title">일일 자동 매수 설정액</div><div class="metric-value-white">{int(total_daily_dca_krw):,} 원</div></div>""", unsafe_allow_html=True)

    st.markdown("#### 📅 1월~12월 예상 배당 현금흐름 (세후 KRW)")
    month_labels = [f"{m}월" for m in range(1, 13)]
    monthly_data = {m: 0.0 for m in month_labels}
    
    for idx, row in filtered_df.iterrows():
        krw_annual = row['연간세후배당(USD)'] * live_rate
        cycle = str(row['배당주기'])
        
        if '월배당' in cycle:
            for m in month_labels:
                monthly_data[m] += krw_annual / 12.0
        elif '분기' in cycle:
            for m in ["3월", "6월", "9월", "12월"]:
                monthly_data[m] += krw_annual / 4.0
        else:
            monthly_data["12월"] += krw_annual
            
    df_monthly_chart = pd.DataFrame(list(monthly_data.items()), columns=['Month', '예상 배당금(원)']).set_index('Month')
    st.bar_chart(df_monthly_chart, color="#2ea043")

    st.subheader("📑 실시간 보유 내역")
    display_df = filtered_df[['계좌', '증권사', '종목코드', '보유수량', '평균매수가(USD)', '현재가(USD)', '수익률(%)', '실시간배당률(%)', '배당락일', '매일모으기(KRW)']].copy()
    st.dataframe(display_df.style.format({'현재가(USD)': '{:.2f}', '수익률(%)': '{:+.2f}%', '실시간배당률(%)': '{:.2f}%', '매일모으기(KRW)': '{:,.0f}'}), use_container_width=True, hide_index=True)

with tab_settings:
    st.info("💡 종목을 추가하실 때는 빈칸(행)을 먼저 만들지 마시고, 데이터가 있는 상태에서 바로 입력해 주시면 오류를 방지할 수 있습니다!")
    
    c1, c2 = st.columns(2)
    with c1: new_g1 = st.number_input("1차 목표 월 배당금", value=st.session_state['goal_1'], step=50000)
    with c2: new_gfinal = st.number_input("최종 목표 월 배당금", value=st.session_state['goal_final'], step=100000)
    
    edited_df = st.data_editor(st.session_state['portfolio_v3'], num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 데이터 저장 및 차트 반영하기", type="primary"):
        st.session_state['goal_1'] = new_g1
        st.session_state['goal_final'] = new_gfinal
        st.session_state['portfolio_v3'] = edited_df
        st.success("완료! 대시보드가 업데이트됩니다.")
        st.rerun()
