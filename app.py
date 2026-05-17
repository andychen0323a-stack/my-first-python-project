import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px

# 1. 頁面基本設定與隱藏 Streamlit 預設標誌
st.set_page_config(page_title="AI 體育量化決策系統", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 2. 側邊欄設計 (Sidebar)
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/bullish.png", width=60)
    st.title("控制中心")
    st.markdown("---")
    st.write("🤖 **核心引擎**: 隨機森林 (Random Forest)")
    st.write("🧮 **資金模型**: 凱利準則 (Kelly Criterion)")
    st.markdown("---")

# 3. 主畫面標題區塊
st.title("📈 AI 量化決策戰情室")
st.markdown("自動化抓取五大聯賽與美洲賽事，透過機器學習尋找最高 EV 價值的投資標的。")

# 4. 讀取數據邏輯
csv_files = glob.glob("advanced_odds_*.csv")
if not csv_files:
    st.info("⚠️ 正在等待雲端伺服器產出今日賽事數據，請稍後再回來看！")
else:
    latest_file = max(csv_files, key=os.path.getctime)
    df = pd.DataFrame(pd.read_csv(latest_file))
    date_str = latest_file.split('_')[2].split('.')[0]
    
    # 🛡️ 【關鍵防呆機制】如果讀到舊版沒有「資金分配」的檔案，自動補上預設值避免閃退
    if '資金分配' not in df.columns:
        df['資金分配'] = "觀望 (0%)"
    if '聯賽' not in df.columns:
        df['聯賽'] = "未知"

    with st.sidebar:
        st.success(f"📅 數據日期: \n**{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}**")
        selected_league = st.selectbox("🎯 篩選特定聯賽", ["全部"] + list(df['聯賽'].unique()))

    # 數據清洗 (轉換凱利值)
    def extract_kelly_fund(val):
        if "觀望" in val or "和局" in val: return 0.0
        try: return float(val.split(" ")[1].replace("%", ""))
        except: return 0.0
        
    df['投資價值(%)'] = df['資金分配'].apply(extract_kelly_fund)
    
    if selected_league != "全部":
        df = df[df['聯賽'] == selected_league]

    valuable_bets = df[df['投資價值(%)'] > 0]

    # 5. 頂部 KPI 數據卡片 (Metrics)
    st.markdown("### 📊 今日盤口速報")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總監控賽事", f"{len(df)} 場")
    with col2:
        st.metric("發現價值注 (EV>0)", f"{len(valuable_bets)} 場", "高勝率機會" if len(valuable_bets)>0 else "")
    with col3:
        st.metric("最高建議資金佔比", f"{df['投資價值(%)'].max()}%" if len(valuable_bets) > 0 else "0%")

    st.markdown("---")

    # 6. 分頁系統 (Tabs)
    tab1, tab2 = st.tabs(["📉 資金配置圖表", "📋 完整賽事明細"])

    with tab1:
        if not valuable_bets.empty:
            fig = px.bar(
                valuable_bets, 
                x='對戰組合', 
                y='投資價值(%)', 
                color='聯賽',
                text='資金分配',
                title='各賽事建議投入資金比例 (分數越高代表 AI 信心越強)',
                template='plotly_dark'
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("😴 今日賽事中，AI 尚未發現具備正期望值 (EV>0) 的投資標的，或是目前讀取到舊版報表，建議觀望。")

    with tab2:
        st.dataframe(
            df.drop(columns=['投資價值(%)']), 
            use_container_width=True, 
            height=500,
            hide_index=True 
        )