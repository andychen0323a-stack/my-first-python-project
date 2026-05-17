import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px

# 1. 頁面基本設定 (寬螢幕模式)
st.set_page_config(page_title="AI 體育量化預測", page_icon="📈", layout="wide")
st.title("📈 體育 AI 量化決策終端機")
st.markdown("---")

# 2. 自動尋找最新的預測報表
csv_files = glob.glob("advanced_odds_*.csv")
if not csv_files:
    st.warning("⚠️ 目前尚未產生任何賽事數據，請等待雲端機器人執行或手動觸發。")
else:
    # 找到日期最新的檔案
    latest_file = max(csv_files, key=os.path.getctime)
    df = pd.DataFrame(pd.read_csv(latest_file))
    
    date_str = latest_file.split('_')[2].split('.')[0]
    st.success(f"✅ 成功載入最新數據：**{date_str[:4]}年{date_str[4:6]}月{date_str[6:]}日**")

    # 3. 數據清洗：提取凱利資金比例作為圖表 Y 軸
    # 將 "主投 10.5%" 轉換為數字 10.5
    def extract_kelly_fund(val):
        if "觀望" in val or "和局" in val: return 0.0
        try: return float(val.split(" ")[1].replace("%", ""))
        except: return 0.0

    df['投資價值(%)'] = df['資金分配'].apply(extract_kelly_fund)
    
    # 4. 頂部數據儀表板 (Metrics)
    col1, col2, col3 = st.columns(3)
    valuable_bets = df[df['投資價值(%)'] > 0]
    
    col1.metric("今日分析總賽事", f"{len(df)} 場")
    col2.metric("發現高價值盤口 (EV>0)", f"{len(valuable_bets)} 場", "+ 獲利機會")
    col3.metric("最高建議本金佔比", f"{df['投資價值(%)'].max()}%" if len(valuable_bets) > 0 else "0%")

    # 5. 視覺化圖表：今日高價值賽事投資比重
    if not valuable_bets.empty:
        st.subheader("📊 今日 AI 資金配置建議")
        fig = px.bar(
            valuable_bets, 
            x='對戰組合', 
            y='投資價值(%)', 
            color='聯賽',
            text='資金分配',
            title='各賽事建議投入資金比例',
            template='plotly_dark'
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    # 6. 互動式數據表格
    st.subheader("📋 完整賽事精算明細")
    # 增加過濾器
    selected_league = st.selectbox("過濾聯賽", ["全部"] + list(df['聯賽'].unique()))
    if selected_league != "全部":
        df_display = df[df['聯賽'] == selected_league]
    else:
        df_display = df

    # 隱藏用來畫圖的輔助欄位，顯示乾淨的表格
    st.dataframe(df_display.drop(columns=['投資價值(%)']), use_container_width=True, height=500)