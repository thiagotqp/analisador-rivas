"""Módulo de análise de perfil baseado no Método Rivas - Pilar 1."""

import re

# Palavras-chave do mercado imobiliário
KEYWORDS_IMOVEIS = [
    "imóvel", "imóveis", "imovel", "imoveis", "imobiliário", "imobiliária", "imobiliario",
    "corretor", "corretora", "creci", "construtora", "incorporadora",
    "apartamento", "casa", "terreno", "lote", "sala comercial", "galpão",
    "lançamento", "alto padrão", "minha casa", "financiamento",
    "comprar", "vender", "alugar", "locação", "temporada",
    "real estate", "broker", "property",
]

KEYWORDS_NICHO = {
    "alto_padrao": ["alto padrão", "luxo", "premium", "exclusivo", "sofisticado", "luxury"],
    "mcmv": ["minha casa", "minha vida", "mcmv", "popular", "subsidiado", "subsídio"],
    "investimento": ["investimento", "investidor", "rentabilidade", "roi", "valorização", "renda passiva"],
    "lancamento": ["lançamento", "na planta", "pré-lançamento", "construção"],
    "temporada": ["temporada", "airbnb", "booking", "curta temporada"],
}

KEYWORDS_AUTORIDADE = [
    "vendas", "milhões", "milhoes", "famílias", "clientes atendidos",
    "anos no mercado", "especialista", "referência", "referencia",
    "primeiro lugar", "top", "prêmio", "premio", "certificado",
    "unidades vendidas", "experiência", "experiencia",
]

KEYWORDS_CTA = [
    "clique", "clica", "link", "whatsapp", "zap", "chama", "entre em contato",
    "agende", "fale comigo", "me chame", "saiba mais", "descubra",
    "conheça", "acesse", "baixe", "cadastre",
]

KEYWORDS_FILOSOFIA = [
    "nietzsche", "jung", "carl jung", "diógenes", "platão", "aristóteles",
    "filosofia", "estoicismo", "mindset", "mentalidade", "desenvolvimento pessoal",
    "coach", "coaching", "autoconhecimento", "meditação", "consciência",
    "napoleon hill", "i ching", "arquétipo",
]

KEYWORDS_EDUCACIONAL = [
    "como", "dicas", "erros", "passo a passo", "aprenda", "entenda",
    "tutorial", "guia", "sabia que", "você sabia", "por que", "descubra",
    "financiar", "financiamento", "score", "documentação", "selic",
]

KEYWORDS_PROVA_SOCIAL = [
    "depoimento", "cliente", "feedback", "resultado", "fechamento",
    "entrega", "chave", "aprovado", "conquistou", "realizou", "sonho",
    "vendido", "assinatura", "contrato",
]

HASHTAGS_GENERICAS = [
    "#love", "#instagood", "#photooftheday", "#beautiful", "#happy",
    "#follow", "#like4like", "#picoftheday", "#selfie", "#instadaily",
    "#followme", "#repost", "#nofilter", "#life", "#smile",
    "#atfive", "#sonicskiesshapes",
]


def contains_keywords(text: str, keywords: list) -> list:
    """Retorna quais keywords foram encontradas no texto."""
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


