import json
import urllib.request
from bs4 import BeautifulSoup

# KBO 데이터 수집 기본 구조
def get_kbo_players():
    # 예시 수집 로직 (기존 저장소 규격에 맞춘 기본 구조)
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
                {"period": "2024 ~ 현재", "team": "한화 이글스", "salary": "8년 총액 170억 원", "note": "KBO 복귀"}
            ]
        }
        # 크롤링 자동 확장 영역
    ]
    return players

if __name__ == "__main__":
    data = get_kbo_players()
    with open('data/players.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
