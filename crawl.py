import json
import os
import time
import requests
from bs4 import BeautifulSoup

def crawl_kbo_all_members():
    print("KBO 전 구단 선수 및 코치진 데이터 수집을 시작합니다...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 10개 구단 코드 (KBO / 포털 표준)
    team_codes = ["HT", "OB", "LT", "SS", "SK", "NC", "HH", "KT", "WO", "LG"]
    team_names = {
        "HT": "KIA", "OB": "두산", "LT": "롯데", "SS": "삼성", "SK": "SSG",
        "NC": "NC", "HH": "한화", "KT": "KT", "WO": "키움", "LG": "LG"
    }

    all_members = []
    member_id = 1

    for code in team_codes:
        team_label = team_names.get(code, code)
        print(f"[{team_label} 베어스/자이언츠 등] 구단 데이터 수집 중...")
        
        # Statiz 또는 야구 포털의 구단별 선수/코치진 명단 페이지
        list_url = f"https://statiz.co.kr/player.php?m=list&team={code}"
        
        try:
            res = requests.get(list_url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.select("table tr")

            for row in rows:
                cols = row.select("td")
                if len(cols) < 3:
                    continue

                name = cols[0].text.strip()
                pos = cols[1].text.strip()
                
                if not name or name == "선수명":
                    continue

                # 코치 여부 판별
                is_coach = "코치" in pos or "감독" in pos

                # 선수 상세 연봉 페이지 추적 (상세 링크가 있는 경우)
                detail_link = cols[0].find("a")
                history = []
                draft_info = "-"

                if detail_link and "href" in detail_link.attrs:
                    player_url = "https://statiz.co.kr/" + detail_link["href"]
                    try:
                        p_res = requests.get(player_url, headers=headers, timeout=5)
                        p_soup = BeautifulSoup(p_res.text, "html.parser")
                        
                        # 연봉 및 구단 이력 테이블 파싱
                        salary_rows = p_soup.select(".salary_table tr, table.table_type01 tr")
                        for s_row in salary_rows:
                            s_cols = s_row.select("td")
                            if len(s_cols) >= 3:
                                year_period = s_cols[0].text.strip()
                                p_team = s_cols[1].text.strip()
                                p_salary = s_cols[2].text.strip()
                                note = s_cols[3].text.strip() if len(s_cols) > 3 else ""

                                if year_period.isdigit() or "~" in year_period:
                                    history.append({
                                        "period": year_period,
                                        "team": p_team,
                                        "salary": p_salary,
                                        "note": note
                                    })
                        time.sleep(0.2) # 서버 부하 방지
                    except Exception as e:
                        pass

                # 연봉 이력이 비어있을 경우 기본 구조 생성
                if not history:
                    history.append({
                        "period": "현재",
                        "team": team_label,
                        "salary": "정보 업데이트 예정",
                        "note": "기본 등록"
                    })

                all_members.append({
                    "id": str(member_id),
                    "name": name,
                    "team": team_label,
                    "positionGroup": pos,
                    "isCoach": is_coach,
                    "draftInfo": draft_info,
                    "history": history
                })
                member_id += 1

        except Exception as e:
            print(f"{team_label} 수집 중 오류 발생:", e)

    # data/players.json 저장
    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_members, f, ensure_ascii=False, indent=2)

    print(f"작업 완료: 총 {len(all_members)}명의 선수/코치진 및 연봉 이력이 data/players.json에 저장되었습니다.")

if __name__ == "__main__":
    crawl_kbo_all_members()
