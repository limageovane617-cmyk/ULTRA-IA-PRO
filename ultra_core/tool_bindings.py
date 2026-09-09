# ============================================================
# 🔌 ALEX IA ULTRA — TOOL BINDINGS
# Conecta as ferramentas reais ao Ultra Core
# ============================================================

from typing import Any, Dict

from .tools import ToolRegistry, tool_registry
from .internet import preparar_pesquisa


# ============================================================
# 🌐 FERRAMENTA DE PESQUISA
# ============================================================

def pesquisar_internet(
    pergunta: str = "",
    prompt: str = "",
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Prepara uma pesquisa para a ferramenta de Internet.

    O Ultra Core pode adicionar automaticamente o argumento
    'prompt' contendo o pedido original do usuário.

    A pergunta explícita possui prioridade.
    Caso 'pergunta' esteja vazia, utiliza 'prompt'.

    O binding permanece desacoplado do cliente Gemini.
    A execução real da pesquisa será feita pela camada
    de IA que possuir o cliente Gemini configurado.
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

    return {
        "success": True,
        "tool": "pesquisa_internet",
        "pergunta": consulta_usuario,
        "consulta": pesquisa,
    }


# ============================================================
# 🛠️ REGISTRO DAS FERRAMENTAS
# ============================================================

def registrar_ferramentas(
    registry: ToolRegistry = tool_registry,
) -> ToolRegistry:
    """
    Registra as ferramentas disponíveis no Ultra Core.

    A função é idempotente:
    se a ferramenta já estiver registrada,
    ela não será registrada novamente.
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
                "categoria": "internet",
                "provider": "google_search",
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
