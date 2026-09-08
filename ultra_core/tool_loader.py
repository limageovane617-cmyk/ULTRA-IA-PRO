# ============================================================
# 🧠 ALEX IA ULTRA — TOOL LOADER
# Carregador das ferramentas reais do sistema
# ============================================================

from typing import Any, Dict

from .tools import tool_registry


def carregar_ferramentas() -> Dict[str, Any]:
    """
    Registra as ferramentas disponíveis na Ultra.

    As funções reais continuam pertencendo aos módulos
    originais. Este arquivo apenas cria a ponte entre elas
    e o Ultra Core.
    """

    ferramentas_carregadas: Dict[str, Any] = {}

    # ========================================================
    # 🎨 IMAGEM
    # ========================================================

    try:
        from gerenciador_imagem import gerar_imagem_pixazo

        if not tool_registry.has("imagem.gerar"):
            tool_registry.register(
                name="imagem.gerar",
                description=(
                    "Gera uma imagem a partir de uma descrição "
                    "usando o sistema de geração de imagens da Ultra."
                ),
                function=gerar_imagem_pixazo,
                metadata={
                    "categoria": "imagem",
                    "tipo": "geracao",
                },
            )

        ferramentas_carregadas["imagem.gerar"] = True

    except Exception as erro:
        ferramentas_carregadas["imagem.gerar"] = {
            "erro": str(erro)
        }

    # ========================================================
    # 🎬 VÍDEO
    # ========================================================

    try:
        from video import (
            gerar_video,
            gerar_video_texto,
            gerar_video_imagem,
            gerar_video_fallback,
        )

        funcoes_video = {
            "video.gerar": (
                gerar_video,
                "Gerenciador principal de geração de vídeo.",
            ),
            "video.texto": (
                gerar_video_texto,
                "Gera vídeo a partir de texto.",
            ),
            "video.imagem": (
                gerar_video_imagem,
                "Gera vídeo a partir de uma imagem.",
            ),
            "video.fallback": (
                gerar_video_fallback,
                "Motor alternativo de geração de vídeo.",
            ),
        }

        for nome, (funcao, descricao) in funcoes_video.items():

            if not tool_registry.has(nome):
                tool_registry.register(
                    name=nome,
                    description=descricao,
                    function=funcao,
                    metadata={
                        "categoria": "video",
                        "tipo": nome.split(".", 1)[1],
                    },
                )

            ferramentas_carregadas[nome] = True

    except Exception as erro:

        ferramentas_carregadas["video"] = {
            "erro": str(erro)
        }

    return ferramentas_carregadas


def ferramentas_disponiveis() -> list[Dict[str, Any]]:
    """
    Retorna a lista de ferramentas atualmente registradas.
    """

    return tool_registry.list_tools()


def status_ferramentas() -> Dict[str, Any]:
    """
    Retorna um resumo do estado das ferramentas.
    """

    ferramentas = tool_registry.list_tools()

    return {
        "total": len(ferramentas),
        "habilitadas": sum(
            1
            for ferramenta in ferramentas
            if ferramenta["enabled"]
        ),
        "ferramentas": ferramentas,
    }


__all__ = [
    "carregar_ferramentas",
    "ferramentas_disponiveis",
    "status_ferramentas",
]
