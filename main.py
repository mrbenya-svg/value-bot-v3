import os
import math
import requests
import threading
import time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from flask import Flask
import telebot

# ================================
# 0. ВЕБ-СЕРВЕР ДЛЯ RENDER ТА KEEP-ALIVE
# ================================
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Value Stats Bot 3 is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

def keep_alive():
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "https://value-bot-v3.onrender.com")
    time.sleep(15)
    while True:
        try:
            response = requests.get(render_url, timeout=10)
            print(f"⏰ [Keep-Alive] External ping sent. Status: {response.status_code}")
        except Exception as e:
            print(f"⚠️ [Keep-Alive] External ping error: {e}")
        time.sleep(600)

threading.Thread(target=keep_alive, daemon=True).start()

# ================================
# 1. КОНФІГУРАЦІЯ ТА РОЗШИРЕНИЙ СПИСОК ЛІГ
# ================================
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
MAX_HOURS_AHEAD = 24

LEAGUES_MAP = {
    "soccer_austria_bundesliga": "Австрія: Бундесліга",
    "soccer_austria_2_liga": "Австрія: 2 ліга",
    "soccer_algeria_ligue_1": "Алжир: Дивізіон 1",
    "soccer_england_championship": "Англія: Чемпіоншип",
    "soccer_england_league1": "Англія: Перша ліга",
    "soccer_england_league2": "Англія: Друга ліга",
    "soccer_england_national_league": "Англія: Національна ліга",
    "soccer_argentina_primera_division": "Аргентина: Прімера",
    "soccer_argentina_primera_b": "Аргентина: Прімера Б Насьональ",
    "soccer_belgium_first_div": "Бельгія: Про-ліга",
    "soccer_brazil_campeonato": "Бразилія: Серія А",
    "soccer_brazil_serie_b": "Бразилія: Серія Б",
    "soccer_brazil_serie_c": "Бразилія: Серія C",
    "soccer_denmark_superliga": "Данія: Суперліга",
    "soccer_denmark_1st_division": "Данія: 1-й дивізіон",
    "soccer_israel_premier_league": "Ізраїль: Прем'єр-ліга",
    "soccer_israel_liga_leumit": "Ізраїль: Ліга Леуміт",
    "soccer_spain_la_liga": "Іспанія: Ла Ліга",
    "soccer_spain_segunda_division": "Іспанія: Сегунда",
    "soccer_italy_serie_a": "Італія: Серія А",
    "soccer_italy_serie_b": "Італія: Серія Б",
    "soccer_italy_serie_c": "Італія: Серія C",
    "soccer_kazakhstan_premier_league": "Казахстан: Прем'єр-ліга",
    "soccer_morocco_pro_league": "Марокко: Ботола Про",
    "soccer_germany_bundesliga": "Німеччина: Бундесліга",
    "soccer_germany_bundesliga2": "Німеччина: Друга Бундесліга",
    "soccer_germany_3_liga": "Німеччина: 3-тя Ліга",
    "soccer_netherlands_eredivisie": "Нідерланди: Ередивізі",
    "soccer_netherlands_eerste_divisie": "Нідерланди: Еесте Дивізі",
    "soccer_norway_eliteserien": "Норвегія: Елітсеріен",
    "soccer_norway_first_div": "Норвегія: ОБОС-ліга",
    "soccer_paraguay_primera_division": "Парагвай: Прімера",
    "soccer_paraguay_division_intermedia": "Парагвай: Дивізіон Інтермедіа",
    "soccer_poland_ekstraklasa": "Польща: Екстракляса",
    "soccer_poland_i_liga": "Польща: Дивізіон 1",
    "soccer_portugal_primeira_liga": "Португалія: Прімейра",
    "soccer_portugal_segunda_liga": "Португалія: 2 ліга",
    "soccer_saudi_arabia_pro_league": "Саудівська Аравія: Професійна ліга",
    "soccer_slovakia_super_liga": "Словаччина: Перша ліга",
    "soccer_slovakia_2_liga": "Словаччина: Друга ліга",
    "soccer_usa_mls": "США: МЛС",
    "soccer_turkey_super_league": "Туреччина: Суперліга",
    "soccer_hungary_nb_i": "Угорщина: НБ 1",
    "soccer_hungary_nb_ii": "Угорщина: НБ 2",
    "soccer_uruguay_segunda_division": "Уругвай: Сегунда",
    "soccer_france_ligue_one": "Франція: Ліга 1",
    "soccer_france_ligue_two": "Франція: Ліга 2",
    "soccer_france_national": "Франція: Ліга 3 (Насьональ)",
    "soccer_czech_republic_first_league": "Чехія: Перша ліга",
    "soccer_czech_republic_2_liga": "Чехія: Дивізіон 2",
    "soccer_chile_camp_nacional": "Чилі: Прімера",
    "soccer_sweden_allsvenskan": "Швеція: Аллсвенскан",
    "soccer_sweden_superettan": "Швеція: Супереттан",
    "soccer_switzerland_superleague": "Швейцарія: Суперліга",
    "soccer_scotland_premier_league": "Шотландія: Прем'єр-ліга",
    "soccer_scotland_championship": "Шотландія: Чемпіоншип",
    "soccer_korea_k_league_1": "Південна Корея: К-Ліга 1",
    "soccer_korea_k_league_2": "Південна Корея: К-Ліга 2",
    "soccer_japan_j_league": "Японія: Джей-ліга",
}

