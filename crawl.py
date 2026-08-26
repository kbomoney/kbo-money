import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_all_kbo_with_selenium():
    print("=== Selenium 브라우저 기반 KBO 전체 수집 시작 ===")

    # 브라우저 옵션 설정 (헤드리스 모드)
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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

    try:
        for team in teams:
            team_code = team["code"]
            team_name = team["name"]
            page = 1
            print(f"[{team_name}] 브라우저 수집 진행 중...")

            while True:
                url = f"https://www.koreabaseball.com/Player/Search.aspx?searchType=TEAM&teamCode={team_code}&page={page}"
                driver.get(url)
                time.sleep(1.5) # 브라우저 로딩 대기

                # 선수 목록 테이블 파싱
                rows = driver.find_elements(By.CSS_SELECTOR, '.tEx tbody tr')
                
                if not rows or "검색된 선수가 없습니다" in driver.page_source:
                    break

                added = 0
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, 'td')
                    if len(cols) >= 4:
                        back_num = cols[0].text.strip()
                        name = cols[1].text.strip()
                        team_str = cols[2].text.strip()
                        position = cols[3].text.strip()
                        draft = cols[4].text.strip() if len(cols) > 4 else ""

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

    finally:
        driver.quit()

    print(f"\n최종 수집 완료: 총 {len(all_players)}명 수집됨")

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print("data/players.json 저장 성공!")

if __name__ == "__main__":
    fetch_all_kbo_with_selenium()
