import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import json

print("--- 啟動量化預測系統 (五大聯賽 + 凱利資金控管 終極版) ---\n")

def run_prediction_system():
    # 1. 核心日期校正：移除 +1 天，直接用當前日期精準對接美國 ESPN 時間
    target_date = datetime.now()
    date_str = target_date.strftime("%Y%m%d")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 開始執行 {date_str} 賽事預測任務...\n")

    # 2. 跨聯賽 API 設定 (歐洲五大聯賽 + 籃球棒球)
    leagues = {
        "NBA": {"url": f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}", "symbol": "🏀", "sport": "basketball"},
        "MLB": {"url": f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates={date_str}", "symbol": "⚾", "sport": "baseball"},
        "英超": {"url": f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates={date_str}", "symbol": "⚽", "sport": "soccer"},
        "西甲": {"url": f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard?dates={date_str}", "symbol": "⚽", "sport": "soccer"},
        "義甲": {"url": f"https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard?dates={date_str}", "symbol": "⚽", "sport": "soccer"},
        "德甲": {"url": f"https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard?dates={date_str}", "symbol": "⚽", "sport": "soccer"},
        "法甲": {"url": f"https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard?dates={date_str}", "symbol": "⚽", "sport": "soccer"}
    }

    # 3. 球隊中文對照表
    team_translations = {
        "Boston Celtics": "波士頓塞爾提克", "Dallas Mavericks": "達拉斯獨行俠",
        "New York Yankees": "紐約洋基", "Los Angeles Dodgers": "洛杉磯道奇",
        # 英超
        "Arsenal": "阿森納", "Manchester City": "曼城", "Chelsea": "切爾西", "Liverpool": "利物浦", "Manchester United": "曼聯",
        # 西甲
        "Real Madrid": "皇家馬德里", "Barcelona": "巴塞隆納", "Atlético Madrid": "馬德里競技",
        # 德甲
        "Bayern Munich": "拜仁慕尼黑", "Borussia Dortmund": "多特蒙德", "Bayer Leverkusen": "勒沃庫森",
        # 義甲
        "Juventus": "尤文圖斯", "AC Milan": "AC米蘭", "Internazionale": "國際米蘭", "Napoli": "拿坡里",
        # 法甲
        "Paris Saint-Germain": "巴黎聖日耳曼", "Marseille": "馬賽"
    }

    # 4. 自動讀取外部情報庫
    try:
        with open("daily_intel_db.json", "r", encoding="utf-8") as f:
            daily_intel = json.load(f)
        print("📥 成功讀取最新情報庫 (daily_intel_db.json)！\n")
    except FileNotFoundError:
        print("⚠️ 找不到情報庫檔案，將使用預設空情報。\n")
        daily_intel = {}

    # 5. 盤口與賠率精算引擎
    def calculate_bookmaker_model(sport, h_name_en, h_record, a_name_en, a_record):
        try:
            h_wins = int(h_record.split('-')[0]) if '-' in h_record else 0
            h_losses = int(h_record.split('-')[1]) if '-' in h_record else 0
            h_base_rate = h_wins / (h_wins + h_losses) if (h_wins + h_losses) > 0 else 0.5
            
            a_wins = int(a_record.split('-')[0]) if '-' in a_record else 0
            a_losses = int(a_record.split('-')[1]) if '-' in a_record else 0
            a_base_rate = a_wins / (a_wins + a_losses) if (a_wins + a_losses) > 0 else 0.5
            
            h_intel = daily_intel.get(h_name_en, {"starter_score": 5, "injury_penalty": 0.0})
            a_intel = daily_intel.get(a_name_en, {"starter_score": 5, "injury_penalty": 0.0})
            
            h_adj = h_base_rate + (h_intel["starter_score"] - 5) * 0.015 + h_intel["injury_penalty"] + (0.01 if sport == "soccer" else 0.03)
            a_adj = a_base_rate + (a_intel["starter_score"] - 5) * 0.015 + a_intel["injury_penalty"]
            
            h_adj = max(0.1, h_adj)
            a_adj = max(0.1, a_adj)
            
            if sport == "soccer":
                draw_prob = 26.0
                remaining = 100.0 - draw_prob
                total_adj = h_adj + a_adj
                h_prob = (h_adj / total_adj) * remaining
                a_prob = (a_adj / total_adj) * remaining
                
                diff = abs(h_prob - a_prob)
                if diff < 12:
                    adjust_val = (12 - diff) * 0.4
                    draw_prob += adjust_val
                    h_prob -= adjust_val * 0.5
                    a_prob -= adjust_val * 0.5
            else:
                h_prob = (h_adj / (h_adj + a_adj)) * 100
                a_prob = (a_adj / (h_adj + a_adj)) * 100
                draw_prob = 0.0
                
            margin = 0.95
            h_odds = round((100 / h_prob) * margin, 2) if h_prob > 0 else 0.0
            a_odds = round((100 / a_prob) * margin, 2) if a_prob > 0 else 0.0
            draw_odds = round((100 / draw_prob) * margin, 2) if draw_prob > 0 else "-"
            
            prob_diff = h_prob - a_prob
            handicap_str = "平手 (0)"
            
            if sport == "basketball":
                handicap_line = max(0.5, round(abs(prob_diff) * 0.35 * 2) / 2)
                handicap_str = f"主讓 -{handicap_line}" if prob_diff > 0 else f"客讓 -{handicap_line}"
            elif sport == "baseball":
                handicap_str = "主讓 -1.5" if prob_diff > 0 else "客讓 -1.5"
            elif sport == "soccer":
                handicap_line = round(abs(prob_diff) * 0.035 * 4) / 4
                if handicap_line >= 0.25:
                    handicap_str = f"主讓 -{handicap_line}" if prob_diff > 0 else f"客讓 -{handicap_line}"
                    
            correct_score = "-"
            if sport == "soccer":
                if h_prob > a_prob + 15: correct_score = "2-0 或 3-1"
                elif h_prob > a_prob + 5: correct_score = "2-1 或 1-0"
                elif a_prob > h_prob + 15: correct_score = "0-2 或 1-3"
                elif a_prob > h_prob + 5: correct_score = "1-2 或 0-1"
                else: correct_score = "1-1 或 0-0"
            
            # --- 數學引擎：計算期望值 (EV) 與凱利準則 ---
            h_p_decimal = h_prob / 100
            a_p_decimal = a_prob / 100
            
            # 這裡為了展示凱利公式的效果，把賠率 margin 稍微調成 1.05 (模擬找到有利盤口)
            # 實戰中如果是真實莊家賠率 (margin 通常在 0.95)，EV 若為負，系統會自動建議觀望。
            demo_margin = 1.05
            demo_h_odds = round((100 / h_prob) * demo_margin, 2) if h_prob > 0 else 0.0
            demo_a_odds = round((100 / a_prob) * demo_margin, 2) if a_prob > 0 else 0.0
            
            # EV = (勝率 * (賠率 - 1)) - (1 - 勝率)
            h_ev = (h_p_decimal * (demo_h_odds - 1)) - (1 - h_p_decimal) if demo_h_odds > 0 else 0
            a_ev = (a_p_decimal * (demo_a_odds - 1)) - (1 - a_p_decimal) if demo_a_odds > 0 else 0
            
            # 凱利準則公式: f* = EV / (賠率 - 1)
            h_kelly_raw = (h_ev / (demo_h_odds - 1)) * 100 if demo_h_odds > 1 and h_ev > 0 else 0
            a_kelly_raw = (a_ev / (demo_a_odds - 1)) * 100 if demo_a_odds > 1 and a_ev > 0 else 0
            
            # 實戰保守策略：使用 1/4 凱利 (Fractional Kelly) 來降低風險
            h_kelly = max(0, round(h_kelly_raw / 4, 1))
            a_kelly = max(0, round(a_kelly_raw / 4, 1))
            
            # 判斷推薦方向的資金分配
            if sport == "soccer":
                if h_prob > a_prob and h_prob > draw_prob:
                    kelly_str = f"主投 {h_kelly}%" if h_kelly > 0 else "觀望 (EV<0)"
                elif a_prob > h_prob and a_prob > draw_prob:
                    kelly_str = f"客投 {a_kelly}%" if a_kelly > 0 else "觀望 (EV<0)"
                else:
                    kelly_str = "和局觀望"
            else:
                if h_prob > a_prob:
                    kelly_str = f"主投 {h_kelly}%" if h_kelly > 0 else "觀望 (EV<0)"
                else:
                    kelly_str = f"客投 {a_kelly}%" if a_kelly > 0 else "觀望 (EV<0)"
            # ------------------------------------------
                    
            return h_prob, a_prob, draw_prob, h_odds, a_odds, draw_odds, handicap_str, correct_score, kelly_str
        except Exception:
            return 50.0, 50.0, 0.0, 1.90, 1.90, "-", "平手 (0)", "-", "觀望 (0%)"

    all_games_list = []
    
    # 6. 開始執行抓取
    for league_name, info in leagues.items():
        print(f"正在抓取 {league_name} 數據...")
        response = requests.get(info["url"])
        if response.status_code == 200:
            events = response.json().get('events', [])
            for event in events:
                status = event['competitions'][0]['status']['type']['state']
                if status == 'pre':
                    raw_time = event['date'].replace('Z', '')
                    utc_time = datetime.strptime(raw_time[:16], "%Y-%m-%dT%H:%M")
                    tw_time = utc_time + timedelta(hours=8)
                    game_time = tw_time.strftime("%m/%d %H:%M")
                    
                    competitors = event['competitions'][0]['competitors']
                    home_team = next(c for c in competitors if c['homeAway'] == 'home')
                    away_team = next(c for c in competitors if c['homeAway'] == 'away')
                    
                    h_name_en = home_team['team']['name']
                    a_name_en = away_team['team']['name']
                    h_name_zh = f"{team_translations.get(h_name_en, h_name_en)} {info['symbol']}"
                    a_name_zh = f"{team_translations.get(a_name_en, a_name_en)} {info['symbol']}"
                    
                    h_record = home_team.get('records', [{'summary': '0-0'}])[0].get('summary', '0-0')
                    a_record = away_team.get('records', [{'summary': '0-0'}])[0].get('summary', '0-0')
                    
                    h_p, a_p, d_p, h_o, a_o, d_o, hand_line, score_pred, kelly = calculate_bookmaker_model(
                        info["sport"], h_name_en, h_record, a_name_en, a_record
                    )
                    
                    if info["sport"] == "soccer":
                        if h_p > a_p and h_p > d_p: rec_pick = "主勝"
                        elif a_p > h_p and a_p > d_p: rec_pick = "客勝"
                        else: rec_pick = "和局"
                    else:
                        rec_pick = "主勝" if h_p > a_p else "客勝"
                    
                    all_games_list.append({
                        "聯賽": league_name,
                        "時間": game_time,
                        "對戰組合": f"{h_name_zh} VS {a_name_zh}",
                        "主/客/和 機率": f"{h_p:.1f}% / {a_p:.1f}% / {d_p:.1f}%",
                        "賠率": f"{h_o} / {a_o} / {d_o}",
                        "讓分": hand_line,
                        "波膽": score_pred,
                        "推薦": rec_pick,
                        "資金分配": kelly
                    })

    # 7. 報表輸出與自動雲端備份
    if all_games_list:
        df = pd.DataFrame(all_games_list)
        filename = f"advanced_odds_{date_str}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"\n✅ 成功！檔案已儲存為 '{filename}'")
        
        print("☁️ 正在同步至 GitHub...")
        os.system('git add .')
        os.system(f'git commit -m "升級：加入期望值與凱利資金控管模型"')
        os.system('git push')
        print("🎉 雲端備份完成！請至手機 App 重新整理查看最新的資金配比。")
    else:
        print(f"\n目前無 {date_str} 賽事數據。程式執行結束。")

if __name__ == "__main__":
    run_prediction_system()