def analyze_profile(profile: dict) -> dict:
    """Analisa um perfil do Instagram segundo o Método Rivas Pilar 1."""
    results = {}
    bio = profile.get("biography", "")
    full_name = profile.get("full_name", "")
    username = profile.get("username", "")
    external_url = profile.get("external_url", "")
    followers = profile.get("followers", 0)
    following = profile.get("following", 0)
    posts = profile.get("posts", [])
    posts_count = profile.get("posts_count", 0)
    category = profile.get("category", "")

    # ============================================================
    # 1. ANÁLISE DO NOME DO PERFIL
    # ============================================================
    nome_score = 5  # base
    nome_feedback = []
    nome_positivos = []

    # Verifica se tem indicação do que faz
    imoveis_no_nome = contains_keywords(full_name, KEYWORDS_IMOVEIS)
    if imoveis_no_nome:
        nome_score += 3
        nome_positivos.append(f"Indica a área de atuação no nome ({', '.join(imoveis_no_nome[:2])})")
    else:
        nome_score -= 2
        nome_feedback.append("Não indica claramente que trabalha com imóveis no nome do perfil")

    # Verifica se tem nicho específico
    nicho_no_nome = False
    for nicho, kws in KEYWORDS_NICHO.items():
        if contains_keywords(full_name, kws):
            nicho_no_nome = True
            nome_score += 2
            nome_positivos.append(f"Menciona nicho específico no nome")
            break
    if not nicho_no_nome:
        nome_feedback.append("Falta especificar o nicho (alto padrão, MCMV, investimento, etc.) no nome")

    # Verifica região no nome
    # Cidades brasileiras comuns
    cidades = ["salvador", "são paulo", "sp", "rio", "rj", "bh", "curitiba", "florianópolis",
               "recife", "fortaleza", "brasília", "campinas", "santos", "balneário"]
    regiao_no_nome = contains_keywords(full_name, cidades)
    if regiao_no_nome:
        nome_score += 1
        nome_positivos.append(f"Menciona região de atuação")

    nome_score = max(0, min(10, nome_score))

    nome_sugestao = f"Sugestão: '{profile.get('full_name', '').split('|')[0].strip()} | Corretor [NICHO] em [CIDADE]'"

    results["nome"] = {
        "score": nome_score,
        "valor_atual": full_name,
        "positivos": nome_positivos,
        "problemas": nome_feedback,
        "sugestao": nome_sugestao,
    }

    # ============================================================
    # 2. ANÁLISE DO ARROBA
    # ============================================================
    arroba_score = 7
    arroba_feedback = []
    arroba_positivos = []

    if len(username) > 20:
        arroba_score -= 2
        arroba_feedback.append("Arroba muito longo, difícil de memorizar")
    else:
        arroba_positivos.append("Tamanho adequado")

    pontos = username.count(".") + username.count("_")
    numeros = sum(1 for c in username if c.isdigit())
    if pontos > 1:
        arroba_score -= 1
        arroba_feedback.append(f"Muitos pontos/underscores ({pontos}) — dificulta memorização")
    if numeros > 2:
        arroba_score -= 1
        arroba_feedback.append("Muitos números — dificulta memorização")
    if pontos <= 1 and numeros <= 1:
        arroba_score += 2
        arroba_positivos.append("Fácil de lembrar e memorizar")

    arroba_score = max(0, min(10, arroba_score))

    results["arroba"] = {
        "score": arroba_score,
        "valor_atual": f"@{username}",
        "positivos": arroba_positivos,
        "problemas": arroba_feedback,
    }

    # ============================================================
    # 3. ANÁLISE DA BIO (MAIS IMPORTANTE)
    # ============================================================
    bio_score = 0
    bio_feedback = []
    bio_positivos = []

    bio_lines = [l.strip() for l in bio.split("\n") if l.strip()]

    # Linha 1 - Como ajuda
    imoveis_na_bio = contains_keywords(bio, KEYWORDS_IMOVEIS)
    if imoveis_na_bio:
        bio_score += 2
        bio_positivos.append("Menciona o mercado imobiliário na bio")
    else:
        bio_feedback.append("LINHA 1 ausente: Não diz claramente como ajuda o cliente com imóveis")

    # Nicho na bio
    nicho_na_bio = False
    nicho_detectado = None
    for nicho, kws in KEYWORDS_NICHO.items():
        found = contains_keywords(bio, kws)
        if found:
            nicho_na_bio = True
            nicho_detectado = nicho
            bio_score += 1
            bio_positivos.append(f"Menciona nicho específico: {found[0]}")
            break
    if not nicho_na_bio:
        bio_feedback.append("Sem nicho definido na bio (alto padrão, MCMV, investidores, etc.)")

    # Região na bio
    regiao_na_bio = contains_keywords(bio, cidades)
    if regiao_na_bio:
        bio_score += 1
        bio_positivos.append(f"Menciona região: {regiao_na_bio[0]}")
    else:
        bio_feedback.append("Sem região de atuação na bio — o cliente não sabe onde você atua")

    # Linha 2 - Autoridade
    autoridade_na_bio = contains_keywords(bio, KEYWORDS_AUTORIDADE)
    numeros_na_bio = re.findall(r'\d+', bio)
    if autoridade_na_bio or (numeros_na_bio and imoveis_na_bio):
        bio_score += 2
        bio_positivos.append("Tem elemento de autoridade/diferencial")
    else:
        bio_feedback.append("LINHA 2 ausente: Sem prova de autoridade (vendas, anos de experiência, clientes atendidos)")

    # Linha 3 - CTA
    cta_na_bio = contains_keywords(bio, KEYWORDS_CTA)
    if cta_na_bio:
        bio_score += 2
        bio_positivos.append(f"Tem chamada para ação: '{cta_na_bio[0]}'")
    else:
        bio_feedback.append("LINHA 3 ausente: Sem CTA (chamada para ação) clara e direta")

    # Link
    if external_url:
        bio_score += 2
        bio_positivos.append(f"Tem link na bio")
    else:
        bio_feedback.append("SEM LINK NA BIO — gravíssimo! Zero conversão, zero leads")

    # Penalidades
    filosofia_na_bio = contains_keywords(bio, KEYWORDS_FILOSOFIA)
    if filosofia_na_bio:
        bio_score -= 1
        bio_feedback.append("Bio com foco em filosofia/desenvolvimento pessoal confunde o posicionamento como corretor")

    # Muitos emojis sem propósito
    emojis = re.findall(r'[\U0001f300-\U0001f9ff]', bio)
    if len(emojis) > 5:
        bio_score -= 1
        bio_feedback.append("Excesso de emojis na bio — poluição visual")

    bio_score = max(0, min(10, bio_score))

    results["bio"] = {
        "score": bio_score,
        "valor_atual": bio,
        "positivos": bio_positivos,
        "problemas": bio_feedback,
        "estrutura_ideal": {
            "linha1": "Como você ajuda + nicho + região",
            "linha2": "Prova de autoridade (números, resultados, tempo de mercado)",
            "linha3": "CTA clara (Clique no link, Me chame no WhatsApp, etc.)",
            "link": "WhatsApp, site ou landing page",
        },
    }

    # ============================================================
    # 4. ANÁLISE DO LINK
    # ============================================================
    link_score = 0 if not external_url else 8
    link_feedback = []
    link_positivos = []

    if external_url:
        link_positivos.append(f"Link presente: {external_url}")
        if "wa.me" in external_url or "whatsapp" in external_url.lower():
            link_score += 2
            link_positivos.append("Link direto para WhatsApp — ótimo para conversão!")
        elif "linktr" in external_url or "linktree" in external_url:
            link_positivos.append("Usando Linktree")
        elif "bit.ly" in external_url or "encurtador" in external_url:
            link_positivos.append("Usando encurtador de URL")
    else:
        link_feedback.append("Sem link na bio = sem conversão. Adicione AGORA um link para WhatsApp ou site.")

    link_score = max(0, min(10, link_score))

    results["link"] = {
        "score": link_score,
        "valor_atual": external_url or "NENHUM",
        "positivos": link_positivos,
        "problemas": link_feedback,
    }

    # ============================================================
    # 5. ANÁLISE DOS POSTS FIXADOS
    # ============================================================
    pinned = [p for p in posts if p.get("pinned")]
    fixados_score = 5
    fixados_feedback = []
    fixados_positivos = []
    fixados_detalhes = []

    if not pinned:
        fixados_score = 0
        fixados_feedback.append("Nenhum post fixado! Você precisa fixar 3 posts estratégicos.")
    else:
        if len(pinned) < 3:
            fixados_score -= 1
            fixados_feedback.append(f"Apenas {len(pinned)} post(s) fixado(s) — o ideal são 3")

        for i, p in enumerate(pinned):
            caption = p.get("caption", "")
            tipo_conteudo = _classify_post(caption)
            fixados_detalhes.append({
                "numero": i + 1,
                "tipo": tipo_conteudo,
                "likes": p.get("likes", 0),
                "comments": p.get("comments", 0),
                "preview": caption[:150] + "..." if len(caption) > 150 else caption,
            })

            if tipo_conteudo == "prova_social":
                fixados_score += 2
                fixados_positivos.append(f"Post fixado {i+1}: Prova social")
            elif tipo_conteudo == "educacional":
                fixados_score += 2
                fixados_positivos.append(f"Post fixado {i+1}: Conteúdo educacional")
            elif tipo_conteudo == "autoridade":
                fixados_score += 2
                fixados_positivos.append(f"Post fixado {i+1}: Conteúdo de autoridade")
            elif tipo_conteudo == "imovel":
                fixados_score += 1
                fixados_positivos.append(f"Post fixado {i+1}: Imóvel/venda")
            elif tipo_conteudo == "filosofia":
                fixados_score -= 1
                fixados_feedback.append(f"Post fixado {i+1}: Conteúdo filosófico/motivacional — não converte visitantes")
            elif tipo_conteudo == "pessoal":
                fixados_score -= 1
                fixados_feedback.append(f"Post fixado {i+1}: Conteúdo pessoal — não estratégico")
            else:
                fixados_feedback.append(f"Post fixado {i+1}: Conteúdo genérico — sem valor estratégico")

    fixados_score = max(0, min(10, fixados_score))

    results["fixados"] = {
        "score": fixados_score,
        "quantidade": len(pinned),
        "positivos": fixados_positivos,
        "problemas": fixados_feedback,
        "detalhes": fixados_detalhes,
        "ideal": [
            "1 post de AUTORIDADE (mostrando expertise no mercado)",
            "1 post de PROVA SOCIAL (depoimento, fechamento, entrega de chave)",
            "1 post EDUCATIVO (dicas, tutoriais que geram valor)",
        ],
    }

    # ============================================================
    # 6. ANÁLISE DA LINHA EDITORIAL
    # ============================================================
    editorial_score = 5
    editorial_feedback = []
    editorial_positivos = []
    tipo_contagem = {
        "educacional": 0,
        "autoridade": 0,
        "prova_social": 0,
        "imovel": 0,
        "filosofia": 0,
        "pessoal": 0,
        "generico": 0,
    }

    total_likes = 0
    total_comments = 0

    for p in posts:
        caption = p.get("caption", "")
        tipo = _classify_post(caption)
        tipo_contagem[tipo] = tipo_contagem.get(tipo, 0) + 1
        total_likes += p.get("likes", 0)
        total_comments += p.get("comments", 0)

    total_posts_analisados = len(posts)

    if total_posts_analisados > 0:
        # Proporções
        pct_educacional = tipo_contagem["educacional"] / total_posts_analisados * 100
        pct_autoridade = tipo_contagem["autoridade"] / total_posts_analisados * 100
        pct_prova_social = tipo_contagem["prova_social"] / total_posts_analisados * 100
        pct_imovel = tipo_contagem["imovel"] / total_posts_analisados * 100
        pct_filosofia = tipo_contagem["filosofia"] / total_posts_analisados * 100

        if pct_educacional >= 20:
            editorial_score += 1
            editorial_positivos.append(f"Bom volume de conteúdo educacional ({pct_educacional:.0f}%)")
        elif pct_educacional == 0:
            editorial_score -= 2
            editorial_feedback.append("0% de conteúdo educacional — precisa ensinar algo ao público")

        if pct_prova_social >= 10:
            editorial_score += 1
            editorial_positivos.append(f"Tem prova social ({pct_prova_social:.0f}%)")
        elif pct_prova_social == 0:
            editorial_score -= 2
            editorial_feedback.append("0% de prova social — precisa postar depoimentos, fechamentos, entregas")

        if pct_autoridade >= 15:
            editorial_score += 1
            editorial_positivos.append(f"Conteúdo de autoridade presente ({pct_autoridade:.0f}%)")

        if pct_imovel > 50:
            editorial_score -= 2
            editorial_feedback.append(f"Perfil virou catálogo de vendas ({pct_imovel:.0f}% é venda direta) — regra 80/20")

        if pct_filosofia > 30:
            editorial_score -= 2
            editorial_feedback.append(f"Muito conteúdo filosófico/motivacional ({pct_filosofia:.0f}%) — confunde o posicionamento")

        # Engajamento médio
        avg_likes = total_likes / total_posts_analisados
        avg_comments = total_comments / total_posts_analisados

        if followers > 0:
            engagement_rate = (avg_likes + avg_comments) / followers * 100
        else:
            engagement_rate = 0

    else:
        pct_educacional = pct_autoridade = pct_prova_social = pct_imovel = pct_filosofia = 0
        avg_likes = avg_comments = engagement_rate = 0

    editorial_score = max(0, min(10, editorial_score))

    results["editorial"] = {
        "score": editorial_score,
        "positivos": editorial_positivos,
        "problemas": editorial_feedback,
        "distribuicao": {
            "educacional": {"qtd": tipo_contagem["educacional"], "pct": round(pct_educacional, 1)},
            "autoridade": {"qtd": tipo_contagem["autoridade"], "pct": round(pct_autoridade, 1)},
            "prova_social": {"qtd": tipo_contagem["prova_social"], "pct": round(pct_prova_social, 1)},
            "imovel_venda": {"qtd": tipo_contagem["imovel"], "pct": round(pct_imovel, 1)},
            "filosofia_motivacional": {"qtd": tipo_contagem["filosofia"], "pct": round(pct_filosofia, 1)},
            "pessoal_generico": {"qtd": tipo_contagem["pessoal"] + tipo_contagem["generico"],
                                 "pct": round((tipo_contagem["pessoal"] + tipo_contagem["generico"]) / max(total_posts_analisados, 1) * 100, 1)},
        },
        "ideal": {
            "educativo": "30%",
            "autoridade": "20%",
            "prova_social": "15%",
            "bastidores": "15%",
            "entretenimento": "10%",
            "venda_direta": "10%",
        },
    }

    # ============================================================
    # 7. ANÁLISE DE ENGAJAMENTO
    # ============================================================
    eng_score = 5
    eng_feedback = []
    eng_positivos = []

    if total_posts_analisados > 0:
        if engagement_rate >= 3:
            eng_score += 3
            eng_positivos.append(f"Taxa de engajamento boa: {engagement_rate:.1f}%")
        elif engagement_rate >= 1:
            eng_score += 1
            eng_positivos.append(f"Taxa de engajamento razoável: {engagement_rate:.1f}%")
        else:
            eng_score -= 2
            eng_feedback.append(f"Taxa de engajamento muito baixa: {engagement_rate:.1f}% (ideal > 3%)")

        if avg_comments < 1:
            eng_score -= 1
            eng_feedback.append(f"Média de comentários muito baixa ({avg_comments:.1f}) — falta usar CTAs nos posts")

    # Proporção seguidores/seguindo
    if following > 0 and followers > 0:
        ratio = followers / following
        if ratio < 0.5:
            eng_score -= 2
            eng_feedback.append(f"Segue {following} pessoas mas só tem {followers} seguidores — proporção desfavorável")
        elif ratio > 2:
            eng_positivos.append("Boa proporção seguidores/seguindo")

    eng_score = max(0, min(10, eng_score))

    results["engajamento"] = {
        "score": eng_score,
        "positivos": eng_positivos,
        "problemas": eng_feedback,
        "metricas": {
            "media_likes": round(avg_likes, 1),
            "media_comentarios": round(avg_comments, 1),
            "taxa_engajamento": round(engagement_rate, 2),
            "seguidores": followers,
            "seguindo": following,
            "total_posts": posts_count,
        },
    }

    # ============================================================
    # 8. ANÁLISE DE HASHTAGS
    # ============================================================
    hashtag_score = 5
    hashtag_feedback = []
    hashtag_positivos = []
    todas_hashtags = []

    for p in posts:
        caption = p.get("caption", "")
        tags = re.findall(r'#\w+', caption.lower())
        todas_hashtags.extend(tags)

    if todas_hashtags:
        genericas = [h for h in todas_hashtags if h in [g.lower() for g in HASHTAGS_GENERICAS]]
        imoveis_tags = [h for h in todas_hashtags if any(kw in h for kw in ["imov", "imob", "corretor", "casa", "apart", "invest"])]

        if genericas:
            hashtag_score -= 2
            hashtag_feedback.append(f"Usa hashtags genéricas que não atraem compradores: {', '.join(list(set(genericas))[:5])}")
        if imoveis_tags:
            hashtag_score += 2
            hashtag_positivos.append(f"Usa hashtags do mercado imobiliário: {', '.join(list(set(imoveis_tags))[:5])}")
        else:
            hashtag_feedback.append("Poucas ou nenhuma hashtag relevante para o mercado imobiliário")
    else:
        hashtag_score -= 2
        hashtag_feedback.append("Não utiliza hashtags nos posts recentes")

    hashtag_score = max(0, min(10, hashtag_score))

    results["hashtags"] = {
        "score": hashtag_score,
        "positivos": hashtag_positivos,
        "problemas": hashtag_feedback,
    }

    # ============================================================
    # 9. NOTA GERAL E PLANO DE AÇÃO
    # ============================================================
    scores = {
        "nome": results["nome"]["score"],
        "arroba": results["arroba"]["score"],
        "bio": results["bio"]["score"],
        "link": results["link"]["score"],
        "fixados": results["fixados"]["score"],
        "editorial": results["editorial"]["score"],
        "engajamento": results["engajamento"]["score"],
        "hashtags": results["hashtags"]["score"],
    }

    # Pesos diferentes para cada critério
    pesos = {
        "nome": 1.0,
        "arroba": 0.5,
        "bio": 2.0,
        "link": 1.5,
        "fixados": 1.0,
        "editorial": 1.5,
        "engajamento": 1.5,
        "hashtags": 0.5,
    }

    total_ponderado = sum(scores[k] * pesos[k] for k in scores)
    total_peso = sum(pesos.values())
    nota_geral = round(total_ponderado / total_peso, 1)

    # Classificação
    if nota_geral >= 8:
        classificacao = "Excelente"
        emoji = "star"
        cor = "green"
    elif nota_geral >= 6:
        classificacao = "Bom"
        emoji = "thumbsup"
        cor = "blue"
    elif nota_geral >= 4:
        classificacao = "Regular"
        emoji = "warning"
        cor = "orange"
    elif nota_geral >= 2:
        classificacao = "Fraco"
        emoji = "alert"
        cor = "red"
    else:
        classificacao = "Crítico"
        emoji = "alert"
        cor = "darkred"

    # Plano de ação priorizado
    plano = _generate_action_plan(results, profile)

    results["geral"] = {
        "nota": nota_geral,
        "classificacao": classificacao,
        "emoji": emoji,
        "cor": cor,
        "scores": scores,
        "plano_acao": plano,
    }

    return results


