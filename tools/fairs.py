"""전국 웨딩박람회 일정 페이지(/fairs) 하나를 만듭니다. build.py 가 불러 씁니다.

데이터: data/fairs.json  (python tools/fetch_fairs.py 로 갱신)
신청 링크: site.json 의 fair_link (알바리치 '전국 웨딩 박람회 일정' 통합 링크 하나)
"""
import datetime
import html
import json
import re
import urllib.parse

WD = "월화수목금토일"
KIND = {
    "fair": ("웨딩박람회", "💒"),
    "honeymoon": ("신혼여행 박람회", "✈️"),
    "sdm": ("스드메 상담", "👗"),
    "hanbok": ("한복 상담", "🎎"),
}
INTRO = {
    "fair": "웨딩박람회에서는 예식장, 스튜디오·드레스·메이크업(스드메), 예물, 혼수, 신혼여행 상담을 한자리에서 받을 수 있어요. "
            "여러 업체의 조건을 하루에 비교할 수 있어서 결혼 준비 초반에 많이 찾아요.",
    "honeymoon": "신혼여행 박람회에서는 여러 여행사의 허니문 상품과 일정을 한 번에 비교하고 상담받을 수 있어요. "
                 "여행지와 예산, 출발 시기를 정해 가면 상담이 훨씬 빨라요.",
    "sdm": "스튜디오·드레스·메이크업 구성을 직접 보고 상담받을 수 있는 곳이에요. "
           "드레스 스타일과 촬영 콘셉트를 미리 생각해 가면 비교하기 쉬워요.",
    "hanbok": "신랑·신부와 혼주 한복을 직접 보고 맞춤 상담을 받을 수 있는 곳이에요. "
              "예식 날짜와 원하는 색감을 미리 정해 가면 좋아요.",
}
PREP = {
    "fair": [("예식 예정 시기와 지역", "날짜가 정해지지 않았어도 희망 계절과 지역을 정해 가면 상담이 구체적이에요."),
             ("예산 범위", "예식장, 스드메, 신혼여행 등 큰 항목별 한도를 대략 정해 두세요."),
             ("예상 하객 수", "예식장 보증 인원과 식대를 비교할 때 꼭 필요해요."),
             ("당일 계약은 천천히", "견적서와 포함 항목을 받아 와서 집에서 비교한 뒤 결정해도 늦지 않아요.")],
    "honeymoon": [("여행 기간과 출발일", "예식 다음 날 출발인지, 며칠 쉬고 출발하는지 정해 가세요."),
                  ("원하는 여행 스타일", "휴양, 관광, 액티비티 중 무엇을 원하는지 둘이 먼저 이야기해 보세요."),
                  ("여권 만료일", "출발일 기준 6개월 이상 남았는지 확인하세요."),
                  ("포함·불포함 항목", "항공, 숙소, 식사, 현지 경비 포함 여부를 꼭 비교하세요.")],
    "sdm": [("원하는 스타일 사진", "마음에 드는 드레스·촬영 사진을 몇 장 저장해 가세요."),
            ("예식일과 촬영 희망 시기", "촬영은 보통 예식 3~5개월 전에 해요."),
            ("추가 비용 항목", "드레스 업그레이드, 원본 사진, 헬퍼 비용 등 추가금 항목을 확인하세요.")],
    "hanbok": [("예식일", "맞춤 한복은 제작 기간이 필요해요."),
               ("입을 사람과 인원", "신랑·신부, 양가 혼주 중 누구 한복을 맞출지 정해 가세요."),
               ("대여와 맞춤 비교", "대여와 맞춤의 조건을 함께 물어보세요.")],
}


def e(s):
    return html.escape(str(s), quote=True)


def d_of(s):
    y, m, d = map(int, s.split("-"))
    return datetime.date(y, m, d)


def period(f):
    a, b = d_of(f["start"]), d_of(f["end"])
    fa = f"{a.month}월 {a.day}일({WD[a.weekday()]})"
    if a == b:
        return fa
    fb = (f"{b.day}일" if (a.year, a.month) == (b.year, b.month) else f"{b.month}월 {b.day}일") + f"({WD[b.weekday()]})"
    return f"{fa} ~ {fb}"


