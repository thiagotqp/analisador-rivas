"""Módulo de scraping do Instagram - Extrai dados públicos de perfis."""

import urllib.request
import json
import re
import time
import random


def extract_username(url_or_username: str) -> str:
    """Extrai o username de uma URL do Instagram ou retorna direto se já for username."""
    url_or_username = url_or_username.strip().rstrip("/")
    match = re.search(r"instagram\.com/([A-Za-z0-9._]+)", url_or_username)
    if match:
        return match.group(1)
    return url_or_username.lstrip("@")


# User agents mobile realistas
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
        "X-ASBD-ID": "129477",
        "Referer": f"https://www.instagram.com/{username}/",
        "Origin": "https://www.instagram.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    })
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode("utf-8"))


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
    ]

    last_error = None

    for method_name, method_fn in methods:
        for attempt in range(3):
            try:
                data = method_fn(username)
                return _parse_user_data(data, username)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    raise ValueError(f"Perfil @{username} não encontrado.")
                last_error = e
                if e.code == 429:
                    # Rate limited — esperar e tentar de novo
                    time.sleep(2 + attempt * 3)
                    continue
                # Outro erro HTTP — tentar próximo método
                break
            except ValueError:
                raise
            except Exception as e:
                last_error = e
                if attempt < 2:
                    time.sleep(1 + attempt * 2)
                    continue
                break

    # Tudo falhou
    raise ValueError(
        "Instagram temporariamente indisponível. "
        "Tente novamente em 1-2 minutos."
    )
