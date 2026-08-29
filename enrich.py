import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE = "https://web1.koreabaseball.com"
OUT_PATH = "data/details.json"
SCHEMA_VERSION = 2          # 파싱 방식이 바뀌면 올린다(이전 수집분 자동 폐기)
REQUEST_DELAY = 0.4

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": BASE + "/",
}

PATH_PITCHER = "/Record/Player/PitcherDetail/Basic.aspx?playerId={pid}"
PATH_HITTER = "/Record/Player/HitterDetail/Basic.aspx?playerId={pid}"
PATH_F_PITCHER = "/Futures/Player/PitcherDetail.aspx?playerId={pid}"
PATH_F_HITTER = "/Futures/Player/HitterDetail.aspx?playerId={pid}"
PATH_R_PITCHER = "/Record/Retire/Pitcher.aspx?playerId={pid}"
PATH_R_HITTER = "/Record/Retire/Hitter.aspx?playerId={pid}"

PLAYER_PATHS = [PATH_PITCHER, PATH_HITTER, PATH_F_PITCHER, PATH_F_HITTER,
                PATH_R_PITCHER, PATH_R_HITTER]
COACH_PATHS = [PATH_R_HITTER, PATH_R_PITCHER, PATH_HITTER, PATH_PITCHER]

# 프로필에서 인정할 라벨(이 목록에 없으면 메뉴/광고로 보고 버린다)
LABELS = {
    "선수명": "name",
    "등번호": "backNo",
    "생년월일": "birth",
    "포지션": "position",
    "신장/체중": "physique",
    "경력": "career",
    "입단 계약금": "signingBonus",
    "입단계약금": "signingBonus",
    "연봉": "salary",
    "지명순위": "draft",
    "입단년도": "debutYear",
}

# 경력 문자열에서 프로 구단으로 인정할 이름
PRO_TEAMS = {
    "KT", "삼성", "LG", "KIA", "두산", "롯데", "한화", "NC", "SSG", "키움",
    "SK", "넥센", "우리", "서울", "히어로즈", "해태", "현대", "쌍방울",
    "태평양", "청보", "삼미", "빙그레", "OB", "MBC", "삼청", "롯데자이언츠",
}
MILITARY_TEAMS = {"상무", "경찰", "국군체육부대"}

session = requests.Session()
session.headers.update(HEADERS)


def fetch(url, retries=2):
    for i in range(retries):
        try:
            res = session.get(url, timeout=20)
            if res.status_code == 404:
                return None
            res.raise_for_status()
            res.encoding = "utf-8"
            return res.text
        except Exception as e:
            if i == retries - 1:
                print(f"    요청 실패: {e}")
                return None
            time.sleep(1.5 * (i + 1))
    return None


def parse_profile(html):
    """프로필 목록에서 '라벨: 값' 쌍만 골라 읽는다.
    라벨을 정확히 대조하므로 '경력증명서 신청' 같은 메뉴에 오염되지 않는다."""
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    out = {}

    for el in soup.find_all(["li", "td", "dd", "p", "span"]):
        if el.find(["li", "td", "dd"]):
            continue  # 다른 항목을 품고 있으면 컨테이너이므로 건너뜀
        text = el.get_text(" ", strip=True)
        if ":" not in text:
            continue
        label, value = text.split(":", 1)
        key = LABELS.get(label.strip())
        if not key:
            continue
        value = value.strip()
        if value and key not in out:
            out[key] = value
    return out


def format_krw(man):
    eok, rem = divmod(man, 10000)
    if eok and rem:
        return f"{eok}억 {rem:,}만원"
    if eok:
        return f"{eok}억원"
    return f"{rem:,}만원"


def parse_salary(raw):
    """'20000만원' -> (200000000, 'KRW', '2억원')"""
    if not raw:
        return None, None, None
    cleaned = raw.replace(",", "").replace(" ", "")

    m = re.search(r"(\d+(?:\.\d+)?)만?달러", cleaned)
    if m:
        num = float(m.group(1))
        if "만" in cleaned:
            return int(num * 10000), "USD", f"{m.group(1)}만 달러"
        return int(num), "USD", f"{int(num):,} 달러"

    m = re.search(r"(\d+)만원", cleaned)
    if m:
        man = int(m.group(1))
        return man * 10000, "KRW", format_krw(man)

    m = re.search(r"(\d+)억", cleaned)
    if m:
        return int(m.group(1)) * 100000000, "KRW", f"{m.group(1)}억원"

    return None, None, None


def parse_career(raw):
    """'가동초-청원중-휘문고-LG-경찰' -> 학교/프로 구분"""
    if not raw:
        return [], []
    tokens = [t.strip() for t in re.split(r"[-–—]", raw) if t.strip()]
    pro = []
    for t in tokens:
        name = t.strip("()（） ")
        if name in PRO_TEAMS or name in MILITARY_TEAMS:
            if not pro or pro[-1]["team"] != name:
                pro.append({
                    "team": name,
                    "type": "military" if name in MILITARY_TEAMS else "pro",
                })
    return tokens, pro