def format_match_date(iso_time_str: str) -> str:
    try:
        dt_utc = datetime.fromisoformat(iso_time_str.replace("Z", "+00:00"))
        dt_kyiv = dt_utc.astimezone(ZoneInfo("Europe/Kyiv"))
        return dt_kyiv.strftime("%d.%m.%Y")
    except Exception:
        return "Дата невідома"

# ================================
# 3. СКАНЕР ТА ФІЛЬТРАЦІЯ ЗА КРИТЕРІЯМИ
# ================================
def run_scan_and_notify(chat_id):
    bot.send_message(chat_id, f"🔎 <b>Запуск статистики Бота 3 ({len(LEAGUES_MAP)} ліг)...</b>", parse_mode="HTML")
    
    valuable_matches = []
    now_utc = datetime.now(timezone.utc)

    for odds_league_key, league_title in LEAGUES_MAP.items():
        try:
            # Запит коефіцієнтів та майбутніх подій
            res_raw = requests.get(
                f"https://api.the-odds-api.com/v4/sports/{odds_league_key}/odds/",
                params={'apiKey': ODDS_API_KEY, 'regions': 'eu', 'markets': 'h2h'},
                timeout=10
            )
            if res_raw.status_code != 200:
                continue
            odds_res = res_raw.json()

            # Запит історичних/поточних результатів для побудови таблиці та статистики команд
            scores_raw = requests.get(
                f"https://api.the-odds-api.com/v4/sports/{odds_league_key}/scores/",
                params={'apiKey': ODDS_API_KEY, 'daysFrom': 30},
                timeout=10
            )
            scores_res = scores_raw.json() if scores_raw.status_code == 200 else []
        except Exception as e:
            continue

        if not isinstance(odds_res, list) or not odds_res:
            continue

        # Збираємо статистику команд на основі зіграних матчів у scores
        team_stats = {} # форма, матчі вдома/на виїзді, голи тощо
        standings = {}  # очки та місця в таблиці

        def init_team(team):
            if team not in team_stats:
                team_stats[team] = {
                    'home_matches': 0, 'home_wins': 0, 'home_draws': 0, 'home_losses': 0,
                    'home_gf': 0, 'home_ga': 0, 'home_clean_sheets': 0,
                    'away_matches': 0, 'away_wins': 0, 'away_draws': 0, 'away_losses': 0,
                    'away_gf': 0, 'away_ga': 0, 'all_recent': [] # список результатів (win/draw/loss) для форми
                }
            if team not in standings:
                standings[team] = {'points': 0, 'played': 0}

        for match in scores_res:
            if not match.get('completed', False):
                continue
            h_team = match['home_team']
            a_team = match['away_team']
            scores = match.get('scores', [])
            if len(scores) != 2:
                continue
            
            h_score = int(scores[0]['score']) if scores[0]['name'] == h_team else int(scores[1]['score'])
            a_score = int(scores[1]['score']) if scores[1]['name'] == a_team else int(scores[1]['score']) if scores[0]['name'] == a_team else 0
            # уточнення рахунку за іменами
            for s in scores:
                if s['name'] == h_team: h_score = int(s['score'])
                if s['name'] == a_team: a_score = int(s['score'])

            init_team(h_team)
            init_team(a_team)

            # Оновлюємо домашню статистику господарів
            ts_h = team_stats[h_team]
            ts_h['home_matches'] += 1
            ts_h['home_gf'] += h_score
            ts_h['home_ga'] += a_score
            if a_score == 0:
                ts_h['home_clean_sheets'] += 1

            # Оновлюємо гостьову статистику гостей
            ts_a = team_stats[a_team]
            ts_a['away_matches'] += 1
            ts_a['away_gf'] += a_score
            ts_a['away_ga'] += h_score

            if h_score > a_score:
                ts_h['home_wins'] += 1
                ts_a['away_losses'] += 1
                standings[h_team]['points'] += 3
                ts_h['all_recent'].append('W')
                ts_a['all_recent'].append('L')
            elif h_score == a_score:
                ts_h['home_draws'] += 1
                ts_a['away_draws'] += 1
                standings[h_team]['points'] += 1
                standings[a_team]['points'] += 1
                ts_h['all_recent'].append('D')
                ts_a['all_recent'].append('D')
            else:
                ts_h['home_losses'] += 1
                ts_a['away_wins'] += 1
                standings[a_team]['points'] += 3
                ts_h['all_recent'].append('L')
                ts_a['all_recent'].append('W')

            standings[h_team]['played'] += 1
            standings[a_team]['played'] += 1

        # Визначаємо позиції в таблиці (сортування за очками)
        sorted_standings = sorted(standings.keys(), key=lambda t: standings[t]['points'], reverse=True)
        positions = {team: idx + 1 for idx, team in enumerate(sorted_standings)}

        # Скануємо майбутні матчі
        for match in odds_res:
            commence_str = match.get('commence_time', '')
            match_dt = None
            if commence_str:
                try:
                    match_dt = datetime.fromisoformat(commence_str.replace("Z", "+00:00"))
                    if match_dt <= now_utc or match_dt - now_utc > timedelta(hours=MAX_HOURS_AHEAD):
                        continue
                except Exception:
                    pass
            if not match_dt:
                continue

            home_team = match['home_team']
            away_team = match['away_team']

            if home_team not in positions or away_team not in positions:
                continue

            # 1. Критерій позицій: господарі вище гостей мінімум на 6 місць
            pos_h = positions[home_team]
            pos_a = positions[away_team]
            pos_diff = pos_a - pos_h # якщо господар 4, а гость 10, то 10 - 4 = 6
            if pos_diff < 6:
                continue

            # Знаходимо максимальний кф на П1 у букмекерів
            max_h_odds = 0.0
            for bm in match.get('bookmakers', []):
                for market in bm.get('markets', []):
                    if market['key'] == 'h2h':
                        for outcome in market.get('outcomes', []):
                            if outcome['name'] == home_team:
                                if outcome['price'] > max_h_odds:
                                    max_h_odds = outcome['price']

            # 2. Критерій коефіцієнта на господарів > 1.5
            if max_h_odds < 1.50:
                continue

            # Перевіряємо наявність достатньої статистики команд
            if home_team not in team_stats or away_team not in team_stats:
                continue

            ts_h = team_stats[home_team]
            ts_a = team_stats[away_team]

            if ts_h['home_matches'] < 3 or ts_a['away_matches'] < 3:
                continue

            # 3. Фільтри гостей (на виїзді):
            # - Домашні матчі гостей (усі матчі вдома) >= 69% ((перемога+нічия)/к-ть матчів вдома)
            # Примітка: використовуємо гостьові або загальні показники згідно з формулою
            home_matches_a = ts_a['home_matches']
            if home_matches_a > 0:
                home_not_loss_a = (ts_a['home_wins'] + ts_a['home_draws']) / home_matches_a
                if home_not_loss_a < 0.69:
                    continue
            else:
                continue

            # - Виїзні матчі гостей >= 60% ((нічия+поразка)/к-ть матчів на виїзді)
            away_matches_a = ts_a['away_matches']
            if away_matches_a > 0:
                away_non_win_a = (ts_a['away_draws'] + ts_a['away_losses']) / away_matches_a
                if away_non_win_a < 0.60:
                    continue

                # - Виїзні поразки гостей <= 35% (поразка/к-ть матчів на виїзді)
                away_loss_rate_a = ts_a['away_losses'] / away_matches_a
                if away_loss_rate_a > 0.35:
                    continue
            else:
                continue

            # 4. Фільтри господарів:
            # - CS команди господарів в домашніх матчах мінімум 20%
            cs_rate_h = ts_h['home_clean_sheets'] / ts_h['home_matches']
            if cs_rate_h < 0.20:
                continue

            # - Форма господарів мінімум 60% (останні 5 матчів з усіх, 3+ не програшні = 60%)
            recent_h = ts_h['all_recent'][-5:]
            if len(recent_h) < 5:
                continue
            not_losses_h = sum(1 for res in recent_h if res in ['W', 'D'])
            form_pct_h = (not_losses_h / 5.0) * 100
            if form_pct_h < 60.0:
                continue

            # Розрахунок додаткових параметрів для рядка
            form_points_h = sum(3 if r == 'W' else (1 if r == 'D' else 0) for r in recent_h)
            
            recent_a = ts_a['all_recent'][-5:]
            form_points_a = sum(3 if r == 'W' else (1 if r == 'D' else 0) for r in recent_a) if recent_a else 0
            form_pct_a = (sum(1 for r in recent_a if r in ['W', 'D']) / 5.0) * 100 if len(recent_a) >= 5 else 0

            pts_diff = standings[home_team]['points'] - standings[away_team]['points']

            # Формуємо рядок табуляції (TSV) для ідеального копіювання в Excel
            tsv_row_data = [
                format_match_date(commence_str),
                str(ts_h['home_matches']),
                str(ts_h['home_wins']),
                str(ts_h['home_draws']),
                str(ts_h['home_losses']),
                str(ts_h['home_gf']),
                str(ts_h['home_ga']),
                f"{int(form_pct_h)}%",
                str(form_points_h),
                str(ts_h['home_clean_sheets']),
                str(ts_a['away_matches']),
                str(ts_a['away_wins']),
                str(ts_a['away_draws']),
                str(ts_a['away_losses']),
                str(ts_a['away_gf']),
                str(ts_a['away_ga']),
                f"{int(form_pct_a)}%",
                str(form_points_a),
                str(pts_diff),
                str(pos_diff)
            ]

            tsv_string = "\t".join(tsv_row_data)

            msg = (
                f"🎯 <b>СТАТИСТИЧНИЙ ЗНАХІДКА (Бот 3)</b>\n"
                f"⚽️ <b>Матч:</b> {home_team} vs {away_team}\n"
                f"🏆 <b>Ліга:</b> {league_title}\n"
                f"📈 <b>Макс. кф П1:</b> {max_h_odds}\n\n"
                f"📋 <b>Рядок для Excel (скопіюйте нижче):</b>\n"
                f"<code>{tsv_string}</code>"
            )
            valuable_matches.append({'match_time': match_dt, 'msg': msg})

    if not valuable_matches:
        bot.send_message(chat_id, "🏁 Сканування завершено. Жодного матчу за цими жорсткими критеріями не знайдено.")
    else:
        for item in valuable_matches:
            bot.send_message(chat_id, item['msg'], parse_mode="HTML")
        bot.send_message(chat_id, f"✅ Завершено. Знайдено матчів: {len(valuable_matches)}")

# ================================
# 4. TELEGRAM HANDLERS
# ================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Бот 3 (Статистика та TSV) готовий.\nНадішли 'скан' або /scan для запуску.")

@bot.message_handler(func=lambda message: message.text.lower() in ['скан', '/scan'])
def handle_scan(message):
    run_scan_and_notify(message.chat.id)

if __name__ == "__main__":
    print("🤖 Бот 3 заведено і чекає на команди...")
    bot.remove_webhook()
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
