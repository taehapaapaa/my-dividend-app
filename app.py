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
    .metric-card {
        background: linear-gradient(135deg, #161b22 0%, #1f242d 100%);
        border: 1px solid #30363d; border-radius: 14px; padding: 18px; margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .metric-title { color: #8b949e; font-size: 0.85rem; font-weight: 500; margin-bottom: 6px; }
    .metric-value-green { color: #2ea043; font-size: 1.5rem; font-weight: 700; }
    .metric-value-cyan { color: #58a6ff; font-size: 1.5rem; font-weight: 700; }
    /* 프로그레스 바 커스텀 */
    .stProgress > div > div > div > div { background-color: #2ea043; }
    .tax-safe { color: #2ea043; font-weight: bold; border: 1px solid #2ea043; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem;}
    .tax-warning { color: #f85149; font-weight: bold; border: 1px solid #f85149; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem;}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 실시간 데이터 수집 (환율 & 실시간 주가)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600) # 10분마다 갱신
def get_live_data(tickers):
    data = {}
    # 환율
    try:
        data['USDKRW'] = round(yf.Ticker("USDKRW=X").fast_info['last_price'], 2)
    except:
        data['USDKRW'] = 1380.00
    
    # 주가
    for t in tickers:
        try:
            data[t] = yf.Ticker(t).fast_info['last_price']
        except:
            data[t] = 0.0 # 오류 시 0 처리
    return data

# -----------------------------------------------------------------------------
# 3. 데이터 및 목표 초기화
# -----------------------------------------------------------------------------
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = pd.DataFrame([
        {"계좌": "내 계좌", "증권사": "토스증권", "종목코드": "SCHD", "보유수량": 45.5, "평균매수가(USD)": 78.5, "매일모으기(USD)": 10.0, "예상시가배당률(%)": 3.4},
        {"계좌": "내 계좌", "증권사": "카카오페이", "종목코드": "JEPI", "보유수량": 30.0, "평균매수가(USD)": 56.2, "매일모으기(USD)": 15.0, "예상시가배당률(%)": 7.5},
        {"계좌": "아내 계좌", "증권사": "토스증권", "종목코드": "JEPQ", "보유수량": 25.0, "평균매수가(USD)": 54.0, "매일모으기(USD)": 10.0, "예상시가배당률(%)": 9.2},
        {"계좌": "아내 계좌", "증권사": "카카오페이", "종목코드": "O", "보유수량": 20.0, "평균매수가(USD)": 55.0, "매일모으기(USD)": 8.0, "예상시가배당률(%)": 5.3},
        {"계좌": "내 계좌", "증권사": "토스증권", "종목코드": "QQQM", "보유수량": 12.0, "평균매수가(USD)": 185.0, "매일모으기(USD)": 5.0, "예상시가배당률(%)": 0.6},
        {"계좌": "내 계좌", "증권사": "토스증권", "종목코드": "GOOGL", "보유수량": 15.0, "평균매수가(USD)": 170.0, "매일모으기(USD)": 5.0, "예상시가배당률(%)": 0.5},
    ])
    st.session_state['goal_1'] = 500000   # 1차 목표: 월 50만 원
    st.session_state['goal_final'] = 3000000 # 최종 목표: 월 300만 원

df = st.session_state['portfolio'].copy()
live_data = get_live_data(list(df['종목코드'].unique()))
live_rate = live_data['USDKRW']

# -----------------------------------------------------------------------------
# 4. 실시간 자산 및 세금 계산 로직
# -----------------------------------------------------------------------------
# 현재가 반영
df['현재가(USD)'] = df['종목코드'].map(lambda x: live_data.get(x, 0))
df['평가금액(USD)'] = df['보유수량'] * df['현재가(USD)']
df['수익률(%)'] = ((df['현재가(USD)'] - df['평균매수가(USD)']) / df['평균매수가(USD)']) * 100

# 세금 및 환율 반영 배당금 계산 (배당소득세 15.4% 공제)
df['연간세전배당(USD)'] = df['평가금액(USD)'] * (df['예상시가배당률(%)'] / 100.0)
df['연간세후배당(USD)'] = df['연간세전배당(USD)'] * (1 - 0.154)

total_assets_krw = df['평가금액(USD)'].sum() * live_rate
total_annual_div_pre_tax_krw = df['연간세전배당(USD)'].sum() * live_rate
total_annual_div_after_tax_krw = df['연간세후배당(USD)'].sum() * live_rate
total_monthly_div_krw = total_annual_div_after_tax_krw / 12.0

# -----------------------------------------------------------------------------
# 5. 대시보드 헤더 및 세금 알림
# -----------------------------------------------------------------------------
col_header1, col_header2 = st.columns([2, 1])
with col_header1:
    st.markdown("### 📈 실시간 배당주 포트폴리오 & 목표 달성 게이지")
with col_header2:
    st.markdown(f"<div style='text-align: right; color: #58a6ff; font-weight: 600;'>● LIVE 환율: 1 USD = {live_rate:,.2f} KRW</div>", unsafe_allow_html=True)
    
    # 세금 종합과세 알림 로직 (연간 세전 배당금이 2,000만원 초과 시)
    if total_annual_div_pre_tax_krw > 20000000:
        st.markdown("<div style='text-align: right; margin-top:5px;'><span class='tax-warning'>⚠️ 금융소득종합과세 주의 (연 2천만원 초과)</span></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='text-align: right; margin-top:5px;'><span class='tax-safe'>✅ 세금 안전구간 (여유: {int((20000000 - total_annual_div_pre_tax_krw)/10000):,}만 원)</span></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. 목표 달성률 게이지 (Gamification)
# -----------------------------------------------------------------------------
goal_1 = st.session_state['goal_1']
goal_final = st.session_state['goal_final']

prog_1 = min(total_monthly_div_krw / goal_1, 1.0)
prog_final = min(total_monthly_div_krw / goal_final, 1.0)

st.markdown("#### 🎯 나의 배당 자유 레벨")
col_g1, col_g2 = st.columns(2)
with col_g1:
    st.markdown(f"**1차 목표 달성률 ({int(goal_1/10000):,}만 원)** - 현재 {int(total_monthly_div_krw):,} 원")
    st.progress(prog_1)
    st.caption(f"{int(prog_1*100)}% 달성 완료!")
with col_g2:
    st.markdown(f"**최종 목표 달성률 ({int(goal_final/10000):,}만 원)**")
    st.progress(prog_final)
    st.caption(f"{int(prog_final*100)}% 달성 완료!")

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. 탭 및 설정 에디터
# -----------------------------------------------------------------------------
tab_dashboard, tab_settings = st.tabs(["📊 통합 대시보드", "⚙️ 내 포트폴리오 및 목표 수정"])

with tab_dashboard:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-title">실수령 월 배당금 (세후 15.4% 공제)</div>
            <div class="metric-value-green">약 {int(total_monthly_div_krw):,} 원</div>
            <div style="color:#8b949e; font-size:0.8rem; margin-top:4px;">연간 {int(total_annual_div_after_tax_krw):,} 원 꽂힘</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-title">총 포트폴리오 평가 자산 (실시간)</div>
            <div class="metric-value-cyan">{int(total_assets_krw):,} 원</div>
            <div style="color:#8b949e; font-size:0.8rem; margin-top:4px;">총 {df['평가금액(USD)'].sum():,.2f} USD</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-title">일일 자동 매수 설정액</div>
            <div class="metric-value-white">${df['매일모으기(USD)'].sum():,.2f}</div>
            <div style="color:#8b949e; font-size:0.8rem; margin-top:4px;">매일 약 {int(df['매일모으기(USD)'].sum() * live_rate):,} 원 투자 중</div>
        </div>""", unsafe_allow_html=True)

    st.subheader("📑 실시간 보유 내역")
    # 보여주기용 깔끔한 데이터프레임 포맷팅
    display_df = df[['계좌', '증권사', '종목코드', '보유수량', '평균매수가(USD)', '현재가(USD)', '수익률(%)', '매일모으기(USD)']].copy()
    st.dataframe(display_df.style.format({'현재가(USD)': '{:.2f}', '수익률(%)': '{:+.2f}%'}), use_container_width=True, hide_index=True)

with tab_settings:
    st.markdown("### 🎯 목표 금액 설정 (원 단위)")
    c1, c2 = st.columns(2)
    with c1:
        new_g1 = st.number_input("1차 목표 월 배당금", value=st.session_state['goal_1'], step=50000)
    with c2:
        new_gfinal = st.number_input("최종 목표 월 배당금", value=st.session_state['goal_final'], step=100000)
    
    st.markdown("### ⚙️ 포트폴리오 & 매일 모으기 에디터")
    edited_df = st.data_editor(st.session_state['portfolio'], num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 모든 설정 및 주식 저장하기", type="primary"):
        st.session_state['goal_1'] = new_g1
        st.session_state['goal_final'] = new_gfinal
        st.session_state['portfolio'] = edited_df
        st.success("데이터가 반영되었습니다! 게이지와 자산이 다시 계산됩니다.")
        st.rerun()
