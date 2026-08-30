import json, time, urllib.request, urllib.parse


DETAIL_PATH = "data/details.json"
SAMPLE = 20
CDX = "https://web.archive.org/cdx/search/cdx"

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "kbo-money/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def main():
    with open(DETAIL_PATH, encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items") or data.get("players") or data
    if isinstance(items, dict):
        items = list(items.values())

    targets = [x for x in items if x.get("sourceUrl") or x.get("detailUrl")][:SAMPLE]
    hit = 0

    for i, p in enumerate(targets, 1):
        src = (p.get("sourceUrl") or p.get("detailUrl")).replace("https://", "").replace("http://", "")
        q = (f"{CDX}?url={urllib.parse.quote(src, safe='')}"
             "&from=20250301&to=20251031&output=json&limit=3&filter=statuscode:200")
        try:
            rows = json.loads(fetch(q) or "[]")
            snaps = rows[1:] if rows else []
        except Exception as e:
            print(f"{i:2d}. {p.get('name')} - 조회 실패: {e}")
            time.sleep(3)
            continue

        if snaps:
            hit += 1
            print(f"{i:2d}. {p.get('name')} - 스냅샷 {len(snaps)}건 (예: {snaps[0][1]})")
        else:
            print(f"{i:2d}. {p.get('name')} - 없음")
        time.sleep(3)

    print(f"\n표본 {len(targets)}명 중 {hit}명 스냅샷 존재 ({hit*100//max(len(targets),1)}%)")

if __name__ == "__main__":
    main()
