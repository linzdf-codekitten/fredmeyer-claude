/**
 * Fred Meyer Export Scripts
 * Discovered 2026-04-04. Use via evaluate_script in chrome-devtools MCP.
 *
 * PAGE STRUCTURE NOTES:
 * - Site is React/Next.js — raw HTML has no item data, must navigate then extract
 * - Order list: /mypurchases?page=N&tab=purchases
 *   Links: a[href*="/mypurchases/detail/"] with text like "In-store March 22, 2026 $65.71"
 * - Order detail: /mypurchases/detail/{div}~{store}~{date}~{terminal}~{txnId}
 *   Items in: aside[role="complementary"] h2 = "Pickup Items" or "In-Store Items"
 *   Each item: li > a[href*="/p/"] — fee lines (Bev Excise etc.) have no /p/ link, naturally skipped
 * - Product URL format: /p/{slug}/{upc13}  — last segment is UPC
 *
 * API NOTES:
 * - POST /atlas/v1/purchase-history/v2/details returns clean JSON per order
 * - Body: [{divisionNumber, storeNumber, transactionDate, terminalNumber, transactionId}]
 * - BUT: Akamai bot protection rate-limits after ~5 direct fetch() calls
 * - Safer approach: navigate to each order page and extract via DOM
 */


// ─────────────────────────────────────────────
// 1. CHECK LOGIN STATUS
// ─────────────────────────────────────────────
/*
() => document.body.innerText.includes('Sign In') ? 'signed-out' : 'signed-in'
*/


// ─────────────────────────────────────────────
// 2. EXTRACT ORDER LIST FROM /mypurchases PAGE
//    Returns [{id, date, type, url}] for all orders on the current page.
//    Run after navigating to /mypurchases?page=N&tab=purchases (wait ~1s after nav).
// ─────────────────────────────────────────────
/*
() => {
  const orders = [];
  document.querySelectorAll('a[href*="/mypurchases/detail/"]').forEach(a => {
    const id = a.getAttribute('href').split('/detail/')[1];
    const text = a.innerText;
    const typeMatch = text.match(/^(In-store|Pickup)/i);
    const dateMatch = text.match(/(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+),\s+(\d{4})/);
    if (!id || !dateMatch) return;
    const months = {January:'01',February:'02',March:'03',April:'04',May:'05',June:'06',
      July:'07',August:'08',September:'09',October:'10',November:'11',December:'12'};
    const date = `${dateMatch[3]}-${months[dateMatch[1]]}-${dateMatch[2].padStart(2,'0')}`;
    const type = typeMatch ? typeMatch[1].toLowerCase().replace('-','') : 'in-store';
    orders.push({ id, date, type, url: 'https://www.fredmeyer.com' + a.getAttribute('href') });
  });
  return orders;
}
*/


// ─────────────────────────────────────────────
// 3. ITEM EXTRACTOR — stores CSV rows in localStorage
//    Run after navigating to /mypurchases/detail/{ID}.
//    Returns item count (not the data itself — keeps context small).
//    Replace DATE, TYPE, ID with actual values before running.
// ─────────────────────────────────────────────
/*
async () => {
  const DATE = '2026-XX-XX';   // e.g. '2026-03-22'
  const TYPE = 'in-store';     // 'in-store' or 'pickup'
  const ID   = 'div~store~date~term~txn';  // e.g. '701~00122~2026-03-22~522~490951'

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
    if (!link) return;  // skips fee lines (Bev Excise etc.) naturally
    const name = li.querySelector('h3')?.innerText?.trim() || '';
    const href = link.getAttribute('href');
    const upc = href.split('/').pop();
    const url = 'https://www.fredmeyer.com' + href;
    const text = li.innerText;
    const qty  = text.match(/Received:\s*([\d.]+ lbs|[\d.]+)/)?.[1] || '';
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
*/


// ─────────────────────────────────────────────
// 4. READ BACK ALL localStorage RESULTS
//    Run once after all orders are processed.
//    Returns {orderId: "csv_rows_string"} and clears localStorage.
// ─────────────────────────────────────────────
/*
() => {
  const keys = Object.keys(localStorage).filter(k => k.startsWith('fm_'));
  const result = {};
  keys.forEach(k => { result[k.slice(3)] = localStorage.getItem(k); });
  keys.forEach(k => localStorage.removeItem(k));
  return result;
}
*/


// ─────────────────────────────────────────────
// 5. PURCHASE HISTORY API (use for first ~5 orders only — Akamai rate-limits after that)
//    Alternative to DOM extraction. Requires cookies to be active (navigate to FM first).
// ─────────────────────────────────────────────
/*
async () => {
  // Parse order ID: '701~00122~2026-03-22~522~490951'
  // Replace with the actual order ID from the crawl phase (format: DIV~STORE~DATE~TERM~TXN)
  const [divisionNumber, storeNumber, transactionDate, terminalNumber, transactionId] =
    'DIV~STORE~DATE~TERM~TXN'.split('~');

  const resp = await fetch('/atlas/v1/purchase-history/v2/details', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'content-type': 'application/json',
      'accept': 'application/json, text/plain, */*',
      'x-kroger-channel': 'WEB'
    },
    body: JSON.stringify([{ divisionNumber, storeNumber, transactionDate, terminalNumber, transactionId }])
  });
  const data = await resp.json();
  // Response: data.purchaseHistoryDetails[0].items[].purchasedData
  //   .displayInfo.description, .customerFacingSize
  //   .pricingInfo.totalPricePaid
  //   .quantityInfo.received
  //   .isWeighted
  //   .upc
  return data;
}
*/


// ─────────────────────────────────────────────
// 6. MERGE + SORT CSV (Python, Phase 3)
//    Run after writing all /tmp/fm-order-*.csv files.
// ─────────────────────────────────────────────
/*
import csv, io, glob

all_rows = []
for path in glob.glob('/tmp/fm-order-*.csv'):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                all_rows.extend(csv.reader([line]))

# Sort: date descending, then item_name ascending
all_rows.sort(key=lambda r: (-int(r[0].replace('-', '')), r[2]))

header = ['date','order_type','item_name','size','quantity','price_paid','product_url','upc']
out = io.StringIO()
w = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
w.writerow(header)
w.writerows(all_rows)

with open('fred-meyer-purchases.csv', 'w') as f:
    f.write(out.getvalue())

print(f'{len(all_rows)} rows written')
*/