def load(root):
    p = root / "data" / "fairs.json"
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    today = datetime.date.today().isoformat()
    data["fairs"] = [f for f in data["fairs"] if f["end"] >= today]
    return data


def style_of(index_html):
    m = re.search(r"<style>.*?</style>", index_html, re.S)
    return m.group(0) if m else ""


EXTRA_CSS = """<style>
  .disclosure { font-size: 12px; color: var(--muted); padding: 12px 0 0; line-height: 1.5; margin: 0; }
  .back { display: inline-flex; gap: 4px; margin-top: 14px; color: var(--sub); font-weight: 600; font-size: 15px; text-decoration: none; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
  .chips button { font: inherit; font-size: 14px; font-weight: 700; color: var(--sub); background: var(--soft); border: 0; border-radius: 99px; padding: 7px 13px; cursor: pointer; }
  .chips button[aria-pressed=true] { background: var(--accent); color: #fff; }
  .wk { font-size: 14px; font-weight: 800; color: var(--accent-text); margin: 22px 4px 8px; }
  .fl { display: grid; gap: 8px; }
  .fi { display: flex; gap: 12px; align-items: center; background: var(--card); border-radius: 16px; padding: 14px; text-decoration: none; color: var(--text); box-shadow: var(--shadow); }
  .fi:hover { background: var(--soft); }
  .fi .ic { width: 44px; height: 44px; flex: none; border-radius: 12px; background: var(--accent-soft); display: grid; place-items: center; font-size: 22px; }
  .fi b { display: block; font-size: 16px; line-height: 1.4; }
  .fi small { display: block; font-size: 13px; color: var(--sub); }
  .fi .go { margin-left: auto; color: var(--muted); font-size: 20px; flex: none; }
  .badge { display: inline-block; font-size: 11px; font-weight: 800; color: var(--accent-text); background: var(--accent-soft); border-radius: 6px; padding: 1px 6px; margin-right: 4px; vertical-align: 1px; }
  .cta { display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 16px; font-weight: 700;
    border-radius: 14px; padding: 15px 16px; background: var(--accent); color: #fff; margin-top: 16px; }
  .cta:hover { background: var(--accent-press); }
  .cta.ghost { background: var(--accent-soft); color: var(--accent-text); }
  .info { width: 100%; border-collapse: collapse; font-size: 15px; }
  .info th, .info td { text-align: left; padding: 11px 4px; border-top: 1px solid var(--line); vertical-align: top; }
  .info tr:first-child th, .info tr:first-child td { border-top: 0; }
  .info th { width: 72px; color: var(--sub); font-weight: 700; white-space: nowrap; }
  .points { list-style: none; padding: 0; margin: 0; counter-reset: p; }
  .points li { counter-increment: p; display: flex; gap: 12px; padding: 12px 0; border-top: 1px solid var(--line); }
  .points li:first-child { border-top: 0; padding-top: 0; }
  .points li::before { content: counter(p); flex: none; width: 26px; height: 26px; border-radius: 50%; background: var(--accent-soft);
    color: var(--accent-text); font-weight: 800; font-size: 14px; display: grid; place-items: center; }
  .points b { display: block; }
  .points span { color: var(--sub); font-size: 14px; }
  .note { font-size: 13px; color: var(--muted); margin: 10px 0 0; }
  .empty { color: var(--muted); text-align: center; padding: 28px 0; }
  .fc { background: var(--card); border-radius: 18px; padding: 16px; box-shadow: var(--shadow); }
  .fh { display: flex; gap: 12px; align-items: center; }
  .fh .ic { width: 44px; height: 44px; flex: none; border-radius: 12px; background: var(--accent-soft); display: grid; place-items: center; font-size: 22px; }
  .fh b { display: block; font-size: 16px; line-height: 1.4; }
  .fh small { display: block; font-size: 13px; color: var(--sub); }
  .fd { display: grid; gap: 2px; margin-top: 10px; font-size: 14px; color: var(--sub); }
  .fb { display: grid; grid-template-columns: 1fr auto; gap: 8px; margin-top: 12px; }
  .fb a { text-decoration: none; font-size: 15px; font-weight: 700; border-radius: 12px; padding: 11px 14px; text-align: center; }
  .fb .ap { background: var(--accent); color: #fff; }
  .fb .ap:hover { background: var(--accent-press); }
  .fb .mp { background: var(--soft); color: var(--sub); }
</style>"""

