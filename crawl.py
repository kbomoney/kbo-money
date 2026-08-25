import json
import os

def update_kbo_data():
    # 데이터베이스에 선수 및 코치 정보 추가
    players = [
        {
            "id": "1",
            "name": "류현진",
            "team": "한화",
            "positionGroup": "투수",
            "isCoach": False,
            "draftInfo": "2006년 2차 1라운드 (한화 이글스)",
            "firstSalary": 2000,
            "history": [
                {"period": "2006 ~ 2012", "team": "한화 이글스", "salary": "2,000만 ~ 4억 3,000만 원", "note": "KBO MVP 및 신인왕"},
                {"period": "2013 ~ 2019", "team": "LA 다저스", "salary": "6년 총액 3,600만 달러", "note": "MLB 진출"},
                {"period": "2020 ~ 2023", "team": "토론토 블루제이스", "salary": "4년 총액 8,000만 달러", "note": "FA 계약"},
                {"period": "2024 ~ 현재", "team": "한화 이글스", "salary": "8년 총액 170억 원", "note": "KBO 리그 복귀"}
            ]
        },
        {
            "id": "2",
            "name": "양의지",
            "team": "두산",
            "positionGroup": "포수",
            "isCoach": False,
            "draftInfo": "2006년 2차 8라운드 (두산 베어스)",
            "firstSalary": 2000,
            "history": [
                {"period": "2006 ~ 2018", "team": "두산 베어스", "salary": "2,000만 ~ 6억 원", "note": "입단 및 주전 포수"},
                {"period": "2019 ~ 2022", "team": "NC 다이노스", "salary": "125억 원 (4년 FA)", "note": "FA 이적 후 우승"},
                {"period": "2023 ~ 현재", "team": "두산 베어스", "salary": "152억 원 (4+2년 FA)", "note": "FA 친정팀 복귀"}
            ]
        },
        {
            "id": "3",
            "name": "김원중",
            "team": "롯데",
            "positionGroup": "투수",
            "isCoach": False,
            "draftInfo": "2012년 1라운드 5순위 (롯데 자이언츠)",
            "firstSalary": 2400,
            "history": [
                {"period": "2012 ~ 2024", "team": "롯데 자이언츠", "salary": "2,400만 ~ 5억 원", "note": "롯데 마무리 투수"},
                {"period": "2025 ~ 현재", "team": "롯데 자이언츠", "salary": "4년 총액 54억 원", "note": "FA 재계약"}
            ]
        },
        {
            "id": "4",
            "name": "전민재",
            "team": "두산",
            "positionGroup": "내야수",
            "isCoach": False,
            "draftInfo": "2018년 2차 4라운드 (두산 베어스)",
            "firstSalary": 2700,
            "history": [
                {"period": "2018 ~ 현재", "team": "두산 베어스", "salary": "2,700만 ~ 8,500만 원", "note": "두산 내야수"}
            ]
        },
        {
            "id": "5",
            "name": "최정",
            "team": "SSG",
            "positionGroup": "내야수",
            "isCoach": False,
            "draftInfo": "2005년 1차 지명 (SK 와이번스)",
            "firstSalary": 2000,
            "history": [
                {"period": "2005 ~ 2018", "team": "SK 와이번스", "salary": "2,000만 ~ 12억 원", "note": "SK 간판 타자"},
                {"period": "2019 ~ 2024", "team": "SSG 랜더스", "salary": "106억 원 (6년 FA)", "note": "첫 번째 FA 계약"},
                {"period": "2025 ~ 현재", "team": "SSG 랜더스", "salary": "4년 총액 110억 원", "note": "두 번째 FA 계약"}
            ]
        },
        {
            "id": "6",
            "name": "구자욱",
            "team": "삼성",
            "positionGroup": "외야수",
            "isCoach": False,
            "draftInfo": "2012년 2차 2라운드 (삼성 라이온즈)",
            "firstSalary": 2400,
            "history": [
                {"period": "2012 ~ 2021", "team": "삼성 라이온즈", "salary": "2,400만 ~ 3억 6,000만 원", "note": "삼성 간판 타자"},
                {"period": "2022 ~ 현재", "team": "삼성 라이온즈", "salary": "5년 총액 120억 원", "note": "비FA 다년계약"}
            ]
        }
    ]
    
    # data 폴더 자동 생성 및 파일 저장
    os.makedirs('data', exist_ok=True)
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

    print(f"업데이트 완료: 총 {len(players)}명의 선수 데이터가 data/players.json에 반영되었습니다.")

if __name__ == "__main__":
    update_kbo_data()
