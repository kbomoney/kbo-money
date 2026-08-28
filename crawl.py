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
FUTURES_HITTER = f"{BASE}/Futures/Player/Hitter.aspx"
FUTURES_PITCHER = f"{BASE}/Futures/Player/Pitcher.aspx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": BASE + "/",
}

# 1군 구단 코드(VIEWSTATE에서 확인)
TEAM_CODE_NAME = {
    "KT": "KT", "SS": "삼성", "HT": "KIA", "LG": "LG", "OB": "두산",
    "NC": "NC", "LT": "롯데", "HH": "한화", "SK": "SSG", "WO": "키움",
}

# 퓨처스 구단 코드(퓨처스 페이지 VIEWSTATE에서 확인) - 상무·고양·울산 포함 12개
FUTURES_CODE_NAME = {
    "HH": "한화", "LG": "LG", "SK": "SSG", "OB": "두산", "WO": "고양",
    "SM": "상무", "KT": "KT", "NC": "NC", "LT": "롯데", "SS": "삼성",
    "HT": "KIA", "UL": "울산",
}

JOB_KEYWORDS = ("감독", "코치", "투수", "포수", "내야수", "외야수")
STAFF_KEYWORDS = ("감독", "코치")

# 팀 전환 시도용 후보들
QUERY_KEYS = ["teamId", "teamCode", "tId", "team", "teamNm", "t_id"]
PREFIX = "ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$"
RPT_NAMES = ["rptTeam", "rptTeams", "rptTeamList", "rptEmblem", "rptTeamEmblem"]
CTL_NAMES = ["lnkTeam", "btnTeam", "lbtnTeam", "lnkEmblem", "imgTeam"]

session = requests.Session()
session.headers.update(HEADERS)


def get(url, params=None, retries=3):
    last = None
    for i in range(retries):
        try:
            r = session.get(url, params=params, timeout=25)
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.text
        except Exception as e:
            last = e
            print(f"  GET 실패({i + 1}/{retries}): {e}")
            time.sleep(2 * (i + 1))
    print(f"  GET 최종 실패: {url} ({last})")
    return None


def post(url, data, retries=2):
    last = None
    for i in range(retries):
        try:
            r = session.post(url, data=data, timeout=30)
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


