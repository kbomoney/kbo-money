import json
import os
import re
import time
from urllib.request import Request, build_opener, HTTPCookieProcessor
from urllib.parse import urlencode

def fetch_all_kbo_players():
    print("=== KBO 공식 로스터 완전 수집 시작 ===")

    # 쿠키 처리를 위한 opener 생성
    opener = build_opener(HTTPCookieProcessor())
    
    # 1. 초기 쿠키 세션 획득
    init_url = "https://www.koreabaseball.com/Player/Search.aspx"
    init_req = Request(init_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    try:
        opener.open(init_req)
    except Exception as e:
        print(f"초기 세션 연결 실패: {e}")

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

    all_players = []
    pid = 1

    for team in teams:
        team_code = team["code"]
        team_name = team["name"]
        page = 1
        print(f"[{team_name}] 데이터 크롤링 진행 중...")

        while True:
            # KBO 실제 검색 요청 주소
            url = f"https://www.koreabaseball.com/Player/Search.aspx?searchType=TEAM&teamCode={team_code}&page={page}"
            
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.koreabaseball.com/Player/Search.aspx',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            })

            try:
                with opener.open(req, timeout=15) as res:
                    html = res.read().decode('utf-8')

                # 선수 목록 테이블 행 파싱
                rows = re.findall(r'<tr>(.*?)</tr>', html, re.DOTALL)
                
                valid_rows = []
                for row in rows:
                    if 'cDetail' in row or 'Search.aspx' in row or 'href' in row:
                        valid_rows.append(row)

                if not valid_rows:
                    break

                added = 0
                for row in valid_rows:
                    cols = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)
                    if len(cols) >= 4:
                        clean = [re.sub(r'<.*?>', '', c).strip() for c in cols]
                        back_num = clean[0]
                        name = clean[1]
                        team_str = clean[2]
                        position = clean[3]
                        draft = clean[4] if len(clean) > 4 else ""

                        if name and name != "선수명":
                            is_coach = "코치" in position or "감독" in position
                            
                            all_players.append({
                                "id": str(pid),
                                "name": name,
                                "team": team_name,
                                "positionGroup": position if position else "등록선수",
                                "isCoach": is_coach,
                                "draftInfo": draft if draft else f"{team_name} 정식 등록",
                                "salary": "KBO 공시 연봉",
                                "history": [
                                    {
                                        "period": "현재",
                                        "team": f"{team_name} 프로야구단",
                                        "salary": "정식 계약",
                                        "note": f"등번호 No.{back_num}" if back_num else "공식 로스터"
                                    }
                                ]
                            })
                            pid += 1
                            added += 1

                if added == 0:
                    break

                page += 1
                time.sleep(0.3)

            except Exception as e:
                print(f"[{team_name}] {page}페이지 파싱 중 오류: {e}")
                break

    print(f"\n최종 수집 인원: {len(all_players)}명")

    # 결과 저장
    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fetch_all_kbo_players()
