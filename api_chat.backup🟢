import os
from pathlib import Path
from typing import List, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai

from gerenciador_imagem import (
    gerar_imagem_pixazo,
    gerar_imagem_zimage,
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
# CONFIGURAÇÃO DAS IMAGENS
# ============================================================

PASTA_IMAGENS = Path(
    "/tmp/alex_ia_ultra_imagens"
)

PASTA_IMAGENS.mkdir(
    parents=True,
    exist_ok=True,
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


# ============================================================
# GEMINI
# ============================================================

def obter_cliente_gemini():

    chave = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )

    if not chave:
        return None

    return genai.Client(
        api_key=chave
    )


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
        "imagens": True,
    }


# ============================================================
# 🖼️ SERVIR IMAGENS PARA O APK
# ============================================================

@app.get("/api/imagens/{filename}")
def servir_imagem(filename: str):

    # --------------------------------------------------------
    # Segurança:
    # nunca permitir que o nome recebido saia da pasta
    # de imagens.
    # --------------------------------------------------------

    nome_seguro = Path(
        filename
    ).name

    caminho = (
        PASTA_IMAGENS
        / nome_seguro
    )

    if not caminho.exists():

        raise HTTPException(
            status_code=404,
            detail="Imagem não encontrada.",
        )

    if not caminho.is_file():

        raise HTTPException(
            status_code=404,
            detail="Arquivo de imagem inválido.",
        )

    try:

        caminho_resolvido = (
            caminho.resolve()
        )

        pasta_resolvida = (
            PASTA_IMAGENS.resolve()
        )

        caminho_resolvido.relative_to(
            pasta_resolvida
        )

    except ValueError:

        raise HTTPException(
            status_code=403,
            detail="Acesso ao arquivo bloqueado.",
        )

    return FileResponse(
        path=caminho_resolvido,
        media_type="image/png",
        filename=nome_seguro,
    )


# ============================================================
# 🎨 GERADOR DE IMAGEM PARA A API
# PIXAZO → Z IMAGE TURBO
# ============================================================

def gerar_imagem_para_api(prompt):

    erros = []

    # ========================================================
    # 🥇 PIXAZO
    # ========================================================

    try:

        caminho = gerar_imagem_pixazo(
            prompt
        )

        caminho_path = Path(
            caminho
        )

        if not caminho_path.exists():

            raise RuntimeError(
                "Pixazo informou que a imagem "
                "foi criada, mas o arquivo "
                "não foi encontrado."
            )

        return (
            caminho_path,
            "Pixazo / Flux 1 Schnell",
            None,
        )

    except Exception as erro_pixazo:

        erros.append(
            f"Pixazo: {erro_pixazo}"
        )

        print(
            "⚠️ Pixazo falhou:",
            erro_pixazo,
        )

    # ========================================================
    # 🥈 Z IMAGE TURBO
    # ========================================================

    try:

        caminho = gerar_imagem_zimage(
            prompt
        )

        caminho_path = Path(
            caminho
        )

        if not caminho_path.exists():

            raise RuntimeError(
                "Z Image Turbo informou que "
                "a imagem foi criada, mas o "
                "arquivo não foi encontrado."
            )

        return (
            caminho_path,
            "Z Image Turbo",
            None,
        )

    except Exception as erro_zimage:

        erros.append(
            f"Z Image Turbo: {erro_zimage}"
        )

        print(
            "⚠️ Z Image Turbo falhou:",
            erro_zimage,
        )

    return (
        None,
        None,
        " | ".join(erros),
    )


# ============================================================
# CHAT — GEMINI + IMAGEM
# ============================================================

@app.post("/api/chat")
def chat(pedido: PedidoChat):

    cliente = obter_cliente_gemini()

    # ========================================================
    # 🖼️ DETECÇÃO AUTOMÁTICA DE PEDIDO DE IMAGEM
    # ========================================================

    pergunta = pedido.pergunta.strip()

    palavras_imagem = (
        "gera uma imagem",
        "gerar uma imagem",
        "cria uma imagem",
        "criar uma imagem",
        "faça uma imagem",
        "fazer uma imagem",
        "faz uma imagem",
        "desenha uma imagem",
        "desenhar uma imagem",
        "gere uma imagem",
    )

    pedido_imagem = any(
        termo in pergunta.lower()
        for termo in palavras_imagem
    )

    if pedido_imagem:

        prompt_imagem = pergunta

        caminho, motor, erro = (
            gerar_imagem_para_api(
                prompt_imagem
            )
        )

        if caminho is None:

            return {
                "success": False,
                "tipo": "imagem",
                "resposta": (
                    "Não consegui gerar a imagem "
                    "neste momento."
                ),
                "error": erro,
                "prompt": prompt_imagem,
            }

        nome_imagem = caminho.name

        imagem_url = (
            f"/api/imagens/{nome_imagem}"
        )

        return {
            "success": True,
            "tipo": "imagem",
            "resposta": (
                "🖼️ Imagem gerada com sucesso."
            ),
            "imagem": imagem_url,
            "imagem_url": imagem_url,
            "prompt": prompt_imagem,
            "motor": motor,
        }

    # ========================================================
    # 🤖 CHAT NORMAL — GEMINI
    # ========================================================

    if cliente is None:

        return {
            "success": False,
            "resposta": (
                "A chave da Gemini não está "
                "configurada no servidor."
            ),
        }

    partes = [
        SYSTEM_PROMPT
    ]

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

    instrucao = "\n".join(
        partes
    )

    try:

        resultado = (
            cliente.models.generate_content(
                model=GEMINI_MODEL,
                contents=instrucao,
            )
        )

        resposta = getattr(
            resultado,
            "text",
            None,
        )

        if not resposta:

            resposta = (
                "Não consegui gerar "
                "uma resposta."
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
                f"Erro ao consultar a Gemini: "
                f"{erro}"
            ),
        }


# ============================================================
# 🖼️ API DIRETA DE IMAGEM
# ============================================================

@app.post("/api/imagem")
def imagem(pedido: PedidoImagem):

    prompt = pedido.prompt.strip()

    if not prompt:

        return {
            "success": False,
            "tipo": "imagem",
            "resposta": (
                "O prompt da imagem está vazio."
            ),
        }

    caminho, motor, erro = (
        gerar_imagem_para_api(
            prompt
        )
    )

    if caminho is None:

        return {
            "success": False,
            "tipo": "imagem",
            "resposta": (
                "Não consegui gerar a imagem "
                "neste momento."
            ),
            "error": erro,
            "prompt": prompt,
        }

    nome_imagem = caminho.name

    imagem_url = (
        f"/api/imagens/{nome_imagem}"
    )

    return {
        "success": True,
        "tipo": "imagem",
        "resposta": (
            "🖼️ Imagem gerada com sucesso."
        ),
        "imagem": imagem_url,
        "imagem_url": imagem_url,
        "prompt": prompt,
        "motor": motor,
    }


# ============================================================
# 🌉 PONTE ALEX V2 — PROXY SEGURO
# ============================================================

@app.post("/api/ponte/processar")
def processar_ponte(
    pedido: PedidoPonte
):

    # Nunca enviaremos a requisição para a
    # Ponte sem a chave configurada no servidor.

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

                "status_code": (
                    resposta.status_code
                ),

                "resposta": (
                    resposta.text[:2000]
                ),
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
