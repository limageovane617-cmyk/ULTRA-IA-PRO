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
    # 🔵 PRIMEIRA TENTATIVA — DUCKDUCKGO LITE
    # ========================================================

    resultado_web = pesquisar_web(consulta_usuario)

    if resultado_web.get("success") and resultado_web.get("resultados"):
        return {
            "success": True,
            "tool": "pesquisa_internet",
            "pergunta": consulta_usuario,
            "consulta": pesquisa,
            "provider": resultado_web.get("provider", "duckduckgo_lite"),
            "resultados": resultado_web.get("resultados", []),
            "fontes": resultado_web.get("fontes", []),
            "quantidade": resultado_web.get("quantidade", 0),
            "verified": False,
            "erro": None,
        }

    erro_ddg = resultado_web.get("erro")

    # ========================================================
    # 🟣 FALLBACK — GOOGLE SEARCH GROUNDING (GEMINI)
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
        "provider": "duckduckgo_lite+google_search_grounding",
        "resultados": [],
        "fontes": [],
        "quantidade": 0,
        "verified": False,
        "erro": f"DuckDuckGo: {erro_ddg or 'sem resultados'}. Google Search: {erro_google or 'sem resultados'}.",
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
                "usando Internet Engine, Wikidata e "
                "DuckDuckGo Lite."
            ),
            function=pesquisar_internet,
            metadata={
                "categoria": "internet",
                "provider": "internet_engine",
                "providers": [
                    "wikidata",
                    "duckduckgo_lite",
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
