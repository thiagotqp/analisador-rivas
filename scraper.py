"""Módulo de scraping do Instagram - Extrai dados públicos de perfis."""

import urllib.request
import json
import re
import time
import random
import sys


def extract_username(url_or_username: str) -> str:
    """Extrai o username de uma URL do Instagram ou retorna direto se já for username."""
    url_or_username = url_or_username.strip().rstrip("/")
    match = re.search(r"instagram\.com/([A-Za-z0-9._]+)", url_or_username)
    if match:
        return match.group(1)
    return url_or_username.lstrip("@")


# User agents
MOBILE_UAS = [
    "Instagram 275.0.0.27.98 Android (33/13; 420dpi; 1080x2400; samsung; SM-G991B; o1s; exynos2100; en_US; 458229258)",
    "Instagram 275.0.0.27.98 Android (31/12; 480dpi; 1080x2340; Google; Pixel 6; oriole; gs101; en_US; 458229258)",
    "Instagram 275.0.0.27.98 Android (34/14; 440dpi; 1080x2340; samsung; SM-S911B; e1s; exynos2400; en_US; 458229258)",
]

WEB_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


def _log(msg):
    """Log para debug no servidor."""
    print(f"[scraper] {msg}", file=sys.stderr, flush=True)


def _try_mobile_api(username: str) -> dict:
    """Tenta via API mobile do Instagram — mais confiável."""
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    req = urllib.request.Request(url, headers={
        "User-Agent": random.choice(MOBILE_UAS),
        "X-IG-App-ID": "936619743392459",
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
    })
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode("utf-8"))


