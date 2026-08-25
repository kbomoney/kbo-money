import json
import os

def generate_kbo_data():
    print("KBO 10개 구단 전체 선수 및 코칭스태프 데이터 생성 중...")

    # 10개 구단 데이터 정의
    teams = ["KIA", "삼성", "LG", "두산", "KT", "SSG", "롯데", "한화", "NC", "키움"]
    
    positions = [
        ("감독", "감독/코치", True),
        ("코치", "감독/코치", True),
        ("투수", "투수", False),
        ("포수", "포수", False),
        ("내야수", "내야수", False),
        ("외야수", "외야수", False)
    ]

    players = []
    pid = 1

    # 전 구단 직군별 기본 스쿼드 생성 (검색 및 서비스 정상 동작용)
    for team in teams:
        for pos_name, pos_group, is_coach in positions:
            # 포지션 및 역할별 8명씩 생성 (구단당 약 48명~80명 분량 데이터 배치)
            for i in range(1, 9):
                name = f"{team}{pos_name}{i}"
                
                # 대표 주요 선수 이름 매핑 (검색 테스트용)
                if team == "KIA" and pos_name == "내야수" and i == 1: name = "김도영"
                elif team == "KIA" and pos_name == "투수" and i == 1: name = "양현종"
                elif team == "KIA" and pos_name == "감독" and i == 1: name = "이범호"
                elif team == "삼성" and pos_name == "외야수" and i == 1: name = "구자욱"
                elif team == "삼성" and pos_name == "투수" and i == 1: name = "원태인"
                elif team == "LG" and pos_name == "내야수" and i == 1: name = "오지환"
                elif team == "두산" and pos_name == "포수" and i == 1: name = "양의지"
                elif team == "한화" and pos_name == "투수" and i == 1: name = "류현진"

                players.append({
                    "id": str(pid),
                    "name": name,
                    "team": team,
                    "positionGroup": pos_group,
                    "isCoach": is_coach,
                    "draftInfo": f"{team} 정식 등록",
                    "history": [
                        {
                            "period": "현재",
                            "team": f"{team} 프로야구단",
                            "salary": "KBO 정식 등록",
                            "note": f"{pos_name} 로스터"
                        }
                    ]
                })
                pid += 1

    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

    print(f"성공: 총 {len(players)}명의 데이터가 data/players.json에 저장되었습니다.")

if __name__ == "__main__":
    generate_kbo_data()
