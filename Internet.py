# ============================================================
# 🌐 ALEX IA ULTRA — INTERNET
# Pesquisa na internet usando Google Search + DuckDuckGo
# + Wikidata para dados estruturados e verificados
#
# Criada por Geovani
# ============================================================

from google.genai import types

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote

import json
import os
import time
import unicodedata
import re


# ============================================================
# 🔵 GOOGLE SEARCH
# ============================================================

def configurar_pesquisa_google():
    """
    Configura a ferramenta de pesquisa do Google para o Gemini.

    Retorna:
        Configuração da ferramenta de busca.
    """

    return types.Tool(
        google_search=types.GoogleSearch()
    )


# ============================================================
# 🔵 PREPARAR PESQUISA
# ============================================================

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


# ============================================================
# 🔵 EXTRAIR FONTES DO GEMINI
# ============================================================

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


# ============================================================
# 🔵 DUCKDUCKGO LITE
# ============================================================

def pesquisar_web(pergunta, limite=5, timeout=15):
    """
    Realiza uma pesquisa web usando DuckDuckGo Lite.

    Esta função continua independente do Google Search/Gemini.

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


# ============================================================
# 🟣 WIKIDATA — CONFIGURAÇÃO
# ============================================================

WIKIDATA_API = "https://www.wikidata.org/w/api.php"

WIKIDATA_HEADERS = {
    "User-Agent": (
        "AlexIAUltra/1.0 "
        "(Internet Engine; "
        "research tool)"
    )
}


# ============================================================
# 💾 CACHE WIKIDATA
# ============================================================

# No Kaggle, /kaggle/input é somente leitura.
# Por isso usamos /kaggle/working quando disponível.
#
# Fora do Kaggle, o cache fica ao lado deste arquivo.

if os.path.isdir("/kaggle/working"):

    WIKIDATA_CACHE = (
        "/kaggle/working/wikidata_cache.json"
    )

else:

    WIKIDATA_CACHE = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "wikidata_cache.json"
    )


def _normalizar_texto(texto):
    """
    Normaliza texto para comparação segura.

    Remove acentos, converte para minúsculas
    e remove espaços duplicados.
    """

    if not texto:
        return ""

    texto = str(texto)

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    texto = texto.lower()

    texto = re.sub(
        r"\s+",
        " ",
        texto
    ).strip()

    return texto


def _carregar_cache_wikidata():

    if not os.path.exists(
        WIKIDATA_CACHE
    ):
        return {}

    try:

        with open(
            WIKIDATA_CACHE,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(arquivo)

            if isinstance(dados, dict):
                return dados

    except Exception:
        pass

    return {}


def _salvar_cache_wikidata(cache):

    try:

        pasta = os.path.dirname(
            WIKIDATA_CACHE
        )

        if pasta:
            os.makedirs(
                pasta,
                exist_ok=True
            )

        with open(
            WIKIDATA_CACHE,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                cache,
                arquivo,
                ensure_ascii=False,
                indent=2
            )

        return True

    except Exception:
        return False


# ============================================================
# 🛡️ VERIFICADOR DE CAPITAL ATUAL
# ============================================================

def _eh_capital_atual(
    descricao,
    pais
):
    """
    Verifica se a descrição da entidade
    realmente identifica a cidade como capital
    do país informado.

    Usa correspondência de palavra inteira
    para evitar falsos positivos como:

        Brasil
        brasileiro
    """

    texto = _normalizar_texto(
        descricao
    )

    pais_normalizado = _normalizar_texto(
        pais
    )

    if not texto or not pais_normalizado:
        return False

    if "capital" not in texto:
        return False

    encontrou_pais = re.search(
        rf"\b{re.escape(pais_normalizado)}\b",
        texto
    )

    return encontrou_pais is not None


# ============================================================
# 🌐 REQUISIÇÃO WIKIDATA
# ============================================================

def _requisicao_wikidata(
    parametros,
    tentativas=3,
    timeout=15
):
    """
    Faz requisição à API pública do Wikidata
    com tratamento básico de 429 e falhas de rede.
    """

    parametros = dict(parametros)

    # Ajuda o servidor a controlar consultas pesadas.
    parametros.setdefault(
        "maxlag",
        "5"
    )

    for tentativa in range(
        1,
        tentativas + 1
    ):

        try:

            resposta = requests.get(
                WIKIDATA_API,
                params=parametros,
                headers=WIKIDATA_HEADERS,
                timeout=timeout
            )

            print(
                f"HTTP {resposta.status_code} "
                f"(tentativa {tentativa})"
            )

            if resposta.status_code == 429:

                if tentativa >= tentativas:
                    return None

                retry_after = resposta.headers.get(
                    "Retry-After"
                )

                try:
                    espera = float(
                        retry_after
                    ) if retry_after else 2 * tentativa

                except Exception:
                    espera = 2 * tentativa

                time.sleep(
                    max(
                        1,
                        espera
                    )
                )

                continue

            resposta.raise_for_status()

            return resposta.json()

        except Exception as erro:

            if tentativa >= tentativas:

                print(
                    "❌ Erro Wikidata:",
                    erro
                )

                return None

            time.sleep(
                tentativa
            )

    return None


# ============================================================
# 🇧🇷🇫🇷 PESQUISA DE CAPITAL
# ============================================================

def pesquisar_capital(pais):
    """
    Pesquisa a capital atual de um país usando Wikidata.

    O resultado só é salvo no cache quando
    uma capital foi realmente verificada.

    Args:
        pais: nome do país.

    Returns:
        Dicionário padronizado.
    """

    if not pais or not str(pais).strip():

        return {
            "success": False,
            "answer": None,
            "source": "Wikidata",
            "verified": False,
            "error": "País vazio."
        }

    pais = str(pais).strip()

    cache = _carregar_cache_wikidata()

    chave_cache = (
        _normalizar_texto(pais)
    )

    # ========================================================
    # 💾 CACHE
    # ========================================================

    if chave_cache in cache:

        resultado_cache = cache[
            chave_cache
        ]

        if (
            isinstance(
                resultado_cache,
                dict
            )
            and resultado_cache.get("success")
            and resultado_cache.get("verified")
            and resultado_cache.get("answer")
        ):

            print(
                "💾 Resultado encontrado no cache."
            )

            return resultado_cache

    # ========================================================
    # 🔎 BUSCAR PAÍS NO WIKIDATA
    # ========================================================

    print(
        f"🔎 Pesquisando: {pais}"
    )

    dados_busca = _requisicao_wikidata(
        {
            "action": "wbsearchentities",
            "search": pais,
            "language": "pt",
            "uselang": "pt",
            "format": "json",
            "limit": "5"
        }
    )

    if not dados_busca:

        return {
            "success": False,
            "answer": None,
            "source": "Wikidata",
            "verified": False,
            "error": "Não foi possível consultar o Wikidata."
        }

    resultados_busca = dados_busca.get(
        "search",
        []
    )

    if not resultados_busca:

        return {
            "success": False,
            "answer": None,
            "source": "Wikidata",
            "verified": False,
            "error": "País não encontrado no Wikidata."
        }

    # ========================================================
    # 🎯 ESCOLHER ENTIDADE DO PAÍS
    # ========================================================

    entidade = None

    for candidato in resultados_busca:

        descricao = _normalizar_texto(
            candidato.get(
                "description",
                ""
            )
        )

        if (
            "pais" in descricao
            or "country" in descricao
        ):

            entidade = candidato
            break

    if entidade is None:
        entidade = resultados_busca[0]

    qid = entidade.get(
        "id"
    )

    nome_entidade = entidade.get(
        "label",
        pais
    )

    if not qid:

        return {
            "success": False,
            "answer": None,
            "source": "Wikidata",
            "verified": False,
            "error": "Entidade sem identificador."
        }

    print(
        f"Entidade encontrada: "
        f"{qid} — {nome_entidade}"
    )

    # ========================================================
    # 📦 BUSCAR DADOS DA ENTIDADE
    # ========================================================

    dados_entidade = _requisicao_wikidata(
        {
            "action": "wbgetentities",
            "ids": qid,
            "props": "claims|labels|descriptions",
            "languages": "pt|en",
            "format": "json"
        }
    )

    if not dados_entidade:

        return {
            "success": False,
            "answer": None,
            "source": "Wikidata",
            "verified": False,
            "error": "Não foi possível obter os dados do país."
        }

    entidades = dados_entidade.get(
        "entities",
        {}
    )

    dados_pais = entidades.get(
        qid,
        {}
    )

    claims = dados_pais.get(
        "claims",
        {}
    )

    # P36 = capital
    valores_capital = claims.get(
        "P36",
        []
    )

    ids_capitais = []

    for claim in valores_capital:

        try:

            datavalue = (
                claim
                .get("mainsnak", {})
                .get("datavalue", {})
            )

            valor = datavalue.get(
                "value",
                {}
            )

            capital_id = valor.get(
                "id"
            )

            if (
                capital_id
                and capital_id not in ids_capitais
            ):

                ids_capitais.append(
                    capital_id
                )

        except Exception:
            continue

    print(
        f"Valores de P36 encontrados: "
        f"{len(ids_capitais)}"
    )

    print(
        f"IDs: {ids_capitais}"
    )

    if not ids_capitais:

        return {
            "success": False,
            "answer": None,
            "source": "Wikidata",
            "verified": False,
            "error": "Nenhuma capital encontrada no Wikidata."
        }

    # ========================================================
    # 🔍 VERIFICAR CADA CANDIDATO
    # ========================================================

    for capital_id in ids_capitais:

        dados_capital = _requisicao_wikidata(
            {
                "action": "wbgetentities",
                "ids": capital_id,
                "props": "labels|descriptions|claims",
                "languages": "pt|en",
                "format": "json"
            }
        )

        if not dados_capital:
            continue

        entidades_capital = (
            dados_capital.get(
                "entities",
                {}
            )
        )

        capital = entidades_capital.get(
            capital_id,
            {}
        )

        labels = capital.get(
            "labels",
            {}
        )

        descriptions = capital.get(
            "descriptions",
            {}
        )

        nome = (
            labels.get("pt", {})
            .get("value")
            or labels.get("en", {})
            .get("value")
            or capital_id
        )

        descricao = (
            descriptions.get("pt", {})
            .get("value")
            or descriptions.get("en", {})
            .get("value")
            or ""
        )

        # ====================================================
        # 🛡️ VERIFICAÇÃO
        # ====================================================

        if _eh_capital_atual(
            descricao,
            pais
        ):

            resultado = {
                "success": True,
                "answer": nome,
                "source": "Wikidata",
                "verified": True,
                "error": None
            }

            print(
                f"✅ Capital confirmada: "
                f"{nome} — {descricao}"
            )

            # Só resultados válidos entram no cache.
            cache[
                chave_cache
            ] = resultado

            _salvar_cache_wikidata(
                cache
            )

            print(
                "💾 Resultado válido salvo no cache."
            )

            return resultado

    # ========================================================
    # ❌ NENHUMA CAPITAL FOI VERIFICADA
    # ========================================================

    print(
        "⚠️ Nenhum candidato foi "
        "confirmado como capital atual."
    )

    return {
        "success": False,
        "answer": None,
        "source": "Wikidata",
        "verified": False,
        "error": (
            "Nenhum candidato foi "
            "confirmado como capital atual."
        )
    }


# ============================================================
# 🔵 DISPONIBILIDADE
# ============================================================

def pesquisa_disponivel():
    """
    Informa se o módulo de pesquisa está disponível.

    A pesquisa possui mecanismos independentes:

    1. DuckDuckGo Lite
    2. Wikidata
    3. Google Search/Gemini como mecanismo adicional

    O Ultra Core poderá escolher o mecanismo
    adequado posteriormente.
    """

    return True
