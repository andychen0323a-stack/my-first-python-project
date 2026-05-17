import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px

# 1. 頁面基本設定與隱藏 Streamlit 預設標誌 (UI 升級核心)
st.set_page_config(page_title="AI 體育量化決策系統", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# 注入自訂 CSS 來隱藏右上角選單與底部浮水印，讓 App 看起來像原生的獨立軟體
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 2. 側邊欄設計 (Sidebar) - 將控制項移到旁邊，保持主畫面乾淨
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/bullish.png", width=60) # 加上一個帥氣的圖示
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
    
    with st.sidebar:
        st.success(f"📅 數據日期: \n**{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}**")
        # 將聯賽過濾器放在側邊欄
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

    # 5. 頂部 KPI 數據卡片 (Metrics) - 加上框線增添科技感
    st.markdown("### 📊 今日盤口速報")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總監控賽事", f"{len(df)} 場")
    with col2:
        st.metric("發現價值注 (EV>0)", f"{len(valuable_bets)} 場", "高勝率機會" if len(valuable_bets)>0 else "")
    with col3:
        st.metric("最高建議資金佔比", f"{df['投資價值(%)'].max()}%" if len(valuable_bets) > 0 else "0%")

    st.markdown("---")

    # 6. 分頁系統 (Tabs) - 讓圖表與表格分開，畫面不擁擠
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
            st.info("😴 今日剩餘賽事中，AI 尚未發現具備正期望值 (EV>0) 的投資標的，建議觀望。")

    with tab2:
        # 隱藏用來畫圖的輔助欄位，顯示乾淨的表格
        st.dataframe(
            df.drop(columns=['投資價值(%)']), 
            use_container_width=True, 
            height=500,
            hide_index=True # 隱藏最左邊的 0,1,2 編號讓表格更俐落
        )