def page_team_name(html):
    """'한화 이글스 선수등록 명단' 같은 제목에서 팀 이름을 뽑는다."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(re.compile(r"^h[1-6]$")):
        text = tag.get_text(" ", strip=True)
        m = re.match(r"(.+?)\s*선수\s*등록\s*명단", text)
        if m:
            return m.group(1).strip()
    return ""


def found_postback_targets(html):
    """페이지에 실제로 박혀 있는 __doPostBack 대상 목록."""
    out, seen = [], set()
    for m in re.finditer(r"__doPostBack\(['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]*)['\"]\)", html or ""):
        key = (m.group(1), m.group(2))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def build_attempts(base_html, index):
    """팀 전환 방법 후보를 순서대로 만든다."""
    attempts = []
    for k in QUERY_KEYS:
        attempts.append(("get_param", k))
    for k in QUERY_KEYS:
        attempts.append(("post_param", k))
    for target, arg in found_postback_targets(base_html):
        attempts.append(("postback_found", (target, arg)))
    for rpt in RPT_NAMES:
        for ctl in CTL_NAMES:
            attempts.append(("postback_tpl", f"{PREFIX}{rpt}$ctl{{IDX}}${ctl}"))
    return attempts


def run_attempt(page_url, kind, value, code, index, form):
    """한 가지 방법으로 페이지를 받아온다."""
    if kind == "get_param":
        return get(page_url, params={value: code})

    if kind == "post_param":
        data = dict(form)
        data[value] = code
        return post(page_url, data)

    data = dict(form)
    if kind == "postback_found":
        target, arg = value
        data["__EVENTTARGET"] = target
        data["__EVENTARGUMENT"] = arg if arg else code
        return post(page_url, data)

    if kind == "postback_tpl":
        data["__EVENTTARGET"] = value.replace("{IDX}", f"{index:02d}")
        data["__EVENTARGUMENT"] = ""
        return post(page_url, data)

    return None


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


def dump_team_area(html):
    """팀 전환에 실패했을 때 팀 버튼 영역을 로그에 남긴다(다음 수정용)."""
    soup = BeautifulSoup(html, "html.parser")
    for ul in soup.find_all("ul"):
        if ul.find("img") and len(ul.find_all("li")) >= 8:
            snippet = str(ul)[:1500]
            print("  [진단] 팀 버튼 영역 HTML:")
            print("  " + snippet.replace("\n", " "))
            return
    print("  [진단] 팀 버튼 영역을 찾지 못했습니다.")


def collect(page_url, league, code_name):
    """한 페이지(1군 또는 퓨처스)의 모든 구단을 순회 수집."""
    print(f"\n--- {league} 수집 시작 ---")
    base_html = get(page_url)
    if not base_html:
        return []

    form = hidden_fields(base_html)
    codes = list(code_name.items())
    people = []
    recipe = None
    diagnosed = False

    # 기본 화면에 이미 떠 있는 구단은 그대로 파싱
    shown = page_team_name(base_html)
    print(f"  기본 표시 구단: {shown or '(확인 실패)'}")
    done = set()
    for code, name in codes:
        if name and name in shown:
            got = parse_roster(base_html, name, league)
            print(f"  {name}: {len(got)}명 (기본 화면)")
            people += got
            done.add(code)
            break

    for index, (code, name) in enumerate(codes):
        if code in done:
            continue

        if recipe:
            attempts = [recipe]
        else:
            attempts = build_attempts(base_html, index)

        html, used = None, None
        for kind, value in attempts:
            trial = run_attempt(page_url, kind, value, code, index, form)
            if trial and name in page_team_name(trial):
                html, used = trial, (kind, value)
                break

        if not html:
            print(f"  {name}: 전환 실패")
            if not diagnosed:
                dump_team_area(base_html)
                diagnosed = True
            continue

        if not recipe:
            recipe = used
            print(f"  전환 방식 확정: {used[0]} / {used[1]}")

        got = parse_roster(html, name, league)
        print(f"  {name}: {len(got)}명")
        people += got
        time.sleep(0.4)

    return people


def fallback_from_viewstate():
    """POST가 막힐 경우를 위한 1군 예비 경로(RegisterAll VIEWSTATE 직접 해독)."""
    print("\n--- 예비 경로: RegisterAll VIEWSTATE 파싱 ---")
    html = get(KBO_REGISTER_ALL)
    if not html:
        return []
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
            "job": job or "선수",
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


def fallback_futures_from_records():
    """퓨처스 전환이 막혔을 때 기록실에서라도 선수를 건진다(부분 수집)."""
    print("\n--- 예비 경로: 퓨처스 기록실 파싱 ---")
    people = []
    for url, job in ((FUTURES_HITTER, "타자"), (FUTURES_PITCHER, "투수")):
        html = get(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if "선수명" not in headers or "팀명" not in headers:
                continue
            i_name, i_team = headers.index("선수명"), headers.index("팀명")
            body = table.find("tbody") or table
            for tr in body.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) <= max(i_name, i_team):
                    continue
                pid, detail, retired = parse_player_link(tds[i_name])
                name = tds[i_name].get_text(strip=True)
                if not name:
                    continue
                people.append({
                    "playerId": pid,
                    "name": name,
                    "team": tds[i_team].get_text(strip=True),
                    "league": "퓨처스",
                    "job": job,
                    "role": "player",
                    "backNo": "",
                    "throwBat": "",
                    "birth": "",
                    "physique": "",
                    "detailUrl": detail,
                    "isRetiredRecord": retired,
                    "salary": {
                        "amount": None, "status": "미확인",
                        "season": None, "source": None,
                    },
                    "history": [],
                })
    print(f"  {len(people)}명 확보(규정타석·이닝 충족 선수 위주라 일부만 잡힙니다)")
    return people


def dedupe(people):
    """playerId 기준 전체 중복 제거. 먼저 들어온 1군 기록을 우선한다."""
    seen, out = set(), []
    for p in people:
        key = p["playerId"] or f'{p["name"]}|{p["team"]}|{p["backNo"]}'
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def main():
    print("=== KBO 선수·코치 명단 수집 시작 ===")

    people = collect(KBO_REGISTER, "1군", TEAM_CODE_NAME)
    if len({p["team"] for p in people}) < 8:
        print(f"1군 수집이 부족합니다(구단 {len({p['team'] for p in people})}개). 예비 경로로 전환합니다.")
        people += fallback_from_viewstate()

    try:
        futures = collect(FUTURES_REGISTER, "퓨처스", FUTURES_CODE_NAME)
    except Exception as e:
        print(f"퓨처스 수집 중 예외(1군 데이터는 유지): {e}")
        futures = []
    if len({p["team"] for p in futures}) < 6:
        futures += fallback_futures_from_records()
    people += futures

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
            teams = sorted({p["team"] for p in sub})
            print(f"  {lg}: {len(sub)}명, 구단 {len(teams)}개 → {', '.join(teams)}")

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
