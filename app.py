import streamlit as st
import pandas as pd
import glob
import os

# 1. 設定網頁基本外觀
st.set_page_config(page_title="AI 體育盤口預測系統", layout="wide")
st.title("📊 跨聯賽 AI 盤口與波膽預測儀表板")
st.markdown("這是一個自動讀取最新 CSV 數據，並允許您自由篩選、排序的預測分析平台。")

# 2. 自動尋找同資料夾下「最新」的 CSV 預測檔案
csv_files = glob.glob("advanced_odds_*.csv")

if not csv_files:
    st.error("⚠️ 找不到任何預測數據檔案！請先執行您的 prediction.py 來產生資料。")
else:
    # 找出日期最新的檔案
    latest_file = max(csv_files, key=os.path.getmtime)
    st.success(f"📥 目前成功連線至最新資料庫：{latest_file}")
    
    # 讀取 CSV 成為表格
    df = pd.read_csv(latest_file)
    
    # 3. 建立網頁左側的「搜尋與篩選」選單
    st.sidebar.header("🔍 快速篩選器")
    
    # 篩選聯賽
    league_options = ["顯示全部"] + list(df['聯賽'].unique())
    selected_league = st.sidebar.selectbox("選擇特定聯賽：", league_options)
    
    # 篩選推薦押注方向
    pick_options = ["顯示全部"] + list(df['推薦'].unique())
    selected_pick = st.sidebar.selectbox("選擇推薦方向：", pick_options)
    
    # 4. 根據使用者的選擇，過濾表格資料
    filtered_df = df.copy()
    if selected_league != "顯示全部":
        filtered_df = filtered_df[filtered_df['聯賽'] == selected_league]
    if selected_pick != "顯示全部":
        filtered_df = filtered_df[filtered_df['推薦'] == selected_pick]
        
    # 5. 在網頁正中央顯示「超級互動式表格」
    st.write(f"共找到 **{len(filtered_df)}** 場符合條件的賽事：")
    st.dataframe(filtered_df, width='stretch', height=600)