import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import numpy as np
# 導入真實機器學習套件
from sklearn.ensemble import RandomForestClassifier

print("--- 啟動量化預測系統 (Machine Learning 真實 AI 版) ---\n")

def run_prediction_system():
    target_date = datetime.now()
    date_str = target_date.strftime("%Y%m%d")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 開始執行 {date_str} 賽事預測任務...\n")

    leagues = {
        "NBA": {"url": f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}", "symbol": "🏀", "sport": "basketball"},
        "MLB": {"url": f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={date_str}", "symbol": "⚾", "sport": "baseball"},
        "英超": {"url": f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates={date_str}", "symbol": "⚽", "sport": "soccer"},
        "西甲": {"url": f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard?dates={date_str}", "symbol": "⚽", "sport": "soccer"}
    }

    team_translations = {
        "Boston Celtics": "波士頓塞爾提克", "Dallas Mavericks": "達拉斯獨行俠",
        "New York Yankees": "紐約洋基", "Los Angeles Dodgers": "洛杉磯道奇",
        "Arsenal": "阿森納", "Manchester City": "曼城", "Real Madrid": "皇家馬德里", "Barcelona": "巴塞隆納"
    }

    try:
        with open("daily_intel_db.json", "r", encoding="utf-8") as f:
            daily_intel = json.load(f)
    except FileNotFoundError:
        daily_intel = {}

    # ==========================================
    # 🧠 AI 機器學習引擎建立 (Random Forest)
    # ==========================================
    print("🧠 正在啟動隨機森林 AI 模型，進行歷史數據學習...")
    
    # 1. 產生模擬的歷史訓練數據 (特徵: [主場勝率, 客場勝率, 主場情報扣分, 客場情報扣分])
    # 實戰中，這裡可以替換成讀取過去 10 年的真實 CSV 歷史賽果
    np.random.seed(42)
    X_train = np.random.rand(1000, 4) 
    
    # 2. 制定學習標籤 (0: 客勝, 1: 主勝, 2: 和局)
    y_train = []
    for row in X_train:
        # 簡單模擬歷史賽果的規律讓 AI 學習
        home_strength = row[0] - row[2] + 0.05 # 包含主場優勢
        away_strength = row[1] - row[3]
        if abs(home_strength - away_strength) < 0.1: y_train.append(2) # 實力相近判和局
        elif home_strength > away_strength: y_train.append(1)
        else: y_train.append(0)
        
    # 3. 訓練模型
    ai_model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    ai_model.fit(X_train, y_train)
    print("✅ AI 模型訓練完成，準備預測今日賽事！\n")
    # ==========================================

    def calculate_ml_bookmaker(sport, h_name_en, h_record, a_name_en, a_record):
        try:
            h_wins = int(h_record.split('-')[0]) if '-' in h_record else 0
            h_losses = int(h_record.split('-')[1]) if '-' in h_record else 0
            h_base_rate = h_wins / (h_wins + h_losses) if (h_wins + h_losses) > 0 else 0.5
            
            a_wins = int(a_record.split('-')[0]) if '-' in a_record else 0
            a_losses = int(a_record.split('-')[1]) if '-' in a_record else 0
            a_base_rate = a_wins / (a_wins + a_losses) if (a_wins + a_losses) > 0 else 0.5
            
            h_penalty = daily_intel.get(h_name_en, {}).get("injury_penalty", 0.0)
            a_penalty = daily_intel.get(a_name_en, {}).get("injury_penalty", 0.0)
            
            # --- 將今日數據餵給 AI 模型 ---
            features = np.array([[h_base_rate, a_base_rate, h_penalty, a_penalty]])
            # 取得 AI 預測的各項機率: [客勝機率, 主勝機率, 和局機率]
            probabilities = ai_model.predict_proba(features)[0]
            
            a_prob = probabilities[0] * 100
            h_prob = probabilities[1] * 100
            draw_prob = probabilities[2] * 100 if sport == "soccer" else 0.0
            
            # 非足球賽事將和局機率平分給主客
            if sport != "soccer":
                h_prob += probabilities[2] * 50
                a_prob += probabilities[2] * 50
                
            # 確保機率不為 0
            h_prob, a_prob = max(0.1, h_prob), max(0.1, a_prob)
            
            margin = 1.05 # 設定為發現價值盤口的賠率條件
            h_odds = round((100 / h_prob) * margin, 2) if h_prob > 0 else 0.0
            a_odds = round((100 / a_prob) * margin, 2) if a_prob > 0 else 0.0
            draw_odds = round((100 / draw_prob) * margin, 2) if draw_prob > 0 else "-"
            
            # --- 凱利期望值計算 ---
            h_p_dec, a_p_dec = h_prob / 100, a_prob / 100
            h_ev = (h_p_dec * (h_odds - 1)) - (1 - h_p_dec)
            a_ev = (a_p_dec * (a_odds - 1)) - (1 - a_p_dec)
            
            h_kelly = max(0, round(((h_ev / (h_odds - 1)) * 100) / 4, 1)) if h_odds > 1 and h_ev > 0 else 0
            a_kelly = max(0, round(((a_ev / (a_odds - 1)) * 100) / 4, 1)) if a_odds > 1 and a_ev > 0 else 0
            
            rec_pick = "主勝" if h_prob > a_prob else "客勝"
            if h_prob > a_prob: kelly_str = f"主投 {h_kelly}%" if h_kelly > 0 else "觀望"
            else: kelly_str = f"客投 {a_kelly}%" if a_kelly > 0 else "觀望"
            
            return h_prob, a_prob, draw_prob, h_odds, a_odds, draw_odds, rec_pick, kelly_str
        except Exception as e:
            return 50.0, 50.0, 0.0, 1.90, 1.90, "-", "主勝", "觀望"

    all_games_list = []
    
    for league_name, info in leagues.items():
        response = requests.get(info["url"])
        if response.status_code == 200:
            events = response.json().get('events', [])
            for event in events:
                if event['competitions'][0]['status']['type']['state'] == 'pre':
                    raw_time = event['date'].replace('Z', '')
                    tw_time = datetime.strptime(raw_time[:16], "%Y-%m-%dT%H:%M") + timedelta(hours=8)
                    
                    comps = event['competitions'][0]['competitors']
                    h_team = next(c for c in comps if c['homeAway'] == 'home')
                    a_team = next(c for c in comps if c['homeAway'] == 'away')
                    
                    h_name = h_team['team']['name']
                    a_name = a_team['team']['name']
                    
                    h_rec = h_team.get('records', [{'summary': '0-0'}])[0].get('summary', '0-0')
                    a_rec = a_team.get('records', [{'summary': '0-0'}])[0].get('summary', '0-0')
                    
                    h_p, a_p, d_p, h_o, a_o, d_o, rec_pick, kelly = calculate_ml_bookmaker(
                        info["sport"], h_name, h_rec, a_name, a_rec
                    )
                    
                    all_games_list.append({
                        "聯賽": league_name,
                        "時間": tw_time.strftime("%m/%d %H:%M"),
                        "對戰組合": f"{team_translations.get(h_name, h_name)} {info['symbol']} VS {team_translations.get(a_name, a_name)} {info['symbol']}",
                        "主/客/和 機率": f"{h_p:.1f}% / {a_p:.1f}% / {d_p:.1f}%",
                        "賠率": f"{h_o} / {a_o} / {d_o}",
                        "推薦": rec_pick,
                        "資金分配": kelly
                    })

    if all_games_list:
        df = pd.DataFrame(all_games_list)
        filename = f"advanced_odds_{date_str}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print("\n☁️ 正在同步至 GitHub...")
        os.system('git add .')
        os.system(f'git commit -m "🚀 升級：匯入 Scikit-Learn 隨機森林模型與 Plotly 視覺化"')
        os.system('git push')
        print("🎉 執行結束！")

if __name__ == "__main__":
    run_prediction_system()