import json, time, urllib.parse, urllib.request

DETAIL_PATH = "data/details.json"
SAMPLE = 20
CDX = "https://web.archive.org/cdx/search/cdx"
UA = {"User-Agent": "Mozilla/5.0 (compatible; kbo-money/1.0)"}


def fetch(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def load_items(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print("최상위 타입:", type(data).__name__)

    items = None
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("items", "players", "people", "details", "data"):
            v = data.get(key)
            if isinstance(v, list):
                items = v
                print("목록 키:", key)
                break
            if isinstance(v, dict):
                items = list(v.values())
                print("목록 키:", key, "(dict)")
                break
        if items is None:
            items = [v for v in data.values() if isinstance(v, dict)]
            print("최상위 dict 값들을 목록으로 사용")
    else:
        items = []

    items = [x for x in items if isinstance(x, dict)]
    print("항목 수:", len(items))
    if items:
        print("첫 항목 키:", ", ".join(list(items[0].keys())[:15]))
    return items


def pick_url(p):
    for k in ("sourceUrl", "detailUrl", "url", "source", "link"):
        v = p.get(k)
        if isinstance(v, str) and "koreabaseball" in v:
            return v
    return None


def main():
    items = load_items(DETAIL_PATH)

    targets = []
    for p in items:
        u = pick_url(p)
        if u:
            targets.append((p.get("name") or p.get("playerId") or "?", u))
        if len(targets) >= SAMPLE:
            break

    print("조회 대상:", len(targets), "명\n")
    if not targets:
        print("URL 필드를 찾지 못했습니다. 위에 출력된 '첫 항목 키'를 알려주세요.")
        return

    hit = 0
    for i, (name, url) in enumerate(targets, 1):
        src = url.split("://", 1)[-1]
        q = (CDX + "?url=" + urllib.parse.quote(src, safe="")
             + "&from=20250301&to=20251031&output=json&limit=3&filter=statuscode:200")
        try:
            body = fetch(q).strip()
            rows = json.loads(body) if body else []
            snaps = rows[1:] if len(rows) > 1 else []
            if snaps:
                hit += 1
                print(f"{i:2d}. {name} - 스냅샷 {len(snaps)}건 (예: {snaps[0][1]})")
            else:
                print(f"{i:2d}. {name} - 없음")
        except Exception as e:
            print(f"{i:2d}. {name} - 조회 실패: {type(e).__name__} {e}")
        time.sleep(3)

    pct = hit * 100 // len(targets)
    print(f"\n표본 {len(targets)}명 중 {hit}명 스냅샷 존재 ({pct}%)")


if __name__ == "__main__":
    main()
