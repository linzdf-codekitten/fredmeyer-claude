import requests, json, csv, io, sys
from datetime import datetime, timedelta

COOKIE_STR = 'abpl=tl_6c050a|tl_49ab38|tl_49ab3b; pid=20c05af6-b02a-5098-9c61-65926f743059; rxVisitorg9i8dbl7=1779641794114J9F8PK08D3JELG00GO20TVENKBTSU4CS; AMCV_371C27E253DB0F910A490D4E%40AdobeOrg=179643557%7CMCIDTS%7C20598%7CMCMID%7C47549751682804057841478970056104865429%7CMCAID%7CNONE%7CMCOPTOUT-1779648995s%7CNONE%7CvVersion%7C5.5.0; _fbp=fb.1.1779641797582.2039161575; _gcl_au=1.1.1739052903.1779641798; _ga=GA1.1.1593616601.1779641798; StoreCode=00832; DivisionID=705; dtCookieg9i8dbl7=v_4_srv_21_sn_E1D7D7E934CDD954830014944A8E21EB_perc_100000_ol_0_mul_1_app-3A5205c01c10dc0122_1_rcs-3Acss_0; msal.cache.encryption=%7B%22id%22%3A%22019e5c2d-82c4-749c-b2f4-7e4bb7ed962d%22%2C%22key%22%3A%22W4PBor_f2CqrjQB7ZjZvGk-S86XB0QCbLXkVf9xkJlU%22%7D; krguid=7a38fed6-d1c5-0119-2b3b-1934f6d3c8b5; bm_mi=128510C700E936B6C084EB626FF1F580~YAAQotAuF/8PIDOeAQAAyawuXB8tXL9DT+YlGQlouQChwEbqgg7laOL2LLQXDQ3V4L6UlAX3mg0V02W4qhbZpy9VvBGz5RJuQz7e//uefIAWbe2j3umU11uNp4Ld/zm0ugnsij3diS3ljCdAztAWN9P2QtYYxVQA453sLlbpS7X8XBQg1oU7Fof76QHIwaD4YBjDjvHHfkYMbDDVdPrMgEwQa1B8Q0W/0VpqaXdnWHZDSYIANXZWkHiujG2gx5xTR4HhTFcgmffW1X5MNYzydvXfOxzW0bbtGCylEJmpaq8W87kTf1oz9NivxTzvI2wWv8LpJqIL4YI1xXwwj42yuD7ZOKX/cTA3C/PXRFV0pNvdcieCtvGA~1; DD_guid=7a38fed6-d1c5-0119-2b3b-1934f6d3c8b5; _gcl_gs=2.1.k1$i1779662943$u239659075; _gcl_dc=GCL.1779662952.EAIaIQobChMIipPfjIHTlAMVZNHCBB39zCTSEAAYASAAEgKWoPD_BwE; s_sq=krgrglobalprod%3D%2526pid%253Dhttps%25253A%25252F%25252Fwww.qfc.com%25252F%25253Fgclsrc%25253Daw.ds%252526%252526cid%25253Dps_adw_ogs_15x1savoffer_t%25253Awww%25252Bqfc%25252Bcom%252526gad_source%25253D1%252526gad_campaignid%25253D22395165245%252526gclid%25253DEAIaIQobChMIipPfjIHTlAMVZNHCBB39zCTSEAAYASAAEgKWoPD_BwE%2526oid%253Dhttps%25253A%25252F%25252Fwww.qfc.com%25252Fmypurchases%2526ot%253DA%26krgrmobileprod%3D%2526pid%253Dhttps%25253A%25252F%25252Fwww.qfc.com%25252F%25253Fgclsrc%25253Daw.ds%252526%252526cid%25253Dps_adw_ogs_15x1savoffer_t%25253Awww%25252Bqfc%25252Bcom%252526gad_source%25253D1%252526gad_campaignid%25253D22395165245%252526gclid%25253DEAIaIQobChMIipPfjIHTlAMVZNHCBB39zCTSEAAYASAAEgKWoPD_BwE%2526oid%253Dhttps%25253A%25252F%25252Fwww.qfc.com%25252Fmypurchases%2526ot%253DA; bm_sc=4~2~264275551~YAAQotAuFxwbIDOeAQAARdIuXAjeHPgn+CL2+YjBykyFcLKLhUU9QBNc+TNURVKf4bxxhIZUO5m1vB73WaIRSF959BV40dzNRdB82SOcUcJjemIEmVpdzrunz3N/AWwCIAMnquFM6vhk01v3LsspAYzTzXhQhQKTbQjAFB/wed6vjvauSLaEtMg448cA3xMQYoXbSeVByg/fbAzpCDo9xi4Iiu5poCtsnUMTcJqQGMIBf/yS3ZOtBD4d0qEAYvZgnN8cfPqM++JKQ4zAvQJaEdyBAIoJksMFSHA+HdVd2cdbgrrU8TYeW+NaqbJIrBxb2b9iB765w02Jl2tBoj/jO4OUbIo4Jlmq7S2Qv5FYmQWAzJwQMNqqATZAKAzI+2WdQAyVDPPdDuySYBz3kWh7DjNEnmgWKHuvkmKxVGzXbWxk4kU3Q78VlkCVcZVCLzcwhBIPCipdR0/FjzR2lnodPuTcp6kSFHQpmoSLNhHEjDieHeWupkCirqYRTFiJHpq9AnGimf6ODFKJstsn8qvSoHSMJ3DgSoGN/6T0I/vGSxZvLvBjjWs/wtrmdSHKM1P3XGgkRZW0TBvB0gyqasGc/T9NQVZV/SVvlXN/3XRn5F4RvLtMA4IosF7V/FKE0T5Ug5MM45V6N4qW4o9g/mjYbOE3OuzEQaRS+3PaqlaQw9dELhIpFhFhMf+me/UNsXAe96tNsMtUmSNFdPGEmkMYk7KyxIBcVcrBoBDYbae3sCEwZop97q/BA1hbnDdcbf5F7XuPyccdtJQa7CY5S16EEtww/hB6/jy260Ax8kjws01tIotDY/K2GU+DsNVrKsy7ALkPBnAkXB36aDyE2PscK94HyvNoDeXwcsxk30FsYR57fJkLr4IaUSNzQ/vwOZxTvvLJQSOrtPbZyuGHsBUmD7vIxwpU/E45cmmuJxZJg1dx9TO5GAY4Hs5R0/BnhE/OCwDAGUjnOHIs/tnKgYfbJvR4mGQxnr1K6jKmZWnuXXkCjvldwS13ZX0E2Vfygeg72g5pFQ/dwQPt3QoXFG6TImpErxaHXlFD1Hx0IaJrdxvjx7w=~0~0~0; _gcl_aw=GCL.1779662958.EAIaIQobChMIipPfjIHTlAMVZNHCBB39zCTSEAAYASAAEgKWoPD_BwE; DD_modStore=70500832; bm_so=CAB109E9F7EBABC614CA09AE3328B21A02D86860D667DAD20B8A1BD34FC44C6C~YAAQotAuFwhVIDOeAQAAXYYvXAdEulaxxGbXkGeXbVwu0WMScqOxnNm17mlrAIh6MWlC9bUeyZdOtVtwUt3cIIgi0gbC637rP+3wgIIrQx+HY3wb8YIT0qEYa88Ccyoyf0aRhU0e7feRhPBtQqAs4l8v0E9/ZBBVHA0EEUM9FJstT4e7rxri5D7ZvYWzK9dcgIHOSRDpr18h/riW7TSQjmk+MZE2iPkc4wvvlm4B0WtZgfyC9hrCEG0XUTS4DvhXsOa/hMaDNQGMPvb1DOil0+wbyRCSn+G4DtY/F4zoSeNPKegQuvR3EuazWy2PP697nw5AYTHJffQau7HsOpWI6LdDLlI/M5DT/M1YwpPMjrK6Tghcg04nTYvl85hIszo65ca20AuR1mpRVkL2AYAwTH+OumvrVsOLKalY+As/Ex2WTpY0XWBDYt1of6eWuck2qjpmiyZVGbQewgDeylOq; dtSag9i8dbl7=false%7Cxhr%7C89%7Cx%7Cx%7C1779662968862%7C62965148_696%7Chttps%3A%2F%2Fwww.qfc.com%2Fconnect-auth%7C%7C%7C%7C%7C%2Fconnect-auth%7C1779662963205%7C%7Ci1%5Esk0%5Esh0%5Est1; abTest=23_a128ad_-2|TL_3a676e_B|3f_8aae36_A|a6_0ee7bc_-2|2b_877ab4_-2; RT="z=1&dm=qfc.com&si=rs32r61652&ss=mpkddo5x&sl=1&tt=0&obo=1"; bm_lso=CAB109E9F7EBABC614CA09AE3328B21A02D86860D667DAD20B8A1BD34FC44C6C~YAAQotAuFwhVIDOeAQAAXYYvXAdEulaxxGbXkGeXbVwu0WMScqOxnNm17mlrAIh6MWlC9bUeyZdOtVtwUt3cIIgi0gbC637rP+3wgIIrQx+HY3wb8YIT0qEYa88Ccyoyf0aRhU0e7feRhPBtQqAs4l8v0E9/ZBBVHA0EEUM9FJstT4e7rxri5D7ZvYWzK9dcgIHOSRDpr18h/riW7TSQjmk+MZE2iPkc4wvvlm4B0WtZgfyC9hrCEG0XUTS4DvhXsOa/hMaDNQGMPvb1DOil0+wbyRCSn+G4DtY/F4zoSeNPKegQuvR3EuazWy2PP697nw5AYTHJffQau7HsOpWI6LdDLlI/M5DT/M1YwpPMjrK6Tghcg04nTYvl85hIszo65ca20AuR1mpRVkL2AYAwTH+OumvrVsOLKalY+As/Ex2WTpY0XWBDYt1of6eWuck2qjpmiyZVGbQewgDeylOq~1779663005661; loggedIn=yes; OptanonAlertBoxClosed=2026-05-24T22:50:06.655Z; firstPageViewTriggered=true; OptanonConsent=isGpcEnabled=0&datestamp=Sun+May+24+2026+22%3A50%3A07+GMT%2B0000+(Coordinated+Universal+Time)&version=202510.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=04fa627b-7f2d-49c9-a882-0aeb2e8eb07b&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=BG1339%3A1%2CC0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1%2CC0009%3A1%2CC0008%3A1&AwaitingReconsent=false&geolocation=US%3BWA; _abck=095D48B6D21B41D137E1D222E7EA7CD8~-1~YAAQotAuF3VeIDOeAQAA6Z0vXA+VSrGxuprfbGzeuub++y9IhQiw1a+6NevKRuZ26XDZQ9z5+Rb4+ros1S/YkRX2o72tyhD06SNvfovAlbE04aybN4CMJWpdTQ7yRH9RGx+zeILTFmj2SNkFdBbJDEXoIwsDf0Lpu642hcqTmhdhJwEddUn4VjBNMhKTmxBESBhZ1Ib2Wcgl8hIJSf0rr1x22+WvH2y+XsxOulcNsYO+vn4/h1BB3Sh6pG9VCBp+EL6y3Di8Jhql7KLFvHCZvFx1QIHuRAkA4UlRva9E+t2Xcs7H4y4HdT3yoMi7lIdEA2J849xyF8DLQCwjsu+rxf0zEeSnxLb1+Xt7C4BMdIsR42aW6SqC/Qns9b+vL0TWm7zNpLpxg01XzaR2bNmnuA5Kv/VlCmz1q8AQIe53RxK2kTPr5WWrT8tUUeQlEp8rzOPCRwbAoPaHsYYeKUkYShd9FT+NNn7Aga8BDbxMAR7eo1WPFFbwRXEV3+1zRiyWYE2I/x89Ve2esOHammyg25NgxIWUwEqAryoXXv+zUCX6AL57hyD5XbmI6zas2OIp9hWF+aHfedppCjUNRxQvxoG/1UaijsO8DplPJVYGVAkRxI3TRHo0kQylO4i/KrI36iVLPlbH0e871L2D0/tHM+Pddpr2HjVapuVQ+gCcL0LgOTjHSttNbvMxB/j/ObiQYDHMvWFSsj5Bo945hY4Wgy1EJHQg9fG1EjZpHWqgwcJcKx6k1qoorz2pH7uH/io6uBRN5IBOqzyZnxQUJqSU4xV07BddM/F4lHEc1ouUonSnSIDeYQXB3IArp+bcdC4AQtHedEdgnlu6A6CUnoFv8l9H+1AQVf5EKv95RaSxyO/xOJFHmr0uaigDrWPOWue6dZC/c1o1LRgXlXskhvJGinVZ7//6Rk3YqLAchjVJ4eFR3VDMZ52dDaPs/pDl8y2N7Q4OLK9pXNOlxP66vZJIdt1o4vaOTNgZrQSWrsiRmHTnIp1As7COKhYFQ7PyKDs+QFvgjl92e76fcZyv3cuS8JnmFC8/Z2CAfMLTmbU7FOLJjWVLxOczC2MHQDKYcTqY4oOrVBesd5XIJpS9+j2px9dawJwubr+n~-1~-1~1779665222~AAQAAAAF%2f%2f%2f%2f%2fzsQ2clVtHPdEyMyPSv1SnsLVkoW8q2lHlDJgY%2fGbn9o7yzhKJETY8OUHoFia9cBrOHsFTmmmaPwMSofzQrpU+k5CrYiQm84y0tP5N7Swsl2LGC2j4qXiRj1wfMDSCFbcFY3ET4%3d~1779663142; bm_sz=2BFFBCFDAFCEE1706E9220907326CA82~YAAQotAuF3heIDOeAQAA6Z0vXB8Qk6sc20G1AqyiEYVOsu2hFUCdx8lTEDiiz9+uJlGladzCrtmAhzTUk7iUYs4FHxm+/g1CMhW9EUA9xwCmMEpUkeWShox3IYpOKrdLpRflx7yYbIq5gGsfSt1KJBKj3Qlo87hfsmQGJIR01rOxG1qHxFUogJaztmCQ5TpVf8tnxplVY6LxhcUqn30P63CbijEcPzEn9aqs1JnZDRjyDGm06d6trV05NEwKGNYf2Ar0YT0WmX6VFMA3lsjBN+bc54Xzi+x5CYpBwSsN4E4zOsTaclWgIrNMbJIGryqOR6QH2t4g6SR7ushFuF1/cAvWwx/I4KBP8LmiVNvIwkp4+nA2oLxes155fyny5D4B5ZT7Dxx2/GcadoCftE2x5H+QyplMl9zBMyOf5OnMHz28V1lrUSjb6O6R1xJABCQ7DgCt4qCku29soJ24Ui2yyJOpLbkRzaFC~3682370~3750196; rxvtg9i8dbl7=1779664809802|1779662946255; _ga_8WFSX616HR=GS2.1.s1779662955$o2$g0$t1779663010$j5$l0$h0; dtPCg9i8dbl7=21$63003376_86h-vMPDUMCHVLKAAOQAIICUEPGKCFUHLNFCC-0e0; bm_sv=DE2E42D20541ECA4DD533572D2AEFD84~YAAQotAuF2iLIDOeAQAAQRMwXB/FmR1hyRaQrj2YvM6tC4CjXafZi9JxEX2M6VuzaizTnmz4rpa/6Kv/JwW2xISHBUtRPykbXdp3Lx2n88tBpO2tihvTrZCFTpYfSYt5WGZc+KRei04qPr/E2OxbqEjA6iU77ogNu0DF/4MWE6FZJbVFWbj/9XKCwLiCczCQCzK3zCUTLUqnYF93C87bYP0DcEKfIUEyZAHnuHsSaovRb6vS3tDJvU/mhRP4Og==~1'

