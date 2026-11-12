
# ============================================================
# 🧠 ALEX IA ULTRA V14 — TOOL LOADER
# Carregador central de ferramentas do Ultra Core
# NVIDIA FLUX.1-dev — IMAGENS
# ============================================================

import sys
import importlib

from pathlib import Path
from typing import Any, Dict

from .tools import tool_registry


# ============================================================
# 📁 CAMINHO RAIZ DO PROJETO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 🔧 REGISTRADOR CENTRAL
# ============================================================

def _registrar(
    nome: str,
    descricao: str,
    funcao: Any,
    categoria: str,
    tipo: str,
) -> bool:

    if not callable(funcao):
        raise TypeError(
            f"A ferramenta {nome} não é executável."
        )

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

    return tool_registry.has(nome)


# ============================================================
# 🌐 PESQUISA NA INTERNET
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
# 🎨 GERAÇÃO DE IMAGENS — NVIDIA FLUX.1-dev
# ============================================================

def _registrar_imagem(
    carregadas: Dict[str, Any],
) -> None:

    try:

        importlib.invalidate_caches()

        modulo = importlib.import_module(
            "gerenciador_imagem"
        )

        # ----------------------------------------------------
        # GERADOR PRINCIPAL NVIDIA
        # ----------------------------------------------------

        funcao = getattr(
            modulo,
            "gerar_imagem",
        )

        carregadas["imagem.gerar"] = _registrar(
            nome="imagem.gerar",
            descricao=(
                "Gera imagens exclusivamente através "
                "da NVIDIA NIM utilizando o modelo "
                "Black Forest Labs FLUX.1-dev."
            ),
            funcao=funcao,
            categoria="imagem",
            tipo="nvidia_flux",
        )

        # ----------------------------------------------------
        # INFORMAÇÕES DO MOTOR
        # ----------------------------------------------------

        carregadas["imagem.motor"] = {
            "nome": "NVIDIA NIM",
            "modelo": "black-forest-labs/flux.1-dev",
            "status": "registrado",
        }

    except Exception as erro:

        carregadas["imagem.gerar"] = {
            "erro": str(erro)
        }


# ============================================================
# 🎬 GERAÇÃO DE VÍDEOS
# ============================================================

def _registrar_video(
    carregadas: Dict[str, Any],
) -> None:

    try:

        importlib.invalidate_caches()

        modulo = importlib.import_module(
            "gerenciador_video"
        )

    except Exception as erro:

        carregadas["video"] = {
            "erro": str(erro)
        }

        return

    ferramentas_video = {

        "video.gerar": (
            "gerar_video",
            "Gerador principal de vídeos.",
        ),

        "video.texto": (
            "gerar_video_texto",
            "Geração de vídeos a partir de texto.",
        ),

        "video.imagem": (
            "gerar_video_imagem",
            "Geração de vídeos a partir de imagens.",
        ),

        "video.magichour": (
            "gerar_magichour",
            "Geração de vídeos utilizando MagicHour.",
        ),

        "video.ltx": (
            "gerar_ltx_huggingface",
            "Geração de vídeos utilizando LTX.",
        ),

        "video.r3gm": (
            "gerar_r3gm",
            "Geração de vídeos utilizando R3GM.",
        ),

        "video.wan": (
            "gerar_wan_comfyui",
            "Geração de vídeos utilizando WAN ComfyUI.",
        ),
    }

    registrados = 0

    for nome, (
        atributo,
        descricao,
    ) in ferramentas_video.items():

        try:

            funcao = getattr(
                modulo,
                atributo,
            )

            carregadas[nome] = _registrar(
                nome=nome,
                descricao=descricao,
                funcao=funcao,
                categoria="video",
                tipo=nome.split(".", 1)[1],
            )

            registrados += 1

        except Exception as erro:

            carregadas[nome] = {
                "erro": str(erro)
            }

    carregadas["video"] = {
        "success": registrados == len(ferramentas_video),
        "registrados": registrados,
        "total": len(ferramentas_video),
    }


# ============================================================
# 🚀 CARREGAMENTO GERAL
# ============================================================

def carregar_ferramentas() -> Dict[str, Any]:

    carregadas: Dict[str, Any] = {}

    # Pesquisa
    _registrar_pesquisa(carregadas)

    # NVIDIA FLUX
    _registrar_imagem(carregadas)

    # Vídeos
    _registrar_video(carregadas)

    return carregadas


# ============================================================
# 🛠️ FERRAMENTAS DISPONÍVEIS
# ============================================================

def ferramentas_disponiveis() -> list:

    return tool_registry.list_tools()


# ============================================================
# 📊 STATUS DAS FERRAMENTAS
# ============================================================

def status_ferramentas() -> Dict[str, Any]:

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


# ============================================================
# 📦 EXPORTAÇÕES
# ============================================================

__all__ = [
    "carregar_ferramentas",
    "ferramentas_disponiveis",
    "status_ferramentas",
]
