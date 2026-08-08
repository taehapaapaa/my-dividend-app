import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
import math

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 다크 핀테크 CSS (일렉트릭 블루 테마 적용)
# -----------------------------------------------------------------------------
THEME_COLOR = "#2997ff" 

st.set_page_config(page_title="Dividend Pro Dashboard", page_icon="🚀", layout="wide")

st.markdown(f"""
<style>
    .reportview-container {{ background-color: #0d1117; color: #e6edf3; }}
    .metric-card {{ background: linear-gradient(135deg, #161b22 0%, #1f242d 100%); border: 1px solid #30363d; border-radius: 14px; padding: 18px; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); }}
    .metric-title {{ color: #8b949e; font-size: 0.85rem; font-weight: 500; margin-bottom: 6px; }}
    .metric-value-green {{ color: {THEME_COLOR}; font-size: 1.5rem; font-weight: 700; }}
    .metric-value-cyan {{ color: #58a6ff; font-size: 1.5rem; font-weight: 700; }}
    .metric-value-white {{ color: #ffffff; font-size: 1.5rem; font-weight: 700; }}
    .alert-card {{ background-color: rgba(41, 151, 255, 0.1); border: 1px solid {THEME_COLOR}; border-radius: 10px; padding: 12px; margin-bottom: 15px; color: {THEME_COLOR}; font-weight: 600; }}
    .stProgress > div > div > div > div {{ background-color: {THEME_COLOR}; }}
</style>
""", unsafe_allow_html=True)

def format_krw(val):
    if val >= 10000: return f"{val/10000:.1f}만원".replace(".0만원", "만원")
    return f"{int(val):,}원"

# -----------------------------------------------------------------------------
# 2. 실시간 데이터 수집 (스마트 롤링 배당률)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_live_data(tickers):
    data = {}
    try: data['USDKRW'] = round(yf.Ticker("USDKRW=X").fast_info['last_price'], 2)
    except: data['USDKRW'] = 1350.00 
    
    for t in tickers:
        if pd.isna(t) or str(t).strip() == "": continue
        tkr = str(t).strip()
        ticker_obj = yf.Ticker(tkr)
        
        try: price = ticker_obj.fast_info['last_price']
        except: price = 0.0
        
        try:
            divs = ticker_obj.dividends
            if not divs.empty and price > 0:
                tz = divs.index.tz
                one_year_ago = pd.Timestamp.now(tz=tz) - pd.DateOffset(years=1)
                recent_divs = divs[divs.index >= one_year_ago]
                ttm_div_sum = recent_divs.sum()
                div_yield_pct = round((ttm_div_sum / price) * 100, 2)
            else:
                fallback_yield = ticker_obj.info.get('trailingAnnualDividendYield', 0.0)
                div_yield_pct = round(fallback_yield * 100, 2) if fallback_yield else 0.0
        except: 
            div_yield_pct = 0.0
        
        try:
            ex_date_ts = ticker_obj.info.get('exDividendDate')
            if ex_date_ts: ex_date_str = datetime.fromtimestamp(ex_date_ts).strftime('%Y-%m-%d')
            else: ex_date_str = "-"
        except: ex_date_str = "-"
        
        data[tkr] = {'price': price, 'yield': div_yield_pct, 'ex_date': ex_date_str}
    return data

# -----------------------------------------------------------------------------
# 3. 데이터 영구 저장소 초기화 (v9 - 데이터 증발 방지)
# -----------------------------------------------------------------------------
if 'portfolio_v9' not in st.session_state:
    st.session_state['portfolio_v9'] = pd.DataFrame([
        {"계좌": "내 계좌", "증권사": "카카오페이", "종목코드": "SCHD", "보유수량": 15.0, "평균매수가(USD)": 78.5, "매일모으기(KRW)": 10000, "배당주기": "분기(3,6,9,12월)"},
        {"계좌": "내 계좌", "증권사": "삼성증권", "종목코드": "SCHD", "보유수량": 30.5, "평균매수가(USD)": 80.2, "매일모으기(KRW)": 0, "배당주기": "분기(3,6,9,12월)"},
        {"계좌": "내 계좌", "증권사": "카카오페이", "종목코드": "JEPI", "보유수량": 30.0, "평균매수가(USD)": 56.2, "매일모으기(KRW)": 15000, "배당주기": "월배당"},
    ])
    st.session_state['goal_1'] = 500000
    st.session_state['goal_final'] = 3000000

