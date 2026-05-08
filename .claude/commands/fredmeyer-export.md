---
description: Crawl Fred Meyer purchase history for the last 3 months and export all items to fred-meyer-purchases.csv with dates, product links, and UPC codes
allowed-tools: mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__evaluate_script, mcp__chrome-devtools__take_snapshot, mcp__chrome-devtools__take_screenshot, mcp__chrome-devtools__click, mcp__chrome-devtools__press_key, mcp__chrome-devtools__type_text, mcp__chrome-devtools__new_page, mcp__chrome-devtools__select_page, mcp__chrome-devtools__list_pages, Read, Write, Bash
---

# Fred Meyer Purchase History Export (`/fredmeyer-export`)

Crawl the last 3 months of purchase history on Fred Meyer and write all items to `fred-meyer-purchases.csv`.

## Architecture

This skill runs in four phases:

0. **Skip phase**: Load `fred-meyer-processed-orders.txt` to build the set of already-processed order IDs — these are skipped during crawl.
1. **Crawl phase**: Log in, paginate the order list, collect all order detail URLs within the 3-month window that haven't been processed yet.
2. **Extraction phase**: For each order, navigate to its detail page, extract all items via `evaluate_script` (NOT `take_snapshot`), and accumulate results in `localStorage`.
3. **Merge phase**: Read all localStorage data back in one call, write temp CSVs, sort, write final output.

> **Context efficiency**: Always use `evaluate_script` instead of `take_snapshot` for extraction. Each snapshot is ~600–900 tokens; a JS extractor returning a row count is ~10 tokens. Use localStorage to accumulate results across pages — read it all back in one final call.

> **Saved scripts**: Ready-to-use JS snippets are in `.claude/scripts/fredmeyer-export-scripts.js`. Read this file before starting Phase 1 — it has copy-paste scripts for login check, order list extraction, the item extractor (localStorage pattern), the read-back call, the API approach (rate-limited after ~5), and the Python merge/sort snippet.

---

## Phase 0: Load processed order history

```bash
cat fred-meyer-processed-orders.txt 2>/dev/null
```

Each line is an order ID (e.g. `701~00122~2026-03-22~522~490951`). Store these as the `already_processed` set. If the file doesn't exist or is empty, `already_processed` is an empty set — all orders will be fetched.

---

## Phase 1: Crawl

Use `chrome-devtools` mcp for all browser interactions.

### Step 1 — Check login

Navigate to `https://www.fredmeyer.com/mypurchases`. Use `evaluate_script` to check login state:

```javascript
() => document.querySelector('[data-testid="header-account-name"]')?.innerText || document.body.innerText.includes('Sign In') ? 'signed-out' : 'unknown'
```

If signed out, tell the user to log in first and wait.

### Step 2 — Compute cutoff

```bash
date -d "3 months ago" +%Y-%m-%d
```

Only collect orders on or after this date.

### Step 3 — Collect all order URLs via evaluate_script

Navigate to `https://www.fredmeyer.com/mypurchases?page={N}&tab=purchases`. For each page, use `evaluate_script` to extract order data directly — do NOT use `take_snapshot`:

```javascript
() => {
  const orders = [];
  document.querySelectorAll('a[href*="/mypurchases/detail/"]').forEach(a => {
    const id = a.getAttribute('href').split('/detail/')[1];
    const text = a.innerText;
    const typeMatch = text.match(/^(In-store|Pickup)/i);
    const dateMatch = text.match(/(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+),\s+(\d{4})/);
    if (!id || !dateMatch) return;
    const months = {January:'01',February:'02',March:'03',April:'04',May:'05',June:'06',July:'07',August:'08',September:'09',October:'10',November:'11',December:'12'};
    const date = `${dateMatch[3]}-${months[dateMatch[1]]}-${dateMatch[2].padStart(2,'0')}`;
    const type = typeMatch ? typeMatch[1].toLowerCase().replace('-','') : 'in-store';
    orders.push({ id, date, type, url: 'https://www.fredmeyer.com' + a.getAttribute('href') });
  });
  return orders;
}
```

Wait ~1 second after navigation before running (page is React/Next.js). If no orders appear, retry up to 5 times with 500ms delay inside the script or re-run the evaluate_script.

For each order:
- If date < cutoff: stop paginating
- If order ID is in `already_processed`: skip
- Otherwise: record `{ url, date, type, id }`

---

## Phase 2: Sequential extraction with localStorage accumulation

### Step 4 — Process each order one at a time

For each order, navigate to its detail page, then immediately run the extractor script. The extractor writes CSV rows to `localStorage['fm_' + ID]` — it does NOT return row data to avoid filling context.

