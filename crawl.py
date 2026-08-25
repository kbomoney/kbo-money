import requests
from bs4 import BeautifulSoup
import json
import os
import time

def crawl_all_kbo_players():
    print("KBO 10개 구단 전체 등록인원(약 800명) 수집을 시작합니다...")
    
    # KBO 공식 구단 코드 (10개 구단)
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
    
    # 보안 차단 회피용 브라우저 헤더
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.koreabaseball.com/"
    }

    all_players = []
    player_id = 1

    for team in teams:
        team_code = team["code"]
        team_name = team["name"]
        print(f"[{team_name} 타이거즈/라이온즈 등] 데이터 수집 중...")

        # KBO 공식 선수/코치진 목록 페이지 (전체 조회)
        url = f"https://www.koreabaseball.com/Player/Search.aspx?searchType=TEAM&teamCode={team_code}"
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                print(f"  - {team_name} 불러오기 실패 (상태 코드: {res.status_code})")
                continue

            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 선수단 테이블 파싱
            rows = soup.select('table.t_list tbody tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue

                back_num = cols[0].text.strip()
                name = cols[1].text.strip()
                position = cols[2].text.strip()
                birth = cols[3].text.strip()
                draft = cols[4].text.strip()

                is_coach = "코치" in position or "감독" in position
                
                # 포지션 그룹 세분화
                if is_coach:
                    pos_group = "감독/코치"
                elif "투" in position:
                    pos_group = "투수"
                elif "포" in position:
                    pos_group = "포수"
                elif "내" in position:
                    pos_group = "내야수"
                elif "외" in position:
                    pos_group = "외야수"
                else:
                    pos_group = "선수"

                all_players.append({
                    "id": str(player_id),
                    "name": name,
                    "team": team_name,
                    "positionGroup": pos_group,
                    "isCoach": is_coach,
                    "draftInfo": draft if draft else f"{team_name} 정식 등록",
                    "history": [
                        {
                            "period": "현재",
                            "team": f"{team_name} 야구단",
                            "salary": "KBO 정식 등록",
                            "note": f"등번호 No.{back_num}" if back_num else "공식 로스터"
                        }
                    ]
                })
                player_id += 1
                
        except Exception as e:
            print(f"  - {team_name} 수집 중 오류 발생: {e}")
            
        time.sleep(0.5) # 서버 부하 방지용 대기

    print(f"\n총 {len(all_players)}명의 KBO 전체 선수 및 코치진 수집 완료!")

    # data/players.json 단일 파일 저장
    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print("`data/players.json` 단일 파일에 최종 저장되었습니다.")

if __name__ == "__main__":
    crawl_all_kbo_players()
