import json
import os

def create_full_800_kbo_data():
    print("KBO 10개 구단 800명 전체 라인업(이력 및 연봉 데이터 포함) 생성 시작...")

    teams = ["KIA", "삼성", "LG", "두산", "KT", "SSG", "롯데", "한화", "NC", "키움"]
    
    # 구단당 80명씩 배치 (총 800명)
    roles = [
        ("감독/코치", True, 10),
        ("투수", False, 35),
        ("포수", False, 7),
        ("내야수", False, 15),
        ("외야수", False, 13)
    ]

    # 주요 선수별 실제 연봉 및 이력 상세 정보 매핑 (KBO 공시 데이터 기반)
    star_player_info = {
        "김광현": {"salary": "30억원", "draft": "2007년 1차 지명 (SK)", "history": [
            {"period": "2007 - 2019", "team": "SK 와이번스", "salary": "최대 15억원", "note": "KBO 데뷔 및 Ace 역할"},
            {"period": "2020 - 2021", "team": "세인트루이스 카디널스", "salary": "ML 계약", "note": "메이저리그 진출"},
            {"period": "2022 - 현재", "team": "SSG 랜더스", "salary": "30억원 (2025)", "note": "4년 151억원 비FA 다년계약 복귀"}
        ]},
        "김도영": {"salary": "5억원", "draft": "2022년 1차 지명 (KIA)", "history": [
            {"period": "2022 - 2023", "team": "KIA 타이거즈", "salary": "3,000만 ~ 5,000만원", "note": "1차 지명 입단"},
            {"period": "2024", "team": "KIA 타이거즈", "salary": "1억원", "note": "정규시즌 MVP 수상"},
            {"period": "2025 - 현재", "team": "KIA 타이거즈", "salary": "5억원", "note": "4년차 최고 연봉 (400% 인상)"}
        ]},
        "류현진": {"salary": "20억원", "draft": "2006년 2차 1라운드 (한화)", "history": [
            {"period": "2006 - 2012", "team": "한화 이글스", "salary": "2,000만 ~ 4억 3,000만원", "note": "신인왕 및 MVP"},
            {"period": "2013 - 2023", "team": "LA 다저스 / 토론토", "salary": "ML 계약", "note": "MLB 진출"},
            {"period": "2024 - 현재", "team": "한화 이글스", "salary": "20억원", "note": "8년 170억원 계약 복귀"}
        ]},
        "최정": {"salary": "17억원", "draft": "2005년 1차 지명 (SK)", "history": [
            {"period": "2005 - 2020", "team": "SK 와이번스", "salary": "FA 계약 체결", "note": "팀 간판 타자"},
            {"period": "2021 - 현재", "team": "SSG 랜더스", "salary": "17억원", "note": "21년차 최고 연봉 경신"}
        ]},
        "구자욱": {"salary": "20억원", "draft": "2012년 2라운드 (삼성)", "history": [
            {"period": "2012 - 현재", "team": "삼성 라이온즈", "salary": "20억원", "note": "비FA 다년계약 체결"}
        ]},
        "양의지": {"salary": "10억원", "draft": "2006년 2차 8라운드 (두산)", "history": [
            {"period": "2006 - 2018", "team": "두산 베어스", "salary": "주전 포수", "note": "두산 1기"},
            {"period": "2019 - 2022", "team": "NC 다이노스", "salary": "FA 125억원", "note": "FA 이적"},
            {"period": "2023 - 현재", "team": "두산 베어스", "salary": "10억원", "note": "4년 152억원 2차 FA 복귀"}
        ]},
        "양현종": {"salary": "10억원", "draft": "2007년 2차 1라운드 (KIA)", "history": [
            {"period": "2007 - 2020", "team": "KIA 타이거즈", "salary": "KBO 최고 투수", "note": "KIA 타이거즈"},
            {"period": "2021", "team": "텍사스 레인저스", "salary": "ML 계약", "note": "MLB 진출"},
            {"period": "2022 - 현재", "team": "KIA 타이거즈", "salary": "10억원", "note": "FA 복귀"}
        ]},
        "강민호": {"salary": "10억원", "draft": "2004년 2차 3라운드 (롯데)", "history": [
            {"period": "2004 - 2017", "team": "롯데 자이언츠", "salary": "FA 계약", "note": "롯데 주전 포수"},
            {"period": "2018 - 현재", "team": "삼성 라이온즈", "salary": "10억원", "note": "삼성 FA 이적"}
        ]},
        "최형우": {"salary": "10억원", "draft": "2002년 2차 6라운드 (삼성)", "history": [
            {"period": "2002 - 2016", "team": "삼성 라이온즈", "salary": "FA 100억원", "note": "삼성 타선 핵심"},
            {"period": "2017 - 현재", "team": "KIA 타이거즈", "salary": "10억원", "note": "24년차 최고 연봉 경신"}
        ]},
        "김택연": {"salary": "1억 4,000만원", "draft": "2024년 1라운드 (두산)", "history": [
            {"period": "2024", "team": "두산 베어스", "salary": "3,000만원", "note": "KBO 신인왕 수상"},
            {"period": "2025 - 현재", "team": "두산 베어스", "salary": "1억 4,000만원", "note": "2년차 최고 연봉 타 기록"}
        ]}
    }

    all_players = []
    pid = 1

    for team in teams:
        for pos_group, is_coach, count in roles:
            for i in range(1, count + 1):
                # 기본 이름 설정
                if is_coach:
                    name = f"{team}코치{i}" if i > 1 else f"{team}감독"
                else:
                    name = f"{team}{pos_group}{i}"

                # 스타 선수 실명 매핑
                if team == "KIA" and pos_group == "감독/코치" and i == 1: name = "이범호"
                elif team == "KIA" and pos_group == "내야수" and i == 1: name = "김도영"
                elif team == "KIA" and pos_group == "투수" and i == 1: name = "양현종"
                elif team == "KIA" and pos_group == "외야수" and i == 1: name = "최형우"
                elif team == "삼성" and pos_group == "감독/코치" and i == 1: name = "박진만"
                elif team == "삼성" and pos_group == "외야수" and i == 1: name = "구자욱"
                elif team == "삼성" and pos_group == "포수" and i == 1: name = "강민호"
                elif team == "LG" and pos_group == "감독/코치" and i == 1: name = "염경엽"
                elif team == "LG" and pos_group == "내야수" and i == 1: name = "오지환"
                elif team == "LG" and pos_group == "외야수" and i == 1: name = "김현수"
                elif team == "두산" and pos_group == "감독/코치" and i == 1: name = "이승엽"
                elif team == "두산" and pos_group == "포수" and i == 1: name = "양의지"
                elif team == "두산" and pos_group == "투수" and i == 1: name = "김택연"
                elif team == "한화" and pos_group == "감독/코치" and i == 1: name = "김경문"
                elif team == "한화" and pos_group == "투수" and i == 1: name = "류현진"
                elif team == "SSG" and pos_group == "투수" and i == 1: name = "김광현"
                elif team == "SSG" and pos_group == "내야수" and i == 1: name = "최정"

                # 이력 및 연봉 정보 구성
                if name in star_player_info:
                    info = star_player_info[name]
                    current_salary = info["salary"]
                    draft_info = info["draft"]
                    history = info["history"]
                else:
                    # 일반/육성 선수 기본값 산출
                    if is_coach:
                        current_salary = "8,000만원 ~ 1억 5,000만원" if i == 1 else "5,000만원 ~ 8,000만원"
                        draft_info = "지도자 계약"
                    else:
                        current_salary = f"{3000 + (i * 200)}만원" if i <= 10 else "3,000만원 (최저 연봉)"
                        draft_info = f"{team} 정식 등록"
                    
                    history = [
                        {
                            "period": "2023 - 2024",
                            "team": f"{team} 육성/퓨처스팀",
                            "salary": "3,000만원",
                            "note": "입단 및 퓨처스리그 출전"
                        },
                        {
                            "period": "2025 - 현재",
                            "team": f"{team} 프로야구단",
                            "salary": current_salary,
                            "note": f"정식 등록 로스터 (ID: {pid})"
                        }
                    ]

                all_players.append({
                    "id": str(pid),
                    "name": name,
                    "team": team,
                    "positionGroup": pos_group,
                    "isCoach": is_coach,
                    "draftInfo": draft_info,
                    "salary": current_salary,
                    "history": history
                })
                pid += 1

    # data/players.json 단일 파일 저장
    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print(f"생성 완료: 연봉 및 이력이 포함된 총 {len(all_players)}명의 players.json 파일이 생성되었습니다.")

if __name__ == "__main__":
    create_full_800_kbo_data()
