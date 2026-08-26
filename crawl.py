import json
import os
import time
import requests
from bs4 import BeautifulSoup

def crawl_kbo_all_players():
    print("=== [KBO API] 전 구단 선수 데이터 수집 시작 ===")

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
    
    # 1. KBO 검색 메인 페이지 접속으로 Cookie 및 Session 활성화
    base_url = "https://www.koreabaseball.com/Player/Search.aspx"
    headers_init = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    try:
        session.get(base_url, headers=headers_init, timeout=10)
    except Exception as e:
        print(f"초기 세션 접속 경고: {e}")

    # 2. AJAX 요청 헤더 설정
    api_url = "https://www.koreabaseball.com/ws/Main.wsgi/GetSearchPlayerList"
    api_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.koreabaseball.com',
        'Referer': base_url
    }

    players = []
    pid = 1

    # 3. 구단별 페이지 순회 수집
    for team in teams:
        team_code = team["code"]
        team_name = team["name"]
        page = 1
        print(f"[{team_name}] 명단 파싱 중...")

        while True:
            payload = {
                'searchType': 'TEAM',
                'teamCode': team_code,
                'page': page
            }

            try:
                res = session.post(api_url, data=payload, headers=api_headers, timeout=10)
                if res.status_code != 200:
                    print(f"[{team_name}] 응답 에러 (Status Code: {res.status_code})")
                    break

                res_data = res.json()
                rows = res_data.get('rows', [])
                if not rows:
                    break

                for item in rows:
                    cols = item.get('row', [])
                    if len(cols) >= 4:
                        # HTML 태그 제거 및 데이터 추출
                        back_num = BeautifulSoup(str(cols[0]), 'html.parser').get_text(strip=True)
                        name = BeautifulSoup(str(cols[1]), 'html.parser').get_text(strip=True)
                        position = str(cols[2]).strip() if len(cols) > 2 else "등록선수"
                        draft = str(cols[4]).strip() if len(cols) > 4 else f"{team_name} 정식 등록"

                        if name and name != "선수명":
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

                total_page = res_data.get('totalPage', 1)
                if page >= total_page:
                    break

                page += 1
                time.sleep(0.1)

            except Exception as e:
                print(f"[{team_name}] {page}페이지 수집 실패: {e}")
                break

    print(f"\n최종 수집 선수 수: {len(players)}명")

    # 수집 결과가 유효한지 검증 (0명 수집 시 에러 발생)
    if len(players) == 0:
        raise Exception("KBO 수집 실패: 응답이 차단되었거나 데이터를 가져오지 못했습니다.")

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

    print("data/players.json 저장 성공!")

if __name__ == "__main__":
    crawl_kbo_all_players()
