# Reta — Niche Dating Affiliate Hub

A static, free-to-host hub site for the Adsterra CPA Network, focused on three under-served audiences:

- **Mature singles (40+, 50+, 60+)**
- **Body-positive singles**
- **Local / regional dating**

Built to be cheap, fast, and compliant. Hosted free on Cloudflare Pages.

## Stack

- **[Astro 4](https://astro.build/)** — static site generator (compounding SEO, zero JS by default).
- **Tailwind CSS** — styling.
- **Content Collections** — type-safe Markdown blog.
- **Sitemap + RSS** — generated automatically.

## Quick start (local)

```bash
cd affiliate
npm install
cp .env.example .env       # then edit SITE_URL
npm run dev                 # http://localhost:4321
```

Build:

```bash
npm run build               # outputs ./dist
npm run preview
```

## Project layout

```
affiliate/
├── src/
│   ├── components/   AgeGate, CookieBanner, Header, Footer, OfferCard
│   ├── content/blog/ Markdown articles (drafts use draft: true)
│   ├── data/         offers.json — the single source of truth for CPA links
│   ├── layouts/      BaseLayout (head, SEO, gates)
│   ├── pages/        Routes
│   │   ├── go/[offer].astro   click-tracking redirect (one per offer)
│   │   ├── blog/...           list + posts
│   │   └── *.astro            home, about, contact, terms, privacy, disclaimer, 404
│   └── styles/       globals.css (Tailwind layers)
├── public/           static assets, robots.txt, _headers
├── CONTENT_PLAN.md   30 SEO articles + 30 TikTok scripts
└── COMPLIANCE.md     pre-launch + per-traffic-source checklist
```

## Adsterra CPA wiring

1. Edit `src/data/offers.json`. Replace each `url` with your real Adsterra CPA tracking URL.
   Use the placeholder `{clickid}` — the redirect page substitutes a unique click ID at runtime.
2. In your Adsterra CPA dashboard, set the **postback URL** to read the `subid` parameter you receive
   (it will look like `<short-id>_<src>`, e.g., `m9k2f4a8_tiktok`). That tells you which traffic source converted.
3. Visit `/go/<offer-id>/` to test. The page should auto-redirect within ~250ms.
4. The redirect URL accepts `?src=<channel>` so you can tag clicks per channel:
   - `/go/mature-match/?src=tiktok`
   - `/go/curve-connect/?src=pinterest`
   - `/go/local-singles/?src=blog-50plus`

## Deploy free on Cloudflare Pages

1. Push this repo to GitHub.
2. Cloudflare → Pages → Create project → Connect GitHub → pick this repo.
3. Build settings:
   - **Framework preset:** Astro
   - **Build command:** `cd affiliate && npm install && npm run build`
   - **Build output directory:** `affiliate/dist`
   - **Environment variable:** `SITE_URL=https://<your-subdomain>.pages.dev`
4. First deploy will be at `https://reta.pages.dev` (or whatever you named the project).
5. Optional: add a custom domain (~$10/year) under Pages → Custom domains.

## Pre-launch checklist

See `COMPLIANCE.md`. Hit every box before sending traffic. Specifically:

- [ ] Replace every `REPLACE_WITH_ADSTERRA_LINK` in `offers.json`.
- [ ] Replace `hello@example.com` in `/contact/`.
- [ ] Add a real `public/og-default.png` (1200×630).
- [ ] Submit sitemap to Google Search Console + Bing Webmaster Tools.

## Traffic strategy

See `CONTENT_PLAN.md` for the 90-day plan: 30 articles, 30 TikTok scripts, and a Pinterest cadence. The short version:

- **TikTok faceless** → link-in-bio = homepage → blog or offer card.
- **Pinterest** → blog article → offer card. Never pin direct affiliate URLs.
- **SEO blog** → compounding long-tail traffic. One article per week minimum.

## Two file conventions worth knowing

- `src/data/offers.json` — change here, click tracker rebuilds for free.
- Article front-matter `featuredOffer: <offer-id>` — auto-shows the offer at the bottom of that article.
