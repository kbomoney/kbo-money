import json
import os
import time
import requests
from bs4 import BeautifulSoup

def crawl_kbo_unlimited():
    print("=== KBO 인원 제한 없는 전체 로스터 수집 시작 ===")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.koreabaseball.com/Player/Search.aspx'
    }

    # KBO 10개 구단 공식 코드
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
        print(f"[{team_name}] 전체 명단 수집 중...")

        while True:
            # 인원 제한 없이 끝 페이지까지 요청
            url = f"https://www.koreabaseball.com/Player/Search.aspx?searchType=TEAM&teamCode={team_code}&page={page}"
            
            try:
                res = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                rows = soup.select('table.t_list tbody tr')
                
                # 데이터가 없거나 마지막 페이지를 넘어가면 해당 구단 수집 종료
                if not rows or "검색된 선수가 없습니다" in soup.text:
                    break

                added_in_page = 0
                for row in rows:
                    cols = row.select('td')
                    if len(cols) < 5:
                        continue

                    back_num = cols[0].text.strip()
                    name = cols[1].text.strip()
                    position = cols[2].text.strip()
                    draft = cols[4].text.strip()

                    if not name:
                        continue

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
                                "team": f"{team_name} 야구단",
                                "salary": "정식 계약",
                                "note": f"등번호 No.{back_num}" if back_num else "공식 로스터"
                            }
                        ]
                    })
                    pid += 1
                    added_in_page += 1

                # 해당 페이지에 추가된 선수가 없으면 다음 구단으로 이동
                if added_in_page == 0:
                    break

                page += 1
                time.sleep(0.3) # 서버 부하 방지

            except Exception as e:
                print(f"[{team_name}] {page}페이지 수집 중 에러: {e}")
                break

    print(f"\n 수집 완료! 총 {len(all_players)}명의 KBO 전체 인원이 수집되었습니다.")

    # 저장
    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print("`data/players.json`에 저장 성공!")

if __name__ == "__main__":
    crawl_kbo_unlimited()
