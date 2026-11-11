"""알바리치 '전국 웨딩 박람회 일정' 공개 페이지에서 박람회 목록을 받아 data/fairs.json 으로 저장합니다.

사용법:  python tools/fetch_fairs.py      (그다음 python tools/build.py)

- 원본 페이지는 매주 업데이트됩니다. 배포 전에 한 번씩 실행하세요.
- 신청 링크는 사이트 전체에서 통합 캠페인 링크 하나(site.json 의 fair_link)만 씁니다.
- 원본의 배너 이미지는 가져오지 않습니다(텍스트 정보만 사용).
"""
import datetime
import html
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_URL = "https://albarich.com/intro/weddingA/"


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def kind_of(name):
    n = name.replace(" ", "")
    if re.search(r"허니문|신혼여행", n): return "honeymoon"
    if re.search(r"한복", n): return "hanbok"
    if re.search(r"드레스|스드메|토탈샵|상담", n): return "sdm"
    return "fair"


def main():
    req = urllib.request.Request(SRC_URL, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=30).read()
    try:
        h = raw.decode("utf-8")
    except UnicodeDecodeError:
        h = raw.decode("cp949", errors="ignore")

    fairs, seen = [], set()
    for sec in re.split(r'<div class="contents" id="sec\d+"', h)[1:]:
        region = clean((re.search(r"<h2>(.*?)</h2>", sec, re.S) or [None, ""])[1]).replace("웨딩박람회 일정", "").strip()
        for m in re.finditer(r'<a href="/intro/([^/"]+)/?"[^>]*>\s*<ul class="list1">(.*?)</ul>', sec, re.S):
            slug, body = m.group(1), m.group(2)
            lis = re.findall(r"<li>(.*?)</li>", body, re.S)
            district = clean(lis[0]) if lis else ""
            name = clean((re.search(r'class="naming">(.*?)</p>', body, re.S) or [None, ""])[1])
            time = clean((re.search(r'class="time">(.*?)</p>', body, re.S) or [None, ""])[1])
            area = clean((re.search(r'class="area">(.*?)</p>', body, re.S) or [None, ""])[1])
            d = re.findall(r"(\d{4})\.(\d{2})\.(\d{2})", time)
            if not name or len(d) < 1:
                continue
            start = "-".join(d[0]); end = "-".join(d[-1])
            fid = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-") + "-" + start.replace("-", "")[4:]
            if fid in seen:
                continue
            seen.add(fid)
            # 같은 주소가 두 번 붙은 경우 정리 (예: "수원 메쎄 전시장 수원 메쎄 전시장")
            words = area.split(" ")
            for k in range(len(words) // 2, 1, -1):
                for i in range(len(words) - 2 * k + 1):
                    if words[i:i + k] == words[i + k:i + 2 * k]:
                        words = words[:i + k] + words[i + 2 * k:]
                        break
            area = " ".join(words)
            fairs.append({"id": fid, "region": region, "district": district, "name": name,
                          "start": start, "end": end, "address": area, "kind": kind_of(name)})

    fairs.sort(key=lambda f: (f["start"], f["end"], f["region"], f["name"]))
    out = {"source": SRC_URL, "fetched": datetime.date.today().isoformat(), "fairs": fairs}
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "fairs.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    regions = {}
    for f in fairs:
        regions[f["region"]] = regions.get(f["region"], 0) + 1
    print(f"박람회 {len(fairs)}개 저장 · " + ", ".join(f"{k} {v}" for k, v in regions.items()))


if __name__ == "__main__":
    main()
