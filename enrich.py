import json
import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://web1.koreabaseball.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 연봉을 찾기 위해 순서대로 시도할 상세 페이지 경로들
CANDIDATE_PATHS = [
    "/Record/Player/PitcherDetail/Basic.aspx?playerId={pid}",
    "/Record/Player/HitterDetail/Basic.aspx?playerId={pid}",
    "/Futures/Player/PitcherDetail.aspx?playerId={pid}",
    "/Futures/Player/HitterDetail.aspx?playerId={pid}",
    "/Record/Retire/Pitcher.aspx?playerId={pid}",
    "/Record/Retire/Hitter.aspx?playerId={pid}",
]

REQUEST_DELAY = 0.4          # KBO 서버 배려용 요청 간격(초)
OUT_PATH = "data/details.json"

# 프로 구단으로 인정할 토큰(경력 문자열에서 학교를 걸러내기 위함)
PRO_TEAMS = {
    "KT", "삼성", "LG", "KIA", "두산", "롯데", "한화", "NC", "SSG", "키움",
    "SK", "넥센", "히어로즈", "해태", "현대", "쌍방울", "태평양", "청보",
    "삼미", "빙그레", "OB", "MBC", "상무", "경찰",
}


def fetch(url, retries=2):
    for i in range(retries):
        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
            if res.status_code == 404:
                return None
            res.raise_for_status()
            res.encoding = res.apparent_encoding or "utf-8"
            return res.text
        except Exception as e:
            if i == retries - 1:
                print(f"    요청 실패: {url} ({e})")
                return None
            time.sleep(1.5 * (i + 1))
    return None


def parse_profile(html):
    """상세 페이지 프로필 영역에서 연봉/계약금/경력/지명순위 등을 추출."""
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    def grab(label):
        # "연봉: 26000만원" 또는 "연봉\n26000만원" 형태 모두 대응
        m = re.search(rf"{label}\s*[:：]?\s*\n?\s*([^\n]{{1,80}})", text)
        return m.group(1).strip() if m else None

    profile = {
        "salaryRaw": grab("연봉"),
        "signingBonusRaw": grab("입단 계약금"),
        "careerRaw": grab("경력") or grab("출신교"),
        "draftRaw": grab("지명순위"),
        "debutRaw": grab("입단년도"),
        "positionRaw": grab("포지션"),
    }
    return profile


def parse_salary(raw):
    """'26000만원' / '180만 달러' 등을 금액과 통화로 분해."""
    if not raw:
        return None, None, None

    cleaned = raw.replace(",", "").strip()

    # 달러 표기(외국인 선수)
    m = re.search(r"([\d.]+)\s*만\s*달러", cleaned)
    if m:
        man = float(m.group(1))
        return int(man * 10000), "USD", f"{m.group(1)}만 달러"

    # 만원 표기(국내 선수)
    m = re.search(r"(\d+)\s*만\s*원", cleaned)
    if m:
        man_won = int(m.group(1))
        return man_won * 10000, "KRW", format_krw(man_won)

    return None, None, None


def format_krw(man_won):
    """13500(만원) -> '1억 3,500만원' 형태로 사람이 읽기 쉽게 변환."""
    eok, man = divmod(man_won, 10000)
    if eok and man:
        return f"{eok}억 {man:,}만원"
    if eok:
        return f"{eok}억원"
    return f"{man:,}만원"


def parse_career(raw):
    """'수진초-매송중-야탑고-SK-SSG' -> 프로 구단 이력만 순서대로 추출."""
    if not raw:
        return [], []

    tokens = [t.strip() for t in re.split(r"[-–—]", raw) if t.strip()]
    pro = []
    for t in tokens:
        # 괄호 표기(예: '(디지털문예대)')는 제외
        name = t.strip("()")
        if name in PRO_TEAMS:
            # 연속 중복은 합치되, 복귀(해태-삼성-해태)는 살림
            if not pro or pro[-1] != name:
                pro.append(name)
    return tokens, pro


def build_history(pro_teams, debut_raw):
    """프로 구단 순서를 타임라인 형태로 변환."""
    history = []
    for idx, team in enumerate(pro_teams):
        history.append({
            "order": idx + 1,
            "team": team,
            "note": "입단" if idx == 0 else "이적",
        })
    if history and debut_raw:
        history[0]["debut"] = debut_raw
    return history


