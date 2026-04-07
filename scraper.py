"""Módulo de scraping do Instagram - Extrai dados públicos de perfis."""

import urllib.request
import json
import re
import html as htmlmod


def extract_username(url_or_username: str) -> str:
    """Extrai o username de uma URL do Instagram ou retorna direto se já for username."""
    url_or_username = url_or_username.strip().rstrip("/")
    match = re.search(r"instagram\.com/([A-Za-z0-9._]+)", url_or_username)
    if match:
        return match.group(1)
    # Remove @ se tiver
    return url_or_username.lstrip("@")


def scrape_profile(username: str) -> dict:
    """Faz scraping dos dados públicos de um perfil do Instagram."""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.instagram.com/{username}/",
    })

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"Perfil @{username} não encontrado.")
        raise ValueError(f"Erro ao acessar Instagram (HTTP {e.code}). Tente novamente.")
    except Exception:
        raise ValueError("Não foi possível conectar ao Instagram. Tente novamente.")

    user = data.get("data", {}).get("user")
    if not user:
        raise ValueError(f"Perfil @{username} não encontrado.")

    if user.get("is_private"):
        raise ValueError(f"O perfil @{username} é privado. Só é possível analisar perfis públicos.")

    # Extrair posts recentes
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

    # Bio links
    bio_links = user.get("bio_links", [])
    external_url = user.get("external_url") or ""
    if not external_url and bio_links:
        external_url = bio_links[0].get("url", "")

    profile_data = {
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

    return profile_data
