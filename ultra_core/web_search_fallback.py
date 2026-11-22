"""Fallback de pesquisa web sem chave de API.

Usa o feed RSS público do Bing. Não gera respostas por IA: retorna
resultados encontrados para que o Ultra Core possa sintetizá-los.
"""
from __future__ import annotations

import html
import logging
import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
from xml.etree import ElementTree

import requests

logger = logging.getLogger(__name__)

BING_RSS_URL = "https://www.bing.com/search"


def _texto(element: ElementTree.Element, tag: str) -> str:
    node = element.find(tag)
    if node is None:
        return ""
    return " ".join(html.unescape("".join(node.itertext())).split())


def _url_destino(url: str) -> str:
    """Desembrulha URLs de redirecionamento do Bing quando possível."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        destino = params.get("url", [None])[0]
        if destino:
            return unquote(destino)
    except Exception:
        pass
    return url


def pesquisar_bing_rss(pergunta: str, limite: int = 5, timeout: int = 12) -> dict[str, Any]:
    """Pesquisa via Bing RSS sem chave. Resultados não equivalem a fatos verificados."""
    consulta = str(pergunta or "").strip()
    if not consulta:
        return {
            "success": False, "provider": "bing_rss",
            "erro": "Pergunta vazia.", "resultados": [], "fontes": [],
            "quantidade": 0, "verified": False,
        }

    try:
        response = requests.get(
            BING_RSS_URL,
            params={"q": consulta, "format": "rss", "setlang": "pt-BR", "mkt": "pt-BR"},
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AlexIAUltra/1.0)",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)

        # Aceita RSS 2.0 padrão e feeds que tragam namespace XML.
        def _filhos_por_nome(elemento, nome):
            return [
                filho for filho in list(elemento)
                if filho.tag.rsplit("}", 1)[-1].lower() == nome.lower()
            ]

        canais = _filhos_por_nome(root, "channel")
        canal = canais[0] if canais else root
        itens = _filhos_por_nome(canal, "item")

        # Alguns endpoints variam o feed conforme os parâmetros regionais.
        # Se a resposta HTTP for válida, mas vier sem itens, tenta a URL RSS
        # simples que também é usada no teste de conectividade do projeto.
        if not itens and (
            response.url.find("setlang=") >= 0
            or response.url.find("mkt=") >= 0
        ):
            retry = requests.get(
                BING_RSS_URL,
                params={"q": consulta, "format": "rss"},
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/rss+xml, application/xml, text/xml, */*",
                },
                timeout=timeout,
            )
            retry.raise_for_status()
            root = ElementTree.fromstring(retry.content)
            canais = _filhos_por_nome(root, "channel")
            canal = canais[0] if canais else root
            itens = _filhos_por_nome(canal, "item")

        resultados = []
        vistos = set()
        for item in itens:
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
                "success": False, "provider": "bing_rss",
                "erro": "O Bing RSS não retornou resultados utilizáveis.",
                "resultados": [], "fontes": [], "quantidade": 0,
                "verified": False,
            }
        return {
            "success": True, "provider": "bing_rss",
            "pergunta": consulta, "resultados": resultados,
            "fontes": fontes, "quantidade": len(resultados),
            "verified": False, "erro": None,
        }
    except Exception as exc:
        logger.warning("Bing RSS indisponível: %s", exc)
        return {
            "success": False, "provider": "bing_rss",
            "erro": f"{type(exc).__name__}: {exc}",
            "resultados": [], "fontes": [], "quantidade": 0,
            "verified": False,
        }



def pesquisar_bing_news_rss(pergunta: str, limite: int = 8, timeout: int = 12) -> dict[str, Any]:
    """Pesquisa notícias no feed oficial Bing News RSS."""
    consulta = str(pergunta or "").strip()
    if not consulta:
        return {
            "success": False, "provider": "bing_news_rss",
            "erro": "Pergunta vazia.", "resultados": [], "fontes": [],
            "quantidade": 0, "verified": False,
        }

    try:
        response = requests.get(
            "https://www.bing.com/news/search",
            params={
                "q": consulta, "format": "rss",
                "mkt": "pt-BR", "setlang": "pt-BR",
            },
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AlexIAUltra/1.0)",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        channel = root.find("channel")
        if channel is None:
            raise ValueError("Feed Bing News RSS sem canal válido.")

        resultados = []
        vistos = set()
        for item in channel.findall("item"):
            titulo = _texto(item, "title")
            url = _url_destino(_texto(item, "link"))
            snippet = _texto(item, "description")
            if not titulo or not url:
                continue
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc or url in vistos:
                continue
            vistos.add(url)
            registro = {"titulo": titulo, "url": url}
            if snippet:
                registro["snippet"] = snippet[:700]
            data = _texto(item, "pubDate")
            if data:
                registro["data"] = data
            resultados.append(registro)
            if len(resultados) >= max(1, min(int(limite), 20)):
                break

        if not resultados:
            return {
                "success": False, "provider": "bing_news_rss",
                "erro": "O Bing News RSS não retornou notícias utilizáveis.",
                "resultados": [], "fontes": [], "quantidade": 0,
                "verified": False,
            }
        return {
            "success": True, "provider": "bing_news_rss",
            "pergunta": consulta, "resultados": resultados,
            "fontes": [item["url"] for item in resultados],
            "quantidade": len(resultados), "verified": False, "erro": None,
        }
    except Exception as exc:
        logger.warning("Bing News RSS indisponível: %s", exc)
        return {
            "success": False, "provider": "bing_news_rss",
            "erro": f"{type(exc).__name__}: {exc}",
            "resultados": [], "fontes": [], "quantidade": 0,
            "verified": False,
        }
