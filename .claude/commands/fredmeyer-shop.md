---
description: Review Fred Meyer purchase history, confirm quantities, check if infrequently-bought items (shampoo, melatonin, deodorant, etc.) are running low, then add everything to cart
allowed-tools: mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__evaluate_script, mcp__chrome-devtools__list_network_requests, mcp__chrome-devtools__get_network_request, mcp__chrome-devtools__take_snapshot, mcp__chrome-devtools__take_screenshot, mcp__chrome-devtools__click, mcp__chrome-devtools__type_text, mcp__chrome-devtools__press_key, mcp__chrome-devtools__fill, mcp__chrome-devtools__new_page, mcp__chrome-devtools__select_page, Read, Write, Bash
---

# Fred Meyer Shopping Assistant (`/fredmeyer-shop`)

Builds a smart grocery order from your purchase history, confirms it with you interactively, and adds everything to your Fred Meyer cart.

> **Context efficiency**: Avoid `take_snapshot` in Phase 4. Use `evaluate_script` to check product status, set quantity, click Add to Cart, and verify the cart. Each snapshot is ~800 tokens; a JS call returning a small object is ~20 tokens. With 30+ items, this difference is enormous.

> **Saved scripts**: Reusable JS snippets for the cart API and DOM interactions are in `.claude/scripts/fredmeyer-cart-api.js`. Read this file at the start of Phase 4 — it contains the cart endpoint, request format, known cart ID, and copy-paste scripts for all common operations.

## Prerequisites

- `fred-meyer-purchases.csv` must exist in the project directory. If it doesn't, tell the user to run `/fredmeyer-export` first.
- Fred Meyer must be open in the browser with the user logged in. If needed, navigate to `https://www.fredmeyer.com` and verify login with `evaluate_script`:
  ```javascript
  () => document.body.innerText.includes('Sign In') ? 'signed-out' : 'signed-in'
  ```

---

## Phase 1: Analyze purchase history

### 1a. Read the CSV

Read `fred-meyer-purchases.csv`. Parse every row into:
`date, order_type, item_name, size, quantity, price_paid, product_url, upc`

### 1b. Compute per-item statistics

Group rows by `upc` (fall back to `item_name` if upc is "unknown"). Determine the total number of distinct orders in the CSV (`total_orders`). For each unique item compute:

| Stat | How to compute |
|------|---------------|
| `last_purchased` | Most recent `date` |
| `purchase_count` | Number of distinct orders it appears in |
| `order_participation_rate` | `purchase_count / total_orders × 100` (round to 1 decimal) |
| `avg_interval_days` | If `purchase_count ≥ 2`: `(last_purchased − first_purchased) / (purchase_count − 1)` in days; else `null` |
| `avg_qty` | Mean `quantity` across all rows (round up to nearest integer) |
| `typical_qty` | Most common `quantity` value (mode); use `avg_qty` as fallback |
| `category` | Infer from name (see categories below) |
| `replacement_for` | UPC of the item this may be substituting (see replacement detection below) |

**Frequency classification** — based on `avg_interval_days` (time between purchases):
- **Staple** — `avg_interval_days ≤ 17` (bought roughly weekly or biweekly)
- **Infrequent** — `avg_interval_days > 17`, or `purchase_count == 1`

**Replacement detection** — after grouping, identify likely substitutions:
1. For any two item groups whose `item_name` values share ≥ 2 significant words (ignoring brand, size, and filler words like "organic", "oz", "fl", "pack"), flag them as related.
2. Among related pairs, the item with fewer purchases is likely a replacement for the one with more. Set its `replacement_for` to the more-frequent item's UPC.
3. When computing `order_participation_rate` for the more-frequent item, also count orders where its replacement appeared (i.e., treat them as the same logical item). Annotate with `(incl. substitutions)` if replacements were found.

**Category inference** — scan `item_name` for keywords (check food categories first, then household):

