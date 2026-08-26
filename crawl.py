import base64
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE = "https://web1.koreabaseball.com"
KBO_REGISTER = f"{BASE}/Player/Register.aspx"
KBO_REGISTER_ALL = f"{BASE}/Player/RegisterAll.aspx"
FUTURES_REGISTER = f"{BASE}/Futures/Player/Register.aspx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": BASE + "/",
}

# VIEWSTATE 안에서 확인된 1군 구단 코드
TEAM_CODE_NAME = {
    "KT": "KT", "SS": "삼성", "LG": "LG", "HT": "KIA", "OB": "두산",
    "LT": "롯데", "HH": "한화", "NC": "NC", "SK": "SSG", "WO": "키움",
}

JOB_KEYWORDS = ("감독", "코치", "투수", "포수", "내야수", "외야수")
STAFF_KEYWORDS = ("감독", "코치")

session = requests.Session()
session.headers.update(HEADERS)


def get(url, retries=3):
    last = None
    for i in range(retries):
        try:
            r = session.get(url, timeout=25)
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.text
        except Exception as e:
            last = e
            print(f"  GET 실패({i + 1}/{retries}): {e}")
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"GET 최종 실패: {url} ({last})")


def post(url, data, retries=3):
    last = None
    for i in range(retries):
        try:
            r = session.post(url, data=data, timeout=25)
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.text
        except Exception as e:
            last = e
            print(f"  POST 실패({i + 1}/{retries}): {e}")
            time.sleep(2 * (i + 1))
    print(f"  POST 최종 실패: {url} ({last})")
    return None


def hidden_fields(html):
    """__VIEWSTATE 등 폼 hidden 값 전부 수집."""
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    for inp in soup.find_all("input", {"type": "hidden"}):
        name = inp.get("name")
        if name:
            data[name] = inp.get("value", "")
    return data


def find_team_buttons(html):
    """페이지 HTML에서 구단 버튼의 __doPostBack 대상을 자동으로 찾아낸다."""
    soup = BeautifulSoup(html, "html.parser")
    found, seen = [], set()

    for a in soup.find_all("a"):
        m = re.search(r"__doPostBack\('([^']+)'\s*,\s*'([^']*)'\)", str(a))
        if not m:
            continue
        target, arg = m.group(1), m.group(2)

        code, label = None, a.get_text(strip=True)
        img = a.find("img")
        if img:
            mm = re.search(r"emblem_([A-Za-z0-9]+)\.png", img.get("src", ""))
            if mm:
                code = mm.group(1).upper()
            if not label:
                label = (img.get("alt") or "").strip()
        if not code:
            continue  # 구단 버튼이 아니면 무시

        key = (target, arg)
        if key in seen:
            continue
        seen.add(key)
        found.append({
            "code": code,
            "name": TEAM_CODE_NAME.get(code, label or code),
            "target": target,
            "arg": arg,
        })
    return found


def parse_player_link(cell):
    a = cell.find("a")
    if not a:
        return None, None, False
    href = a.get("href", "")
    m = re.search(r"playerId=(\d+)", href)
    pid = m.group(1) if m else None
    detail = href if href.startswith("http") else BASE + href
    return pid, detail, "/Record/Retire/" in href


def parse_roster(html, team_name, league):
    """구단 페이지의 명단 표를 파싱. 등/말소 표는 자동으로 제외된다."""
    soup = BeautifulSoup(html, "html.parser")
    people = []

    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if len(headers) < 2 or headers[0] != "등번호":
            continue
        job = headers[1]
        if not any(k in job for k in JOB_KEYWORDS):
            continue  # '선수명' 헤더인 등/말소 표는 건너뜀

        body = table.find("tbody") or table
        for tr in body.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            name = tds[1].get_text(strip=True)
            if not name:
                continue

            pid, detail, retired = parse_player_link(tds[1])
            is_staff = any(k in job for k in STAFF_KEYWORDS)

            people.append({
                "playerId": pid,
                "name": name,
                "team": team_name,
                "league": league,
                "job": job,
                "role": "coach" if is_staff else "player",
                "backNo": tds[0].get_text(strip=True),
                "throwBat": tds[2].get_text(strip=True) if len(tds) > 2 else "",
                "birth": tds[3].get_text(strip=True) if len(tds) > 3 else "",
                "physique": tds[4].get_text(strip=True) if len(tds) > 4 else "",
                "detailUrl": detail,
                "isRetiredRecord": retired,
                "salary": {
                    "amount": None,
                    "status": "비공개" if is_staff else "미확인",
                    "season": None,
                    "source": None,
                },
                "history": [],
            })
    return people


