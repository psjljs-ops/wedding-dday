"""site.json 을 읽어 dist/ 폴더에 배포할 사이트를 만듭니다.

사용법:  python tools/build.py

만드는 것
  dist/index.html, offers.html, 404.html   {{...}} 자리 채움 + SEO·통계·확인 태그 삽입
  dist/og.png                             공유 미리보기 이미지 (1200x630)
  dist/sitemap.xml, robots.txt
  dist.zip                                Cloudflare 대시보드 '파일 끌어서 놓기' 업로드용

주의: Cloudflare Pages 는 /offers.html 을 /offers 로 바꿔 보여 줍니다.
      그래서 내부 링크와 sitemap 은 확장자 없는 주소를 씁니다.
"""
import datetime
import html
import json
import pathlib
import shutil
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, DIST = ROOT / "src", ROOT / "dist"
cfg = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))

URL = f"https://{cfg['name']}.pages.dev"
TODAY = datetime.date.today().isoformat()
e = lambda s: html.escape(str(s), quote=True)


def seo_block(path, title, desc):
    lines = [
        f'<meta name="description" content="{e(desc)}">',
        f'<link rel="canonical" href="{URL}{path}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{URL}{path}">',
        f'<meta property="og:image" content="{URL}/og.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:locale" content="ko_KR">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if path == "/":  # 서치콘솔·서치어드바이저 확인 태그는 메인에만
        if cfg.get("google_verification"):
            lines.append(f'<meta name="google-site-verification" content="{e(cfg["google_verification"])}">')
        if cfg.get("naver_verification"):
            lines.append(f'<meta name="naver-site-verification" content="{e(cfg["naver_verification"])}">')
    if cfg.get("goatcounter"):
        lines.append(f'<script data-goatcounter="https://{e(cfg["goatcounter"])}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>')
    return "\n".join(lines)


def render(name, path, title, desc):
    s = (SRC / name).read_text(encoding="utf-8")
    values = {
        "SITE_TITLE": cfg["title"], "OFFERS_TITLE": cfg["offers_title"],
        "EYEBROW": cfg["eyebrow"], "HEADLINE_1": cfg["headline_1"], "HEADLINE_2": cfg["headline_2"],
        "TAGLINE": cfg["tagline"],
    }
    for k, v in values.items():
        s = s.replace("{{" + k + "}}", e(v))
    s = s.replace("<!--SEO-->", seo_block(path, title, desc))
    left = [t for t in ("{{", "}}") if t in s]
    if left:
        raise SystemExit(f"{name}: 채워지지 않은 {{...}} 자리가 있습니다")
    (DIST / name).write_text(s, encoding="utf-8")


def make_og():
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1200, 630
    oc = {"bg": "#f2f4f6", "accent": "#3182f6", "accent_soft": "#e8f3ff", "accent_text": "#1b64da", **cfg.get("og_colors", {})}
    im = Image.new("RGB", (W, H), oc["bg"])
    d = ImageDraw.Draw(im)
    F = lambda size, bold=True: ImageFont.truetype(
        "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf", size)
    d.rounded_rectangle((40, 40, W - 40, H - 40), 40, fill="#ffffff")
    w = d.textlength(cfg["eyebrow"], font=F(26)) + 44
    d.rounded_rectangle((100, 110, 100 + w, 160), 25, fill=oc["accent_soft"])
    d.text((122, 116), cfg["eyebrow"], font=F(26), fill=oc["accent_text"])
    d.text((100, 195), cfg["headline_1"], font=F(66), fill="#191f28")
    d.text((100, 280), cfg["headline_2"], font=F(66), fill=oc["accent"])
    d.text((100, 390), cfg["tagline"], font=F(30, False), fill="#4e5968")
    x = 100
    for chip in cfg.get("og_chips", [])[:4]:
        w = d.textlength(chip, font=F(24)) + 40
        d.rounded_rectangle((x, 460, x + w, 510), 25, fill=oc["bg"])
        d.text((x + 20, 468), chip, font=F(24), fill="#4e5968")
        x += w + 12
    d.text((W - 100 - d.textlength(URL[8:], font=F(24, False)), 520), URL[8:], font=F(24, False), fill="#8b95a1")
    im.save(DIST / "og.png", optimize=True)


def main():
    DIST.mkdir(exist_ok=True)
    for f in DIST.iterdir():  # 폴더는 두고 안의 파일만 지움 (미리보기 서버가 폴더를 쓰고 있어도 됨)
        shutil.rmtree(f) if f.is_dir() else f.unlink()
    render("index.html", "/", cfg["title"], cfg["description"])
    render("offers.html", "/offers", f'{cfg["offers_title"]} | {cfg["title"]}', cfg["description"])
    render("404.html", "/404", cfg["title"], cfg["description"])
    make_og()

    urls = [("/", "1.0"), ("/offers", "0.6")] + [(f"/offers?c={c}", "0.7") for c in cfg.get("offer_categories", [])]
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{URL}{p}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>\n" for p, pr in urls)
        + "</urlset>\n", encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {URL}/sitemap.xml\n", encoding="utf-8")

    with zipfile.ZipFile(ROOT / "dist.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(DIST.iterdir()):
            z.write(f, f.name)
    print(f"완료: {URL}  (dist/ {len(list(DIST.iterdir()))}개 파일, dist.zip)")


if __name__ == "__main__":
    main()
