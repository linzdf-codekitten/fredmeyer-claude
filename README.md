# Fred Meyer Claude Code Skills

Two Claude Code slash commands that automate Fred Meyer grocery shopping via browser automation:

- **`/fredmeyer-export`** — Crawls your Fred Meyer purchase history for the last 3 months and exports all items to `fred-meyer-purchases.csv` with dates, product links, and UPC codes.
- **`/fredmeyer-shop`** — Reads your purchase history, suggests a shopping list (staples + infrequent items), lets you confirm quantities, then adds everything to your Fred Meyer cart.

---

## Prerequisites

- A [Fred Meyer](https://www.fredmeyer.com) account with purchase history
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- Google Chrome
- The `chrome-devtools` MCP server (see setup below)

---

## Chrome DevTools MCP Setup

The skills use the `chrome-devtools` MCP to control Chrome. This requires two things: Chrome launched with remote debugging enabled, and the MCP configured in Claude Code.

### 1. Install the MCP server

```bash
claude mcp add chrome-devtools -- npx -y @chrome-devtools/mcp@latest
```

Or add it manually to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "@chrome-devtools/mcp@latest"]
    }
  }
}
```

### 2. Launch Chrome with remote debugging

Chrome must be started with `--remote-debugging-port=9222` **before** running the skills. Use a dedicated profile to avoid interfering with your regular Chrome session.

**macOS / Linux:**
```bash
google-chrome --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug \
  --no-first-run
```

**Windows:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="C:\Users\YOUR_USERNAME\Chrome Profiles\chrome-debug" ^
  --no-first-run
```

**Windows from WSL:**
```bash
"/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:\Users\YOUR_USERNAME\Chrome Profiles\chrome-debug" \
  --no-first-run
```

### 3. Verify the connection

After launching Chrome, visit `http://localhost:9222/json/list` in your browser — you should see a JSON list of open tabs. If that works, Claude Code can connect to Chrome.

---

## Installation

Copy the `.claude/` directory into your project folder (or any directory you'll run `claude` from):

```bash
git clone https://github.com/YOUR_USERNAME/fredmeyer-skills
cd fredmeyer-skills
# The skills are now available when you run `claude` from this directory
```

The skills are project-scoped — they appear as `/fredmeyer-export` and `/fredmeyer-shop` only when Claude Code is running in this directory (or a subdirectory).

---

## Usage

### Step 1: Export purchase history

1. Launch Chrome with remote debugging (see above)
2. Navigate to [fredmeyer.com](https://www.fredmeyer.com) and log in
3. In Claude Code: `/fredmeyer-export`

This creates `fred-meyer-purchases.csv` with your last 3 months of purchases. On subsequent runs it skips already-processed orders (tracked in `fred-meyer-processed-orders.txt`).

### Step 2: Build and submit a cart

1. Make sure Chrome is open and you're logged in to Fred Meyer
2. In Claude Code: `/fredmeyer-shop`

The skill will:
- Analyze your purchase history to identify staples and infrequent items
- Present a suggested shopping list grouped by category
- Let you adjust quantities, remove items, or add infrequent items
- Add the confirmed list to your Fred Meyer cart via the cart API

---

## File Layout

```
.claude/
  commands/
    fredmeyer-export.md      # /fredmeyer-export skill definition
    fredmeyer-shop.md        # /fredmeyer-shop skill definition
  scripts/
    fredmeyer-export-scripts.js   # Reusable JS snippets for the export skill
    fredmeyer-cart-api.js         # Reusable JS snippets for cart operations
cdp.py                       # Optional: standalone CDP helper for direct use
```

**Runtime files** (generated, not tracked in git):
- `fred-meyer-purchases.csv` — exported purchase history
- `fred-meyer-processed-orders.txt` — order IDs already exported (for incremental runs)

---

## Known Limitations

- **Cart ID is session-specific**: The cart API uses a UUID that changes when you check out or clear your cart. The skill discovers it fresh each run.
- **Akamai rate limiting**: The purchase history JSON API is rate-limited after ~5 calls. The skills use DOM extraction by default, which is more reliable.
- **React rendering delay**: Fred Meyer is a React/Next.js app. The skills wait for DOM hydration before extracting — if your machine is slow, occasional retries may be needed.
- **In-store items only show paid price**: Quantity and size extraction depends on the receipt format shown on order detail pages, which can vary.