def collect(page_url, league):
    """한 페이지(1군 또는 퓨처스)의 모든 구단을 순회 수집."""
    print(f"\n--- {league} 수집 시작 ---")
    html = get(page_url)
    teams = find_team_buttons(html)
    if not teams:
        print(f"  구단 버튼을 찾지 못했습니다: {page_url}")
        return []
    print(f"  구단 버튼 {len(teams)}개 발견: {[t['code'] for t in teams]}")

    people = []
    # 첫 화면에 이미 표시된 구단은 그대로 파싱
    first = parse_roster(html, teams[0]["name"], league)
    print(f"  {teams[0]['name']}: {len(first)}명")
    people += first

    for t in teams[1:]:
        base_html = get(page_url)          # 매번 새 VIEWSTATE 확보
        form = hidden_fields(base_html)
        form["__EVENTTARGET"] = t["target"]
        form["__EVENTARGUMENT"] = t["arg"]
        res = post(page_url, form)
        if not res:
            continue
        got = parse_roster(res, t["name"], league)
        print(f"  {t['name']}: {len(got)}명")
        people += got
        time.sleep(0.5)

    return people


def fallback_from_viewstate():
    """POST가 막힐 경우를 위한 예비 경로.
    RegisterAll.aspx의 VIEWSTATE 안에 들어있는 전체 명단 데이터를 직접 읽는다."""
    print("\n--- 예비 경로: RegisterAll VIEWSTATE 파싱 ---")
    html = get(KBO_REGISTER_ALL)
    m = re.search(r'id="__VIEWSTATE"\s+value="([^"]+)"', html)
    if not m:
        return []
    try:
        blob = base64.b64decode(m.group(1)).decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  디코딩 실패: {e}")
        return []

    people = []
    for chunk in re.findall(r"<Table\s[^>]*>(.*?)</Table>", blob, re.S):
        def val(tag):
            mm = re.search(rf"<{tag}>(.*?)</{tag}>", chunk, re.S)
            return mm.group(1).strip() if mm else ""

        name, code, job = val("P_NM"), val("T_ID"), val("JOB_SC")
        if not name or not code:
            continue
        is_staff = any(k in job for k in STAFF_KEYWORDS)
        people.append({
            "playerId": val("P_ID") or None,
            "name": name,
            "team": TEAM_CODE_NAME.get(code.upper(), code),
            "league": "1군",
            "job": job,
            "role": "coach" if is_staff else "player",
            "backNo": val("BACK_NO"),
            "throwBat": "",
            "birth": "",
            "physique": "",
            "detailUrl": None,
            "isRetiredRecord": False,
            "salary": {
                "amount": None,
                "status": "비공개" if is_staff else "미확인",
                "season": None,
                "source": None,
            },
            "history": [],
        })
    print(f"  {len(people)}명 확보")
    return people


def dedupe(people):
    seen, out = set(), []
    for p in people:
        key = (p["league"], p["playerId"] or f'{p["team"]}|{p["name"]}|{p["backNo"]}')
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def main():
    print("=== KBO 선수·코치 명단 수집 시작 ===")

    people = collect(KBO_REGISTER, "1군")
    teams_found = {p["team"] for p in people}
    if len(teams_found) < 8:
        print(f"1군 수집이 부족합니다(구단 {len(teams_found)}개). 예비 경로로 전환합니다.")
        people += fallback_from_viewstate()

    try:
        people += collect(FUTURES_REGISTER, "퓨처스")
    except Exception as e:
        print(f"퓨처스 수집 실패(1군 데이터는 유지): {e}")

    people = dedupe(people)
    if not people:
        raise RuntimeError("수집 결과가 0건입니다. 페이지 구조를 다시 확인해야 합니다.")

    players = [p for p in people if p["role"] == "player"]
    coaches = [p for p in people if p["role"] == "coach"]
    with_id = [p for p in people if p["playerId"]]

    print("\n=== 수집 결과 ===")
    print(f"총 인원: {len(people)}명 (선수 {len(players)} / 감독·코치 {len(coaches)})")
    print(f"playerId 확보: {len(with_id)}명")
    for lg in ("1군", "퓨처스"):
        sub = [p for p in people if p["league"] == lg]
        if sub:
            print(f"  {lg}: {len(sub)}명, 구단 {len(set(p['team'] for p in sub))}개")

    os.makedirs("data", exist_ok=True)
    out = {
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": [KBO_REGISTER, FUTURES_REGISTER],
        "note": "연봉·이력은 enrich.py가 상세 페이지에서 채웁니다.",
        "totalCount": len(people),
        "playerCount": len(players),
        "coachCount": len(coaches),
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