def parse_cookies(s):
    cookies = {}
    for part in s.split('; '):
        if '=' in part:
            k, _, v = part.partition('=')
            cookies[k.strip()] = v.strip()
    return cookies

cookies = parse_cookies(COOKIE_STR)

session = requests.Session()
session.cookies.update(cookies)
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.qfc.com/mypurchases',
    'x-kroger-channel': 'WEB',
})

cutoff = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
print(f"Cutoff date: {cutoff}", flush=True)

# Step 1: fetch purchase history list pages
all_orders = []
for page in range(1, 20):
    print(f"Fetching order list page {page}...", flush=True)
    resp = session.get(
        f'https://www.qfc.com/mypurchases',
        params={'page': page, 'tab': 'purchases'},
        headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'},
    )
    print(f"  Status: {resp.status_code}, URL: {resp.url}", flush=True)

    # Look for order links in the HTML (server-side rendered)
    import re
    links = re.findall(r'/mypurchases/detail/([A-Z0-9~]+)', resp.text)
    links = list(dict.fromkeys(links))  # dedupe preserving order

    if not links:
        print(f"  No orders found on page {page}, stopping.", flush=True)
        break

    months = {'January':'01','February':'02','March':'03','April':'04','May':'05','June':'06',
              'July':'07','August':'08','September':'09','October':'10','November':'11','December':'12'}
    stop = False
    for order_id in links:
        # Try to find date near the link in HTML
        pattern = rf'/mypurchases/detail/{re.escape(order_id)}.{{0,300}}?(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+),\s+(\d{{4}})'
        m = re.search(pattern, resp.text, re.DOTALL)
        if m:
            date = f"{m.group(3)}-{months[m.group(1)]}-{m.group(2).zfill(2)}"
        else:
            date = '0000-00-00'

        type_m = re.search(rf'/mypurchases/detail/{re.escape(order_id)}.{{0,100}}?(In-store|Pickup)', resp.text, re.DOTALL | re.IGNORECASE)
        order_type = type_m.group(1).lower().replace('-','') if type_m else 'in-store'

        if date != '0000-00-00' and date < cutoff:
            print(f"  Order {order_id} date {date} before cutoff, stopping.", flush=True)
            stop = True
            break

        all_orders.append({'id': order_id, 'date': date, 'type': order_type,
                           'url': f'https://www.qfc.com/mypurchases/detail/{order_id}'})
        print(f"  Found order {order_id} ({date}, {order_type})", flush=True)

    if stop:
        break

