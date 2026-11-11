"""가이드 글(guides/*.md)을 /guide/<이름> 페이지와 /guide/ 목록으로 만듭니다.

글 파일 형식 (guides/전입신고.md 처럼 파일 이름 = 주소의 <이름>, 영문·숫자·하이픈 권장)
    title: 글 제목
    desc: 검색 결과에 나올 한두 문장 설명
    date: 2026-11-11
    cta: 버튼 문구 | /주소          (여러 줄 가능, 사이트 안쪽 주소만)
    ---
    본문.  "## 소제목", "- 목록", "1. 번호 목록", "> 팁 상자", 빈 줄로 문단 구분, **굵게**

가이드 글에는 제휴 링크를 직접 넣지 않습니다(사이트 안쪽 페이지로만 연결).
"""
import datetime
import html
import json
import re

E = lambda s: html.escape(str(s), quote=True)

CSS = """<style>
  header.hero { display: block; text-align: left; }
  header.hero h1 { font-size: clamp(24px, 6.5vw, 30px); }
  .crumb { font-size: 13px; color: var(--muted); margin-top: 16px; }
  .crumb a { color: var(--sub); text-decoration: none; font-weight: 600; }
  .art { font-size: 16px; line-height: 1.8; }
  .art h2 { font-size: 20px; margin: 30px 0 10px; }
  .art h2:first-child { margin-top: 0; }
  .art p { margin: 0 0 14px; color: var(--text); }
  .art ul, .art ol { margin: 0 0 16px; padding-left: 22px; }
  .art li { margin: 4px 0; }
  .art strong { font-weight: 800; }
  .art .tip { background: var(--soft); border-radius: 14px; padding: 14px 16px; margin: 0 0 16px; font-size: 15px; color: var(--sub); }
  .meta { font-size: 13px; color: var(--muted); margin-top: 6px; }
  .gl { display: grid; gap: 8px; }
  .gl a { display: block; background: var(--soft); border-radius: 14px; padding: 14px 16px; text-decoration: none; color: var(--text); }
  .gl a:hover { background: var(--line); }
  .gl b { display: block; font-size: 16px; }
  .gl small { display: block; font-size: 13px; color: var(--sub); margin-top: 2px; }
  .ctas { display: grid; gap: 8px; margin-top: 8px; }
  .ctas a { display: flex; align-items: center; justify-content: center; text-decoration: none; font-size: 16px; font-weight: 700;
    border-radius: 14px; padding: 15px 16px; background: var(--ACCENT); color: #fff; }
  .ctas a + a { background: var(--ACCENT_SOFT); color: var(--ACCENT_TEXT); }
</style>"""


def parse(path):
    raw = path.read_text(encoding="utf-8")
    head, body = raw.split("\n---\n", 1)
    meta = {"cta": []}
    for line in head.strip().splitlines():
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if k == "cta":
            label, href = [x.strip() for x in v.split("|")]
            meta["cta"].append((label, href))
        else:
            meta[k] = v
    meta["slug"] = path.stem
    meta["body"] = body.strip()
    return meta


