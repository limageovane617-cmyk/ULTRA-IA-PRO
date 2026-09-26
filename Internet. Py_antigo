# ============================================================
# 🌐 ALEX IA ULTRA — INTERNET
# Pesquisa na internet usando Google Search + DuckDuckGo
# Criada por Geovani
# ============================================================

from google.genai import types

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote


def configurar_pesquisa_google():
    """
    Configura a ferramenta de pesquisa do Google para o Gemini.

    Retorna:
        Configuração da ferramenta de busca.
    """

    return types.Tool(
        google_search=types.GoogleSearch()
    )


def preparar_pesquisa(pergunta):
    """
    Prepara uma pergunta para ser pesquisada na internet.

    Args:
        pergunta: pergunta enviada pelo usuário.

    Returns:
        Texto preparado para pesquisa.
    """

    if not pergunta or not pergunta.strip():
        return None

    return f"""
Pesquise na internet informações atuais para responder
à pergunta abaixo.

Pergunta do usuário:
{pergunta.strip()}

Regras:

- Use informações encontradas na pesquisa.
- Priorize informações atuais e confiáveis.
- Responda em português do Brasil.
- Seja clara e objetiva.
- Não invente informações.
- Se houver informações conflitantes, explique.
- Quando possível, considere as fontes encontradas.
"""


def extrair_fontes(resposta):
    """
    Tenta extrair as fontes utilizadas pelo Gemini.

    Retorna:
        Lista de URLs encontradas ou lista vazia.
    """

    fontes = []

    try:

        candidatos = resposta.candidates

        if not candidatos:
            return fontes

        grounding_metadata = (
            candidatos[0].grounding_metadata
        )

        if not grounding_metadata:
            return fontes

        chunks = grounding_metadata.grounding_chunks

        if not chunks:
            return fontes

        for chunk in chunks:

            if hasattr(chunk, "web") and chunk.web:

                uri = getattr(
                    chunk.web,
                    "uri",
                    None
                )

                if uri and uri not in fontes:

                    fontes.append(uri)

    except Exception:
        pass

    return fontes


def pesquisar_web(pergunta, limite=5, timeout=15):
    """
    Realiza uma pesquisa web real usando DuckDuckGo Lite.

    Esta função não depende do Google Search/Gemini
    para realizar a busca.

    Args:
        pergunta: pergunta ou termo de pesquisa.
        limite: quantidade máxima de resultados.
        timeout: tempo máximo da requisição.

    Returns:
        Dicionário com os resultados encontrados.
    """

    if not pergunta or not pergunta.strip():
        return {
            "success": False,
            "provider": "duckduckgo_lite",
            "erro": "Pergunta vazia.",
            "resultados": [],
            "fontes": [],
            "quantidade": 0,
        }

    try:

        resposta = requests.get(
            "https://lite.duckduckgo.com/lite/",
            params={
                "q": pergunta.strip()
            },
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=timeout,
        )

        resposta.raise_for_status()

        soup = BeautifulSoup(
            resposta.text,
            "html.parser"
        )

        resultados = []
        fontes = []

        for link in soup.find_all("a"):

            href = link.get("href")
            titulo = link.get_text(
                " ",
                strip=True
            )

            if not href:
                continue

            if "uddg=" not in href:
                continue

            if not titulo:
                continue

            if href.startswith("//"):
                href = "https:" + href

            dados = parse_qs(
                urlparse(href).query
            )

            original = next(
                iter(
                    dados.get(
                        "uddg",
                        []
                    )
                ),
                None
            )

            if not original:
                continue

            url_original = unquote(original)

            if url_original in fontes:
                continue

            resultados.append({
                "titulo": titulo,
                "url": url_original,
            })

            fontes.append(url_original)

            if len(resultados) >= limite:
                break

        return {
            "success": True,
            "provider": "duckduckgo_lite",
            "pergunta": pergunta.strip(),
            "resultados": resultados,
            "fontes": fontes,
            "quantidade": len(resultados),
        }

    except Exception as erro:

        return {
            "success": False,
            "provider": "duckduckgo_lite",
            "pergunta": pergunta.strip(),
            "resultados": [],
            "fontes": [],
            "quantidade": 0,
            "erro": str(erro),
        }


def pesquisa_disponivel():
    """
    Informa se o módulo de pesquisa está disponível.

    A pesquisa web possui um mecanismo independente
    usando DuckDuckGo Lite.

    O Google Search/Gemini continua disponível
    como mecanismo adicional quando houver acesso.
    """

    return True
