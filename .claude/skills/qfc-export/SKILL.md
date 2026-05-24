---
name: qfc-export
description: Crawls QFC purchase history via the chrome-devtools MCP and exports the last 3 months of items to a CSV with dates, product URLs, and UPC codes. Use when the user wants to export, archive, or analyze their QFC order history, or as a prerequisite for building a shopping list.
---

# QFC Purchase History Export

Crawl the last 1 week of purchase history on qfc.com and write all items to `qfc-purchases.csv`.

## Prerequisites

- The user's own Chrome (not a headless instance launched by Claude) running with remote debugging on port 9222, signed in to qfc.com.
- The `chrome-devtools` MCP server configured.

**IMPORTANT — do not launch Chrome yourself.** QFC's bot detection (Akamai) blocks any headless or CDP-driven browser that Claude launches. The skill only works if the user's real Chrome is already on port 9222 with an active QFC session.

Before Phase 0, verify Chrome is ready:
```bash
curl -s http://localhost:9222/json/version | grep -i "HeadlessChrome\|headless"
```
- If the port is unreachable: stop and ask the user to launch Chrome with `--remote-debugging-port=9222` and sign in to qfc.com, then try again.
- If the result contains `HeadlessChrome` or `headless`: stop and tell the user this is a headless browser — QFC will block it. Ask them to launch a real (non-headless) Chrome window with `--remote-debugging-port=9222 --user-data-dir=$HOME/.config/google-chrome`.
- If the result shows a normal Chrome version with no headless flag: proceed.

Read `../_shared/chrome-devtools-tips.md` once before starting — it covers the patterns this skill depends on (`evaluate_script` over `take_snapshot`, React render waits, localStorage accumulation).

The reusable JS and Python snippets — order-list extractor, item extractor, localStorage read-back, the API alternative, the merge step — live in `references/extract-snippets.md`. Read that file before Phase 1 so the snippets are in context when the loop starts.

## Architecture

Run in four phases:

0. **Skip phase**: Load `qfc-processed-orders.txt` to build the set of already-processed order IDs.
1. **Crawl phase**: Verify login, paginate the order list, collect order detail URLs that fall within the 3-month window and aren't already processed.
2. **Extraction phase**: Visit each order detail page, extract items via `chrome-devtools:evaluate_script`, accumulate rows into `localStorage`.
3. **Merge phase**: Read all `localStorage` data back in one call, write temp CSVs, sort, write final output, record processed IDs.

---

## Phase 0: Load processed order history

Read `qfc-processed-orders.txt` (one order ID per line, format `DIV~STORE~DATE~TERM~TXN`). Treat a missing or empty file as an empty set — every in-window order will be fetched.

---

## Phase 1: Crawl

### Step 1 — Check login

Navigate to `https://www.qfc.com/mypurchases`. Run snippet 1 (login check) from `references/extract-snippets.md`. If signed out, ask the user to sign in and wait.

### Step 2 — Compute the cutoff date

```bash
date -d "1 week ago" +%Y-%m-%d
```

Only collect orders on or after this date.

### Step 3 — Collect order URLs

Paginate through `https://www.qfc.com/mypurchases?page={N}&tab=purchases`. For each page, run the order-list extractor (snippet 2 in `references/extract-snippets.md`) via `chrome-devtools:evaluate_script`. Wait ~1 second after navigation before running.

For each returned order:
- If date < cutoff: stop paginating.
- If order ID is in `already_processed`: skip.
- Otherwise: record `{ url, date, type, id }`.

If no orders appear on a page that should have orders, retry up to 5 times — React hydration can lag.

---

## Phase 2: Sequential extraction with localStorage accumulation

### Step 4 — Process each order

For each order URL:

1. Navigate to the detail page with `chrome-devtools:navigate_page`.
2. Run the item extractor (snippet 3 in `references/extract-snippets.md`), substituting `DATE`, `TYPE`, and `ID` with the order's values.

The extractor writes CSV rows to `localStorage['qfc_' + ID]` and returns the row count only — item data stays out of context. Items without `/p/` links (fee lines like "Bev Excise") are skipped automatically.

### Step 5 — Read back all localStorage data

Run the read-back snippet (snippet 4 in `references/extract-snippets.md`). It returns `{ orderId: "csv_rows" }` for every accumulated key and clears them.

Write each order's rows to `/tmp/qfc/qfc-order-{ID}.csv`.


---

## Notes

- The purchase-history JSON API (`POST /atlas/v1/purchase-history/v2/details`) returns clean data, but Akamai rate-limits direct fetches after ~5 calls. DOM extraction is more reliable for a full crawl. Snippet 6 documents the API for cases where ~5 orders is sufficient.
- localStorage survives navigation within the same origin, so accumulation across order pages works correctly.
- QFC runs on the same Kroger platform as Fred Meyer. URL structure, page layout, and API endpoints are identical — only the domain differs.