raw_df = st.session_state['portfolio_v9'].copy()
live_data = get_live_data(list(raw_df['종목코드'].unique()))
live_rate = live_data.get('USDKRW', 1350.0)

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
    with col_f1: selected_account = st.selectbox("👤 계좌 필터", ["전체 합산"] + list(raw_df["계좌"].dropna().unique()))
    with col_f2: selected_broker = st.selectbox("🏛️ 증권사 필터", ["전체 증권사"] + list(raw_df["증권사"].dropna().unique()))
    
    filtered_df = raw_df.copy()
    if selected_account != "전체 합산": filtered_df = filtered_df[filtered_df["계좌"] == selected_account]
    if selected_broker != "전체 증권사": filtered_df = filtered_df[filtered_df["증권사"] == selected_broker]

    filtered_df['현재가(USD)'] = filtered_df['종목코드'].map(lambda x: live_data.get(str(x).strip(), {}).get('price', 0) if pd.notna(x) else 0)
    filtered_df['실시간배당률(%)'] = filtered_df['종목코드'].map(lambda x: live_data.get(str(x).strip(), {}).get('yield', 0) if pd.notna(x) else 0)
    filtered_df['배당락일'] = filtered_df['종목코드'].map(lambda x: live_data.get(str(x).strip(), {}).get('ex_date', '-') if pd.notna(x) else '-')
    
    filtered_df['평가금액(USD)'] = pd.to_numeric(filtered_df['보유수량'], errors='coerce').fillna(0) * filtered_df['현재가(USD)']
    avg_price = pd.to_numeric(filtered_df['평균매수가(USD)'], errors='coerce').fillna(1).replace(0, 1) 
    filtered_df['수익률(%)'] = ((filtered_df['현재가(USD)'] - avg_price) / avg_price) * 100
    
    filtered_df['연간세전배당(USD)'] = filtered_df['평가금액(USD)'] * (filtered_df['실시간배당률(%)'] / 100.0)
    filtered_df['연간세후배당(USD)'] = filtered_df['연간세전배당(USD)'] * (1 - 0.154)

    total_assets_krw = filtered_df['평가금액(USD)'].sum() * live_rate
    total_monthly_div_krw = (filtered_df['연간세후배당(USD)'].sum() * live_rate) / 12.0
    total_daily_dca_krw = pd.to_numeric(filtered_df['매일모으기(KRW)'], errors='coerce').fillna(0).sum()
    
    st.markdown("---")
    
    # 상단 요약 카드
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="metric-card"><div class="metric-title">실수령 월 평균 배당금 (세후)</div><div class="metric-value-green">약 {format_krw(total_monthly_div_krw)}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-card"><div class="metric-title">총 포트폴리오 평가 자산</div><div class="metric-value-cyan">{format_krw(total_assets_krw)}</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-card"><div class="metric-title">일일 자동 매수 설정액</div><div class="metric-value-white">{format_krw(total_daily_dca_krw)}</div></div>""", unsafe_allow_html=True)

    # 목표 달성률 게이지 & 예상 기간 계산
    st.markdown("### 🎯 배당 자유 목표 달성률")
    gc1, gc2 = st.columns(2)
    
    goal_1 = st.session_state['goal_1']
    goal_final = st.session_state['goal_final']
    
    prog_1 = min(total_monthly_div_krw / goal_1, 1.0) if goal_1 > 0 else 0
    prog_final = min(total_monthly_div_krw / goal_final, 1.0) if goal_final > 0 else 0
    
    with gc1:
        st.markdown(f"**1차 목표 ({format_krw(goal_1)})** — {int(prog_1*100)}% 달성")
        st.progress(prog_1)
    with gc2:
        st.markdown(f"**최종 목표 ({format_krw(goal_final)})** — {int(prog_final*100)}% 달성")
        st.progress(prog_final)

    monthly_dca_monthly = total_daily_dca_krw * 30.0 
    if total_monthly_div_krw < goal_final:
        remaining_gap = goal_final - total_monthly_div_krw
        effective_monthly_add = monthly_dca_monthly * 0.005 
        if effective_monthly_add > 0:
            est_months = math.ceil(remaining_gap / max(effective_monthly_add, 10000))
            st.info(f"💡 현재 적립 속도({format_krw(monthly_dca_monthly)}/월) 및 배당 재투자를 감안할 때, 최종 목표 달성까지 약 **{est_months}개월** 소요될 것으로 예상됩니다.")

    st.markdown("---")

    # 월별 현금흐름 에메랄드/블루 차트
    st.markdown("#### 📅 1월~12월 예상 배당 현금흐름 (세후 KRW)")
    month_labels = [f"{m}월" for m in range(1, 13)]
    monthly_data = {m: 0.0 for m in month_labels}
    
    for idx, row in filtered_df.iterrows():
        krw_annual = row['연간세후배당(USD)'] * live_rate
        cycle = str(row['배당주기'])
        if '월배당' in cycle:
            for m in month_labels: monthly_data[m] += krw_annual / 12.0
        elif '분기' in cycle:
            for m in ["3월", "6월", "9월", "12월"]: monthly_data[m] += krw_annual / 4.0
        else:
            monthly_data["12월"] += krw_annual
            
    df_monthly_chart = pd.DataFrame(list(monthly_data.items()), columns=['Month', 'Amount'])
    df_monthly_chart['Text'] = df_monthly_chart['Amount'].apply(format_krw)
    
    fig = px.bar(df_monthly_chart, x='Month', y='Amount', text='Text')
    fig.update_traces(textposition='outside', marker_color=THEME_COLOR, textfont_size=12, textfont_color='#e6edf3')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#8b949e'), margin=dict(t=25, b=20, l=0, r=0), xaxis_title=None, yaxis_title=None, yaxis=dict(showticklabels=False, showgrid=False))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 종목별 배당 비중 파이 차트 & 상세 표
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("#### 🥧 종목별 연간 배당 기여도")
        div_df = filtered_df.groupby('종목코드').agg({'연간세후배당(USD)': 'sum'}).reset_index()
        div_df['금액(원)'] = div_df['연간세후배당(USD)'] * live_rate
        if not div_df.empty and div_df['금액(원)'].sum() > 0:
            fig_pie = px.pie(div_df, values='금액(원)', names='종목코드', hole=0.4)
            fig_pie.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e6edf3'), margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("데이터가 부족합니다.")
            
    with col_p2:
        st.markdown("#### 💰 종목별 상세 배당금 내역")
        table_df = filtered_df.groupby('종목코드').agg({'보유수량':'sum', '연간세후배당(USD)':'sum'}).reset_index()
        table_df['연간 세후배당금'] = (table_df['연간세후배당(USD)'] * live_rate).apply(format_krw)
        table_df['월 평균 배당금'] = (table_df['연간세후배당(USD)'] * live_rate / 12.0).apply(format_krw)
        st.dataframe(table_df[['종목코드', '보유수량', '연간 세후배당금', '월 평균 배당금']], use_container_width=True, hide_index=True)

    st.subheader("📑 실시간 전체 자산 내역")
    display_df = filtered_df[['계좌', '증권사', '종목코드', '보유수량', '평균매수가(USD)', '현재가(USD)', '수익률(%)', '실시간배당률(%)', '배당락일', '매일모으기(KRW)']].copy()
    for col in ['현재가(USD)', '수익률(%)', '실시간배당률(%)', '매일모으기(KRW)']:
        display_df[col] = pd.to_numeric(display_df[col], errors='coerce').fillna(0)
    st.dataframe(display_df.style.format({'현재가(USD)': '{:.2f}', '수익률(%)': '{:+.2f}%', '실시간배당률(%)': '{:.2f}%', '매일모으기(KRW)': '{:,.0f}'}), use_container_width=True, hide_index=True)

with tab_settings:
    st.info("💡 이곳에서 입력하고 하단의 저장 버튼을 누르면 데이터가 영구 보존됩니다!")
    sc1, sc2 = st.columns(2)
    with sc1: new_g1 = st.number_input("1차 목표 월 배당금", value=st.session_state['goal_1'], step=50000)
    with sc2: new_gfinal = st.number_input("최종 목표 월 배당금", value=st.session_state['goal_final'], step=100000)
    
    edited_df = st.data_editor(
        st.session_state['portfolio_v9'],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "계좌": st.column_config.SelectboxColumn("계좌", options=["내 계좌", "아내 계좌", "자녀 계좌", "공동 계좌", "기타"], required=True),
            "증권사": st.column_config.SelectboxColumn("증권사", options=["카카오페이", "토스증권", "삼성증권", "미래에셋증권", "키움증권", "한국투자증권", "NH투자증권", "KB증권", "신한투자증권", "기타"], required=True),
            "배당주기": st.column_config.SelectboxColumn("배당주기", options=["월배당", "분기(3,6,9,12월)", "분기(1,4,7,10월)", "분기(2,5,8,11월)", "반기", "연배당", "기타"], required=True)
        }
    )
    
    if st.button("💾 데이터 영구 저장 및 반영하기", type="primary"):
        st.session_state['goal_1'] = new_g1
        st.session_state['goal_final'] = new_gfinal
        st.session_state['portfolio_v9'] = edited_df
        st.success("데이터가 안전하게 저장되었습니다!")
        st.rerun()
