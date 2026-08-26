import json
import os
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def crawl_kbo_official():
    print("=== [KBO API] 전 구단 실시간 명단 수집 시작 ===")

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

    with sync_playwright() as p:
        # 브라우저 생성 및 보안 탐지 방지 설정
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        page = context.new_page()

        # 브라우저 자동화 감지 변수 초기화
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("1. KBO 메인 세션 연결 중...")
        try:
            page.goto("https://www.koreabaseball.com/Player/Search.aspx", wait_until="networkidle", timeout=30000)
            time.sleep(2)
        except Exception as e:
            print(f"메인 세션 접속 경고: {e}")

        # 구단별 검색 진행
        for team in teams:
            team_code = team["code"]
            team_name = team["name"]
            page_num = 1
            print(f"[{team_name}] 실시간 데이터 파싱 중...")

            while True:
                # 브라우저 내부 세션을 그대로 사용하여 KBO 백엔드 API 호출
                js_code = f"""
                async () => {{
                    try {{
                        const res = await fetch('https://www.koreabaseball.com/ws/Main.wsgi/GetSearchPlayerList', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                'X-Requested-With': 'XMLHttpRequest'
                            }},
                            body: 'searchType=TEAM&teamCode={team_code}&page={page_num}'
                        }});
                        return await res.json();
                    }} catch (err) {{
                        return null;
                    }}
                }}
                """
                
                res_data = page.evaluate(js_code)
                
                if not res_data or 'rows' not in res_data:
                    print(f"[{team_name}] API 응답 없음/차단됨")
                    break

                rows = res_data.get('rows', [])
                if not rows:
                    break

                for item in rows:
                    cols = item.get('row', [])
                    if len(cols) >= 4:
                        # 등번호, 이름 파싱
                        back_num = BeautifulSoup(str(cols[0]), 'html.parser').get_text(strip=True)
                        name = BeautifulSoup(str(cols[1]), 'html.parser').get_text(strip=True)
                        position = str(cols[2]).strip() if len(cols) > 2 else "등록선수"
                        draft = str(cols[4]).strip() if len(cols) > 4 else f"{team_name} 정식 등록"

                        if name and name != "선수명":
                            is_coach = "코치" in position or "감독" in position
                            
                            # 기존 포맷과 100% 동일하게 생성
                            all_players.append({
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
                if page_num >= total_page:
                    break

                page_num += 1
                time.sleep(0.1)

        browser.close()

    print(f"\n최종 수집 인원: {len(all_players)}명")

    # 수집 인원이 100명 미만이면 오류 처리 (차단 여부 확인)
    if len(all_players) < 100:
        raise Exception(f"수집 실패 (현재 수집된 인원: {len(all_players)}명)")

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print("data/players.json 저장 성공!")

if __name__ == "__main__":
    crawl_kbo_official()
