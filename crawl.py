import json
import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://web1.koreabaseball.com"
REGISTER_ALL = f"{BASE}/Player/RegisterAll.aspx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

TEAM_FULL = {
    "KT": "KT 위즈", "삼성": "삼성 라이온즈", "LG": "LG 트윈스",
    "KIA": "KIA 타이거즈", "두산": "두산 베어스", "롯데": "롯데 자이언츠",
    "한화": "한화 이글스", "NC": "NC 다이노스", "SSG": "SSG 랜더스",
    "키움": "키움 히어로즈",
}

# 코치진으로 취급할 보직 키워드
STAFF_KEYWORDS = ("감독", "코치")


def fetch(url, retries=3):
    last_err = None
    for i in range(retries):
        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
            res.raise_for_status()
            res.encoding = res.apparent_encoding or "utf-8"
            return res.text
        except Exception as e:
            last_err = e
            print(f"  요청 실패({i + 1}/{retries}): {e}")
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"요청 최종 실패: {url} ({last_err})")


def parse_player_id(cell):
    """이름 셀의 링크에서 playerId와 상세 URL을 추출."""
    a = cell.find("a")
    if not a:
        return None, None, False
    href = a.get("href", "")
    m = re.search(r"playerId=(\d+)", href)
    pid = m.group(1) if m else None
    detail = href if href.startswith("http") else BASE + href
    # 은퇴 선수 경로면 지도자(코치진)로 판단
    is_retired_path = "/Record/Retire/" in href
    return pid, detail, is_retired_path


def parse_register_all(html):
    """전체 등록 현황 페이지에서 구단별 감독/코치/선수를 파싱."""
    soup = BeautifulSoup(html, "html.parser")
    people = []

    for table in soup.find_all("table"):
        # 헤더에서 보직(감독/코치/투수/포수/내야수/외야수) 확인
        head = table.find("thead")
        if not head:
            continue
        head_cols = [th.get_text(strip=True) for th in head.find_all("th")]
        if len(head_cols) < 2 or head_cols[0] != "등번호":
            continue
        job = head_cols[1]  # 감독, 코치, 투수, 포수, 내야수, 외야수

        # 이 테이블이 속한 구단명 찾기 (직전 제목 요소 탐색)
        team = None
        for prev in table.find_all_previous(["h4", "h5", "h6", "caption", "strong"]):
            text = prev.get_text(strip=True)
            m = re.search(r"(KT|삼성|LG|KIA|두산|롯데|한화|NC|SSG|키움)", text)
            if m:
                team = m.group(1)
                break
        if not team:
            continue

        body = table.find("tbody") or table
        for tr in body.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue

            back_no = tds[0].get_text(strip=True)
            name_cell = tds[1]
            name = name_cell.get_text(strip=True)
            if not name or name == job:
                continue

            pid, detail, retired_path = parse_player_id(name_cell)
            throw_bat = tds[2].get_text(strip=True) if len(tds) > 2 else ""
            birth = tds[3].get_text(strip=True) if len(tds) > 3 else ""
            physique = tds[4].get_text(strip=True) if len(tds) > 4 else ""

            is_staff = any(k in job for k in STAFF_KEYWORDS)

            people.append({
                "playerId": pid,
                "name": name,
                "team": team,
                "teamFull": TEAM_FULL.get(team, team),
                "league": "1군",
                "job": job,
                "role": "coach" if is_staff else "player",
                "backNo": back_no,
                "throwBat": throw_bat,
                "birth": birth,
                "physique": physique,
                "detailUrl": detail,
                "isRetiredRecord": retired_path,
                # 연봉은 별도 파일(data/salary.json)에서 병합. 여기서는 상태만 표기.
                "salary": {
                    "amount": None,
                    "status": "비공개" if is_staff else "미확인",
                    "season": None,
                    "source": None,
                },
                # 이적 이력은 다음 단계에서 상세 페이지로 채움.
                "history": [],
            })

    return people


def dedupe(people):
    """playerId 기준 중복 제거(등/말소 표에 중복 등장하는 경우 대비)."""
    seen = {}
    for p in people:
        key = p["playerId"] or f'{p["team"]}|{p["name"]}|{p["backNo"]}'
        if key not in seen:
            seen[key] = p
    return list(seen.values())


def main():
    print("=== KBO 1군 등록 현황 수집 시작 ===")
    html = fetch(REGISTER_ALL)
    people = dedupe(parse_register_all(html))

    if not people:
        raise RuntimeError("파싱 결과가 0건입니다. 페이지 구조가 변경된 것으로 보입니다.")

    # 절대 인원수 대신 '구단이 모두 수집됐는지'를 구조적으로 검증
    teams_found = sorted({p["team"] for p in people})
    missing = [t for t in TEAM_FULL if t not in teams_found]
    if missing:
        raise RuntimeError(f"누락된 구단이 있습니다: {missing} (수집된 구단: {teams_found})")

    players = [p for p in people if p["role"] == "player"]
    coaches = [p for p in people if p["role"] == "coach"]

    print(f"구단 수: {len(teams_found)}")
    print(f"선수: {len(players)}명 / 감독·코치: {len(coaches)}명 / 합계: {len(people)}명")
    for t in teams_found:
        cnt = sum(1 for p in people if p["team"] == t)
        print(f"  - {t}: {cnt}명")

    os.makedirs("data", exist_ok=True)
    out = {
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "source": REGISTER_ALL,
        "note": "1군 등록 현황 기준. 연봉은 data/salary.json에서 병합됩니다.",
        "totalCount": len(people),
        "people": people,
    }
    with open("data/players.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("data/players.json 저장 완료")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[실패] {e}", file=sys.stderr)
        sys.exit(1)