def inline(s):
    s = E(s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def md(body):
    out, lst = [], None
    for block in re.split(r"\n\s*\n", body):
        lines = [l.rstrip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        if lines[0].startswith("## "):
            out.append(f"<h2>{inline(lines[0][3:])}</h2>")
            lines = lines[1:]
            if not lines:
                continue
        if all(l.startswith("- ") for l in lines):
            out.append("<ul>" + "".join(f"<li>{inline(l[2:])}</li>" for l in lines) + "</ul>")
        elif all(re.match(r"\d+\. ", l) for l in lines):
            out.append("<ol>" + "".join(f"<li>{inline(re.sub(r'^\d+\. ', '', l))}</li>" for l in lines) + "</ol>")
        elif all(l.startswith("> ") for l in lines):
            out.append('<div class="tip">' + "<br>".join(inline(l[2:]) for l in lines) + "</div>")
        else:
            out.append("<p>" + " ".join(inline(l) for l in lines) + "</p>")
    return "\n".join(out)


def style_of(index_html, colors):
    m = re.search(r"<style>.*?</style>", index_html, re.S)
    st = m.group(0) if m else ""
    css = CSS.replace("var(--ACCENT)", colors["accent"]).replace("var(--ACCENT_SOFT)", colors["soft"]).replace("var(--ACCENT_TEXT)", colors["text"])
    return st + "\n" + css


def page(title, desc, url, canonical_path, site, style, body_html, ld, theme, gc=""):
    seo = "\n".join([
        f'<meta name="description" content="{E(desc)}">',
        f'<link rel="canonical" href="{url}{canonical_path}">',
        '<meta property="og:type" content="article">',
        f'<meta property="og:title" content="{E(title)}">',
        f'<meta property="og:description" content="{E(desc)}">',
        f'<meta property="og:url" content="{url}{canonical_path}">',
        f'<meta property="og:image" content="{url}/og.png">',
        '<meta property="og:locale" content="ko_KR">',
        '<meta name="twitter:card" content="summary_large_image">',
    ] + ['<script type="application/ld+json">' + json.dumps(b, ensure_ascii=False) + "</script>" for b in ld])
    if gc:
        seo += f'\n<script data-goatcounter="https://{gc}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'
    return (f'<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{E(title)}</title>\n<meta name="theme-color" content="{theme}">\n{seo}\n'
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">\n'
            f'{style}\n</head>\n<body>\n<div class="wrap">\n{body_html}\n'
            f'  <footer>{E(site["footer"])}</footer>\n</div>\n</body>\n</html>\n')


def build(root, out, site):
    """site: url, name, colors{accent,soft,text}, index_html, footer, goatcounter, theme"""
    gdir = root / "guides"
    if not gdir.exists():
        return []
    guides = [parse(p) for p in sorted(gdir.glob("*.md"))]
    guides.sort(key=lambda g: g.get("order", "9"))
    style = style_of(site["index_html"], site["colors"])
    url, name = site["url"], site["name"]
    (out / "guide").mkdir(exist_ok=True)
    for g in guides:
        others = "".join(f'<a href="/guide/{o["slug"]}"><b>{E(o["title"])}</b><small>{E(o["desc"])}</small></a>' for o in guides if o is not g)
        ctas = "".join(f'<a href="{E(h)}">{E(l)}</a>' for l, h in g["cta"])
        d = datetime.date.fromisoformat(g["date"])
        body = f'''  <p class="crumb"><a href="/">{E(name)}</a> › <a href="/guide/">가이드</a></p>
  <header class="hero" style="padding-top:14px">
    <h1>{E(g["title"])}</h1>
    <p class="lead">{E(g["desc"])}</p>
    <p class="meta">{d.year}년 {d.month}월 {d.day}일 작성</p>
  </header>
  <article class="card art">
{md(g["body"])}
  </article>
  <section class="card">
    <h2>바로 해 보기</h2>
    <div class="ctas">{ctas}</div>
  </section>
  {f'<section class="card"><h2>함께 읽으면 좋은 글</h2><div class="gl">{others}</div></section>' if others else ''}'''
        ld = [{"@context": "https://schema.org", "@type": "Article", "headline": g["title"], "description": g["desc"],
               "datePublished": g["date"], "dateModified": g.get("updated", g["date"]), "inLanguage": "ko",
               "mainEntityOfPage": f'{url}/guide/{g["slug"]}', "image": f"{url}/og.png",
               "author": {"@type": "Organization", "name": name}, "publisher": {"@type": "Organization", "name": name}},
              {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                  {"@type": "ListItem", "position": 1, "name": name, "item": url + "/"},
                  {"@type": "ListItem", "position": 2, "name": "가이드", "item": url + "/guide/"},
                  {"@type": "ListItem", "position": 3, "name": g["title"], "item": f'{url}/guide/{g["slug"]}'}]}]
        (out / "guide" / f'{g["slug"]}.html').write_text(
            page(f'{g["title"]} | {name}', g["desc"], url, f'/guide/{g["slug"]}', site, style, body, ld, site["theme"], site.get("goatcounter", "")),
            encoding="utf-8")
    items = "".join(f'<a href="/guide/{g["slug"]}"><b>{E(g["title"])}</b><small>{E(g["desc"])}</small></a>' for g in guides)
    body = f'''  <p class="crumb"><a href="/">{E(name)}</a> › 가이드</p>
  <header class="hero" style="padding-top:14px"><h1>{E(name)} 가이드</h1><p class="lead">준비하면서 자주 찾는 내용을 정리했어요.</p></header>
  <section class="card"><div class="gl">{items}</div></section>
  <section class="card"><div class="ctas"><a href="/">{E(name)} 바로 쓰기</a></div></section>'''
    (out / "guide" / "index.html").write_text(
        page(f"가이드 | {name}", f"{name} 가이드 모음", url, "/guide/", site, style, body, [], site["theme"], site.get("goatcounter", "")),
        encoding="utf-8")
    return guides


def card(guides):
    """메인 페이지에 넣을 '가이드' 카드 HTML."""
    if not guides:
        return ""
    items = "".join(f'<a href="/guide/{g["slug"]}"><b>{E(g["title"])}</b><small>{E(g["desc"])}</small></a>' for g in guides)
    return ('  <section class="card">\n    <h2>알아 두면 좋은 가이드</h2>\n'
            '    <style>.gl{display:grid;gap:8px}.gl a{display:block;background:var(--soft);border-radius:14px;padding:14px 16px;text-decoration:none;color:var(--text)}'
            '.gl a:hover{background:var(--line)}.gl b{display:block;font-size:16px}.gl small{display:block;font-size:13px;color:var(--sub);margin-top:2px}</style>\n'
            f'    <div class="gl">{items}</div>\n  </section>\n')
