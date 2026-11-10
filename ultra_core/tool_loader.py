
# ============================================================
# ALEX IA ULTRA — TOOL LOADER V2
# Carregador central de ferramentas
# ============================================================

import sys
from pathlib import Path
from typing import Any, Dict

from .tools import tool_registry


# ============================================================
# CAMINHO RAIZ DO PROJETO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# REGISTRAR UMA FERRAMENTA
# ============================================================

def _registrar(
    nome: str,
    descricao: str,
    funcao: Any,
    categoria: str,
    tipo: str,
) -> bool:

    if not callable(funcao):
        return False

    if not tool_registry.has(nome):
        tool_registry.register(
            name=nome,
            description=descricao,
            function=funcao,
            metadata={
                "categoria": categoria,
                "tipo": tipo,
            },
        )

    return True


# ============================================================
# PESQUISA NA INTERNET
# ============================================================

def _registrar_pesquisa(
    carregadas: Dict[str, Any],
) -> None:

    try:
        from .tool_bindings import registrar_ferramentas

        registrar_ferramentas(tool_registry)

        carregadas["pesquisa_internet"] = (
            tool_registry.has("pesquisa_internet")
        )

    except Exception as erro:
        carregadas["pesquisa_internet"] = {
            "erro": str(erro)
        }


# ============================================================
# GERAÇÃO DE IMAGENS
# ============================================================

def _registrar_imagem(
    carregadas: Dict[str, Any],
) -> None:

    try:
        from gerenciador_imagem import gerar_imagem_pixazo

        carregadas["imagem.gerar"] = _registrar(
            nome="imagem.gerar",
            descricao="Gera imagens através do motor Pixazo.",
            funcao=gerar_imagem_pixazo,
            categoria="imagem",
            tipo="geracao",
        )

    except Exception as erro:
        carregadas["imagem.gerar"] = {
            "erro": str(erro)
        }


# ============================================================
# GERAÇÃO DE VÍDEOS
# ============================================================

def _registrar_video(
    carregadas: Dict[str, Any],
) -> None:

    try:
        import gerenciador_video

    except Exception as erro:
        carregadas["video"] = {
            "erro": str(erro)
        }
        return

    ferramentas_video = {
        "video.gerar": (
            "gerar_video",
            "Geração principal de vídeos.",
        ),
        "video.texto": (
            "gerar_video_texto",
            "Geração de vídeos a partir de texto.",
        ),
        "video.imagem": (
            "gerar_video_imagem",
            "Geração de vídeos a partir de imagens.",
        ),
        "video.fallback": (
            "gerar_video_fallback",
            "Motor alternativo de geração de vídeos.",
        ),
    }

    for nome, (atributo, descricao) in ferramentas_video.items():

        try:
            funcao = getattr(
                gerenciador_video,
                atributo,
            )

            carregadas[nome] = _registrar(
                nome=nome,
                descricao=descricao,
                funcao=funcao,
                categoria="video",
                tipo=nome.split(".", 1)[1],
            )

        except Exception as erro:
            carregadas[nome] = {
                "erro": str(erro)
            }


# ============================================================
# CARREGAMENTO GERAL
# ============================================================

def carregar_ferramentas() -> Dict[str, Any]:

    carregadas: Dict[str, Any] = {}

    _registrar_pesquisa(carregadas)

    _registrar_imagem(carregadas)

    _registrar_video(carregadas)

    return carregadas


# ============================================================
# FERRAMENTAS DISPONÍVEIS
# ============================================================

def ferramentas_disponiveis() -> list:

    return tool_registry.list_tools()


# ============================================================
# STATUS
# ============================================================

def status_ferramentas() -> Dict[str, Any]:

    ferramentas = tool_registry.list_tools()

    return {
        "total": len(ferramentas),
        "habilitadas": sum(
            1 for ferramenta in ferramentas
            if ferramenta["enabled"]
        ),
        "ferramentas": ferramentas,
    }


# ============================================================
# EXPORTAÇÕES
# ============================================================

__all__ = [
    "carregar_ferramentas",
    "ferramentas_disponiveis",
    "status_ferramentas",
]
