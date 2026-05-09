---
name: fredmeyer-shop
description: Reviews Fred Meyer purchase history, builds a shopping list of staples and infrequently-bought items, confirms quantities with the user, and adds the order to the cart via the chrome-devtools MCP. Use when the user wants help building, refreshing, or submitting a Fred Meyer grocery order, asks what to buy this week from Fred Meyer, or wants to check whether household items are running low.
---

# Fred Meyer Shopping Assistant

Build a grocery order from purchase history, confirm it interactively with the user, and add it to the Fred Meyer cart via the cart API.

## Prerequisites

- `fred-meyer-purchases.csv` exists in the project directory. If not, ask the user to run the `fredmeyer-export` skill first.
- Chrome is launched with remote debugging and the user is signed in to fredmeyer.com.
- The `chrome-devtools` MCP server is configured.

## References

Read these once before starting:

- `../_shared/chrome-devtools-tips.md` — patterns this skill depends on (`chrome-devtools:evaluate_script` over `take_snapshot`, React render waits).
- `references/cart-snippets.md` — JS snippets for cart-API discovery, replace-cart fetch, product status, DOM add-to-cart, and cart verification.
- `references/categories.md` — keyword tables used to classify items.
- `references/output-format.md` — exact templates for the suggested-list and final-order prompts.

---

## Phase 1: Analyze purchase history

### 1a. Read the CSV

Read `fred-meyer-purchases.csv`. Parse each row into:
`date, order_type, item_name, size, quantity, price_paid, product_url, upc`.

### 1b. Compute per-item statistics

Group rows by `upc` (fall back to `item_name` if upc is `unknown`). Determine `total_orders` (the number of distinct orders in the CSV). For each unique item compute:

| Stat | Definition |
|------|------------|
| `last_purchased` | Most recent `date` |
| `purchase_count` | Number of distinct orders the item appears in |
| `order_participation_rate` | `purchase_count / total_orders × 100` (round to 1 decimal) |
| `avg_interval_days` | If `purchase_count ≥ 2`: `(last_purchased − first_purchased) / (purchase_count − 1)` in days. Otherwise `null`. |
| `avg_qty` | Mean `quantity` across all rows (round up to nearest integer) |
| `typical_qty` | Most common `quantity` value (mode); fall back to `avg_qty` |
| `category` | Inferred from `item_name` per `references/categories.md` |
| `replacement_for` | UPC of the item this may be substituting for (see 1c) |

**Frequency classification** (from `avg_interval_days`):
- **Staple** — `avg_interval_days ≤ 17` (roughly weekly or biweekly).
- **Infrequent** — `avg_interval_days > 17`, or `purchase_count == 1`.

### 1c. Replacement detection

Identify likely substitutions so the same logical item under different brands isn't double-counted:

1. For any two item groups whose `item_name` values share ≥ 2 significant words (ignoring brand, size, and filler like "organic", "oz", "fl", "pack"), flag them as related.
2. Among related pairs, the item with fewer purchases is likely a replacement for the one with more. Set its `replacement_for` to the more-frequent item's UPC.
3. When computing `order_participation_rate` for the more-frequent item, also count orders where its replacement appeared. Annotate with `(incl. substitutions)` if replacements were found.

---

## Phase 2: Build the suggested shopping list

Render the suggested list using the template in `references/output-format.md` — staples (✓, included by default) and infrequent items (·, opt-in) in a single prompt, grouped by category.

Category display order (omit any with no items):
Protein → Dairy/Alternatives → Fruit → Vegetables → Bread/Grains → Beverages → Snacks/Sweets → Condiments/Pantry → Frozen → Personal Care → Medications/Supplements → Cleaning Supplies → Paper/Household → Baby/Child → Pet → Other.

Wait for user input. Apply changes (qty edits, removals, infrequent additions). When the user accepts ("ok") or has no further changes, move to Phase 3.

---

## Phase 3: Final confirmation

Show the complete final order using the FINAL ORDER template in `references/output-format.md`. Then ask:

> Ready to add these to your cart? (yes / no / [further changes])

If "no" or further changes, return to Phase 2. If "yes", proceed.

---

## Phase 4: Add items to cart

Read `references/cart-snippets.md` before starting. Use `chrome-devtools:evaluate_script` for everything in this phase — never `chrome-devtools:take_snapshot`. Snapshots cost ~800 tokens each; small JS payloads cost ~20.

### 4a. Verify fulfillment mode

Run snippet 1 (fulfillment-mode check) from `references/cart-snippets.md`. If the mode is "Delivery" or unset, ask the user to set their preferred pickup store before proceeding.

### 4b. Discover the cart API

The cart ID is session-specific — discover it fresh each run.

1. Navigate to the first item's `product_url`.
2. Run snippet 2 (product status). If `outOfStock` or `deliveryOnly`, record the item as unavailable and move to the next one.
3. Run snippet 3 (set quantity + click Add to Cart) to add the item via the DOM.
4. Capture the cart endpoint:
   - Run snippet 4 (recent network resources) to list candidate `/api/`, `/atlas/`, or `/cart` requests.
   - Use `chrome-devtools:list_network_requests` to inspect POSTs that fired after the click. Save the URL, headers, and body shape as `cart_api`.

### 4c. Add remaining items via cart-API fetch

With `cart_api` known, replace the cart in a single fetch (snippet 5 in `references/cart-snippets.md`) — no further navigation required. Items go in as `{upc, qty}` pairs.

If the cart API cannot be discovered (no clear POST captured), fall back to per-item navigate + DOM add (snippets 2 + 3) — still no snapshots.

### 4d. Items without a `product_url`

Navigate to `https://www.fredmeyer.com/search?query={url-encoded-item-name}`. Run snippet 6 (first product link from search results), then continue with snippets 2 + 3.

### 4e. Verify the cart

Run snippet 7 (cart count, no navigation) or navigate to `https://www.fredmeyer.com/cart` and run snippet 8 (cart item names) to confirm.

---

## Phase 5: Report

If every item went in:

> All N items added — your cart is ready at https://www.fredmeyer.com/cart

Otherwise:

```
Your Fred Meyer cart is ready for review!
→ https://www.fredmeyer.com/cart

Added: N items
Could not add (M items):
  - {item}: out of stock for pickup
  - {item}: product page not found
```
