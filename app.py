import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
import math

# -----------------------------------------------------------------------------
# 🌟 추천 컬러: 일렉트릭 블루 (가독성과 세련됨의 끝판왕)
# -----------------------------------------------------------------------------
THEME_COLOR = "#2997ff" 

st.set_page_config(page_title="Dividend Pro Dashboard", page_icon="🚀", layout="wide")

st.markdown(f"""
<style>
    .reportview-container {{ background-color: #0d1117; color: #e6edf3; }}
    .metric-card {{ background: linear-gradient(135deg, #161b22 0%, #1f242d 100%); border: 1px solid #30363d; border-radius: 14px; padding: 18px; margin-bottom: 12px; }}
    .metric-title {{ color: #8b949e; font-size: 0.85rem; font-weight: 500; margin-bottom: 6px; }}
    .metric-value-green {{ color: {THEME_COLOR}; font-size: 1.5rem; font-weight: 700; }}
    .metric-value-cyan {{ color: #58a6ff; font-size: 1.5rem; font-weight: 700; }}
    .metric-value-white {{ color: #ffffff; font-size: 1.5rem; font-weight: 700; }}
    .alert-card {{ background-color: rgba(41, 151, 255, 0.1); border: 1px solid {THEME_COLOR}; border-radius: 10px; padding: 12px; margin-bottom: 15px; color: {THEME_COLOR}; font-weight: 600; }}
    .stProgress > div > div > div > div {{ background-color: {THEME_COLOR}; }}
</style>
""", unsafe_allow_html=True)

# (나머지 로직은 이전과 동일합니다.)
# ... [이하 코드는 v3.2의 전체 로직을 그대로 사용하세요] ...
