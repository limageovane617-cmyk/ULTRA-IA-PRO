# ============================================================
# 🔌 ALEX IA ULTRA — TOOL BINDINGS
# Conecta as ferramentas reais ao Ultra Core
# ============================================================

from typing import Any, Dict

from .tools import ToolRegistry, tool_registry

# O arquivo real está na raiz do projeto.
# No Linux/Kaggle o nome precisa respeitar maiúsculas/minúsculas.
from Internet import preparar_pesquisa


# ============================================================
# 🌐 FERRAMENTA DE PESQUISA
# ============================================================

def pesquisar_internet(
    pergunta: str,
) -> Dict[str, Any]:
    """
    Prepara uma pesquisa para a ferramenta de Internet.

    A execução real da chamada ao Gemini continua
    pertencendo à camada de IA que possui o cliente Gemini.

    Este binding apenas conecta a ferramenta ao Ultra Core.
    """

    if not pergunta or not pergunta.strip():
        raise ValueError(
            "A pergunta para pesquisa não pode estar vazia."
        )

    pesquisa = preparar_pesquisa(
        pergunta.strip()
    )

    if pesquisa is None:
        raise ValueError(
            "Não foi possível preparar a pesquisa."
        )

    return {
        "success": True,
        "tool": "pesquisa_internet",
        "pergunta": pergunta.strip(),
        "consulta": pesquisa,
    }


# ============================================================
# REGISTRO DAS FERRAMENTAS
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
                "usando a infraestrutura de pesquisa do Gemini."
            ),
            function=pesquisar_internet,
            metadata={
                "category": "internet",
                "provider": "google_search",
                "language": "pt-BR",
            },
        )

    return registry


# ============================================================
# INICIALIZAÇÃO PADRÃO
# ============================================================

registrar_ferramentas()


__all__ = [
    "pesquisar_internet",
    "registrar_ferramentas",
]
