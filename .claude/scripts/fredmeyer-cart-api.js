/**
 * Fred Meyer Cart API Scripts
 * Discovered 2026-04-04. Use via evaluate_script in chrome-devtools MCP.
 *
 * CART ENDPOINT: PUT /atlas/v1/carts/{cartId}
 * - Full replace: all lineItems in the body become the cart contents
 * - Returns: { data: { carts: { lineItemCount, lineItems[], versionKey } } }
 *
 * HOW TO GET cartId:
 *   GET /atlas/v1/carts  →  data.carts[0].id  (but may return empty if cart exists)
 *   OR: add one item via DOM click, then inspect network for the PUT request URL
 *   Cart ID must be discovered per session — see Script 2 (DISCOVER CART ID) below.
 */

// ─────────────────────────────────────────────
// 1. REPLACE ENTIRE CART (main script for /fredmeyer-shop)
//    Pass an array of {upc, qty} objects.
// ─────────────────────────────────────────────
async function replaceCart(cartId, items) {
  const lineItems = items.map(i => ({
    gtin13: i.upc,
    modalityType: 'PICKUP',
    quantity: i.qty,
    channel: 'WEB',
    substitutionPolicy: 'SHOPPER_CHOICE'
  }));

  const resp = await fetch(`/atlas/v1/carts/${cartId}`, {
    method: 'PUT',
    credentials: 'include',
    headers: {
      'content-type': 'application/json',
      'accept': 'application/json, text/plain, */*',
      'x-kroger-channel': 'WEB',
    },
    body: JSON.stringify({ lineItems })
  });

  const data = await resp.json();
  const cart = data?.data?.carts;
  return { status: resp.status, lineItemCount: cart?.lineItemCount };
}

// Usage in evaluate_script (inline the items array):
/*
async () => {
  // Discover cartId first using Script 2 (DISCOVER CART ID) below
  const cartId = 'YOUR_CART_ID';
  const items = [
    {upc:'0004410015621', qty:5},  // Planet Oat Vanilla Oat Milk
    {upc:'0004157005618', qty:3},  // Almond Breeze Almond Milk
    // ... etc
  ];
  const lineItems = items.map(i => ({
    gtin13: i.upc, modalityType: 'PICKUP', quantity: i.qty,
    channel: 'WEB', substitutionPolicy: 'SHOPPER_CHOICE'
  }));
  const resp = await fetch(`/atlas/v1/carts/${cartId}`, {
    method: 'PUT', credentials: 'include',
    headers: {'content-type':'application/json','accept':'application/json, text/plain, */*','x-kroger-channel':'WEB'},
    body: JSON.stringify({ lineItems })
  });
  const data = await resp.json();
  return { status: resp.status, lineItemCount: data?.data?.carts?.lineItemCount };
}
*/


// ─────────────────────────────────────────────
// 2. DISCOVER CART ID
//    Run on any fredmeyer.com page after adding one item via DOM click.
//    Inspect the PUT request in network tab, or use this after a click:
// ─────────────────────────────────────────────
/*
async () => {
  // Add one item first via DOM, then run this to find the cart ID
  const resp = await fetch('/atlas/v1/carts', { credentials: 'include' });
  const data = await resp.json();
  // If empty, the cart ID is in the most recent PUT network request URL
  return data;
}
*/


// ─────────────────────────────────────────────
// 3. CHECK PRODUCT PAGE STATUS (no snapshot needed)
//    Run after navigating to a /p/ product URL.
// ─────────────────────────────────────────────
/*
async () => {
  await new Promise(r => setTimeout(r, 3000)); // wait for React render
  return {
    title: document.querySelector('h1')?.innerText?.trim() || '',
    outOfStock: !!document.body.innerText.match(/out of stock/i),
    deliveryOnly: !!document.body.innerText.match(/delivery only/i),
    hasQtyInput: !!document.querySelector('input[aria-label*="Quantity" i], [role="spinbutton"]')
  };
}
*/


// ─────────────────────────────────────────────
// 4. ADD TO CART VIA DOM (fallback if API unavailable)
//    Sets quantity and clicks Add to Cart button.
// ─────────────────────────────────────────────
/*
async () => {
  const qty = 2; // set desired quantity
  const inp = document.querySelector('input[aria-label*="Quantity" i], [role="spinbutton"]');
  if (inp) {
    const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    nativeSetter.call(inp, String(qty));
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    inp.dispatchEvent(new Event('change', { bubbles: true }));
    await new Promise(r => setTimeout(r, 300));
  }
  const btn = [...document.querySelectorAll('button')].find(b => /add to cart/i.test(b.innerText) && !b.disabled);
  if (!btn) return 'no-button';
  btn.click();
  await new Promise(r => setTimeout(r, 1500));
  return { result: 'clicked', qtySet: !!inp };
}
*/


// ─────────────────────────────────────────────
// 5. VERIFY CART (no snapshot needed)
// ─────────────────────────────────────────────
/*
() => ({
  itemCount: document.body.innerText.match(/(\d+) item/i)?.[1],
  estimatedTotal: document.body.innerText.match(/estimated total[^\$]*\$([\d,.]+)/i)?.[1]
})
*/