print(f"\nTotal orders to fetch: {len(all_orders)}", flush=True)

if not all_orders:
    print("No orders found. The session cookies may have expired or the page is fully client-side rendered.")
    print("\nFalling back to direct API...", flush=True)
    # Try the direct details API with just the division/store from cookies
    sys.exit(1)

# Step 2: fetch details for each order via the API
header = ['date','order_type','item_name','size','quantity','price_paid','product_url','upc']
all_rows = []

for order in all_orders:
    parts = order['id'].split('~')
    if len(parts) < 5:
        print(f"Skipping malformed order ID: {order['id']}")
        continue
    div, store, txn_date, term, txn_id = parts[0], parts[1], parts[2], parts[3], parts[4]
    print(f"Fetching details for {order['id']}...", flush=True)

    resp = session.post(
        'https://www.qfc.com/atlas/v1/purchase-history/v2/details',
        json=[{'divisionNumber': div, 'storeNumber': store, 'transactionDate': txn_date,
               'terminalNumber': term, 'transactionId': txn_id}],
        headers={'content-type': 'application/json', 'accept': 'application/json, text/plain, */*'},
    )
    print(f"  Status: {resp.status_code}", flush=True)
    if resp.status_code != 200:
        print(f"  Response: {resp.text[:200]}", flush=True)
        continue

    data = resp.json()
    details = data.get('data', {}).get('purchaseHistoryDetails', [{}])[0]
    items = details.get('items', [])
    for item in items:
        pd = item.get('purchasedData', {})
        di = pd.get('displayInfo', {})
        pi = pd.get('pricingInfo', {})
        qi = pd.get('quantityInfo', {})
        upc = pd.get('upc', '')
        name = di.get('description', '')
        size = di.get('customerFacingSize', '')
        qty = str(qi.get('received', ''))
        price = f"${pi.get('totalPricePaid', '')}"
        url = f"https://www.qfc.com/p/{name.lower().replace(' ','-')}/{upc}" if upc else ''
        all_rows.append([order['date'], order['type'], name, size, qty, price, url, upc])

    print(f"  Got {len(items)} items", flush=True)

# Step 3: sort and write CSV
all_rows.sort(key=lambda r: (-int(r[0].replace('-','')) if r[0] != '0000-00-00' else 0, r[2]))

with open('qfc-purchases.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(all_rows)

print(f"\nDone. {len(all_rows)} rows written to qfc-purchases.csv")
