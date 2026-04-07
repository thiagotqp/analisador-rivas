import sys, urllib.request, re, json
sys.stdout.reconfigure(encoding='utf-8')

username = 'diogenesssc'
url = f'https://www.instagram.com/{username}/'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
})
resp = urllib.request.urlopen(req, timeout=15)
html = resp.read().decode('utf-8')

scripts = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL)

for i, s in enumerate(scripts):
    if 'diogenesssc' not in s:
        continue

    idx = s.find('"username":"diogenesssc"')
    if idx == -1:
        continue

    print(f'Block {i}: username at index {idx}')

    search_back = s[max(0, idx-10000):idx]
    search_fwd = s[idx:idx+10000]
    combined = search_back + search_fwd

    bio_m = re.search(r'"biography"\s*:\s*"((?:[^"\\\\]|\\\\.)*)"', combined)
    fn_m = re.search(r'"full_name"\s*:\s*"((?:[^"\\\\]|\\\\.)*)"', combined)
    fol_m = re.search(r'"edge_followed_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)', combined)
    fing_m = re.search(r'"edge_follow"\s*:\s*\{\s*"count"\s*:\s*(\d+)', combined)
    media_m = re.search(r'"edge_owner_to_timeline_media"\s*:\s*\{\s*"count"\s*:\s*(\d+)', combined)
    cat_m = re.search(r'"category_name"\s*:\s*"((?:[^"\\\\]|\\\\.)*)"', combined)
    priv_m = re.search(r'"is_private"\s*:\s*(true|false)', combined)
    biz_m = re.search(r'"is_business_account"\s*:\s*(true|false)', combined)
    pic_m = re.search(r'"profile_pic_url_hd"\s*:\s*"((?:[^"\\\\]|\\\\.)*)"', combined)

    print(f'  full_name: {fn_m.group(1)[:60] if fn_m else "NOT FOUND"}')
    print(f'  biography: {bio_m.group(1)[:60] if bio_m else "NOT FOUND"}')
    print(f'  followers: {fol_m.group(1) if fol_m else "NOT FOUND"}')
    print(f'  following: {fing_m.group(1) if fing_m else "NOT FOUND"}')
    print(f'  media: {media_m.group(1) if media_m else "NOT FOUND"}')
    print(f'  category: {cat_m.group(1) if cat_m else "NOT FOUND"}')
    print(f'  private: {priv_m.group(1) if priv_m else "NOT FOUND"}')
    print(f'  business: {biz_m.group(1) if biz_m else "NOT FOUND"}')
    print(f'  pic: {"YES" if pic_m else "NOT FOUND"}')
    break
