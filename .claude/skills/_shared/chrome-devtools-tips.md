# Chrome DevTools MCP — usage tips

Both Fred Meyer skills drive Chrome through the `chrome-devtools` MCP server. Follow these patterns — they significantly reduce token cost and avoid the most common failure modes.

## Tool name format

In prose, refer to MCP tools as `chrome-devtools:<tool>` (for example `chrome-devtools:evaluate_script`, `chrome-devtools:navigate_page`, `chrome-devtools:list_network_requests`).

## Prefer `evaluate_script` over `take_snapshot` for extraction

A single `chrome-devtools:take_snapshot` call costs roughly 600–900 tokens; an `chrome-devtools:evaluate_script` call returning a small object or count is ~10–20 tokens. Across a 30+ item workflow, the difference dominates context.

When the goal is "extract data" or "check status," write a JS function that returns the minimum payload:

```javascript
() => ({
  title: document.querySelector('h1')?.innerText?.trim() || '',
  outOfStock: /out of stock/i.test(document.body.innerText),
})
```

Reserve `chrome-devtools:take_snapshot` for cases where structure has to be discovered (an unknown selector, an unfamiliar layout).

## Wait for React to render

Fred Meyer is a React/Next.js app — raw HTML has no item data. After `chrome-devtools:navigate_page`, allow ~1 second before extracting, or poll inside the script:

```javascript
async () => {
  for (let i = 0; i < 10; i++) {
    if (document.querySelector('expected-selector')) break;
    await new Promise(r => setTimeout(r, 500));
  }
  // ... extract
}
```

## Accumulate across pages with localStorage

Returning data from each call across many pages fills the conversation context. Instead, write each page's results to `localStorage['<prefix>_' + id]` and read them all back in a single final call:

```javascript
() => {
  const keys = Object.keys(localStorage).filter(k => k.startsWith('myprefix_'));
  const out = {};
  keys.forEach(k => { out[k.slice('myprefix_'.length)] = localStorage.getItem(k); });
  keys.forEach(k => localStorage.removeItem(k));
  return out;
}
```

`localStorage` survives navigation within the same origin, so accumulation across order pages works correctly.

## Login check

```javascript
() => document.body.innerText.includes('Sign In') ? 'signed-out' : 'signed-in'
```

If signed out, ask the user to sign in and wait. Do not try to automate the login flow.
