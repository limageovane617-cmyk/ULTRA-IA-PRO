mport os
from typing import List, Optional

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

from gerenciador_imagem import gerar_imagem_pixazo

from video import (
    gerar_video,
    gerar_video_texto,
    gerar_video_imagem,
    gerar_video_fallback,
)

from config_ultra import SYSTEM_PROMPT, GEMINI_MODEL


app = FastAPI(title="Alex IA Ultra API")


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CONFIGURAÇÃO DA PONTE
# ============================================================

PONTE_API_URL = os.environ.get(
    "PONTE_API_URL",
    "https://ponte-alex-v2.onrender.com/api/ponte/v2/processar",
).rstrip("/")


PONTE_API_SECRET = (
    os.environ.get("PONTE_API_SECRET")
    or os.environ.get("PONTE_API_SECRETO")
    or os.environ.get("ALEX_BRIDGE_SECRET")
)


# ============================================================
# MODELOS
# ============================================================

class Mensagem(BaseModel):
    role: str
    content: str


class PedidoChat(BaseModel):
    pergunta: str
    historico: Optional[List[Mensagem]] = []
    contexto_arquivo: Optional[str] = ""
    nome_arquivo: Optional[str] = ""


class PedidoPonte(BaseModel):
    fileContent: str
    instruction: str
    filename: Optional[str] = "script_alex.py"
    outputFilename: Optional[str] = None
    searchTarget: Optional[str] = None
    replaceWith: Optional[str] = None


class PedidoImagem(BaseModel):
    prompt: str


class PedidoVideo(BaseModel):
    prompt: str
    imagem: Optional[str] = None
    duracao: Optional[int] = 5
    motor: Optional[str] = "automatico"


# ============================================================
# GEMINI
# =============================================================

def obter_cliente_gemini():

    chave = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )

    if not chave:
        return None

    return genai.Client(api_key=chave)


# ============================================================
# ROTAS BÁSICAS
# ============================================================

@app.get("/")
def inicio():

    return {
        "success": True,
        "service": "Alex IA Ultra API",
        "status": "online",
    }


@app.get("/api/health")
def health():

    cliente = obter_cliente_gemini()

    return {
        "success": True,
        "gemini": cliente is not None,
        "ponte": bool(PONTE_API_SECRET),
    }


# ============================================================
# CHAT — GEMINI
# ============================================================

@app.post("/api/chat")
def chat(pedido: PedidoChat):

    cliente = obter_cliente_gemini()

    if cliente is None:

        return {
            "success": False,
            "resposta": (
                "A chave da Gemini não está "
                "configurada no servidor."
            ),
        }

    partes = [SYSTEM_PROMPT]

    if pedido.historico:

        partes.append(
            "\nHISTÓRICO DA CONVERSA:\n"
        )

        for mensagem in pedido.historico[-20:]:

            partes.append(
                f"{mensagem.role}: "
                f"{mensagem.content}"
            )

    if pedido.contexto_arquivo:

        partes.append(
            "\nCONTEXTO DO ARQUIVO:\n"
        )

        partes.append(
            pedido.contexto_arquivo
        )

    partes.append(
        "\nNOVA PERGUNTA:\n"
    )

    partes.append(
        pedido.pergunta
    )

    instrucao = "\n".join(partes)

    try:

        resultado = cliente.models.generate_content(
            model=GEMINI_MODEL,
            contents=instrucao,
        )

        resposta = getattr(
            resultado,
            "text",
            None,
        )

        if not resposta:

            resposta = (
                "Não consegui gerar uma resposta."
            )

        return {
            "success": True,
            "resposta": resposta,
            "modelo": GEMINI_MODEL,
        }

    except Exception as erro:

        return {
            "success": False,
            "resposta": (
                f"Erro ao consultar a Gemini: {erro}"
            ),
        }


# ============================================================
# IMAGEM — PIXAZO
# ============================================================

@app.post("/api/imagem")
def imagem(pedido: PedidoImagem):

    try:

        caminho = gerar_imagem_pixazo(
            pedido.prompt
        )

        return {
            "success": True,
            "imagem": caminho,
            "prompt": pedido.prompt,
            "motor": "Pixazo / Flux 1 Schnell",
        }

    except Exception as erro:

        return {
            "success": False,
            "error": str(erro),
        }


# ============================================================
# PONTE ALEX V2 — PROXY SEGURO
# ============================================================

@app.post("/api/ponte/processar")
def processar_ponte(pedido: PedidoPonte):

    # Nunca enviaremos a requisição para a Ponte
    # sem a chave configurada no servidor.

    if not PONTE_API_SECRET:

        return {
            "success": False,
            "error": (
                "A chave da Ponte não está "
                "configurada no servidor."
            ),
        }

    payload = {
        "fileContent": pedido.fileContent,
        "instruction": pedido.instruction,
        "filename": pedido.filename,
        "outputFilename": pedido.outputFilename,
        "searchTarget": pedido.searchTarget,
        "replaceWith": pedido.replaceWith,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-secret": PONTE_API_SECRET,
    }

    try:

        resposta = requests.post(
            PONTE_API_URL,
            json=payload,
            headers=headers,
            timeout=90,
        )

        try:

            dados = resposta.json()

        except ValueError:

            dados = {
                "success": False,
                "error": (
                    "A Ponte retornou uma "
                    "resposta inválida."
                ),
                "status_code": resposta.status_code,
                "resposta": resposta.text[:2000],
            }

        return dados

    except requests.Timeout:

        return {
            "success": False,
            "error": (
                "A Ponte demorou muito "
                "para responder."
            ),
        }

    except requests.RequestException as erro:

        return {
            "success": False,
            "error": (
                "Não foi possível conectar "
                "à Ponte Alex v2."
            ),
            "detalhes": str(erro),
        }

    except Exception as erro:

        return {
            "success": False,
            "error": (
                "Erro inesperado ao acessar "
                "a Ponte Alex v2."
            ),
            "detalhes": str(erro),
        }
