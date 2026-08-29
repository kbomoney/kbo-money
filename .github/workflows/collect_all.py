"""KBO 전체 선수 명단 수집 (선수 조회 페이지 기반).

기존 crawl.py / players.json 은 건드리지 않고
결과를 data/players_all.json 에 따로 저장한다.
"""

import json
import os
import re
import time
from collections import deque

import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://web1.koreabaseball.com/Player/Search.aspx"
OUT_PATH = "data/players_all.json"
SEED_PATH = "data/players.json"

PAGE_SIZE = 20        # 한 화면에 보이는 최대 건수
REQUEST_DELAY = 0.3
MAX_REQUESTS = 6000   # 안전장치

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": SEARCH_URL,
}

CURRENT_TEAMS = {"KT", "삼성", "LG", "KIA", "두산", "롯데", "한화", "NC", "SSG", "키움"}

# 처음 던져볼 검색어: 흔한 성씨 + 외국인 선수 이름에 자주 쓰이는 글자
SEED_TERMS = list(
    "김이박최정강조윤장임한오서신권황안송류전홍고문양손배백허유남심노하곽성차주우구원"
    "라로리마바베카에이오시스아켈헤데드폰페토무엔윌호"
)

HANGUL = re.compile(r"[가-힣]")

session = requests.Session()
session.headers.update(HEADERS)


def syllables(name):
    return [ch for ch in name if HANGUL.match(ch)]


def bigrams(name):
    s = syllables(name)
    return {s[i] + s[i + 1] for i in range(len(s) - 1)}


def fetch(term, retries=2):
    for i in range(retries):
        try:
            res = session.get(SEARCH_URL, params={"searchWord": term}, timeout=20)
            res.raise_for_status()
            res.encoding = "utf-8"
            return res.text
        except Exception as exc:
            if i == retries - 1:
                print(f"    요청 실패({term}): {exc}")
                return None
            time.sleep(1.5 * (i + 1))
    return None


def parse(html):
    """(전체건수, [사람...]) 형태로 돌려준다."""
    if not html:
        return 0, []

    soup = BeautifulSoup(html, "html.parser")

    total = 0
    m = re.search(r"검색결과\s*:\s*([\d,]+)\s*건", soup.get_text(" ", strip=True))
    if m:
        total = int(m.group(1).replace(",", ""))

    people = []
    for tr in soup.select("table tbody tr"):
        tds = tr.find_all("td")
        if len(tds) < 7:
            continue
        link = tds[1].find("a", href=True)
        if not link:
            continue
        pid = re.search(r"playerId=(\d+)", link["href"])
        if not pid:
            continue

        href = link["href"]
        if href.startswith("/"):
            href = "https://web1.koreabaseball.com" + href

        people.append({
            "playerId": pid.group(1),
            "name": link.get_text(strip=True),
            "backNo": tds[0].get_text(strip=True),
            "team": tds[2].get_text(strip=True),
            "position": tds[3].get_text(strip=True),
            "birth": tds[4].get_text(strip=True),
            "physique": tds[5].get_text(strip=True),
            "career": tds[6].get_text(strip=True),
            "detailUrl": href,
            "isRetiredRecord": "/Retire/" in href,
        })
    return total, people


def seed_terms():
    """기존 명단이 있으면 거기 이름에서도 검색어를 뽑아 출발점을 넓힌다."""
    terms = set(SEED_TERMS)
    if os.path.exists(SEED_PATH):
        with open(SEED_PATH, encoding="utf-8") as f:
            for p in json.load(f).get("people", []):
                terms.update(syllables(p.get("name", "")))
    return terms


def collect():
    queue = deque(sorted(seed_terms()))
    queried = set(queue)
    overflowed = []          # 20건을 넘겨 잘린 검색어
    known_bigrams = set()
    people = {}
    requests_made = 0

    while queue and requests_made < MAX_REQUESTS:
        term = queue.popleft()
        html = fetch(term)
        requests_made += 1
        time.sleep(REQUEST_DELAY)

        total, rows = parse(html)
        new = 0
        for person in rows:
            if person["playerId"] not in people:
                people[person["playerId"]] = person
                new += 1

        # 새로 알게 된 이름에서 다음 검색어를 뽑는다
        fresh_bigrams = set()
        for person in rows:
            for ch in syllables(person["name"]):
                if ch not in queried:
                    queried.add(ch)
                    queue.append(ch)
            fresh_bigrams |= bigrams(person["name"])
        known_bigrams |= fresh_bigrams

        # 20건이 꽉 찼다면 잘린 것이므로 두 글자로 쪼개 다시 던진다
        if total > PAGE_SIZE:
            overflowed.append((term, total))
            for bg in known_bigrams:
                if term in bg and bg not in queried:
                    queried.add(bg)
                    queue.append(bg)
        else:
            # 이미 넘쳤던 검색어를 품은 새 두 글자 조합도 뒤늦게 추가
            for bg in fresh_bigrams:
                if bg in queried:
                    continue
                if any(prev in bg for prev, _ in overflowed):
                    queried.add(bg)
                    queue.append(bg)

        if requests_made % 50 == 0:
            print(f"  {requests_made}회 요청 · 누적 {len(people)}명 · 대기 {len(queue)}개",
                  flush=True)

    return people, requests_made, overflowed


def main():
    print("선수 조회 페이지에서 전체 명단을 모읍니다.")
    people, requests_made, overflowed = collect()

    everyone = list(people.values())
    active = [p for p in everyone if p["team"] in CURRENT_TEAMS
              and not p["isRetiredRecord"]]

    os.makedirs("data", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": SEARCH_URL,
            "requestCount": requests_made,
            "totalFound": len(everyone),
            "activeCount": len(active),
            "people": sorted(active, key=lambda p: (p["team"], p["name"])),
            "allPeople": sorted(everyone, key=lambda p: p["name"]),
        }, f, ensure_ascii=False, indent=2)

    by_team = {}
    for p in active:
        by_team[p["team"]] = by_team.get(p["team"], 0) + 1

    print("\n=== 수집 완료 ===")
    print(f"요청 횟수     : {requests_made}회")
    print(f"검색된 인원   : {len(everyone)}명 (은퇴·과거구단 포함)")
    print(f"현역 10개구단 : {len(active)}명")
    print(f"넘친 검색어   : {len(overflowed)}개")
    for team in sorted(by_team, key=lambda t: -by_team[t]):
        print(f"  {team}: {by_team[team]}명")
    print(f"\n저장: {OUT_PATH}")


if __name__ == "__main__":
    main()
