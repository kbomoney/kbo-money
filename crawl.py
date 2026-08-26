import json
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def crawl_kbo_html(teams):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.koreabaseball.com/Player/Search.aspx'
    })

    players = []
    pid = 1

    for team in teams:
        team_code = team["code"]
        team_name = team["name"]
        page = 1

        while True:
            url = f"https://www.koreabaseball.com/Player/Search.aspx?searchType=TEAM&teamCode={team_code}&page={page}"
            try:
                res = session.get(url, timeout=5)
                if res.status_code != 200:
                    break

                soup = BeautifulSoup(res.text, 'html.parser')
                table = soup.select_one('table.tEx')
                if not table:
                    break

                rows = table.select('tbody tr')
                if not rows:
                    break

                added = 0
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        back_num = cols[0].get_text(strip=True)
                        name = cols[1].get_text(strip=True)
                        position = cols[3].get_text(strip=True)
                        draft = cols[4].get_text(strip=True) if len(cols) > 4 else ""

                        if name and name != "선수명" and "검색된" not in name:
                            is_coach = "코치" in position or "감독" in position
                            players.append({
                                "id": str(pid),
                                "name": name,
                                "team": team_name,
                                "positionGroup": position if position else "등록선수",
                                "isCoach": is_coach,
                                "draftInfo": draft if draft else f"{team_name} 정식 등록",
                                "salary": "KBO 공시 연봉",
                                "history": [{
                                    "period": "현재",
                                    "team": f"{team_name} 프로야구단",
                                    "salary": "정식 계약",
                                    "note": f"등번호 No.{back_num}" if back_num else "공식 로스터"
                                }]
                            })
                            pid += 1
                            added += 1

                if added == 0:
                    break

                page += 1
                time.sleep(0.1)

            except Exception:
                break

    return players

def crawl_kbo_api(teams):
    players = []
    pid = 1

    for team in teams:
        team_code = team["code"]
        team_name = team["name"]
        page = 1

        while True:
            api_url = "https://www.koreabaseball.com/ws/Main.wsgi/GetSearchPlayerList"
            payload = urlencode({'searchType': 'TEAM', 'teamCode': team_code, 'page': page}).encode('utf-8')
            req = Request(api_url, data=payload, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://www.koreabaseball.com/Player/Search.aspx'
            })

            try:
                with urlopen(req, timeout=5) as response:
                    res_data = json.loads(response.read().decode('utf-8'))

                rows = res_data.get('rows', [])
                if not rows:
                    break

                for item in rows:
                    cols = item.get('row', [])
                    if len(cols) >= 4:
                        back_num = cols[0].split('>')[-1].split('<')[0].strip() if '<' in str(cols[0]) else str(cols[0]).strip()
                        name = cols[1].split('>')[-1].split('<')[0].strip() if '<' in str(cols[1]) else str(cols[1]).strip()
                        position = cols[2].strip() if len(cols) > 2 else "등록선수"
                        draft = cols[4].strip() if len(cols) > 4 else f"{team_name} 정식 등록"

                        if name and name != "선수명":
                            is_coach = "코치" in position or "감독" in position
                            players.append({
                                "id": str(pid),
                                "name": name,
                                "team": team_name,
                                "positionGroup": position,
                                "isCoach": is_coach,
                                "draftInfo": draft if draft else f"{team_name} 정식 등록",
                                "salary": "KBO 공시 연봉",
                                "history": [{
                                    "period": "현재",
                                    "team": f"{team_name} 프로야구단",
                                    "salary": "정식 계약",
                                    "note": f"등번호 No.{back_num}" if back_num else "공식 로스터"
                                }]
                            })
                            pid += 1

                total_page = res_data.get('totalPage', 1)
                if page >= total_page:
                    break

                page += 1
                time.sleep(0.1)

            except Exception:
                break

    return players

def generate_fallback_players():
    # 해외 IP 차단 시 최소한 파일이 생성되도록 안전 장치 적용
    return [
        {"id": "1", "name": "손아섭", "team": "NC", "positionGroup": "외야수", "isCoach": False, "draftInfo": "2007 롯데 2차 2라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "NC 다이노스", "salary": "정식 계약", "note": "등번호 No.31"}]},
        {"id": "2", "name": "류현진", "team": "한화", "positionGroup": "투수", "isCoach": False, "draftInfo": "2006 한화 2차 1라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "한화 이글스", "salary": "정식 계약", "note": "등번호 No.99"}]},
        {"id": "3", "name": "김도영", "team": "KIA", "positionGroup": "내야수", "isCoach": False, "draftInfo": "2022 KIA 1차지명", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "KIA 타이거즈", "salary": "정식 계약", "note": "등번호 No.5"}]},
        {"id": "4", "name": "구자욱", "team": "삼성", "positionGroup": "외야수", "isCoach": False, "draftInfo": "2012 삼성 2라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "삼성 라이온즈", "salary": "정식 계약", "note": "등번호 No.5"}]},
        {"id": "5", "name": "홍창기", "team": "LG", "positionGroup": "외야수", "isCoach": False, "draftInfo": "2016 LG 2차 3라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "LG 트윈스", "salary": "정식 계약", "note": "등번호 No.51"}]}
    ]

def main():
    teams = [
        {"code": "HT", "name": "KIA"},
        {"code": "SS", "name": "삼성"},
        {"code": "LG", "name": "LG"},
        {"code": "OB", "name": "두산"},
        {"code": "KT", "name": "KT"},
        {"code": "SK", "name": "SSG"},
        {"code": "LT", "name": "롯데"},
        {"code": "HH", "name": "한화"},
        {"code": "NC", "name": "NC"},
        {"code": "WO", "name": "키움"}
    ]

    print("=== KBO 수집 프로세스 실행 ===")
    players = crawl_kbo_html(teams)

    if not players:
        print("HTML 수집 차단됨 -> API 파싱 시도")
        players = crawl_kbo_api(teams)

    if not players:
        print("경고: KBO 서버 차단으로 인해 기본 로스터 데이터로 안전 적용합니다.")
        players = generate_fallback_players()

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

    print(f"data/players.json 저장 성공! (총 {len(players)}명)")

if __name__ == "__main__":
    main()
