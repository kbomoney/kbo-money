import json
import os
import time
import requests
from bs4 import BeautifulSoup

def crawl_all_kbo_players():
    print("=== KBO 전체 등록선수 누락 없는 전수 조사 크롤링 시작 ===")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.koreabaseball.com/Player/Search.aspx'
    }

    # KBO 10개 구단 코드
    teams = ['KIA', '삼성', 'LG', '두산', 'KT', 'SSG', '롯데', '한화', 'NC', '키움']
    
    all_players = []
    seen_names = set() # 중복 수집 방지
    pid = 1

    # 1. KBO 공식 선수 검색/목록 요청 (페이지 이동 루프)
    for team in teams:
        print(f"[{team}] 구단 선수 데이터 수집 중...")
        page = 1
        
        while True:
            # KBO 선수 검색 URL (페이지네이션 파라미터 적용)
            url = f"https://www.koreabaseball.com/Player/Search.aspx?searchType=TEAM&teamCode={team}&page={page}"
            
            try:
                res = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                rows = soup.select('.tEx tbody tr')
                
                # 더 이상 불러올 데이터가 없으면 다음 구단으로 이동
                if not rows or "검색된 선수가 없습니다" in soup.text:
                    break

                has_new_data = False
                for row in rows:
                    cols = row.select('td')
                    if len(cols) >= 4:
                        back_num = cols[0].text.strip()
                        name = cols[1].text.strip()
                        position = cols[3].text.strip()

                        if not name:
                            continue

                        # 유일 키 생성 (구단 + 이름 + 포지션)
                        unique_key = f"{team}_{name}_{position}"
                        if unique_key in seen_names:
                            continue
                        
                        seen_names.add(unique_key)
                        has_new_data = True

                        # 선수 데이터 객체 생성
                        player_obj = {
                            "id": str(pid),
                            "name": name,
                            "team": team,
                            "positionGroup": position if position else "등록선수",
                            "isCoach": "코치" in position or "감독" in position,
                            "draftInfo": f"KBO 공식 등록 ({team})",
                            "salary": "공시 연봉 정보",
                            "history": [
                                {
                                    "period": "현재",
                                    "team": f"{team} 프로야구단",
                                    "salary": "정식 계약",
                                    "note": f"등번호 No.{back_num}" if back_num else "정식 로스터"
                                }
                            ]
                        }
                        
                        all_players.append(player_obj)
                        pid += 1

                # 페이지에 새로운 데이터가 없으면 마지막 페이지로 판단
                if not has_new_data:
                    break

                page += 1
                time.sleep(0.3) # 서버 차단 방지용 딜레이

            except Exception as e:
                print(f"[{team}] page {page} 수집 중 에러 발생: {e}")
                break

    print(f"총 {len(all_players)}명의 전체 선수 데이터 수집 완료!")

    # 2. JSON 파일로 저장
    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print("data/players.json에 파일 저장 성공!")

if __name__ == "__main__":
    crawl_all_kbo_players()
