# ============================================================
# 🌐 ALEX IA ULTRA — INTERNET
# Pesquisa na internet usando Google Search + Gemini
# Criada por Geovani
# ============================================================

from google.genai import types


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


def pesquisa_disponivel():
    """
    Informa se o módulo de pesquisa está disponível.

    O Google Search é fornecido pelo Gemini,
    portanto não exige uma API separada neste módulo.
    """

    return True
