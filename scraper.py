"""Módulo de scraping do Instagram - Múltiplos métodos com fallback."""

import urllib.request
import http.cookiejar
import json
import re
import os
import sys
import time
import random
import urllib.parse


def extract_username(url_or_username: str) -> str:
    url_or_username = url_or_username.strip().rstrip("/")
    match = re.search(r"instagram\.com/([A-Za-z0-9._]+)", url_or_username)
    if match:
        return match.group(1)
    return url_or_username.lstrip("@")


def _log(msg):
    print(f"[scraper] {msg}", file=sys.stderr, flush=True)


def _try_with_cookies(username: str) -> dict:
    """Acessa Instagram simulando navegador real com cookies."""
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    # Passo 1: Visitar Instagram para pegar cookies
    req0 = urllib.request.Request("https://www.instagram.com/", headers={"User-Agent": ua})
    resp0 = opener.open(req0, timeout=10)
    resp0.read()

    # Passo 2: Chamar API com cookies
    ig_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    req1 = urllib.request.Request(ig_url, headers={
        "User-Agent": ua,
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.instagram.com/{username}/",
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })
    resp1 = opener.open(req1, timeout=15)
    return json.loads(resp1.read().decode("utf-8"))


def _try_mobile_api(username: str) -> dict:
    """Tenta via endpoint mobile."""
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    uas = [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Instagram 275.0.0.27.98 Android (33/13; 420dpi; 1080x2400; samsung; SM-G991B; o1s; exynos2100; en_US; 458229258)",
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    ]
    req = urllib.request.Request(url, headers={
        "User-Agent": random.choice(uas),
        "X-IG-App-ID": "936619743392459",
        "Accept": "*/*",
    })
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode("utf-8"))


def _try_graphql(username: str) -> dict:
    """Tenta via endpoint GraphQL."""
    # Primeiro pegar o user_id da página
    page_url = f"https://www.instagram.com/{username}/"
    req = urllib.request.Request(page_url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    })
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode("utf-8")

    user_id_match = re.search(r'"profilePage_(\d+)"', html)
    if not user_id_match:
        raise ValueError("Não encontrou user_id")

    user_id = user_id_match.group(1)

    # Usar API de user info
    info_url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    req2 = urllib.request.Request(info_url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "X-IG-App-ID": "936619743392459",
    })
    resp2 = urllib.request.urlopen(req2, timeout=15)
    return json.loads(resp2.read().decode("utf-8"))


def _parse_user_data(data: dict, username: str) -> dict:
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
            "caption": caption, "likes": likes, "comments": comments,
            "is_video": is_video, "type": typename, "pinned": pinned,
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
    methods = [
        ("cookies", _try_with_cookies),
        ("mobile_api", _try_mobile_api),
        ("graphql", _try_graphql),
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
                    time.sleep(3 + attempt * 5)
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
        "Instagram temporariamente indisponível. Tente novamente em 1-2 minutos."
    )
