import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px

# 1. 頁面基本設定
st.set_page_config(page_title="AI 體育量化決策系統", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 🌍 【超級鋼鐵字典】全美職棒、全美職籃、歐洲足球全收錄！
TEAM_MAP = {
    # === NBA 籃球 (全 30 隊) ===
    "Celtics": "波士頓塞爾提克", "Bucks": "密爾瓦基公鹿", "76ers": "費城76人", "Cavaliers": "克里夫蘭騎士",
    "Knicks": "紐約尼克", "Nets": "布魯克林籃網", "Hawks": "亞特蘭大老鷹", "Heat": "邁阿密熱火",
    "Raptors": "多倫多暴龍", "Bulls": "芝加哥公牛", "Pacers": "印第安納溜馬", "Wizards": "華盛頓巫師",
    "Magic": "奧蘭多魔術", "Hornets": "夏洛特黃蜂", "Pistons": "底特律活塞", "Nuggets": "丹佛金塊",
    "Grizzlies": "曼非斯灰熊", "Kings": "沙加緬度國王", "Suns": "鳳凰城太陽", "Clippers": "洛杉磯快艇",
    "Warriors": "金州勇士", "Lakers": "洛杉磯湖人", "Timberwolves": "明尼蘇達灰狼", "Pelicans": "紐奧良鵜鶘",
    "Thunder": "奧克拉荷馬雷霆", "Mavericks": "達拉斯獨行俠", "Jazz": "猶他爵士", "Blazers": "波特蘭拓荒者",
    "Spurs": "聖安東尼奧馬刺", "Rockets": "休士頓火箭",
    
    # === MLB 棒球 (全 30 隊) ===
    "Yankees": "紐約洋基", "Red Sox": "波士頓紅襪", "Orioles": "巴爾地摩金鶯", "Rays": "坦帕灣光芒", "Blue Jays": "多倫多藍鳥",
    "Guardians": "克里夫蘭守護者", "Twins": "明尼蘇達雙城", "Royals": "堪薩斯皇家", "Tigers": "底特律老虎", "White Sox": "芝加哥白襪",
    "Astros": "休士頓太空人", "Mariners": "西雅圖水手", "Rangers": "德州遊騎兵", "Angels": "洛杉磯天使", "Athletics": "奧克蘭運動家",
    "Braves": "亞特蘭大勇士", "熱愛": "邁阿密馬林魚", "Marlins": "邁阿密馬林魚", "Mets": "紐約大都會", "Phillies": "費城費城人", "Nationals": "華盛頓國民",
    "Brewers": "密爾瓦基釀酒人", "Cubs": "芝加哥小熊", "Cardinals": "聖路易紅雀", "Pirates": "匹茲堡海盜", "Reds": "辛辛那提紅人",
    "Dodgers": "洛杉磯道奇", "Giants": "舊金山巨人", "Padres": "聖地牙哥教士", "Diamondbacks": "亞利桑那響尾蛇", "Rockies": "科羅拉多洛磯",

    # === 足球五大聯賽熱門 ===
    "Arsenal": "阿森納", "Burnley": "伯恩利", "Man City": "曼城", "Man United": "曼聯", "Liverpool": "利物浦",
    "Chelsea": "切爾西", "Tottenham": "熱刺", "Aston Villa": "阿斯頓維拉", "Newcastle": "紐卡索聯",
    "Real Madrid": "皇家馬德里", "Barcelona": "巴塞隆納", "Atletico": "馬德里競技",
    "Bayern": "拜仁慕尼黑", "Dortmund": "多特蒙德", "Inter": "國際米蘭", "Milan": "AC米蘭", "Juventus": "尤文圖斯", "PSG": "巴黎聖日耳曼"
}

def translate_matchup_fuzzy(matchup_str, league_name):
    if not isinstance(matchup_str, str): return matchup_str
    
    clean_str = matchup_str
    for emoji in ["🏀", "⚾", "⚽", "🏐"]:
        clean_str = clean_str.replace(emoji, "")
        
    if " VS " in clean_str:
        teams = clean_str.split(" VS ")
        t1 = teams[0].strip()
        t2 = teams[1].strip()
        
        # 只要新一天的球隊名字有出現在強大字典裡，立刻強制對譯成中文！
        for eng, zh in TEAM_MAP.items():
            if eng.lower() in t1.lower(): t1 = zh
            if eng.lower() in t2.lower(): t2 = zh
            
        if "NBA" in str(league_name): return f"🏀 {t1} VS {t2}"
        elif "MLB" in str(league_name): return f"⚾ {t1} VS {t2}"
        elif "超" in str(league_name) or "甲" in str(league_name): return f"⚽ {t1} VS {t2}"
        return f"{t1} VS {t2}"
        
    return matchup_str

# 2. 側邊欄設計
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/bullish.png", width=60)
    st.title("控制中心")
    st.markdown("---")
    st.write("🤖 **核心引擎**: 隨機森林 (Random Forest)")
    st.write("🧮 **資金模型**: 凱利準則 (Kelly Criterion)")
    st.markdown("---")

# 3. 主畫面標題
st.title("📈 AI 量化決策戰情室")
st.markdown("自動化抓取五大聯賽與美洲賽事，透過機器學習尋找最高 EV 價值的投資標的。")

# 4. 讀取數據
csv_files = glob.glob("advanced_odds_*.csv")
if not csv_files:
    st.info("⚠️ 正在等待雲端伺服器產出今日賽事數據，請稍後再回來看！")
else:
    latest_file = max(csv_files) 
    df = pd.DataFrame(pd.read_csv(latest_file))
    
    try:
        date_str = latest_file.split('_')[2].split('.')[0]
    except:
        date_str = "20260519"
    
    if '資金分配' not in df.columns: df['資金分配'] = "觀望 (0%)"
    if '聯賽' not in df.columns: df['聯賽'] = "未知"

    with st.sidebar:
        st.success(f"📅 數據日期: \n**{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}**")
        selected_league = st.selectbox("🎯 篩選特定聯賽", ["全部"] + list(df['聯賽'].unique()))

    # 提取數字
    def extract_kelly_fund_robust(val):
        if not isinstance(val, str): return 0.0
        if "觀望" in val or "0%" in val: return 0.0
        try:
            if "%" in val:
                num_str = "".join([c for c in val if c.isdigit() or c == '.'])
                return float(num_str)
        except:
            pass
        return 0.0
        
    df['投資價值(%)'] = df['資金分配'].apply(extract_kelly_fund_robust)
    
    # 全中文翻譯對戰組合
    df['對戰組合'] = df.apply(lambda row: translate_matchup_fuzzy(row['對戰組合'], row['聯賽']), axis=1)
    
    if selected_league != "全部":
        df = df[df['聯賽'] == selected_league]

    valuable_bets = df[df['投資價值(%)'] > 0]

    # 5. 今日盤口速報
    st.markdown("### 📊 今日盤口速報")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總監控賽事", f"{len(df)} 場")
    with col2:
        st.metric("發現價值注 (EV>0)", f"{len(valuable_bets)} 場", "高勝率機會" if len(valuable_bets)>0 else "")
    with col3:
        max_val = df['投資價值(%)'].max() if len(df) > 0 else 0.0
        st.metric("最高建議資金佔比", f"{max_val}%")

    st.markdown("---")

    # 6. 分頁系統
    tab1, tab2 = st.tabs(["📉 資金配置圖表", "📋 完整賽事明細"])

    with tab1:
        if not valuable_bets.empty:
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
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("😴 今日賽事中，AI 建議全面空手觀望，請至『完整賽事明細』查看今日監控清單。")

    with tab2:
        # 🛡️ 雙重保險：絕對保留 CSV 的原始所有欄位（包括足球正確比分推薦）
        display_df = df.copy()
        if '投資價值(%)' in display_df.columns:
            display_df = display_df.drop(columns=['投資價值(%)'])
            
        st.dataframe(
            display_df, 
            width="stretch", 
            height=500,
            hide_index=True 
        )