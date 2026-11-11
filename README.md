# site-starter

제휴 수익형 정적 사이트를 빠르게 만들어 Cloudflare Pages(`이름.pages.dev`)에 올리기 위한 시작 템플릿입니다.
이사 체크리스트(isa-checklist.pages.dev)를 만들며 정리한 구조를 그대로 담았습니다.

## 들어 있는 것

| 파일 | 역할 |
|---|---|
| `site.json` | 사이트 이름·제목·문구·통계·확인 태그. **새 사이트는 여기부터 고칩니다** |
| `src/index.html` | 메인 페이지. 제휴 링크를 넣지 않고 맨 아래에 제휴 안내 한 줄만 둡니다 |
| `src/offers.html` | 제휴 추천 모음. `/offers?c=카테고리` 하나로 여러 페이지를 보여 줍니다 |
| `src/404.html` | 없는 주소 안내 |
| `tools/build.py` | `dist/`와 `dist.zip`을 만듭니다 (SEO 태그, OG 이미지, sitemap, robots 포함) |

## 새 사이트 만드는 순서

1. GitHub에서 이 저장소의 **Use this template** → 새 저장소 만들기
2. `site.json` 고치기 (`name`이 곧 `name.pages.dev` 주소)
3. `src/index.html`의 "핵심 기능 자리" 카드를 실제 기능으로 바꾸기
4. `src/offers.html`의 `CATEGORIES`에 제휴 업체·상품 넣기, `site.json`의 `offer_categories`도 맞추기
5. `python tools/build.py`
6. 배포 (아래)
7. 구글 서치콘솔·네이버 서치어드바이저 확인 태그를 `site.json`에 넣고 다시 빌드·배포, sitemap 제출

## 배포

- **wrangler 로그인을 해 둔 경우:** `npx wrangler pages deploy dist --project-name=<name> --branch=main`
- **아닌 경우:** Cloudflare 대시보드 → Workers 및 Pages → 만들기 → Pages → 파일 끌어서 놓기 → `dist.zip` 업로드.
  수정 배포는 프로젝트 화면의 **새 배포 만들기**.

## 제휴 규칙 메모

- 쿠팡 파트너스: 상품이 있는 페이지 첫머리에 지정 문구 (offers.html이 자동 표시)
- 아정당: 지정 문구 필수, 제목·계정명에 '아정당' 금지, 사칭·공식 혜택 외 금액 언급 금지
- 알바리치·텐핑: 머천트별 홍보 가능 매체와 금지 문구 확인, 순위·최상급 표현은 광고주 공식 문구만
- 텐핑은 하루 한도가 있으니 같은 카테고리에 예비 업체를 2~3곳 넣어 두기 (`url`을 비우면 다음 업체가 올라옴)

## Cloudflare 주의

Cloudflare Pages는 `/offers.html`을 `/offers`로 308 리다이렉트합니다. 내부 링크와 sitemap은 확장자 없는 주소를 씁니다.