def _classify_post(caption: str) -> str:
    """Classifica um post pelo tipo de conteúdo baseado na legenda."""
    caption_lower = caption.lower()

    # Prova social
    if contains_keywords(caption_lower, KEYWORDS_PROVA_SOCIAL):
        if any(w in caption_lower for w in ["depoimento", "cliente", "conquist", "realiz", "sonho", "aprovad", "chave"]):
            return "prova_social"

    # Educacional
    edu_matches = contains_keywords(caption_lower, KEYWORDS_EDUCACIONAL)
    if len(edu_matches) >= 2:
        return "educacional"

    # Filosofia/motivacional
    if contains_keywords(caption_lower, KEYWORDS_FILOSOFIA):
        return "filosofia"

    # Imóvel/venda direta
    imovel_indicators = ["quartos", "suíte", "m²", "vagas", "entrada", "financ",
                         "lançamento", "residencial", "condomínio", "empreendimento",
                         "apartamento", "unidade", "planta"]
    if any(w in caption_lower for w in imovel_indicators):
        return "imovel"

    # Autoridade
    if contains_keywords(caption_lower, KEYWORDS_AUTORIDADE):
        return "autoridade"

    # Pessoal
    if len(caption) < 100 and not contains_keywords(caption_lower, KEYWORDS_IMOVEIS):
        return "pessoal"

    return "generico"