| Category | Keywords to look for |
|----------|---------------------|
| Protein | chicken, beef, pork, turkey, salmon, tuna, shrimp, fish, egg, eggs, tofu, tempeh, beans, lentils, peanut butter, almond butter, nut butter, nuts, almonds, walnuts |
| Dairy / alternatives | milk, yogurt, cheese, butter, cream, oat milk, almond milk, soy milk, kefir |
| Fruit | apple, banana, berry, strawberry, blueberry, raspberry, mango, peach, grape, melon, orange, lemon, lime, citrus, avocado, cherry, pear, plum |
| Vegetables | lettuce, spinach, kale, arugula, carrot, broccoli, cauliflower, onion, garlic, tomato, pepper, cucumber, zucchini, squash, celery, cabbage, chard, beet, corn |
| Bread / grains | bread, tortilla, wrap, pasta, noodle, rice, oat, oatmeal, cereal, granola, cracker, bagel, muffin, roll, bun |
| Beverages | water, soda, juice, coffee, tea, sparkling, kombucha, lemonade, drink, beverage |
| Snacks / sweets | chip, chips, cookie, candy, chocolate, popcorn, pretzel, bar, snack, cracker, gummy |
| Condiments / pantry | sauce, dressing, vinegar, oil, spice, seasoning, salt, pepper, mustard, ketchup, mayo, salsa, hummus, jam, honey, syrup, broth, stock |
| Frozen | frozen |
| Personal care | shampoo, conditioner, body wash, deodorant, antiperspirant, razor, shave, toothpaste, toothbrush, floss, mouthwash, lotion, moisturizer, sunscreen, face wash |
| Medications / supplements | melatonin, vitamin, supplement, ibuprofen, acetaminophen, allergy, antacid, cough, cold, sleep, probiotic |
| Cleaning supplies | dish soap, laundry, detergent, cleaner, spray, bleach, sponge, scrub, mop, broom |
| Paper / household | paper towel, toilet paper, tissue, napkin, trash bag, garbage bag, zip bag, foil, wrap, batteries, light bulb |
| Baby / child | diaper, wipe, formula, baby |
| Pet | dog food, cat food, litter, pet, treat |

---

## Phase 2: Build the suggested shopping list

Present **all** items — staples and infrequent — in a **single prompt**, grouped by category within each section. Staples are automatically included in the order; infrequent items are shown for the user to opt in.

Display order for categories (omit any with no items):
Protein → Dairy/Alternatives → Fruit → Vegetables → Bread/Grains → Beverages → Snacks/Sweets → Condiments/Pantry → Frozen → Personal Care → Medications/Supplements → Cleaning Supplies → Paper/Household → Baby/Child → Pet → Other

```
SUGGESTED SHOPPING LIST
========================

── STAPLES (avg interval ≤ 17 days — already in your order) ──────────

Protein:
  ✓ Adams Creamy Natural Peanut Butter (36 oz)     qty: 2   [every 7d, 87% of orders]
  ✓ Vital Farms Pasture-Raised Large Brown Eggs    qty: 1   [every 14d, 54% of orders]
Dairy / Alternatives:
  ✓ Planet Oat Vanilla Oat Milk (52 fl oz)         qty: 5   [every 9d, 92% of orders (incl. substitutions)]
Vegetables:
  ✓ Gotham Greens Butterhead Lettuce (9 oz)        qty: 2   [every 12d, 73% of orders]
Bread / Grains:
  ✓ Dave's Killer Bread 21 Whole Grains (27 oz)    qty: 1   [every 15d, 61% of orders]

── INFREQUENT — add any you're running low on ────────────────────────

Personal Care (last bought):
  · Native Body Wash Sea Salt & Cedar (18 fl oz)           Mar 16
  · Harry's Stone Charcoal & Lime Body Wash (18 fl oz)     Mar 15   [→ substitution for Native]
Paper / Household:
  · Comforts Universal Diaper Pail Refill Bags             Mar 1
Protein:
  · Simple Truth Organic Extra Firm Tofu                   Mar 10
Beverages:
  · Olipop Watermelon Lime Prebiotic Soda                  Mar 17
```

Then ask:
> "Staples (✓) are already in your order. For infrequent items (·), reply with any you need.
>
> You can also:
> - Change a staple quantity: e.g. `peanut butter: 3`
> - Remove a staple: e.g. `remove oat milk`
> - Add an infrequent item: e.g. `body wash` or `body wash: 2`
> - Accept as-is: type `ok`
>
> Any changes?"

Wait for user input. Apply all changes. If the user says "ok" or makes no more changes, move to Phase 3.

---

## Phase 3: Final confirmation

Show the complete final order list:

```
FINAL ORDER — ready to add to cart
====================================
 1. Adams Creamy Natural Peanut Butter (36 oz)          x2
 2. Planet Oat Vanilla Oat Milk (52 fl oz)              x5
 3. Gotham Greens Butterhead Lettuce (9 oz)             x2
 4. Vital Farms Pasture-Raised Large Brown Eggs         x1
 5. Dave's Killer Bread Organic 21 Whole Grains         x1
    [+ any infrequent items the user added]
 ...

Total: N items
```

Ask:
> "Ready to add these to your cart? (yes / no / [make more changes])"

If "no" or the user requests changes, return to Phase 2. If "yes", proceed.

---

## Phase 4: Add items to cart

> **NEVER use `take_snapshot` in this phase.** Use `evaluate_script` for all checks and interactions. Snapshots cost ~800 tokens each; JS calls cost ~20 tokens.

### 4a. Ensure the store/fulfillment mode is set