**Extractor script** (returns item count only):

```javascript
async () => {
  const DATE = '{date}', TYPE = '{type}', ID = '{order_id}';
  // Wait for items to load (React renders async)
  let aside = null;
  for (let i = 0; i < 10; i++) {
    aside = [...document.querySelectorAll('aside,[role="complementary"]')]
      .find(a => {
        const h = a.querySelector('h2')?.innerText || '';
        return h.includes('Items') && !h.includes('Out of Stock');
      });
    if (aside && aside.querySelectorAll('li').length > 0) break;
    await new Promise(r => setTimeout(r, 500));
  }
  if (!aside) { localStorage.setItem('fm_' + ID, ''); return 0; }

  const esc = s => {
    s = String(s);
    return (s.includes(',') || s.includes('"')) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };

  const rows = [];
  aside.querySelectorAll('li').forEach(li => {
    const link = li.querySelector('a[href*="/p/"]');
    if (!link) return;
    const name = li.querySelector('h3')?.innerText?.trim() || '';
    const href = link.getAttribute('href');
    const upc = href.split('/').pop();
    const url = 'https://www.fredmeyer.com' + href;
    const text = li.innerText;
    const qty = text.match(/Received:\s*([\d.]+ lbs|[\d.]+)/)?.[1] || '';
    const paid = '$' + (text.match(/Paid:\s*\$([\d.]+)/)?.[1] || '');
    // Extract size: first non-label text node after h3's parent
    const h3 = li.querySelector('h3');
    let size = '';
    if (h3) {
      let node = h3.parentElement?.nextSibling;
      while (node) {
        const t = (node.textContent || '').trim();
        if (t && !/^(Add to Cart|Delivery Only|Item|Received|Paid|Save|Buy|Coupon|Featured|Everyday|Price Cut|Discounted|Low Stock|Out of)/i.test(t)) {
          size = t; break;
        }
        node = node.nextSibling;
      }
    }
    rows.push([DATE, TYPE, name, size, qty, paid, url, upc].map(esc).join(','));
  });

  localStorage.setItem('fm_' + ID, rows.join('\n'));
  return rows.length;
}
```

Replace `{date}`, `{type}`, `{order_id}` with the actual values for each order. The script returns the row count so you can log progress without returning item data.

> **Note**: Items without `/p/` links (fee lines like "Bev Excise") are naturally skipped.

### Step 5 — Read back all localStorage data

After all orders are processed, run this once to collect all results:

```javascript
() => {
  const keys = Object.keys(localStorage).filter(k => k.startsWith('fm_'));
  const result = {};
  keys.forEach(k => { result[k.slice(3)] = localStorage.getItem(k); });
  keys.forEach(k => localStorage.removeItem(k));
  return result;
}
```

This returns a `{ order_id: "csv_rows" }` object. For each order ID, write its rows to `/tmp/fm-order-{ID}.csv`.

---

## Phase 3: Merge and sort

### Step 6 — Merge temp files and sort using Python

Use Python (not bash sort) because bash sort doesn't handle quoted CSV fields correctly:

```python
import csv, io, glob

# Collect all temp files
all_rows = []
for path in glob.glob('/tmp/fm-order-*.csv'):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                all_rows.extend(csv.reader([line]))

# Sort: date descending, then item_name ascending
all_rows.sort(key=lambda r: (-int(r[0].replace('-', '')), r[2]))

# Write (append if file already exists with header)
header = ['date','order_type','item_name','size','quantity','price_paid','product_url','upc']
out = io.StringIO()
w = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
w.writerow(header)
w.writerows(all_rows)

with open('fred-meyer-purchases.csv', 'w') as f:
    f.write(out.getvalue())

print(f'{len(all_rows)} rows written')
```

### Step 7 — Record processed order IDs

Write all newly processed order IDs to `fred-meyer-processed-orders.txt`:

```bash
printf '%s\n' {id1} {id2} ... >> fred-meyer-processed-orders.txt
```

### Step 8 — Clean up and report

```bash
rm -f /tmp/fm-order-*.csv
```

Summarize:
- Date range covered (oldest → newest)
- Number of new orders processed (skipped N already-processed)
- Number of unique UPCs
- Total rows written
- Path: `fred-meyer-purchases.csv`

---

## Notes

- **API exists but is rate-limited**: `POST /atlas/v1/purchase-history/v2/details` returns clean JSON but Akamai bot protection blocks it after ~5 requests. The DOM-extraction approach is more reliable.
- **Page is React/Next.js**: Raw HTML has no item data. Always navigate first, then extract with `evaluate_script` after DOM loads.
- **localStorage survives page navigation** within the same origin, so accumulation across order pages works correctly.
