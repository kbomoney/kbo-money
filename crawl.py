import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def crawl_kbo_html(teams):
    print("=== [1차 시도] KBO 웹사이트 HTML 파싱 시작 ===")
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
                res = session.get(url, timeout=10)
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

            except Exception as e:
                print(f"[{team_name}] HTML 수집 중 에러: {e}")
                break

    return players

def crawl_kbo_api(teams):
    print("=== [2차 시도] KBO 백엔드 API 수집 시작 ===")
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
                with urlopen(req, timeout=10) as response:
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

            except Exception as e:
                print(f"[{team_name}] API 수집 중 에러: {e}")
                break

    return players

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

    # 1. HTML 직접 수집
    players = crawl_kbo_html(teams)

    # 2. 실패 시 API 수집 시도
    if not players:
        print("HTML 수집 실패. API 수집 방식으로 전환합니다.")
        players = crawl_kbo_api(teams)

    print(f"\n최종 수집 결과: 총 {len(players)}명 수집 완료")

    if not players:
        raise Exception("크롤링 데이터 수집에 전면 실패했습니다. KBO 차단 상태를 확인해주세요.")

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

    print("data/players.json 정상 기록 완료!")

if __name__ == "__main__":
    main()
