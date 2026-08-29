"""연도별 연봉 이력 파일을 만든다.

details.json 의 '올해 연봉'을 salary_history.json 에 해당 연도로 기록한다.
손으로 넣은 과거 연봉(source=manual)은 건드리지 않는다.
매년 이 스크립트가 돌면 그해 연봉이 한 줄씩 쌓인다.
"""

import json
import os

SEASON = 2026                       # 기록할 시즌(매년 바꿔주면 된다)
DETAIL_PATH = "data/details.json"
OUT_PATH = "data/salary_history.json"
NAME_PATHS = ["data/players_all.json", "data/players.json"]


def load(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def team_map():
    """playerId -> 현재 구단"""
    teams = {}
    for path in NAME_PATHS:
        data = load(path)
        if not data:
            continue
        rows = data["people"] if isinstance(data, dict) else data
        for p in rows:
            pid = str(p.get("playerId") or "")
            if pid and pid not in teams:
                teams[pid] = p.get("team") or ""
    return teams


def main():
    detail = load(DETAIL_PATH)
    if not detail:
        raise RuntimeError("data/details.json 이 없습니다. enrich 를 먼저 실행하세요.")

    teams = team_map()
    history = load(OUT_PATH) or {}
    players = history.get("players", {}) if isinstance(history, dict) else {}

    added = 0
    updated = 0
    kept_manual = 0

    for d in detail.get("details", []):
        pid = str(d.get("playerId") or "")
        salary = d.get("salary") or {}
        amount = salary.get("amount")
        if not pid or amount is None:
            continue        # 감독·코치 등 연봉 비공개는 건너뜀

        entry = players.setdefault(pid, {"name": d.get("name"), "salaries": []})
        entry["name"] = d.get("name") or entry.get("name")

        row = {
            "year": SEASON,
            "team": teams.get(pid, ""),
            "amount": amount,
            "currency": salary.get("currency") or "KRW",
            "display": salary.get("display"),
            "source": "kbo",
        }

        for i, old in enumerate(entry["salaries"]):
            if old.get("year") != SEASON:
                continue
            if old.get("source") == "manual":
                kept_manual += 1     # 손으로 고친 값은 존중한다
            else:
                entry["salaries"][i] = row
                updated += 1
            break
        else:
            entry["salaries"].append(row)
            added += 1

        entry["salaries"].sort(key=lambda r: r.get("year", 0))

    out = {
        "season": SEASON,
        "players": players,
        "playerCount": len(players),
        "note": "source=kbo 는 자동 수집분, source=manual 은 직접 입력분",
    }

    os.makedirs("data", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    rows = sum(len(v["salaries"]) for v in players.values())

    print("\n=== 연봉 이력 갱신 ===")
    print(f"시즌        : {SEASON}")
    print(f"신규 기록   : {added}건")
    print(f"갱신 기록   : {updated}건")
    print(f"수동값 유지 : {kept_manual}건")
    print(f"대상 인원   : {len(players)}명")
    print(f"총 연봉 줄  : {rows}건")
    print(f"저장        : {OUT_PATH}")


if __name__ == "__main__":
    main()
