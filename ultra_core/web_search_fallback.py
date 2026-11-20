"""Fallback de pesquisa web sem chave de API.

Usa RSS público do Bing. Consultas explicitamente jornalísticas usam Bing News;
consultas gerais continuam usando Bing Search. Resultados não são fatos verificados.
"""
from __future__ import annotations

import html
import logging
import re
import unicodedata
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from xml.etree import ElementTree

import requests

logger = logging.getLogger(__name__)

BING_RSS_URL = "https://www.bing.com/search"
BING_NEWS_RSS_URL = "https://www.bing.com/news/search"

# Termos que indicam intenção explícita de acompanhar notícias/atualidades.
_TERMOS_NOTICIAS = {
    "noticia", "noticias", "jornalismo", "manchete", "manchetes",
    "ultimas", "recentes", "novidades", "aconteceu", "acontecimentos",
}


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or "").lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def _eh_consulta_de_noticias(pergunta: str) -> bool:
    """Identifica pedidos de notícias sem classificar toda busca como notícia."""
    termos = set(re.findall(r"[a-z0-9]+", _normalizar(pergunta)))
    return bool(termos & _TERMOS_NOTICIAS)


def _texto(element: ElementTree.Element, tag: str) -> str:
    node = element.find(tag)
    if node is None:
        return ""
    return " ".join(html.unescape("".join(node.itertext())).split())


def _url_destino(url: str) -> str:
    """Desembrulha URLs de redirecionamento do Bing News quando possível."""
    if not url:
        return ""
    try:
        params = parse_qs(urlparse(url).query)
        destino = params.get("url", [None])[0]
        if destino:
            return unquote(destino)
    except Exception:
        pass
    return url


def pesquisar_bing_rss(pergunta: str, limite: int = 5, timeout: int = 12) -> dict[str, Any]:
    """Pesquisa RSS sem chave; notícias usam /news/search e buscas gerais /search."""
    consulta = str(pergunta or "").strip()
    if not consulta:
        return {
            "success": False, "provider": "bing_rss",
            "erro": "Pergunta vazia.", "resultados": [], "fontes": [],
            "quantidade": 0, "verified": False,
        }

    eh_noticias = _eh_consulta_de_noticias(consulta)
    endpoint = BING_NEWS_RSS_URL if eh_noticias else BING_RSS_URL
    provider = "bing_news_rss" if eh_noticias else "bing_rss"

    try:
        response = requests.get(
            endpoint,
            params={
                "q": consulta,
                "format": "rss",
                "setlang": "pt-BR",
                "mkt": "pt-BR",
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
                "Accept-Language": "pt-BR,pt;q=0.9",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        channel = root.find("channel")
        if channel is None:
            raise ValueError("Feed RSS do Bing sem canal válido.")

        resultados = []
        vistos = set()
        for item in channel.findall("item"):
            titulo = _texto(item, "title")
            url = _url_destino(_texto(item, "link"))
            snippet = _texto(item, "description")
            if not titulo or not url:
                continue
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                continue
            if url in vistos:
                continue
            vistos.add(url)
            registro = {"titulo": titulo, "url": url}
            if snippet:
                registro["snippet"] = snippet[:700]
            data = _texto(item, "pubDate")
            if data:
                registro["data"] = data
            resultados.append(registro)
            if len(resultados) >= max(1, min(int(limite), 10)):
                break

        fontes = [item["url"] for item in resultados]
        if not resultados:
            return {
                "success": False, "provider": provider,
                "erro": f"O Bing RSS ({'News' if eh_noticias else 'Search'}) não retornou resultados utilizáveis.",
                "resultados": [], "fontes": [], "quantidade": 0,
                "verified": False,
            }
        return {
            "success": True, "provider": provider,
            "pergunta": consulta, "resultados": resultados,
            "fontes": fontes, "quantidade": len(resultados),
            "verified": False, "erro": None,
        }
    except Exception as exc:
        logger.warning("Bing RSS indisponível: %s", exc)
        return {
            "success": False, "provider": provider,
            "erro": f"{type(exc).__name__}: {exc}",
            "resultados": [], "fontes": [], "quantidade": 0,
            "verified": False,
        }
