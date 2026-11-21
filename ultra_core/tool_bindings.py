# ============================================================
# 🔌 ALEX IA ULTRA — TOOL BINDINGS
# Conecta as ferramentas reais ao Ultra Core
# ============================================================

from typing import Any, Dict
import re
import os
import logging

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

from .tools import ToolRegistry, tool_registry

# Internet.py está na raiz do projeto ULTRA-IA-PRO.
from Internet import (
    preparar_pesquisa,
    pesquisar_web,
    pesquisar_capital,
)
from .web_search_fallback import pesquisar_bing_rss, pesquisar_bing_news_rss


_STOPWORDS_PESQUISA = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos",
    "em", "no", "na", "nos", "nas", "para", "por", "com", "sobre", "e",
    "ou", "que", "qual", "quais", "como", "quando", "onde", "mais", "menos",
    "me", "diga", "mostre", "pesquise", "pesquisa", "internet", "atual",
    "atuais", "recente", "recentes", "noticia", "noticias"
}


def _normalizar_termos_pesquisa(texto: str) -> set[str]:
    import unicodedata
    texto = unicodedata.normalize("NFKD", str(texto or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return {
        termo for termo in re.findall(r"[a-z0-9]{3,}", texto)
        if termo not in _STOPWORDS_PESQUISA
    }


def filtrar_resultados_relevantes(pergunta: str, resultados: list) -> list:
    """Remove resultados sem correspondência lexical mínima com a consulta."""
    termos = _normalizar_termos_pesquisa(pergunta)
    if not termos:
        return resultados

    relevantes = []
    for item in resultados:
        if not isinstance(item, dict):
            continue
        texto = " ".join(str(item.get(campo) or "") for campo in (
            "titulo", "title", "snippet", "description", "resumo"
        ))
        termos_resultado = _normalizar_termos_pesquisa(texto)
        correspondencias = termos.intersection(termos_resultado)
        # Uma correspondência basta para consultas específicas; para consultas
        # muito amplas, exigir duas reduz falsos positivos de palavras comuns.
        minimo = 1 if len(termos) <= 3 else 2
        if len(correspondencias) >= minimo:
            relevantes.append(item)
    return relevantes


# ============================================================
# 🌐 FERRAMENTA DE PESQUISA
# ============================================================

def pesquisar_google_grounded(pergunta: str) -> Dict[str, Any]:
    """
    Pesquisa conteúdo atual usando Google Search Grounding do Gemini.
    Retorna resposta e fontes extraídas dos metadados reais da pesquisa.
    """
    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or ""
    ).strip()

    if not api_key:
        return {
            "success": False,
            "provider": "google_search_grounding",
            "erro": "GEMINI_API_KEY não configurada.",
            "resultados": [],
            "fontes": [],
        }

    model = os.environ.get("GEMINI_SEARCH_MODEL", "gemini-3.1-flash-lite").strip()
    prompt = (
        "Pesquise na web informações atuais para responder à pergunta. "
        "Priorize fontes primárias e confiáveis. Responda em português do Brasil. "
        "Não invente fatos nem fontes. Diferencie fatos confirmados de incertezas.\n\n"
        f"Pergunta: {pergunta.strip()}"
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        answer = str(getattr(response, "text", "") or "").strip()
        fontes = []
        resultados = []

        candidates = getattr(response, "candidates", None) or []
        if candidates:
            metadata = getattr(candidates[0], "grounding_metadata", None)
            chunks = getattr(metadata, "grounding_chunks", None) or []
            for chunk in chunks:
                web = getattr(chunk, "web", None)
                if not web:
                    continue
                uri = getattr(web, "uri", None)
                title = getattr(web, "title", None) or uri
                if uri and uri not in fontes:
                    fontes.append(uri)
                    resultados.append({
                        "titulo": title,
                        "url": uri,
                    })

        if not answer:
            raise RuntimeError("O Google Search Grounding retornou resposta vazia.")

        return {
            "success": bool(fontes),
            "provider": "google_search_grounding",
            "answer": answer,
            "resultados": resultados,
            "fontes": fontes,
            "quantidade": len(resultados),
            "verified": bool(fontes),
            "erro": None if fontes else "Resposta sem fontes de grounding; não foi considerada pesquisa verificada.",
        }

    except Exception as erro:
        logger.warning("Google Search Grounding indisponível: %s", erro)
        return {
            "success": False,
            "provider": "google_search_grounding",
            "erro": f"{type(erro).__name__}: {erro}",
            "resultados": [],
            "fontes": [],
            "quantidade": 0,
            "verified": False,
        }


def pesquisar_internet(
    pergunta: str = "",
    prompt: str = "",
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Executa uma pesquisa real na internet.

    Aceita tanto 'pergunta' quanto 'prompt' para manter
    compatibilidade com o Ultra Core.

    Para perguntas estruturadas sobre a capital de um país,
    utiliza Wikidata através do Internet Engine.

    Para outras perguntas, mantém o mecanismo DuckDuckGo.
    """

    consulta_usuario = (
        str(pergunta or "").strip()
        or str(prompt or "").strip()
    )

    if not consulta_usuario:
        raise ValueError(
            "A pergunta para pesquisa não pode estar vazia."
        )

    pesquisa = preparar_pesquisa(
        consulta_usuario
    )

    if pesquisa is None:
        raise ValueError(
            "Não foi possível preparar a pesquisa."
        )

    # ========================================================
    # 🟣 DETECÇÃO DE PERGUNTA SOBRE CAPITAL
    # ========================================================

    consulta_normalizada = (
        consulta_usuario.lower()
    )

    termos_capital = (
        "capital do ",
        "capital da ",
        "capital de ",
        "capital dos ",
        "capital das ",
    )

    eh_pergunta_capital = any(
        termo in consulta_normalizada
        for termo in termos_capital
    )

    if eh_pergunta_capital:

        # ----------------------------------------------------
        # Extrai somente o país, sem incluir instruções das
        # frases seguintes (ex.: "Consulte uma fonte externa").
        # ----------------------------------------------------

        padrao_pais = re.search(
            r"\bcapital\s+(?:do|da|de|dos|das)\s+(.+?)"
            r"(?=\s*[?.!,;:]|\s+\b(?:consulte|informe|forneca|"
            r"cite|inclua|mostre|apresente)\b|$)",
            consulta_normalizada,
            re.IGNORECASE,
        )

        pais = padrao_pais.group(1).strip() if padrao_pais else ""

        if pais:
            resultado_capital = pesquisar_capital(pais)

            if resultado_capital.get("success"):
                qid_pais = resultado_capital.get("qid_pais")
                url_fonte = (
                    f"https://www.wikidata.org/wiki/{qid_pais}"
                    if qid_pais
                    else "https://www.wikidata.org/"
                )

                return {
                    "success": True,
                    "tool": "pesquisa_internet",
                    "pergunta": consulta_usuario,
                    "consulta": pesquisa,
                    "provider": resultado_capital.get("source", "Wikidata"),
                    "answer": resultado_capital.get("answer"),
                    "verified": resultado_capital.get("verified", False),
                    "resultados": [
                        {
                            "titulo": f"Capital de {pais}",
                            "resposta": resultado_capital.get("answer"),
                        }
                    ],
                    "fontes": [url_fonte],
                    "quantidade": 1,
                    "erro": None,
                }

            # Uma falha no Wikidata não é sucesso.
            # Continua para a pesquisa web geral como alternativa.

    # ========================================================
    # 📰 CONSULTAS DE NOTÍCIAS — BING NEWS RSS
    # ========================================================

    # A detecção de notícias precisa preservar palavras como "notícias"
    # e "recentes". _normalizar_termos_pesquisa remove essas palavras
    # como stopwords, portanto não deve ser usada nesta decisão.
    import unicodedata
    texto_para_detectar = unicodedata.normalize(
        "NFKD", consulta_usuario.lower()
    )
    texto_para_detectar = "".join(
        caractere for caractere in texto_para_detectar
        if not unicodedata.combining(caractere)
    )
    termos_noticias = {
        "noticia", "noticias", "manchete", "manchetes", "jornalismo",
        "ultima", "ultimas", "recente", "recentes", "acontecimento",
        "acontecimentos", "novidade", "novidades", "atualidade",
        "atualidades",
    }
    palavras_consulta = set(re.findall(r"[a-z0-9]+", texto_para_detectar))
    eh_consulta_noticias = bool(palavras_consulta & termos_noticias)

    if eh_consulta_noticias:
        resultado_news = pesquisar_bing_news_rss(consulta_usuario)
        noticias = resultado_news.get("resultados") or []
        # Notícias já vêm do endpoint específico do Bing News. Não aplicar
        # o filtro lexical rígido que pode eliminar manchetes válidas.
        if resultado_news.get("success") and noticias:
            return {
                "success": True,
                "tool": "pesquisa_internet",
                "pergunta": consulta_usuario,
                "consulta": pesquisa,
                "provider": "bing_news_rss",
                "resultados": noticias,
                "fontes": resultado_news.get("fontes", []),
                "quantidade": len(noticias),
                "verified": False,
                "erro": None,
            }

    # ========================================================
    # 🔵 PRIMEIRA TENTATIVA — DUCKDUCKGO LITE
    # ========================================================

    resultado_web = pesquisar_web(consulta_usuario)

    resultados_ddg = resultado_web.get("resultados") or []
    resultados_ddg_relevantes = filtrar_resultados_relevantes(
        consulta_usuario, resultados_ddg
    )

    if resultado_web.get("success") and resultados_ddg_relevantes:
        fontes_ddg = [
            item.get("url") for item in resultados_ddg_relevantes
            if isinstance(item, dict) and item.get("url")
        ]
        return {
            "success": True,
            "tool": "pesquisa_internet",
            "pergunta": consulta_usuario,
            "consulta": pesquisa,
            "provider": resultado_web.get("provider", "duckduckgo_lite"),
            "resultados": resultados_ddg_relevantes,
            "fontes": fontes_ddg or resultado_web.get("fontes", []),
            "quantidade": len(resultados_ddg_relevantes),
            "verified": False,
            "erro": None,
        }

    erro_ddg = resultado_web.get("erro") or (
        "DuckDuckGo retornou resultados, mas nenhum passou na validação de relevância."
        if resultados_ddg else "DuckDuckGo não retornou resultados."
    )

    # ========================================================
    # 🟠 SEGUNDA TENTATIVA — BING RSS (SEM CHAVE DE API)
    # ========================================================

    resultado_bing = pesquisar_bing_rss(consulta_usuario)

    resultados_bing = resultado_bing.get("resultados") or []
    resultados_bing_relevantes = filtrar_resultados_relevantes(
        consulta_usuario, resultados_bing
    )

    if resultado_bing.get("success") and resultados_bing_relevantes:
        fontes_bing = [
            item.get("url") for item in resultados_bing_relevantes
            if isinstance(item, dict) and item.get("url")
        ]
        return {
            "success": True,
            "tool": "pesquisa_internet",
            "pergunta": consulta_usuario,
            "consulta": pesquisa,
            "provider": resultado_bing.get("provider", "bing_rss"),
            "resultados": resultados_bing_relevantes,
            "fontes": fontes_bing,
            "quantidade": len(resultados_bing_relevantes),
            "verified": False,
            "erro": None,
        }

    erro_bing = resultado_bing.get("erro") or (
        "Bing RSS retornou resultados, mas nenhum passou na validação de relevância."
        if resultados_bing else "Bing RSS não retornou resultados."
    )

    # ========================================================
    # 🟣 ÚLTIMA TENTATIVA — GOOGLE SEARCH GROUNDING (GEMINI)
    # ========================================================

    if os.environ.get("ALEX_GOOGLE_SEARCH_ENABLED", "true").strip().lower() not in ("0", "false", "no", "off"):
        resultado_google = pesquisar_google_grounded(consulta_usuario)

        if resultado_google.get("success"):
            return {
                "success": True,
                "tool": "pesquisa_internet",
                "pergunta": consulta_usuario,
                "consulta": pesquisa,
                "provider": resultado_google.get("provider"),
                "answer": resultado_google.get("answer"),
                "resultados": resultado_google.get("resultados", []),
                "fontes": resultado_google.get("fontes", []),
                "quantidade": resultado_google.get("quantidade", 0),
                "verified": resultado_google.get("verified", False),
                "erro": None,
            }

        erro_google = resultado_google.get("erro")
    else:
        erro_google = "Google Search Grounding desativado por ALEX_GOOGLE_SEARCH_ENABLED."

    return {
        "success": False,
        "tool": "pesquisa_internet",
        "pergunta": consulta_usuario,
        "consulta": pesquisa,
        "provider": "duckduckgo_lite+bing_rss+google_search_grounding",
        "resultados": [],
        "fontes": [],
        "quantidade": 0,
        "verified": False,
        "erro": f"DuckDuckGo: {erro_ddg or 'sem resultados'}. Bing RSS: {erro_bing or 'sem resultados'}. Google Search: {erro_google or 'sem resultados'}.",
    }


# ============================================================
# 🛠️ REGISTRO DAS FERRAMENTAS
# ============================================================

def registrar_ferramentas(
    registry: ToolRegistry = tool_registry,
) -> ToolRegistry:
    """
    Registra as ferramentas disponíveis no Ultra Core.
    """

    if not registry.has(
        "pesquisa_internet"
    ):
        registry.register(
            name="pesquisa_internet",
            description=(
                "Pesquisa informações atuais na internet "
                "usando Wikidata, DuckDuckGo Lite, Bing RSS e Google Search Grounding como último fallback."
            ),
            function=pesquisar_internet,
            metadata={
                "categoria": "internet",
                "provider": "internet_engine",
                "providers": [
                    "wikidata",
                    "duckduckgo_lite",
                    "bing_rss",
                ],
                "language": "pt-BR",
            },
        )

    return registry


# ============================================================
# 🚀 INICIALIZAÇÃO PADRÃO
# ============================================================

registrar_ferramentas()


# ============================================================
# 📦 EXPORTAÇÕES
# ============================================================

__all__ = [
    "pesquisar_internet",
    "registrar_ferramentas",
]
