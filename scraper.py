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


def _build_request(username: str) -> urllib.request.Request:
    """Cria request com headers realistas para evitar bloqueio."""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    ]

    return urllib.request.Request(url, headers={
        "User-Agent": random.choice(user_agents),
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "identity",
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest",
        "X-ASBD-ID": "129477",
        "Referer": f"https://www.instagram.com/{username}/",
        "Origin": "https://www.instagram.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Ch-Ua-Platform": '"Windows"',
    })


def _fallback_scrape(username: str) -> dict:
    """Método alternativo: extrai dados das meta tags da página do perfil."""
    url = f"https://www.instagram.com/{username}/"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode("utf-8")
    except Exception:
        raise ValueError("Não foi possível acessar o Instagram no momento. Tente novamente em alguns minutos.")

    # Extrair dados das meta tags
    import html as htmlmod

    og_title = re.findall(r'og:title.*?content="(.*?)"', html)
    og_desc = re.findall(r'og:description.*?content="(.*?)"', html)
    og_image = re.findall(r'og:image.*?content="(.*?)"', html)

    if not og_title:
        raise ValueError(f"Perfil @{username} não encontrado.")

    title = htmlmod.unescape(og_title[0]) if og_title else ""
    desc = htmlmod.unescape(og_desc[0]) if og_desc else ""
    pic_url = htmlmod.unescape(og_image[0]) if og_image else ""

    # Parse: "666 seguidores, seguindo 1,900, 794 posts"
    followers = following = posts_count = 0
    num_match = re.findall(r'([\d,.]+)\s+seguidores.*?seguindo\s+([\d,.]+).*?([\d,.]+)\s+posts', desc)
    if num_match:
        followers = int(num_match[0][0].replace(",", "").replace(".", ""))
        following = int(num_match[0][1].replace(",", "").replace(".", ""))
        posts_count = int(num_match[0][2].replace(",", "").replace(".", ""))

    # Parse nome do title: "Nome (@username)"
    full_name = title.split("(")[0].strip() if "(" in title else title.split("•")[0].strip()

    # Tentar extrair bio do JSON embutido
    biography = ""
    bio_match = re.findall(r'"biography":"(.*?)"', html)
    if bio_match:
        try:
            biography = bio_match[0].encode().decode("unicode_escape")
        except Exception:
            biography = bio_match[0]

    external_url = ""
    url_match = re.findall(r'"external_url":"(.*?)"', html)
    if url_match and url_match[0] != "null":
        external_url = url_match[0]

    category = ""
    cat_match = re.findall(r'"category_name":"(.*?)"', html)
    if cat_match:
        category = cat_match[0]

    return {
        "username": username,
        "full_name": full_name,
        "biography": biography,
        "external_url": external_url,
        "followers": followers,
        "following": following,
        "posts_count": posts_count,
        "is_verified": False,
        "is_business": bool(category),
        "category": category,
        "is_private": False,
        "profile_pic_url": pic_url,
        "posts": [],  # Fallback não consegue pegar posts
    }


def scrape_profile(username: str) -> dict:
    """Faz scraping dos dados públicos de um perfil do Instagram com retry."""
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            req = _build_request(username)
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read().decode("utf-8"))

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

        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(f"Perfil @{username} não encontrado.")
            last_error = e
            if e.code == 429 and attempt < max_retries - 1:
                # Rate limited — esperar e tentar de novo
                time.sleep(2 + attempt * 3)
                continue
            # Se 429 na última tentativa, tenta fallback
            if e.code == 429:
                break
        except ValueError:
            raise
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(1 + attempt * 2)
                continue
            break

    # Fallback: tenta via meta tags da página
    try:
        return _fallback_scrape(username)
    except ValueError:
        raise
    except Exception:
        if last_error:
            raise ValueError(f"Instagram temporariamente indisponível. Tente novamente em 1-2 minutos.")
        raise ValueError("Não foi possível acessar o perfil. Verifique o username e tente novamente.")
