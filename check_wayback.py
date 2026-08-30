import json, time, urllib.parse, urllib.request

DETAIL_PATH = "data/details.json"
SAMPLE = 20
API = "https://archive.org/wayback/available"
UA = {"User-Agent": "Mozilla/5.0 (compatible; kbo-money/1.0)"}


def fetch(url, timeout=25, tries=2):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(2)
    raise last


def main():
    with open(DETAIL_PATH, encoding="utf-8") as f:
        items = json.load(f)["details"]

    targets = []
    for p in items:
        pos = str(p.get("position") or "")
        url = str(p.get("sourceUrl") or "")
        if "감독" in pos or "코치" in pos or "Retire" in url:
            continue
        if "koreabaseball" not in url:
            continue
        targets.append((p.get("name"), url.replace("web1.", "www.")))
        if len(targets) >= SAMPLE:
            break

    print("조회 대상:", len(targets), "명\n")
    hit = 0

    for i, (name, url) in enumerate(targets, 1):
        src = url.split("://", 1)[-1]
        q = API + "?url=" + urllib.parse.quote(src, safe="") + "&timestamp=20250601"
        try:
            snap = (json.loads(fetch(q)).get("archived_snapshots") or {}).get("closest")
            if snap:
                ts = snap.get("timestamp", "")
                mark = "O" if ts.startswith("2025") else "x(연도불일치)"
                if ts.startswith("2025"):
                    hit += 1
                print(f"{i:2d}. {name} - {mark} {ts}")
            else:
                print(f"{i:2d}. {name} - 없음")
        except Exception as e:
            print(f"{i:2d}. {name} - 실패: {type(e).__name__}")
        time.sleep(2)

    print(f"\n표본 {len(targets)}명 중 2025년 스냅샷 {hit}명 ({hit*100//max(len(targets),1)}%)")


if __name__ == "__main__":
    main()