def enrich_one(person):
    pid = person.get("playerId")
    if not pid:
        return None

    # 현역/지도자에 따라 시도 순서를 조정해 요청 수를 줄임
    paths = list(CANDIDATE_PATHS)
    if person.get("role") == "coach" or person.get("isRetiredRecord"):
        paths = CANDIDATE_PATHS[4:] + CANDIDATE_PATHS[:4]

    elif "투수" in (person.get("job") or ""):
        pass  # 투수 경로가 이미 먼저임
    else:
        paths = [CANDIDATE_PATHS[1], CANDIDATE_PATHS[0]] + CANDIDATE_PATHS[2:]

    best = {}
    used_url = None

    for path in paths:
        url = BASE + path.format(pid=pid)
        html = fetch(url)
        if not html:
            continue
        profile = parse_profile(html)
        if not any(profile.values()):
            continue

        # 더 많은 정보를 담은 결과를 채택
        if profile.get("salaryRaw") or profile.get("careerRaw"):
            best = profile
            used_url = url
            # 연봉까지 확보했으면 더 볼 필요 없음
            if profile.get("salaryRaw"):
                break

        time.sleep(REQUEST_DELAY)

    if not best:
        return None

    amount, currency, display = parse_salary(best.get("salaryRaw"))
    tokens, pro_teams = parse_career(best.get("careerRaw"))

    is_coach = person.get("role") == "coach"

    if amount is not None:
        status = "공시"
    elif is_coach:
        status = "비공개"
    else:
        status = "미공시"

    return {
        "playerId": pid,
        "name": person.get("name"),
        "sourceUrl": used_url,
        "salary": {
            "amount": amount,
            "currency": currency,
            "display": display,
            "status": status,
            "raw": best.get("salaryRaw"),
        },
        "signingBonus": best.get("signingBonusRaw"),
        "careerRaw": best.get("careerRaw"),
        "careerTokens": tokens,
        "history": build_history(pro_teams, best.get("debutRaw")),
        "draft": best.get("draftRaw"),
        "debut": best.get("debutRaw"),
    }


def main():
    if not os.path.exists("data/players.json"):
        raise RuntimeError("data/players.json이 없습니다. crawl.py를 먼저 실행하세요.")

    with open("data/players.json", encoding="utf-8") as f:
        base = json.load(f)

    people = base["people"] if isinstance(base, dict) else base

    # 기존 결과가 있으면 이어서 진행(증분 수집)
    existing = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as f:
            prev = json.load(f)
        for item in prev.get("details", []):
            existing[item["playerId"]] = item
        print(f"기존 수집분 {len(existing)}건을 재사용합니다.")

    results = dict(existing)
    total = len(people)
    salary_found = 0

    for i, person in enumerate(people, 1):
        pid = person.get("playerId")
        if not pid:
            continue

        # 이미 연봉까지 확보된 인원은 건너뜀
        prev = results.get(pid)
        if prev and prev.get("salary", {}).get("amount") is not None:
            salary_found += 1
            continue

        print(f"[{i}/{total}] {person.get('team')} {person.get('name')} ...")
        info = enrich_one(person)
        if info:
            results[pid] = info
            if info["salary"]["amount"] is not None:
                salary_found += 1
                print(f"    연봉: {info['salary']['display']}")
            else:
                print(f"    연봉 없음 ({info['salary']['status']})")
        else:
            print("    상세 정보 없음")

        time.sleep(REQUEST_DELAY)

        # 중간 저장(장시간 작업 중 중단 대비)
        if i % 50 == 0:
            save(results)
            print(f"  -- 중간 저장 ({len(results)}건) --")

    save(results)

    print("\n=== 수집 완료 ===")
    print(f"대상 인원: {total}명")
    print(f"상세 확보: {len(results)}명")
    print(f"연봉 확보: {salary_found}명")


def save(results):
    os.makedirs("data", exist_ok=True)
    out = {
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "count": len(results),
        "details": list(results.values()),
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[실패] {e}", file=sys.stderr)
        sys.exit(1)
