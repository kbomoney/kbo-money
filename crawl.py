import json
import os
import time

def generate_kbo_data():
    print("=== KBO 연봉 및 선수 데이터 생성 시작 ===")

    # 1. 크롤링 실패 시에도 100% 작동하는 백업/주요 선수 기본 로스터 (손아섭 포함)
    base_players = [
        {"id": "1", "name": "손아섭", "team": "NC", "positionGroup": "외야수", "isCoach": False, "draftInfo": "2007 롯데 2차 2라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "NC 다이노스", "salary": "정식 계약", "note": "등번호 No.31"}]},
        {"id": "2", "name": "류현진", "team": "한화", "positionGroup": "투수", "isCoach": False, "draftInfo": "2006 한화 2차 1라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "한화 이글스", "salary": "정식 계약", "note": "등번호 No.99"}]},
        {"id": "3", "name": "김도영", "team": "KIA", "positionGroup": "내야수", "isCoach": False, "draftInfo": "2022 KIA 1차지명", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "KIA 타이거즈", "salary": "정식 계약", "note": "등번호 No.5"}]},
        {"id": "4", "name": "구자욱", "team": "삼성", "positionGroup": "외야수", "isCoach": False, "draftInfo": "2012 삼성 2라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "삼성 라이온즈", "salary": "정식 계약", "note": "등번호 No.5"}]},
        {"id": "5", "name": "홍창기", "team": "LG", "positionGroup": "외야수", "isCoach": False, "draftInfo": "2016 LG 2차 3라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "LG 트윈스", "salary": "정식 계약", "note": "등번호 No.51"}]},
        {"id": "6", "name": "양의지", "team": "두산", "positionGroup": "포수", "isCoach": False, "draftInfo": "2006 두산 2차 8라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "두산 베어스", "salary": "정식 계약", "note": "등번호 No.25"}]},
        {"id": "7", "name": "강백호", "team": "KT", "positionGroup": "포수/외야수", "isCoach": False, "draftInfo": "2018 KT 2차 1라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "KT 위즈", "salary": "정식 계약", "note": "등번호 No.50"}]},
        {"id": "8", "name": "최정", "team": "SSG", "positionGroup": "내야수", "isCoach": False, "draftInfo": "2005 SK 1차지명", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "SSG 랜더스", "salary": "정식 계약", "note": "등번호 No.14"}]},
        {"id": "9", "name": "전준우", "team": "롯데", "positionGroup": "내야수", "isCoach": False, "draftInfo": "2008 롯데 2차 2라운드", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "롯데 자이언츠", "salary": "정식 계약", "note": "등번호 No.8"}]},
        {"id": "10", "name": "이정후", "team": "키움", "positionGroup": "외야수", "isCoach": False, "draftInfo": "2017 키움 1차지명", "salary": "KBO 공시 연봉", "history": [{"period": "2026", "team": "키움 히어로즈", "salary": "정식 계약", "note": "공식 로스터"}]}
    ]

    crawled_players = []
import json
import os
import time
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def crawl_kbo_official_api():
    print("=== KBO 공식 백엔드 API 직접 수집 시작 ===")

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
        print(f"[{team_name}] 데이터 수집 중...")

        while True:
            # KBO 내부 데이터 조회 API
            api_url = "https://www.koreabaseball.com/ws/Main.wsgi/GetSearchPlayerList"
            
            payload = urlencode({
                'searchType': 'TEAM',
                'teamCode': team_code,
                'page': page
            }).encode('utf-8')

            # 차단 우회를 위한 KBO 헤더 설정
            req = Request(api_url, data=payload, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://www.koreabaseball.com/Player/Search.aspx'
            })

            try:
                with urlopen(req, timeout=10) as response:
                    res_body = response.read().decode('utf-8')
                    res_data = json.loads(res_body)

                # API 응답 내 행 데이터 파싱
                rows = res_data.get('rows', [])
                if not rows:
                    break

                for item in rows:
                    cols = item.get('row', [])
                    if len(cols) >= 4:
                        # HTML 태그 제거
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

                total_page = res_data.get('totalPage', 1)
                if page >= total_page:
                    break

                page += 1
                time.sleep(0.1)

            except Exception as e:
                print(f"[{team_name}] {page}페이지 API 수집 중 에러: {e}")
                break

    print(f"\n최종 수집 완료: 총 {len(all_players)}명 수집됨")

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print("data/players.json 저장 성공!")

if __name__ == "__main__":
    crawl_kbo_official_api()
    # 2. Selenium을 이용한 동적 동기화 시도
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        teams = ["HT", "SS", "LG", "OB", "KT", "SK", "LT", "HH", "NC", "WO"]
        pid = 11

        for t_code in teams:
            driver.get(f"https://www.koreabaseball.com/Player/Search.aspx?searchType=TEAM&teamCode={t_code}")
            time.sleep(1)
            
            rows = driver.find_elements(By.CSS_SELECTOR, '.tEx tbody tr')
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if len(cols) >= 4:
                    p_name = cols[1].text.strip()
                    p_team = cols[2].text.strip()
                    p_pos = cols[3].text.strip()
                    
                    if p_name and p_name != "선수명" and p_name != "손아섭": # 중복 방지
                        crawled_players.append({
                            "id": str(pid),
                            "name": p_name,
                            "team": p_team,
                            "positionGroup": p_pos,
                            "isCoach": "코치" in p_pos,
                            "draftInfo": "KBO 정식 등록",
                            "salary": "KBO 공시 연봉",
                            "history": [{"period": "현재", "team": p_team, "salary": "정식 계약", "note": "공식 로스터"}]
                        })
                        pid += 1
        driver.quit()
    except Exception as e:
        print(f"실시간 크롤링 경고 (기본 내장 데이터로 대체 적용): {e}")

    # 크롤링 성공 데이터와 기본 안전 데이터 합치기
    final_players = base_players + crawled_players
    print(f"최종 생성된 데이터 수: {len(final_players)}명")

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(final_players, f, ensure_ascii=False, indent=2)

    print("data/players.json 저장 정상 완료!")

if __name__ == "__main__":
    generate_kbo_data()
