import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE = "https://web1.koreabaseball.com"
SEARCH = f"{BASE}/Player/Search.aspx"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 현재 존재하는 구단만 인정(쌍방울·MBC 등 과거 구단 제외)
CURRENT_TEAMS = {
    "KT", "삼성", "KIA", "LG", "두산", "NC", "롯데", "한화", "SSG", "키움",
    "상무", "고양", "울산",
}

session = requests.Session()
session.headers.update(HEADERS)


def search(word):
    r = session.get(SEARCH, params={"searchWord": word}, timeout=25)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text


def parse_rows(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if "선수명" not in headers or "팀명" not in headers:
            continue
        body = table.find("tbody") or table
        for tr in body.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 6:
                continue
            a = tds[1].find("a")
            href = a.get("href", "") if a else ""
            m = re.search(r"playerId=(\d+)", href)
            rows.append({
                "backNo": tds[0].get_text(strip=True).replace("#", ""),
                "name": tds[1].get_text(strip=True),
                "team": tds[2].get_text(strip=True),
                "job": tds[3].get_text(strip=True),
                "birth": tds[4].get_text(strip=True),
                "physique": tds[5].get_text(strip=True),
                "playerId": m.group(1) if m else None,
                "href": href,
            })
    return rows


def to_person(row):
    href = row["href"]
    detail = href if href.startswith("http") else BASE + href
    return {
        "playerId": row["playerId"],
        "name": row["name"],
        "team": row["team"],
        "league": "퓨처스" if "/Futures/" in href else "1군",
        "job": row["job"] or "선수",
        "role": "player",
        "backNo": row["backNo"],
        "throwBat": "",
        "birth": row["birth"],
        "physique": row["physique"],
        "detailUrl": detail,
        "isRetiredRecord": "/Record/Retire/" in href,
        "salary": {"amount": None, "status": "미확인", "season": None, "source": None},
        "history": [],
    }


def main():
    with open("data/players.json", encoding="utf-8") as f:
        data = json.load(f)
    people = data["people"]
    known = {p["playerId"] for p in people if p.get("playerId")}

    names = []
    if os.path.exists("data/add_names.json"):
        with open("data/add_names.json", encoding="utf-8") as f:
            names = json.load(f).get("names", [])
    names += sys.argv[1:]
    if not names:
        print("추가할 이름이 없습니다. data/add_names.json 을 확인하세요.")
        return

    added = 0
    for name in names:
        try:
            rows = parse_rows(search(name))
        except Exception as e:
            print(f"  {name}: 검색 실패 ({e})")
            continue

        hits = [r for r in rows
                if r["name"] == name
                and r["playerId"]
                and r["playerId"] not in known
                and r["team"] in CURRENT_TEAMS
                and "/Record/Retire/" not in r["href"]]

        if not hits:
            print(f"  {name}: 추가할 항목 없음(이미 있거나 은퇴)")
        for r in hits:
            people.append(to_person(r))
            known.add(r["playerId"])
            added += 1
            print(f"  + {r['name']} ({r['team']}, {r['job']}, id={r['playerId']})")
        time.sleep(0.4)

    players = [p for p in people if p["role"] == "player"]
    coaches = [p for p in people if p["role"] == "coach"]
    data.update({
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "totalCount": len(people),
        "playerCount": len(players),
        "coachCount": len(coaches),
        "people": people,
    })
    with open("data/players.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n{added}명 추가 → 총 {len(people)}명")


if __name__ == "__main__":
    main()
