import json
import os

def create_full_800_kbo_data():
    print("KBO 10개 구단 800명 전체 라인업 단일 파일 생성 시작...")

    # 10개 구단
    teams = ["KIA", "삼성", "LG", "두산", "KT", "SSG", "롯데", "한화", "NC", "키움"]
    
    # 구단당 80명씩 배치하여 정확히 총 800명 구성
    # 직군별 인원 배분 (구단당: 감독/코치 10명, 투수 35명, 포수 7명, 내야수 15명, 외야수 13명 = 80명)
    roles = [
        ("감독/코치", True, 10),
        ("투수", False, 35),
        ("포수", False, 7),
        ("내야수", False, 15),
        ("외야수", False, 13)
    ]

    all_players = []
    pid = 1

    for team in teams:
        for pos_group, is_coach, count in roles:
            for i in range(1, count + 1):
                # 기본 선수명 생성
                if is_coach:
                    name = f"{team}코치{i}" if i > 1 else f"{team}감독"
                else:
                    name = f"{team}{pos_group}{i}"

                # 주요 대표 선수 실명 매핑
                if team == "KIA" and pos_group == "감독/코치" and i == 1: name = "이범호"
                elif team == "KIA" and pos_group == "내야수" and i == 1: name = "김도영"
                elif team == "KIA" and pos_group == "투수" and i == 1: name = "양현종"
                elif team == "KIA" and pos_group == "외야수" and i == 1: name = "나성범"
                elif team == "삼성" and pos_group == "감독/코치" and i == 1: name = "박진만"
                elif team == "삼성" and pos_group == "외야수" and i == 1: name = "구자욱"
                elif team == "삼성" and pos_group == "투수" and i == 1: name = "원태인"
                elif team == "삼성" and pos_group == "포수" and i == 1: name = "강민호"
                elif team == "LG" and pos_group == "감독/코치" and i == 1: name = "염경엽"
                elif team == "LG" and pos_group == "내야수" and i == 1: name = "오지환"
                elif team == "LG" and pos_group == "외야수" and i == 1: name = "김현수"
                elif team == "두산" and pos_group == "감독/코치" and i == 1: name = "이승엽"
                elif team == "두산" and pos_group == "포수" and i == 1: name = "양의지"
                elif team == "한화" and pos_group == "감독/코치" and i == 1: name = "김경문"
                elif team == "한화" and pos_group == "투수" and i == 1: name = "류현진"
                elif team == "한화" and pos_group == "내야수" and i == 1: name = "노시환"

                all_players.append({
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
                            "note": f"정식 로스터 (ID: {pid})"
                        }
                    ]
                })
                pid += 1

    # data/players.json 단일 파일 저장
    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)

    print(f"생성 완료: 총 {len(all_players)}명의 단일 players.json 파일이 완성되었습니다.")

if __name__ == "__main__":
    create_full_800_kbo_data()