def build_history(pro, current_team, debut_year):
    """프로 구단 이력을 순서대로 만든다. 군팀 복무 뒤 원소속 복귀도 반영."""
    history = []
    for i, item in enumerate(pro):
        if item["type"] == "military":
            note = "군 복무"
        elif i == 0:
            note = "입단"
        else:
            note = "이적"
        history.append({"order": len(history) + 1, "team": item["team"], "note": note})

    # 군팀에서 끝났는데 현 소속팀이 따로 있으면 복귀 항목을 붙인다
    if current_team and (not history or history[-1]["team"] != current_team):
        note = "복귀" if history and history[-1]["team"] in MILITARY_TEAMS else "현 소속"
        history.append({"order": len(history) + 1, "team": current_team, "note": note})

    if history and debut_year:
        history[0]["debut"] = debut_year
    return history


def enrich_one(person):
    pid = person.get("playerId")
    if not pid:
        return None

    is_coach = person.get("role") == "coach"
    paths = COACH_PATHS if (is_coach or person.get("isRetiredRecord")) else PLAYER_PATHS

    best, used = {}, None
    for path in paths:
        url = BASE + path.format(pid=pid)
        html = fetch(url)
        time.sleep(REQUEST_DELAY)
        if not html:
            continue
        prof = parse_profile(html)
        if not prof.get("career") and not prof.get("salary"):
            continue
        # 더 많은 항목을 가진 페이지를 채택
        if len(prof) > len(best):
            best, used = prof, url
        if prof.get("salary") and prof.get("career"):
            break

    if not best:
        return None

    amount, currency, display = parse_salary(best.get("salary"))
    tokens, pro = parse_career(best.get("career"))

    if amount is not None:
        status = "공시"
    elif is_coach:
        status = "비공개"
    else:
        status = "미공시"

    return {
        "schemaVersion": SCHEMA_VERSION,
        "playerId": pid,
        "name": person.get("name"),
        "sourceUrl": used,
        "salary": {
            "amount": amount,
            "currency": currency,
            "display": display,
            "status": status,
            "raw": best.get("salary"),
        },
        "signingBonus": best.get("signingBonus"),
        "careerRaw": best.get("career"),
        "careerTokens": tokens,
        "history": build_history(pro, person.get("team"), best.get("debutYear")),
        "draft": best.get("draft"),
        "debutYear": best.get("debutYear"),
        "position": best.get("position"),
        "birth": best.get("birth"),
        "physique": best.get("physique"),
    }


def save(results):
    os.makedirs("data", exist_ok=True)
    items = list(results.values())
    out = {
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schemaVersion": SCHEMA_VERSION,
        "count": len(items),
        "salaryCount": sum(1 for i in items if i["salary"]["amount"] is not None),
        "historyCount": sum(1 for i in items if i["history"]),
        "details": items,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def main():
    people = []
    seen = set()

    for path in ("data/players_all.json", "data/players.json"):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            base = json.load(f)
        rows = base["people"] if isinstance(base, dict) else base
        for p in rows:
            pid = p.get("playerId")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            people.append(p)
        print(f"{path} 반영 후 누적 {len(people)}명")

    if not people:
        raise RuntimeError("명단 파일이 없습니다. collect_all.py를 먼저 실행하세요.")


    # 이전 수집분은 같은 스키마 버전일 때만 재사용
    results = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as f:
            prev = json.load(f)
        if prev.get("schemaVersion") == SCHEMA_VERSION:
            for it in prev.get("details", []):
                results[it["playerId"]] = it
            print(f"기존 수집분 {len(results)}건 재사용")
        else:
            print("파싱 방식이 바뀌어 전체를 다시 수집합니다.")

    total = len(people)
    for i, p in enumerate(people, 1):
        pid = p.get("playerId")
        if not pid or pid in results:
            continue
        print(f"[{i}/{total}] {p.get('team')} {p.get('name')}", flush=True)
        info = enrich_one(p)
        if info:
            results[pid] = info
            sal = info["salary"]["display"] or info["salary"]["status"]
            path = " → ".join(h["team"] for h in info["history"]) or "이력 없음"
            print(f"    연봉 {sal} | {path}", flush=True)
        else:
            print("    상세 정보 없음", flush=True)

        if i % 50 == 0:
            save(results)
            print(f"  -- 중간 저장 {len(results)}건 --", flush=True)

    save(results)

    items = list(results.values())
    salary_ok = sum(1 for it in items if it["salary"]["amount"] is not None)
    history_ok = sum(1 for it in items if it["history"])
    career_ok = sum(1 for it in items if it.get("careerRaw"))

    print("\n=== 수집 완료 ===")
    print(f"대상 인원   : {total}명")
    print(f"상세 확보   : {len(items)}명")
    print(f"연봉 확보   : {salary_ok}명")
    print(f"경력 확보   : {career_ok}명")
    print(f"이력 생성   : {history_ok}명")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[실패] {e}", file=sys.stderr)
        sys.exit(1)
