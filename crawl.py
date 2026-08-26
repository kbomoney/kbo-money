import json
import os
import re
import time
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def crawl_kbo_all():
    print("=== KBO 전 구단 무제한 실시간 수집 시작 ===")
    
    # KBO 공식 팀 코드
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
        print(f"[{team_name}] 전체 로스터 수집 중...")

        while True:
            url = f"https://www.koreabaseball.com/Player/Search.aspx?searchType=TEAM&teamCode={team_code}&page={page}"
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            try:
                with urlopen(req, timeout=10) as response:
                    html = response.read().decode('utf-8')

                # 테이블 tr 추출 (정규식 기반)
                rows = re.findall(r'<tr>(.*?)</tr>', html, re.DOTALL)
                
                # 데이터가 없는 경우 종료
                if not rows or "검색된 선수가 없습니다" in html:
                    break

                found_count = 0
                for row in rows:
                    cols = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)
                    if len(cols) >= 5:
                        # 태그 제거
                        clean_cols = [re.sub(r'<.*?>', '', c).strip() for c in cols]
                        back_num = clean_cols[0]
                        name = clean_cols[1]
                        position = clean_cols[2]
                        draft = clean_cols[4]

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
                                        "team": f"{team_name} 야구단",
                                        "salary": "정식 계약",
                                        "note": f"등번호 No.{back_num}" if back_num else "공식 로스터"
                                    }
                                ]
                            })
                            pid += 1
                            found_count += 1

                if found_count == 0:
                    break

                page += 1
                time.sleep(0.2)

            except Exception as e:
                print(f"[{team_name}] {page}페이지 처리 중 오류: {e}")
                break

    print(f"\n 수집 완료! 총 {len(all_players)}명의 전체 인원이 수집되었습니다.")

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print("data/players.json 저장 완")

if __name__ == "__main__":
    crawl_kbo_all()