def _generate_action_plan(results: dict, profile: dict) -> list:
    """Gera plano de ação priorizado baseado nos problemas encontrados."""
    plano = []

    # Prioridade 1: Link na bio
    if results["link"]["score"] == 0:
        plano.append({
            "prioridade": "URGENTE",
            "acao": "Adicionar link na bio (WhatsApp ou site)",
            "motivo": "Sem link = zero conversão. Nenhum lead vai te encontrar.",
            "dia": "HOJE",
        })

    # Prioridade 2: Bio
    if results["bio"]["score"] < 5:
        plano.append({
            "prioridade": "URGENTE",
            "acao": "Reescrever a bio seguindo as 3 linhas do Método Rivas",
            "motivo": "A bio é a primeira impressão. Precisa comunicar nicho + autoridade + CTA.",
            "dia": "HOJE",
        })

    # Prioridade 3: Posts fixados
    if results["fixados"]["score"] < 5:
        plano.append({
            "prioridade": "ALTA",
            "acao": "Trocar os posts fixados por conteúdo estratégico (autoridade + prova social + educativo)",
            "motivo": "Posts fixados são a vitrine do perfil. Visitantes novos veem primeiro.",
            "dia": "Dia 2",
        })

    # Prioridade 4: Conteúdo
    if results["editorial"]["score"] < 5:
        plano.append({
            "prioridade": "ALTA",
            "acao": "Reestruturar linha editorial: 30% educativo, 20% autoridade, 15% prova social",
            "motivo": "Conteúdo desalinhado não atrai compradores e confunde o algoritmo.",
            "dia": "Dia 3-4",
        })

    # Prioridade 5: Prova social
    dist = results["editorial"].get("distribuicao", {})
    if dist.get("prova_social", {}).get("qtd", 0) == 0:
        plano.append({
            "prioridade": "ALTA",
            "acao": "Postar pelo menos 1 prova social (depoimento, print, bastidor de fechamento)",
            "motivo": "Prova social é a melhor propaganda que existe.",
            "dia": "Dia 3",
        })

    # Prioridade 6: Engajamento
    if results["engajamento"]["score"] < 5:
        plano.append({
            "prioridade": "MÉDIA",
            "acao": "Aplicar hacks de engajamento: CTAs nas legendas, responder comentários em 1h, stories diários com enquetes",
            "motivo": "Engajamento baixo = algoritmo não entrega seu conteúdo.",
            "dia": "Dia 4-5",
        })

    # Prioridade 7: Hashtags
    if results["hashtags"]["score"] < 5:
        plano.append({
            "prioridade": "MÉDIA",
            "acao": "Trocar hashtags genéricas por 5-10 hashtags de nicho imobiliário",
            "motivo": "Hashtags certas atraem público comprador, não curiosos.",
            "dia": "Dia 5",
        })

    # Sempre incluir calendário
    plano.append({
        "prioridade": "SEMANAL",
        "acao": "Montar calendário de conteúdo para 7 dias com 1 post/dia alternando tipos",
        "motivo": "Consistência é mais importante que perfeição.",
        "dia": "Dia 6-7",
    })

    return plano
