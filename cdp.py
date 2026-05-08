#!/usr/bin/env python3
"""Minimal CDP helper for Fred Meyer scraping."""
import json, time, sys, urllib.request, websocket

CDP_URL = "http://localhost:9222"

def get_target():
    data = json.loads(urllib.request.urlopen(f"{CDP_URL}/json/list").read())
    # Find first normal page tab
    for t in data:
        if t.get("type") == "page" and not t["url"].startswith("chrome"):
            return t
    # Fallback: first page type
    for t in data:
        if t.get("type") == "page":
            return t
    return data[0]

def cdp_cmd(ws, method, params=None, msg_id=1):
    msg = {"id": msg_id, "method": method, "params": params or {}}
    ws.send(json.dumps(msg))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == msg_id:
            return data.get("result", {})

def navigate(ws, url, wait=3):
    cdp_cmd(ws, "Page.navigate", {"url": url}, msg_id=1)
    time.sleep(wait)

def get_snapshot(ws):
    result = cdp_cmd(ws, "Accessibility.getFullAXTree", {}, msg_id=2)
    return result

def get_text(ws):
    """Get visible text via JS."""
    result = cdp_cmd(ws, "Runtime.evaluate", {
        "expression": "document.body.innerText",
        "returnByValue": True
    }, msg_id=3)
    return result.get("result", {}).get("value", "")

def get_links(ws):
    """Get all links on page."""
    result = cdp_cmd(ws, "Runtime.evaluate", {
        "expression": """
            Array.from(document.querySelectorAll('a[href]')).map(a => ({
                text: a.innerText.trim(),
                href: a.getAttribute('href')
            }))
        """,
        "returnByValue": True
    }, msg_id=4)
    return result.get("result", {}).get("value", [])

def get_html(ws, selector="body"):
    result = cdp_cmd(ws, "Runtime.evaluate", {
        "expression": f"document.querySelector({json.dumps(selector)})?.innerHTML || ''",
        "returnByValue": True
    }, msg_id=5)
    return result.get("result", {}).get("value", "")

def open_ws():
    target = get_target()
    ws_url = target["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url, timeout=30)
    return ws

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "text"
    ws = open_ws()
    if cmd == "navigate":
        navigate(ws, sys.argv[2], wait=int(sys.argv[3]) if len(sys.argv) > 3 else 3)
        print("Navigated.")
    elif cmd == "text":
        print(get_text(ws))
    elif cmd == "links":
        links = get_links(ws)
        for l in links:
            print(f"{l['text']} | {l['href']}")
    ws.close()