```javascript
() => document.querySelector('[data-testid*="fulfillment"], [aria-label*="fulfillment"], [class*="FulfillmentSelector"]')?.innerText?.trim() || 'unknown'
```

If it shows "Delivery" or is unset, ask the user to set their preferred pickup store manually before proceeding.

### 4b. Discover the cart API (item 1 only)

**First**: read `.claude/scripts/fredmeyer-cart-api.js` — it has all ready-to-use scripts. Run Script 2 (DISCOVER CART ID) to get the current cart ID — it is session-specific and must be discovered fresh each time.

Navigate to the first item's `product_url`. Use `evaluate_script` to check the product and attempt the add-to-cart:

**Step 1 — Check product status:**
```javascript
() => ({
  title: document.querySelector('h1')?.innerText?.trim() || '',
  outOfStock: !!(document.body.innerText.match(/out of stock/i) && document.body.innerText.match(/pickup/i)),
  deliveryOnly: !!document.body.innerText.match(/delivery only/i),
  hasQtyInput: !!document.querySelector('input[aria-label*="Quantity" i], [role="spinbutton"]')
})
```

If `outOfStock` or `deliveryOnly`, record as unavailable and skip.

**Step 2 — Set quantity and click Add to Cart:**
```javascript
(qty) => {
  // Set quantity
  const inp = document.querySelector('input[aria-label*="Quantity" i], [role="spinbutton"]');
  if (inp) {
    const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    nativeSetter.call(inp, String(qty));
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    inp.dispatchEvent(new Event('change', { bubbles: true }));
  }
  // Click Add to Cart
  const btn = [...document.querySelectorAll('button')].find(b =>
    /add to cart/i.test(b.innerText) && !b.disabled
  );
  if (!btn) return 'no-button';
  btn.click();
  return 'clicked';
}
```

**Step 3 — Capture the cart API call** (after clicking, wait ~1s then):
```javascript
() => performance.getEntriesByType('resource')
  .filter(e => e.name.includes('/api/') || e.name.includes('/atlas/') || e.name.includes('/cart'))
  .map(e => e.name)
  .slice(-10)
```

Also use `list_network_requests` and inspect POST requests that fired after the click to find the cart endpoint (URL, headers, body structure). Save this as `cart_api`.

### 4c. Add remaining items via cart API fetch

Once you have `cart_api` (endpoint + headers + body structure), use `evaluate_script` with `fetch()` for all remaining items — **no page navigation required**:

```javascript
async (items) => {
  // items = [{upc, qty, name}, ...]
  const results = [];
  for (const item of items) {
    try {
      // Adapt body to match the discovered cart_api structure
      const resp = await fetch(cart_api.url, {
        method: 'POST',
        credentials: 'include',
        headers: cart_api.headers,
        body: JSON.stringify(cart_api.buildBody(item.upc, item.qty))
      });
      const ok = resp.ok;
      results.push({ name: item.name, ok, status: resp.status });
    } catch(e) {
      results.push({ name: item.name, ok: false, error: e.message });
    }
    // Small delay to avoid rate limiting
    await new Promise(r => setTimeout(r, 300));
  }
  return results;
}
```

If the cart API cannot be discovered (no clear POST captured), fall back to the navigate-and-evaluate approach for each item using the Step 1/2 pattern above — still no snapshots.

### 4d. Fallback: items with no product_url

For items missing a `product_url`, navigate to:
`https://www.fredmeyer.com/search?query={url-encoded-item-name}`

Use `evaluate_script` to find the first matching product link:
```javascript
(name) => {
  const cards = [...document.querySelectorAll('article, [data-testid*="product"]')];
  const match = cards.find(c => c.innerText.toLowerCase().includes(name.toLowerCase().split(' ')[0]));
  return match?.querySelector('a[href*="/p/"]')?.getAttribute('href') || null;
}
```

Then navigate to that URL and use the Step 1/2 pattern.

### 4e. Verify cart

After all items are processed, check cart contents without a snapshot:
```javascript
() => {
  const count = document.querySelector('[data-testid*="cart-count"], [aria-label*="cart"]')?.innerText?.trim();
  return { cartCount: count };
}
```

Or navigate to `https://www.fredmeyer.com/cart` and use `evaluate_script` to read item names:
```javascript
() => [...document.querySelectorAll('[data-testid*="cart-item"] h2, [class*="CartItem"] h2')]
  .map(h => h.innerText.trim())
```

---

## Phase 5: Done — report to user

Tell the user:

```
Your Fred Meyer cart is ready for review!
→ https://www.fredmeyer.com/cart

Added: {N} items
Could not add ({M} items):
  - {item name}: out of stock for pickup
  - {item name}: product page not found
```

If all items were added successfully, just say "All {N} items added — your cart is ready at https://www.fredmeyer.com/cart"