DISCLOSURE = "이 페이지의 초대권·상담 신청 링크는 제휴 광고 링크이며, 신청 후 상담이 이루어지면 운영자가 수수료를 받을 수 있습니다. 신청과 박람회 입장은 무료입니다."


def head(title, seo, style, theme):
    return (f'<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{e(title)}</title>\n<meta name="theme-color" content="{theme}">\n{seo}\n'
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">\n'
            f'{style}\n{EXTRA_CSS}\n</head>\n')


def card(f, cfg):
    kname, icon = KIND[f["kind"]]
    maplink = "https://map.naver.com/p/search/" + urllib.parse.quote(f["address"])
    return (f'<div class="fc"><div class="fh"><span class="ic" aria-hidden="true">{icon}</span><div><b>{e(f["name"])}</b>'
            f'<small><span class="badge">{e(kname)}</span>{e(f["district"])}</small></div></div>'
            f'<div class="fd"><span>📅 {e(period(f))}</span><span>📍 {e(f["address"])}</span></div>'
            f'<div class="fb"><a class="ap" href="{e(cfg["fair_link"])}" target="_blank" rel="sponsored nofollow noopener">무료 초대권 신청</a>'
            f'<a class="mp" href="{e(maplink)}" target="_blank" rel="noopener">지도</a></div></div>')


