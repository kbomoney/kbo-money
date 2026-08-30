import json, re, time, urllib.parse, urllib.request

DETAIL_PATH = "data/details.json"
SAMPLE = 5
API = "https://archive.org/wayback/available"
UA = {"User-Agent": "Mozilla/5.0 (compatible; kbo-money/1.0)"}


def fetch(url, timeout=30, tries=2):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(3)
    raise last


def find_salary(html):
    text = re.sub(r"<[^>]+>", "|", html)
    text = re.sub(r"\s+", " ", text)
    i = text.find("연봉")
    if i < 0:
        return "'연봉' 문자열 없음"
    return "주변: " + text[i:i + 120]


def main():
    with open(DETAIL_PATH, encoding="utf-8") as f:
        items = json.load(f)["details"]

    targets = []
    for p in items:
        url = str(p.get("sourceUrl") or "")
        sal = p.get("salary") or {}
        if "koreabaseball" not in url or sal.get("amount") is None:
            continue
        cur = sal.get("display") or sal.get("amount")
        targets.append((p.get("name"), url.replace("web1.", "www."), cur))
        if len(targets) >= SAMPLE:
            break

    print("조회 대상:", len(targets), "명")

    for i, (name, url, cur) in enumerate(targets, 1):
        src = url.split("://", 1)[-1]
        q = API + "?url=" + urllib.parse.quote(src, safe="") + "&timestamp=20250601"
        print(f"\n{i}. {name} (현재 2026 값: {cur})")
        try:
            snap = (json.loads(fetch(q)).get("archived_snapshots") or {}).get("closest")
            if not snap:
                print("   스냅샷 없음")
                continue
            ts = snap.get("timestamp", "")
            print("   스냅샷 시점:", ts)
            arch = snap["url"].replace("http://", "https://")
            html = fetch(arch, timeout=45)
            print("   HTML 길이:", len(html))
            print("   추출:", find_salary(html))
        except Exception as e:
            print("   실패:", type(e).__name__, e)
        time.sleep(3)


if __name__ == "__main__":
    main()
