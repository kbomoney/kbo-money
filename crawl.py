import json
import os
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def crawl_kbo_with_browser():
    print("=== [Playwright] 브라우저 우회 기반 KBO 실시간 수집 시작 ===")

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

    players = []
    pid = 1

    with sync_playwright() as p:
        # 헤드리스 크롬 브라우저 실행
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()

        # 1. KBO 메인 페이지 접속으로 방화벽 인증 통과
        print("KBO 세션 접속 중...")
        try:
            page.goto("https://www.koreabaseball.com/Player/Search.aspx", wait_until="networkidle", timeout=30000)
            time.sleep(2)
        except Exception as e:
            print(f"페이지 접속 초기화 오류: {e}")

        # 2. 구단별 AJAX API 직접 호출
        for team in teams:
            team_code = team["code"]
            team_name = team["name"]
            curr_page = 1
            print(f"[{team_name}] 실시간 명단 파싱 시작...")

            while True:
                # 브라우저 콘솔 내에서 fetch 실행하여 방화벽 우회
                fetch_script = f"""
                async () => {{
                    const response = await fetch('https://www.koreabaseball.com/ws/Main.wsgi/GetSearchPlayerList', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                            'X-Requested-With': 'XMLHttpRequest'
                        }},
                        body: 'searchType=TEAM&teamCode={team_code}&page={curr_page}'
                    }});
                    return await response.json();
                }}
                """
                try:
                    res_data = page.evaluate(fetch_script)
                    rows = res_data.get('rows', [])
                    if not rows:
                        break

                    for item in rows:
                        cols = item.get('row', [])
                        if len(cols) >= 4:
                            back_num = BeautifulSoup(str(cols[0]), 'html.parser').get_text(strip=True)
                            name = BeautifulSoup(str(cols[1]), 'html.parser').get_text(strip=True)
                            position = str(cols[2]).strip() if len(cols) > 2 else "등록선수"
                            draft = str(cols[4]).strip() if len(cols) > 4 else f"{team_name} 정식 등록"

                            if name and name != "선수명":
                                is_coach = "코치" in position or "감독" in position
                                players.append({
                                    "id": str(pid),
                                    "name": name,
                                    "team": team_name,
                                    "positionGroup": position if position else "등록선수",
                                    "isCoach": is_coach,
                                    "draftInfo": draft if draft else f"{team_name} 정식 등록",
                                    "salary": "KBO 공시 연봉",
                                    "history": [{
                                        "period": "현재",
                                        "team": f"{team_name} 프로야구단",
                                        "salary": "정식 계약",
                                        "note": f"등번호 No.{back_num}" if back_num else "공식 로스터"
                                    }]
                                })
                                pid += 1

                    total_page = res_data.get('totalPage', 1)
                    if curr_page >= total_page:
                        break

                    curr_page += 1
                    time.sleep(0.1)

                except Exception as e:
                    print(f"[{team_name}] {curr_page}페이지 수집 실패: {e}")
                    break

        browser.close()

    print(f"\n최종 수집 선수 수: {len(players)}명")

    if len(players) == 0:
        raise Exception("KBO 방화벽 차단으로 수집 실패")

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

    print("data/players.json 저장 완료!")

if __name__ == "__main__":
    crawl_kbo_with_browser()
