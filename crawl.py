import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def crawl_kbo_official_all():
    print("KBO 공식 웹사이트 전 구단 선수/코치진 크롤링 시작...")

    # Headless Chrome 설정 (GitHub Actions 및 일반 환경 호환)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    
    # KBO 10개 구단 코드
    teams = [
        {"code": "HT", "name": "KIA"},
        {"code": "OB", "name": "두산"},
        {"code": "SS", "name": "삼성"},
        {"code": "LG", "name": "LG"},
        {"code": "KT", "name": "KT"},
        {"code": "SK", "name": "SSG"},
        {"code": "LT", "name": "롯데"},
        {"code": "NC", "name": "NC"},
        {"code": "HH", "name": "한화"},
        {"code": "WO", "name": "키움"}
    ]

    all_members = []
    member_id = 1

    try:
        for team in teams:
            team_code = team["code"]
            team_name = team["name"]
            print(f"[{team_name}] 전 명단 수집 중...")

            # KBO 공식 선수 등록 명단 URL
            url = f"https://www.koreabaseball.com/Player/RegisterAll.aspx?teamId={team_code}"
            driver.get(url)
            time.sleep(2) # 페이지 로딩 대기

            # 명단 테이블 파싱
            rows = driver.find_elements(By.CSS_SELECTOR, ".tData table tbody tr")

            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 4:
                    continue

                back_num = cols[0].text.strip()
                name = cols[1].text.strip()
                position = cols[2].text.strip()
                birth = cols[3].text.strip()

                if not name:
                    continue

                is_coach = "코치" in position or "감독" in position

                all_members.append({
                    "id": str(member_id),
                    "name": name,
                    "team": team_name,
                    "positionGroup": position,
                    "isCoach": is_coach,
                    "draftInfo": f"생년월일: {birth} / 등번호: {back_num}",
                    "history": [
                        {
                            "period": "현재",
                            "team": f"{team_name} 프로야구단",
                            "salary": "KBO 공식 등록",
                            "note": "정식 명단"
                        }
                    ]
                })
                member_id += 1

    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
    finally:
        driver.quit()

    # data/players.json 저장
    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_members, f, ensure_ascii=False, indent=2)

    print(f"수집 완료: 총 {len(all_members)}명의 전 구단 인원이 data/players.json에 저장되었습니다.")

if __name__ == "__main__":
    crawl_kbo_official_all()
