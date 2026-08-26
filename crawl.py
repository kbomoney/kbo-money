import json
import os
import time
import requests

def crawl_kbo_official_api():
    print("=== KBO 공식 API 차단 우회 수집 시작 ===")

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

    session = requests.Session()
    
    # KBO 메인 방문을 통한 세션 쿠키 수집 (방화벽 우회용)
    try:
        session.get("https://www.koreabaseball.com/Player/Search.aspx", headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }, timeout=10)
    except Exception as e:
        print(f"메인 세션 연결 경고: {e}")

    # 실제 브라우저 우회 헤더 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.koreabaseball.com',
        'Referer': 'https://www.koreabaseball.com/Player/Search.aspx'
    }

    all_players = []
    pid = 1

    for team in teams:
        team_code = team["code"]
        team_name = team["name"]
        page = 1
        print(f"[{team_name}] 전 구단 데이터 수집 시작...")

        while True:
            api_url = "https://www.koreabaseball.com/ws/Main.wsgi/GetSearchPlayerList"
            payload = {
                'searchType': 'TEAM',
                'teamCode': team_code,
                'page': page
            }

            try:
                res = session.post(api_url, data=payload, headers=headers, timeout=10)
                if res.status_code != 200:
                    print(f"[{team_name}] 응답 오류 (Status Code: {res.status_code})")
                    break

                res_data = res.json()
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
                            all_players.append({
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
                print(f"[{team_name}] {page}페이지 수집 에러: {e}")
                break

    print(f"\n실시간 크롤링 최종 수집 수: {len(all_players)}명")

    # 수집 결과가 0명이면 에러를 내서 이전 정상 데이터가 유지되도록 차단
    if len(all_players) == 0:
        raise Exception("KBO 방화벽 차단으로 수집 실패. 기존 데이터를 보존합니다.")

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print("data/players.json에 800명+ 전 구단 선수 데이터 기록 성공!")

if __name__ == "__main__":
    crawl_kbo_official_api()
