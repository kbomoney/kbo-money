import json
import os
import re
import time
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def fetch_kbo_official_data():
    print("=== KBO 공식 API를 통한 전체 선수 수집 시작 ===")

    # KBO 공식 팀 코드 및 팀명 매핑
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
        print(f"[{team_name}] 데이터 수집 중...")

        while True:
            # KBO 내부 Search API 호출
            url = f"https://www.koreabaseball.com/ws/Main.wsgi/GetSearchPlayerList"
            params = urlencode({
                'searchType': 'TEAM',
                'teamCode': team_code,
                'page': page
            }).encode('utf-8')

            req = Request(url, data=params, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest'
            })

            try:
                with urlopen(req, timeout=10) as response:
                    res_json = json.loads(response.read().decode('utf-8'))

                rows = res_json.get('rows', [])
                if not rows:
                    break

                for item in rows:
                    # JSON 응답 항목 데이터 파싱
                    cols = item.get('row', [])
                    if len(cols) >= 4:
                        back_num = re.sub(r'<.*?>', '', str(cols[0])).strip()
                        name = re.sub(r'<.*?>', '', str(cols[1])).strip()
                        position = re.sub(r'<.*?>', '', str(cols[2])).strip()
                        draft = re.sub(r'<.*?>', '', str(cols[4])).strip() if len(cols) >= 5 else ""

                        if name:
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

                # 다음 페이지 확인
                total_page = res_json.get('totalPage', 1)
                if page >= total_page:
                    break

                page += 1
                time.sleep(0.1)

            except Exception as e:
                print(f"[{team_name}] {page}페이지 요청 실패: {e}")
                break

    print(f"\n수집 완료: 총 {len(all_players)}명의 선수 데이터가 정상 수집되었습니다.")

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print("data/players.json 저장 완료!")

if __name__ == "__main__":
    fetch_kbo_official_data()
