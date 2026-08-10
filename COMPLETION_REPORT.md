# SOGO Style Sentinel — Completion Report

## What was added in this revision

- Continuous scan scheduler: scans throughout the day (default every 30 minutes) and sends the accumulated report at 08:00 Europe/Istanbul.
- Daily report now uses a configurable lookback window instead of discovering everything only at 08:00.
- Multilingual query planner: Turkish, English, Russian, Simplified Chinese and Italian.
- Target category coverage: women's sweatshirt, matching set, velour set, half-zip set and plus-size set.
- Detail vocabulary: contrast trim/garni, stripe, embroidery, sports-luxe, premium, side panel, textured/ribbed and crystal details.
- Premium brand research universe expanded to 50+ relevant brands.
- Retail source universe expanded: Farfetch, YOOX, LuisaViaRoma, MODES, VITKAC, Giglio, Julian Fashion, Bernardelli, Mytheresa, NET-A-PORTER, SSENSE, TSUM, Lamoda, Wildberries, Ozon, Tmall, Taobao, JD and 1688.
- Social/color research universe: Instagram, Pinterest, Xiaohongshu/RED, Douyin, Weibo and Pantone.
- Instagram target-account list added, including the accounts previously requested.
- Authorized/licensed search-provider adapter added so one configured provider can discover indexed product pages across global, Russian, Chinese and social sources without pretending direct API access exists.
- Transparent source health: unconfigured or permission-gated sources stay `disabled` rather than returning fake success.
- Trend score implemented using recency + freshness language + source confidence.
- Multilingual attribute extraction implemented for fabric, collar, detail, silhouette, style and color.
- Feedback learning now learns source, brand and extracted visual/text style attributes instead of only a few title words.
- Image URL quality ranking added before perceptual deduplication.
- Exactly up to 3 distinct images are saved per product: main, detail, back/angle.
- Existing URL and perceptual duplicate protection preserved.
- Railway/Supabase defensive prestart from the earlier fixed build preserved; no destructive DB reset/drop logic added.

## Deliberately not faked

Some requested platforms do not provide unrestricted public product APIs. Instagram, Pinterest, RED/Xiaohongshu, Douyin, Weibo, Farfetch partner feeds and some Russian/Chinese marketplaces may require official API permission, partner access, or a licensed data/search provider. The project now contains the full source/query plan and a configurable authorized search adapter, but credentials must still be supplied in Railway for live collection. The code does not bypass logins, CAPTCHAs, rate limits or access controls.

Pantone proprietary swatch databases are not scraped. The project supports official/public trend research and a manually supplied palette through `MANUAL_COLOR_PALETTE`.

## Deployment-critical environment variables

At minimum: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_REPORT_CHAT_ID`, `DATABASE_URL`, `DATABASE_URL_SYNC`.
For broad multi-source discovery: `SEARCH_PROVIDER_URL`, `SEARCH_PROVIDER_KEY`.

## Behaviour after deployment

1. Web server starts without waiting forever on an unbounded migration.
2. Scheduler starts and performs repeated scans throughout the day.
3. New products are normalized, filtered, deduplicated, scored and stored.
4. Feedback buttons update style weights.
5. At 08:00 Istanbul time, the bot sends the best unseen products from the configured lookback period, each with up to three distinct images and its product link.
