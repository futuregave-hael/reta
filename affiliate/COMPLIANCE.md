# Compliance Checklist — Reta CPA Affiliate

Before launch and before any paid ad campaign, every item below must be a green check. This list keeps Reta out of trouble with Adsterra CPA, ad platforms, app stores, and Tier 1 regulators (FTC, ICO, CNIL, ASIC).

## Site

- [x] **18+ age gate** on first visit (`AgeGate.astro`).
- [x] **Affiliate disclosure** in footer of every page.
- [x] **Dedicated `/disclaimer/`** explaining how Reta makes money.
- [x] **Privacy Policy** at `/privacy/`.
- [x] **Terms of Service** at `/terms/`.
- [x] **Cookie banner** that defaults to no tracking until accepted.
- [x] **`/go/` blocked** from search engines (`robots.txt` + `noindex`).
- [x] **Sponsored markers** on every offer card ("Sponsored · 18+").
- [ ] **Replace `hello@example.com`** in `/contact/` with a real inbox.
- [ ] **OG image** at `public/og-default.png` (1200x630).

## Content

- [ ] No "guaranteed match" or "find love in 24 hours" language anywhere.
- [ ] No fake testimonials. If you use a testimonial, mark it as a composite or stock.
- [ ] No before/after photos.
- [ ] No claims about specific people or platforms you cannot back up.
- [ ] All photos either licensed (Unsplash/Pexels) or AI-generated and labelled as such.

## Adsterra CPA

- [ ] Read your offer's individual terms. Some forbid incentivised traffic, social DMs, or specific GEOs.
- [ ] Confirm your traffic source is on the offer's allow list (e.g., "SEO, social organic OK; pop traffic disallowed").
- [ ] Configure postback URL in Adsterra dashboard so conversions attribute back to your `subid` (the click ID).
- [ ] Use a unique `subid` per traffic source (`home`, `tiktok`, `pinterest`, `seo-50plus`) — already supported via `?src=` param on `/go/<id>`.

## Social organic — TikTok

- [ ] Account bio says "18+" and "Resources & advice." Not "free dating" or anything claim-like.
- [ ] No mass-DMing. No comment-spam. No follow/unfollow loops.
- [ ] No nudity, no suggestive minors-adjacent content, no shock content.
- [ ] No "link in bio" overlays that hide link destinations.
- [ ] Use Reta as link-in-bio (homepage `/`), not direct CPA link.

## Social organic — Pinterest

- [ ] Pins link to **blog articles**, never directly to `/go/<offer>` and never directly to the offer URL. Pinterest auto-flags affiliate links and has banned dating-affiliate accounts en masse.
- [ ] No "before/after" or weight-loss-style imagery.
- [ ] Disclose affiliate at the bottom of any pin description that points to a post with offers.

## SEO

- [ ] Sitemap submitted to Google Search Console + Bing Webmaster.
- [ ] No doorway pages (each article must have its own genuine value).
- [ ] No exact-match anchor text spam (don't write "best dating site" linking to `/go/<id>` 50 times).
- [ ] Schema.org `Article` markup on each post (TODO: add to `[...slug].astro`).

## Data & GDPR

- [ ] No analytics cookies until the user accepts the banner.
- [ ] Provide a clear "Decline" path and respect it.
- [ ] If targeting EU, pick an analytics provider that does not require consent (Plausible, simple-analytics, server-side GoatCounter).

## When in doubt

If a tactic feels like it relies on the user *not realising* something — disclose it more, or do not do it.