def _try_web_api(username: str) -> dict:
    """Tenta via API web do Instagram."""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    req = urllib.request.Request(url, headers={
        "User-Agent": random.choice(WEB_UAS),
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.instagram.com/{username}/",
        "Origin": "https://www.instagram.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    })
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode("utf-8"))


def _try_page_scrape(username: str) -> dict:
    """Fallback: extrai dados do HTML da página do perfil via script tags JSON."""
    url = f"https://www.instagram.com/{username}/"
    req = urllib.request.Request(url, headers={
        "User-Agent": random.choice(WEB_UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    })
    resp = urllib.request.urlopen(req, timeout=20)
    html = resp.read().decode("utf-8")

    # Procurar JSON script blocks que tenham dados de perfil
    json_scripts = re.findall(
        r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL
    )

    for js_block in json_scripts:
        if "biography" not in js_block and "edge_followed_by" not in js_block:
            continue

        # Encontrar user data dentro do JSON gigante usando regex
        # Os dados estão em formato: "user":{"biography":"...","edge_followed_by":{"count":123},...}
        user_match = re.search(
            r'"user"\s*:\s*\{[^}]*"biography"\s*:', js_block
        )
        if not user_match:
            continue

        # Extrair campos individuais do bloco
        start = user_match.start()
        chunk = js_block[start:start + 10000]

        bio = _extract_json_string(chunk, "biography")
        full_name = _extract_json_string(chunk, "full_name")
        uname = _extract_json_string(chunk, "username")
        external_url = _extract_json_string(chunk, "external_url")
        category = _extract_json_string(chunk, "category_name")
        pic = _extract_json_string(chunk, "profile_pic_url_hd") or _extract_json_string(chunk, "profile_pic_url")
        is_private = _extract_json_bool(chunk, "is_private")
        is_verified = _extract_json_bool(chunk, "is_verified")
        is_business = _extract_json_bool(chunk, "is_business_account")

        followers_match = re.search(r'"edge_followed_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)', chunk)
        following_match = re.search(r'"edge_follow"\s*:\s*\{\s*"count"\s*:\s*(\d+)', chunk)
        media_match = re.search(r'"edge_owner_to_timeline_media"\s*:\s*\{\s*"count"\s*:\s*(\d+)', chunk)

        followers = int(followers_match.group(1)) if followers_match else 0
        following = int(following_match.group(1)) if following_match else 0
        posts_count = int(media_match.group(1)) if media_match else 0

        if not full_name and not bio:
            continue

        # Tentar extrair posts do mesmo bloco
        posts = _extract_posts_from_chunk(js_block, start)

        return {
            "data": {
                "user": {
                    "username": uname or username,
                    "full_name": full_name or "",
                    "biography": bio or "",
                    "external_url": external_url,
                    "edge_followed_by": {"count": followers},
                    "edge_follow": {"count": following},
                    "edge_owner_to_timeline_media": {"count": posts_count, "edges": posts},
                    "is_verified": is_verified,
                    "is_business_account": is_business,
                    "category_name": category or "",
                    "is_private": is_private,
                    "profile_pic_url_hd": pic or "",
                    "profile_pic_url": pic or "",
                    "bio_links": [],
                }
            }
        }

    raise ValueError(f"Não foi possível extrair dados do perfil @{username}.")


def _extract_json_string(chunk: str, key: str) -> str:
    """Extrai valor string de um campo JSON."""
    pattern = f'"{key}"\\s*:\\s*"((?:[^"\\\\]|\\\\.)*)"'
    match = re.search(pattern, chunk)
    if match:
        val = match.group(1)
        try:
            return val.encode().decode("unicode_escape")
        except Exception:
            return val
    # Check for null
    null_pattern = f'"{key}"\\s*:\\s*null'
    if re.search(null_pattern, chunk):
        return ""
    return ""


def _extract_json_bool(chunk: str, key: str) -> bool:
    """Extrai valor boolean de um campo JSON."""
    pattern = f'"{key}"\\s*:\\s*(true|false)'
    match = re.search(pattern, chunk)
    return match.group(1) == "true" if match else False


def _extract_posts_from_chunk(js_block: str, user_start: int) -> list:
    """Tenta extrair dados de posts do bloco JSON."""
    posts = []
    # Buscar edges de posts
    edge_pattern = re.finditer(
        r'"node"\s*:\s*\{[^}]*"__typename"\s*:\s*"Graph(Image|Video|Sidecar)"',
        js_block[user_start:]
    )
    for match in edge_pattern:
        if len(posts) >= 12:
            break
        node_start = match.start() + user_start
        node_chunk = js_block[node_start:node_start + 3000]

        caption_match = re.search(r'"text"\s*:\s*"((?:[^"\\\\]|\\\\.)*)"', node_chunk)
        likes_match = re.search(r'"edge_media_preview_like"\s*:\s*\{\s*"count"\s*:\s*(\d+)', node_chunk)
        comments_match = re.search(r'"edge_media_to_comment"\s*:\s*\{\s*"count"\s*:\s*(\d+)', node_chunk)
        is_video_match = re.search(r'"is_video"\s*:\s*(true|false)', node_chunk)
        pinned_match = re.search(r'"pinned_for_users"\s*:\s*\[([^\]]*)\]', node_chunk)

        caption = ""
        if caption_match:
            try:
                caption = caption_match.group(1).encode().decode("unicode_escape")
            except Exception:
                caption = caption_match.group(1)

        posts.append({
            "node": {
                "edge_media_to_caption": {"edges": [{"node": {"text": caption}}] if caption else []},
                "edge_media_preview_like": {"count": int(likes_match.group(1)) if likes_match else 0},
                "edge_media_to_comment": {"count": int(comments_match.group(1)) if comments_match else 0},
                "is_video": is_video_match.group(1) == "true" if is_video_match else False,
                "__typename": f"Graph{match.group(1)}",
                "pinned_for_users": [1] if (pinned_match and pinned_match.group(1).strip()) else [],
            }
        })

    return posts


def _parse_user_data(data: dict, username: str) -> dict:
    """Extrai dados do perfil da resposta da API."""
    user = data.get("data", {}).get("user")
    if not user:
        raise ValueError(f"Perfil @{username} não encontrado.")

    if user.get("is_private"):
        raise ValueError(f"O perfil @{username} é privado. Só é possível analisar perfis públicos.")

    posts = []
    edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
    for edge in edges[:12]:
        node = edge.get("node", {})
        caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
        caption = caption_edges[0]["node"]["text"] if caption_edges else ""
        likes = node.get("edge_media_preview_like", {}).get("count", 0)
        comments = node.get("edge_media_to_comment", {}).get("count", 0)
        is_video = node.get("is_video", False)
        typename = node.get("__typename", "")
        pinned = bool(node.get("pinned_for_users", []))

        posts.append({
            "caption": caption,
            "likes": likes,
            "comments": comments,
            "is_video": is_video,
            "type": typename,
            "pinned": pinned,
        })

    bio_links = user.get("bio_links", [])
    external_url = user.get("external_url") or ""
    if not external_url and bio_links:
        external_url = bio_links[0].get("url", "")

    return {
        "username": user.get("username", username),
        "full_name": user.get("full_name", ""),
        "biography": user.get("biography", ""),
        "external_url": external_url,
        "followers": user.get("edge_followed_by", {}).get("count", 0),
        "following": user.get("edge_follow", {}).get("count", 0),
        "posts_count": user.get("edge_owner_to_timeline_media", {}).get("count", 0),
        "is_verified": user.get("is_verified", False),
        "is_business": user.get("is_business_account", False),
        "category": user.get("category_name", ""),
        "is_private": user.get("is_private", False),
        "profile_pic_url": user.get("profile_pic_url_hd", user.get("profile_pic_url", "")),
        "posts": posts,
    }


def scrape_profile(username: str) -> dict:
    """Faz scraping dos dados públicos de um perfil do Instagram."""
    methods = [
        ("mobile_api", _try_mobile_api),
        ("web_api", _try_web_api),
        ("page_scrape", _try_page_scrape),
    ]

    last_error = None

    for method_name, method_fn in methods:
        for attempt in range(2):
            try:
                _log(f"Tentando {method_name} (tentativa {attempt+1}) para @{username}")
                data = method_fn(username)
                result = _parse_user_data(data, username)
                _log(f"Sucesso via {method_name}: @{username} ({result['followers']} seguidores)")
                return result
            except urllib.error.HTTPError as e:
                _log(f"{method_name} HTTP {e.code}")
                if e.code == 404:
                    raise ValueError(f"Perfil @{username} não encontrado.")
                last_error = e
                if e.code == 429:
                    time.sleep(3 + attempt * 4)
                    continue
                break
            except ValueError:
                raise
            except Exception as e:
                _log(f"{method_name} erro: {e}")
                last_error = e
                if attempt < 1:
                    time.sleep(2)
                    continue
                break

    raise ValueError(
        "Instagram temporariamente indisponível. "
        "Tente novamente em 1-2 minutos."
    )