def list_page(data, cfg, seo, style, theme):
    fairs = data["fairs"]
    regions = []
    for f in fairs:
        if f["region"] not in regions:
            regions.append(f["region"])
    fd = d_of(data["fetched"])
    js_data = json.dumps([{k: f[k] for k in ("region", "district", "name", "start", "end", "kind", "address")} for f in fairs], ensure_ascii=False)
    # 검색엔진용: 자바스크립트 없이도 목록이 보이게 서버에서 한 번 그려 둠
    static = "".join(card(f, cfg) for f in fairs)
    chips = '<button type="button" data-r="" aria-pressed="true">전체</button>' + "".join(
        f'<button type="button" data-r="{e(r)}" aria-pressed="false">{e(r)}</button>' for r in regions)
    kchips = '<button type="button" data-k="" aria-pressed="true">전체</button>' + "".join(
        f'<button type="button" data-k="{k}" aria-pressed="false">{v[0]}</button>' for k, v in KIND.items() if any(f["kind"] == k for f in fairs))
    title = "전국 웨딩박람회 일정 | " + cfg["title"]
    return head(title, seo, style, theme) + f'''<body>
<div class="wrap">
  <p class="disclosure">{DISCLOSURE}</p>
  <a class="back" href="/">‹ 결혼 준비 D-day</a>
  <header class="hero" style="padding-top:20px">
    <span class="eyebrow">{fd.month}월 {fd.day}일 기준 · {len(fairs)}개 일정</span>
    <h1>전국 웨딩박람회<br><em>일정 한눈에 보기</em></h1>
    <p class="lead">웨딩박람회에서는 예식장, 스드메, 예물, 혼수, 신혼여행 상담을 하루에 비교할 수 있어요. 지역을 고르고 날짜순으로 확인하세요.</p>
  </header>
  <section class="card">
    <span class="label">지역</span>
    <div class="chips" id="rc">{chips}</div>
    <span class="label" style="margin-top:14px">종류</span>
    <div class="chips" id="kc">{kchips}</div>
  </section>
  <div id="list"><div class="fl">{static}</div></div>
  <a class="cta" href="{e(cfg["fair_link"])}" target="_blank" rel="sponsored nofollow noopener">전국 박람회 무료 초대권 신청하기</a>
  <p class="note">신청 페이지에서 지역 탭을 누르면 원하는 박람회를 찾을 수 있어요. 일정은 주최 측 사정으로 바뀔 수 있으니 신청 페이지에서 한 번 더 확인하세요.</p>
  <footer>박람회 정보는 주최 측 안내를 모아 정리한 것으로, 일정과 혜택은 주최 측 사정에 따라 달라질 수 있습니다.<br>이 페이지에는 제휴 링크가 포함되어 있으며, 이를 통해 운영자가 수수료를 받을 수 있습니다.</footer>
</div>
<script>
var F = {js_data};
var KIND = {json.dumps({k: v for k, v in KIND.items()}, ensure_ascii=False)};
var WD = "일월화수목금토", R = "", K = "", LINK = {json.dumps(cfg["fair_link"])};
function esc(s) {{ return String(s).replace(/[&<>"]/g, function (c) {{ return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]; }}); }}
function dt(s) {{ var a = s.split("-"); return new Date(+a[0], +a[1]-1, +a[2]); }}
function per(f) {{
  var a = dt(f.start), b = dt(f.end), s = (a.getMonth()+1) + "월 " + a.getDate() + "일(" + WD[a.getDay()] + ")";
  if (f.start === f.end) return s;
  return s + " ~ " + (a.getMonth() === b.getMonth() ? "" : (b.getMonth()+1) + "월 ") + b.getDate() + "일(" + WD[b.getDay()] + ")";
}}
function draw() {{
  var t = new Date(); t.setHours(0,0,0,0);
  var items = F.filter(function (f) {{ return dt(f.end) >= t && (!R || f.region === R) && (!K || f.kind === K); }});
  var groups = [], key = "";
  items.forEach(function (f) {{
    var long = (dt(f.end) - dt(f.start)) / 864e5 > 6;
    var g = long ? "한 달 내내 상담" : per(f);
    if (dt(f.start) <= t && !long) g = "지금 진행 중 · " + g;
    if (!groups.length || groups[groups.length-1][0] !== g) groups.push([g, []]);
    groups[groups.length-1][1].push(f);
  }});
  groups.sort(function (a, b) {{ return (a[0] === "한 달 내내 상담") - (b[0] === "한 달 내내 상담"); }});
  var h = groups.map(function (g) {{
    return '<div class="wk">' + esc(g[0]) + ' · ' + g[1].length + '곳</div><div class="fl">' + g[1].map(function (f) {{
      return '<div class="fc"><div class="fh"><span class="ic" aria-hidden="true">' + KIND[f.kind][1] + '</span><div><b>' + esc(f.name) + '</b><small><span class="badge">' +
        esc(KIND[f.kind][0]) + '</span>' + esc(f.district) + '</small></div></div><div class="fd"><span>📅 ' + per(f) + '</span><span>📍 ' + esc(f.address) + '</span></div>' +
        '<div class="fb"><a class="ap" href="' + LINK + '" target="_blank" rel="sponsored nofollow noopener">무료 초대권 신청</a><a class="mp" href="https://map.naver.com/p/search/' +
        encodeURIComponent(f.address) + '" target="_blank" rel="noopener">지도</a></div></div>';
    }}).join("") + '</div>';
  }}).join("");
  document.getElementById("list").innerHTML = h || '<p class="empty">조건에 맞는 일정이 없어요. 다른 지역을 골라 보세요.</p>';
}}
function chip(id, set) {{
  document.getElementById(id).addEventListener("click", function (ev) {{
    var b = ev.target.closest("button"); if (!b) return;
    this.querySelectorAll("button").forEach(function (x) {{ x.setAttribute("aria-pressed", x === b); }});
    set(b.dataset.r !== undefined ? b.dataset.r : b.dataset.k); draw();
  }});
}}
chip("rc", function (v) {{ R = v; }}); chip("kc", function (v) {{ K = v; }});
draw();
</script>
</body>
</html>
'''
