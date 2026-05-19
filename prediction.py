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

# 🌍 【新增：全球頂尖球隊中英文對譯字典】
TEAM_TRANSLATIONS = {
    # NBA 籃球
    "Thunder": "奧克拉荷馬雷霆", "Spurs": "聖安東尼奧馬刺",
    
    # MLB 棒球
    "Marlins": "邁阿密馬林魚", "Braves": "亞特蘭大勇士",
    "Rays": "坦帕灣光芒", "Orioles": "巴爾地摩金鶯",
    "Phillies": "費城費城人", "Reds": "辛辛那提紅人",
    "Tigers": "底特律老虎", "Guardians": "克里夫蘭守護者",
    "Nationals": "華盛頓國民", "Mets": "紐約大都會",
    "Yankees": "紐約洋基", "Blue Jays": "多倫多藍鳥",
    "Royals": "堪薩斯皇家", "Red Sox": "波士頓紅襪",
    "Twins": "明尼蘇達雙城", "Astros": "休士頓太空人",
    "Cubs": "芝加哥小熊", "Brewers": "密爾瓦基釀酒人",
    "Rockies": "科羅拉多洛磯", "Rangers": "德州遊騎兵",
    "Angels": "洛杉磯天使", "Athletics": "奧克蘭運動家",
    "Mariners": "西雅圖水手", "White Sox": "芝加哥白襪",
    "Padres": "聖地牙哥教士", "Dodgers": "洛杉磯道奇",
    "Diamondbacks": "亞利桑那響尾蛇", "Giants": "舊金山巨人",
    
    # 足球五大聯賽 (英超/西甲/義甲/德甲/法甲精選)
    "Arsenal": "阿森納", "阿森納": "阿森納", 
    "Burnley": "伯恩利", "Burnley ": "伯恩利",
    "Man City": "曼城", "Man United": "曼聯", "Liverpool": "利物浦",
    "Chelsea": "切爾西", "Tottenham": "熱刺", "Real Madrid": "皇家馬德里",
    "Barcelona": "巴塞隆納", "Bayern": "拜仁慕尼黑", "PSG": "巴黎聖日耳曼"
}

# 🛠️ 翻譯核心函式
def translate_matchup(matchup_str):
    if not isinstance(matchup_str, str):
        return matchup_str
    
    # 清理並統一過濾掉球隊文字後面的表情符號
    emojis = ["🏀", "⚾", "⚽", "🏐"]
    clean_str = matchup_str
    for emoji in emojis:
        clean_str = clean_str.replace(emoji, "")
        
    # 切割對戰組合 (例如 "Thunder VS Spurs")
    if " VS " in clean_str:
        teams = clean_str.split(" VS ")
        team1 = teams[0].strip()
        team2 = teams[1].strip()
        
        # 進行字典查表，查不到就留原名
        t1_zh = TEAM_TRANSLATIONS.get(team1, team1)
        t2_zh = TEAM_TRANSLATIONS.get(team2, team2)
        
        # 根據聯賽類型補回對應的乾淨表情符號
        if "NBA" in str(st.session_state.get('current_league', '')):
            return f"🏀 {t1_zh} VS {t2_zh}"
        elif "MLB" in str(st.session_state.get('current_league', '')):
            return f"⚾ {t1_zh} VS {t2_zh}"
        elif "超" in str(st.session_state.get('current_league', '')) or "甲" in str(st.session_state.get('current_league', '')):
            return f"⚽ {t1_zh} VS {t2_zh}"
        else:
            return f"{t1_zh} VS {t2_zh}"
            
    return matchup_str

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
    # 嚴格按檔名排序抓最新檔案
    latest_file = max(csv_files) 
    df = pd.DataFrame(pd.read_csv(latest_file))
    
    try:
        date_str = latest_file.split('_')[2].split('.')[0]
    except:
        date_str = "20260518"
    
    if '資金分配' not in df.columns: df['資金分配'] = "觀望 (0%)"
    if '聯賽' not in df.columns: df['聯賽'] = "未知"

    with st.sidebar:
        st.success(f"📅 數據日期: \n**{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}**")
        selected_league = st.selectbox("🎯 篩選特定聯賽", ["全部"] + list(df['聯賽'].unique()))

    # 將當前篩選狀態塞入 session，方便翻譯函式判斷圖標
    st.session_state['current_league'] = selected_league if selected_league != "全部" else "混合"

    # 數據清洗與「動態即時中文翻譯」
    df['對戰組合'] = df.apply(
        lambda row: (st.session_state.update({'current_league': row['聯賽']}) or True) and translate_matchup(row['對戰組合']), 
        axis=1
    )
    
    def extract_kelly_fund(val):
        if not isinstance(val, str): return 0.0
        if "觀望" in val or "和局" in val: return 0.0
        try:
            parts = val.split(" ")
            if len(parts) >= 2:
                return float(parts[1].replace("%", ""))
        except:
            pass
        return 0.0
        
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
            st.info("😴 今日賽事中，AI 尚未發現具備正期望值 (EV>0) 的投資標的，建議觀望。")

    with tab2:
        st.dataframe(
            df.drop(columns=['投資價值(%)']), 
            use_container_width=True, 
            height=500,
            hide_index=True 
        )