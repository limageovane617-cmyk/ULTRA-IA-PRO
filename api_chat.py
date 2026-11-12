import os
import re
import base64
import binascii
from pathlib import Path
from typing import List, Optional

import requests
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

from gerenciador_imagem import gerar_imagem_zimage

from gerenciador_video import (
    gerar_video,
    gerar_video_texto,
    gerar_video_imagem,
    gerar_video_fallback,
)

from config_ultra import SYSTEM_PROMPT, GEMINI_MODEL

# ============================================================
# ULTRA CORE
# ============================================================

from ultra_core.tool_loader import carregar_ferramentas
from ultra_core.brain import UltraBrain
from ultra_core.intelligence import intelligence
from gemini_bridge import criar_gemini_bridge


# ============================================================
# ALEX IA ULTRA API
# ============================================================

app = FastAPI(
    title="Alex IA Ultra API"
)


# ============================================================
# ULTRA CORE
# ============================================================

status_ultra = carregar_ferramentas()


# ============================================================
# GEMINI BRIDGE
# ============================================================

gemini_api_key = (
    os.environ.get("GEMINI_API_KEY")
    or os.environ.get("GOOGLE_API_KEY")
)

gemini_bridge = criar_gemini_bridge(
    api_key=gemini_api_key,
    model=GEMINI_MODEL,
)


# ============================================================
# ULTRA BRAIN
# ============================================================

ultra_brain = UltraBrain(
    task_intelligence=intelligence,
    gemini_bridge=gemini_bridge,
)


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
# CONFIGURACAO DA PONTE
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
# SEGREDO PARA CONEXAO EXTERNA — PONTE → ULTRA
# ============================================================

ULTRA_API_SECRET = (
    os.environ.get("ULTRA_API_SECRET")
    or os.environ.get("ULTRA_API_SECRETO")
    or os.environ.get("ALEX_ULTRA_SECRET")
)


# ============================================================
# CONFIGURACOES DE IMAGEM
# ============================================================

TAMANHO_MAXIMO_IMAGEM = 10 * 1024 * 1024

TIPOS_IMAGEM_PERMITIDOS = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}


# ============================================================
# TESTE DE AUTENTICACAO — PONTE → ULTRA
# ============================================================

@app.get("/api/ultra/ping")
def ultra_ping(
    x_api_secret: Optional[str] = Header(default=None),
):
    if not ULTRA_API_SECRET:
        raise HTTPException(
            status_code=503,
            detail="ULTRA_API_SECRET nao configurado no servidor.",
        )

    if x_api_secret != ULTRA_API_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Segredo invalido.",
        )

    return {
        "success": True,
        "authenticated": True,
        "service": "Alex IA Ultra API",
        "connection": "Ponte → ULTRA",
    }


# ============================================================
# CONFIGURACAO DOS ARQUIVOS GERADOS
# ============================================================

PASTA_IMAGENS = Path(
    "/tmp/alex_ia_ultra_imagens"
)

PASTA_VIDEOS = Path(
    "/tmp/alex_ia_ultra_videos"
)

PASTA_IMAGENS.mkdir(
    parents=True,
    exist_ok=True,
)

PASTA_VIDEOS.mkdir(
    parents=True,
    exist_ok=True,
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

    # Imagem enviada pelo aplicativo em Base64.
    # Aceita Base64 puro ou data URI.
    imagem: Optional[str] = None

    # MIME opcional: image/jpeg, image/png etc.
    image_mime_type: Optional[str] = None


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
# DECODIFICAR IMAGEM RECEBIDA PELO CHAT
# ============================================================

def decodificar_imagem_chat(
    imagem_base64: Optional[str],
    mime_informado: Optional[str] = None,
):
    if not imagem_base64:
        return None, None

    dados_imagem = imagem_base64.strip()

    if not dados_imagem:
        raise HTTPException(
            status_code=400,
            detail="Imagem enviada vazia.",
        )

    mime_data_uri = None

    # --------------------------------------------------------
    # ACEITAR DATA URI
    # Exemplo: data:image/png;base64,AAAA...
    # --------------------------------------------------------

    if dados_imagem.startswith("data:"):

        correspondencia = re.match(
            r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.*)$",
            dados_imagem,
            re.DOTALL,
        )

        if not correspondencia:
            raise HTTPException(
                status_code=400,
                detail="Formato de imagem Base64 invalido.",
            )

        mime_data_uri = (
            correspondencia.group(1).lower()
        )

        dados_imagem = (
            correspondencia.group(2)
        )

    # --------------------------------------------------------
    # IDENTIFICAR MIME
    # --------------------------------------------------------

    mime_type = (
        mime_informado
        or mime_data_uri
        or "image/jpeg"
    ).lower().strip()

    if mime_type not in TIPOS_IMAGEM_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail="Tipo de imagem nao permitido.",
        )

    # --------------------------------------------------------
    # DECODIFICAR BASE64
    # --------------------------------------------------------

    try:
        imagem_bytes = base64.b64decode(
            dados_imagem,
            validate=True,
        )

    except (binascii.Error, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Imagem em Base64 invalida.",
        )

    if not imagem_bytes:
        raise HTTPException(
            status_code=400,
            detail="Imagem recebida sem conteudo.",
        )

    # --------------------------------------------------------
    # LIMITE DE TAMANHO
    # --------------------------------------------------------

    if len(imagem_bytes) > TAMANHO_MAXIMO_IMAGEM:
        raise HTTPException(
            status_code=413,
            detail="A imagem ultrapassa o limite de 10 MB.",
        )

    return imagem_bytes, mime_type


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
# URL PUBLICA DA IMAGEM
# ============================================================

def criar_url_imagem(caminho_imagem):
    if not caminho_imagem:
        return None

    nome = Path(
        str(caminho_imagem)
    ).name

    return f"/api/imagens/{nome}"


# ============================================================
# URL PUBLICA DO VIDEO
# ============================================================

def criar_url_video(caminho_video):
    if not caminho_video:
        return None

    nome = Path(
        str(caminho_video)
    ).name

    return f"/api/videos/{nome}"


# ============================================================
# ROTAS BASICAS
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

    hf_token = (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGINGFACE_TOKEN")
    )

    return {
        "success": True,
        "gemini": cliente is not None,
        "ponte": bool(PONTE_API_SECRET),
        "hf_token": bool(hf_token),
    }


# ============================================================
# SERVIR IMAGENS GERADAS
# ============================================================

@app.get("/api/imagens/{filename}")
def servir_imagem(filename: str):
    nome = Path(
        filename
    ).name

    caminho = PASTA_IMAGENS / nome

    if not caminho.exists():
        raise HTTPException(
            status_code=404,
            detail="Imagem nao encontrada.",
        )

    if not caminho.is_file():
        raise HTTPException(
            status_code=404,
            detail="Imagem invalida.",
        )

    return FileResponse(
        caminho,
        media_type="image/png",
        filename=nome,
    )


# ============================================================
# SERVIR VIDEOS GERADOS
# ============================================================

@app.get("/api/videos/{filename}")
def servir_video(filename: str):
    nome = Path(
        filename
    ).name

    caminho = PASTA_VIDEOS / nome

    if not caminho.exists():
        raise HTTPException(
            status_code=404,
            detail="Video nao encontrado.",
        )

    if not caminho.is_file():
        raise HTTPException(
            status_code=404,
            detail="Video invalido.",
        )

    return FileResponse(
        caminho,
        media_type="video/mp4",
        filename=nome,
    )


# ============================================================
# CHAT — ULTRA CORE COM SUPORTE A IMAGENS
# ============================================================

@app.post("/api/chat")
def chat(pedido: PedidoChat):

    if gemini_bridge is None:
        return {
            "success": False,
            "resposta": (
                "A chave da Gemini nao esta "
                "configurada no servidor."
            ),
        }

    try:

        # ----------------------------------------------------
        # PERGUNTA
        # ----------------------------------------------------

        pergunta_ultra = (
            pedido.pergunta.strip()
            if pedido.pergunta
            else ""
        )

        # ----------------------------------------------------
        # RECEBER E VALIDAR IMAGEM
        # ----------------------------------------------------

        imagem_bytes, image_mime_type = (
            decodificar_imagem_chat(
                pedido.imagem,
                pedido.image_mime_type,
            )
        )

        if not pergunta_ultra and imagem_bytes:
            pergunta_ultra = (
                "Analise a imagem enviada e "
                "descreva o que consegue identificar."
            )

        if not pergunta_ultra:
            raise HTTPException(
                status_code=400,
                detail="Envie uma pergunta ou uma imagem.",
            )

        # ----------------------------------------------------
        # HISTORICO E CONTEXTO
        # ----------------------------------------------------

        historico = [
            {
                "role": mensagem.role,
                "content": mensagem.content,
            }
            for mensagem in (pedido.historico or [])[-20:]
        ]

        contexto_arquivo = (
            pedido.contexto_arquivo or ""
        )

        nome_arquivo = (
            pedido.nome_arquivo or ""
        )

        # ----------------------------------------------------
        # EXECUTAR ULTRA BRAIN
        # ----------------------------------------------------

        resultado_ultra = ultra_brain.run(
            pergunta_ultra,
            history=historico,
            file_context=contexto_arquivo,
            file_name=nome_arquivo,
            image_bytes=imagem_bytes,
            image_mime_type=image_mime_type,
        )

        # ----------------------------------------------------
        # OBTER RESPOSTA FINAL
        # ----------------------------------------------------

        if isinstance(resultado_ultra, dict):

            resposta = (
                resultado_ultra.get(
                    "final_response",
                    "",
                )
                or resultado_ultra.get(
                    "resposta",
                    "",
                )
            )

        elif isinstance(resultado_ultra, str):
            resposta = resultado_ultra

        else:
            resposta = ""

        if not resposta:
            return {
                "success": False,
                "resposta": (
                    "Nao consegui gerar uma resposta."
                ),
            }

        # ----------------------------------------------------
        # EXPOR METADADOS REAIS DA PESQUISA
        # ----------------------------------------------------

        dados_pesquisa = None

        if isinstance(resultado_ultra, dict):
            execucao = resultado_ultra.get("execution") or {}

            for etapa in execucao.get("results", []):
                if etapa.get("tool") != "pesquisa_internet":
                    continue

                bruto = etapa.get("result")
                if isinstance(bruto, dict):
                    dados_pesquisa = {
                        "success": bruto.get("success", False),
                        "provider": bruto.get("provider"),
                        "answer": bruto.get("answer"),
                        "verified": bruto.get("verified", False),
                        "fontes": bruto.get("fontes", []),
                        "resultados": bruto.get("resultados", []),
                        "erro": bruto.get("erro"),
                    }
                break

        # ----------------------------------------------------
        # DETECTAR ACAO DE GERACAO DE IMAGEM
        # ----------------------------------------------------

        texto_resposta = resposta.strip()

        if (
            "dalle.text2im" in texto_resposta
            or '"action": "dalle.text2im"' in texto_resposta
            or "'action': 'dalle.text2im'" in texto_resposta
        ):

            prompt_imagem = None

            padroes_prompt = [
                r'"prompt"\s*:\s*"([^"]+)"',
                r"'prompt'\s*:\s*'([^']+)'",
            ]

            for padrao in padroes_prompt:

                correspondencia = re.search(
                    padrao,
                    texto_resposta,
                    re.IGNORECASE,
                )

                if correspondencia:
                    prompt_imagem = (
                        correspondencia.group(1)
                    )
                    break

            if not prompt_imagem:
                prompt_imagem = pergunta_ultra

            try:

                caminho_imagem = gerar_imagem_zimage(prompt_imagem)

                caminho_validado = Path(caminho_imagem)
                if not caminho_validado.is_file() or caminho_validado.stat().st_size == 0:
                    raise RuntimeError("O gerador não retornou um arquivo de imagem válido.")

                url_imagem = criar_url_imagem(caminho_imagem)

                return {
                    "success": True,
                    "resposta": "Pronto! A imagem foi gerada e validada pelo Z-Image Turbo.",
                    "imagem": url_imagem,
                    "imagem_url": url_imagem,
                    "arquivo_imagem": caminho_validado.name,
                    "prompt": prompt_imagem,
                    "motor": "Z-Image Turbo / Hugging Face",
                    "acao": "imagem",
                    "modelo": GEMINI_MODEL,
                    "ultra_core": True,
                }

            except Exception as erro_imagem:

                return {
                    "success": False,
                    "resposta": "Entendi que você pediu uma imagem, mas o Z-Image Turbo não conseguiu gerá-la.",
                    "imagem": None,
                    "imagem_url": None,
                    "erro": str(erro_imagem),
                    "acao": "imagem",
                    "modelo": GEMINI_MODEL,
                    "ultra_core": True,
                }

        # ----------------------------------------------------
        # RESPOSTA NORMAL
        # ----------------------------------------------------

        return {
            "success": True,
            "resposta": resposta,
            "modelo": GEMINI_MODEL,
            "ultra_core": True,
            "pesquisa": dados_pesquisa,
        }

    except HTTPException:
        raise

    except Exception as erro:

        return {
            "success": False,
            "resposta": (
                "Erro ao executar o Ultra Core."
            ),
            "erro": str(erro),
        }


# ============================================================
# CHAT PROTEGIDO — PONTE → ULTRA
# ============================================================

@app.post("/api/ultra/chat")
def ultra_chat(
    pedido: PedidoChat,
    x_api_secret: Optional[str] = Header(default=None),
):
    if not ULTRA_API_SECRET:
        raise HTTPException(
            status_code=503,
            detail="ULTRA_API_SECRET nao configurado no servidor.",
        )

    if x_api_secret != ULTRA_API_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Segredo invalido.",
        )

    return chat(pedido)


# ============================================================
# ============================================================
# IMAGEM — Z-IMAGE TURBO
# ============================================================

@app.post("/api/imagem")
def imagem(pedido: PedidoImagem):
    try:
        caminho = gerar_imagem_zimage(pedido.prompt)
        arquivo = Path(caminho)

        if not arquivo.is_file() or arquivo.stat().st_size == 0:
            raise RuntimeError("O gerador não retornou um arquivo de imagem válido.")

        url_imagem = criar_url_imagem(caminho)

        return {
            "success": True,
            "imagem": url_imagem,
            "imagem_url": url_imagem,
            "arquivo_imagem": arquivo.name,
            "prompt": pedido.prompt,
            "motor": "Z-Image Turbo / Hugging Face",
        }

    except Exception as erro:
        return {
            "success": False,
            "imagem": None,
            "imagem_url": None,
            "error": str(erro),
            "motor": "Z-Image Turbo / Hugging Face",
        }


# ============================================================
# VIDEO — GERENCIADOR DE VIDEO
# ============================================================

@app.post("/api/video")
def video(pedido: PedidoVideo):
    try:
        imagem_bytes = None

        # ----------------------------------------------------
        # RECEBER IMAGEM BASE64
        # ----------------------------------------------------

        if pedido.imagem:
            dados_imagem = pedido.imagem

            if "," in dados_imagem:
                dados_imagem = (
                    dados_imagem.split(",", 1)[1]
                )

            try:
                imagem_bytes = base64.b64decode(
                    dados_imagem,
                    validate=True,
                )

            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Imagem em base64 invalida.",
                )

        # ----------------------------------------------------
        # VIDEO A PARTIR DE IMAGEM
        # ----------------------------------------------------

        if imagem_bytes:
            resultado = gerar_video_imagem(
                imagem_bytes=imagem_bytes,
                nome_imagem="imagem_alex.png",
                prompt=pedido.prompt,
                duracao=float(pedido.duracao or 5),
            )

        # ----------------------------------------------------
        # VIDEO A PARTIR DE TEXTO
        # ----------------------------------------------------

        else:
            resultado = gerar_video_texto(
                prompt=pedido.prompt,
                duracao=float(pedido.duracao or 5),
            )

        # ----------------------------------------------------
        # VERIFICAR RESULTADO
        # ----------------------------------------------------

        if not resultado.get("sucesso"):
            return {
                "success": False,
                "sucesso": False,
                "motor": resultado.get("motor"),
                "erro": resultado.get("erro"),
                "video": None,
                "video_url": None,
                "arquivo": None,
            }

        caminho_video = (
            resultado.get("video")
            or resultado.get("arquivo")
        )

        if not caminho_video:
            return {
                "success": False,
                "sucesso": False,
                "motor": resultado.get("motor"),
                "erro": (
                    "O video foi processado, mas "
                    "nenhum arquivo foi retornado."
                ),
                "video": None,
                "video_url": None,
                "arquivo": None,
            }

        caminho_video = Path(
            str(caminho_video)
        )

        nome_video = caminho_video.name

        destino_video = (
            PASTA_VIDEOS / nome_video
        )

        if caminho_video.resolve() != destino_video.resolve():
            try:
                if caminho_video.exists():
                    destino_video.write_bytes(
                        caminho_video.read_bytes()
                    )

            except Exception as erro_copia:
                return {
                    "success": False,
                    "sucesso": False,
                    "motor": resultado.get("motor"),
                    "erro": (
                        "O video foi gerado, mas nao "
                        "foi possivel prepara-lo para o APK."
                    ),
                    "detalhes": str(erro_copia),
                    "video": None,
                    "video_url": None,
                    "arquivo": None,
                }

        if not destino_video.exists():
            return {
                "success": False,
                "sucesso": False,
                "motor": resultado.get("motor"),
                "erro": (
                    "O arquivo de video nao foi "
                    "encontrado apos a geracao."
                ),
                "video": None,
                "video_url": None,
                "arquivo": nome_video,
            }

        if not destino_video.is_file():
            return {
                "success": False,
                "sucesso": False,
                "motor": resultado.get("motor"),
                "erro": (
                    "O caminho do video nao corresponde "
                    "a um arquivo valido."
                ),
                "video": None,
                "video_url": None,
                "arquivo": nome_video,
            }

        url_video = criar_url_video(
            destino_video
        )

        return {
            "success": True,
            "sucesso": True,
            "motor": resultado.get("motor"),
            "video": url_video,
            "video_url": url_video,
            "arquivo": nome_video,
            "arquivo_video": nome_video,
            "duracao": pedido.duracao or 5,
            "erro": None,
        }

    except HTTPException:
        raise

    except Exception as erro:
        return {
            "success": False,
            "sucesso": False,
            "motor": None,
            "erro": str(erro),
            "video": None,
            "video_url": None,
            "arquivo": None,
        }


# ============================================================
# VIDEO — DOWNLOAD / ABRIR NO APK
# ============================================================

@app.get("/api/videos/{filename}")
def download_video(filename: str):
    nome = Path(
        filename
    ).name

    caminho = PASTA_VIDEOS / nome

    if not caminho.exists():
        raise HTTPException(
            status_code=404,
            detail="Video nao encontrado.",
        )

    if not caminho.is_file():
        raise HTTPException(
            status_code=404,
            detail="Arquivo de video invalido.",
        )

    return FileResponse(
        path=caminho,
        media_type="video/mp4",
        filename=nome,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        },
    )


# ============================================================
# PONTE ALEX V2 — PROXY SEGURO
# ============================================================

@app.post("/api/ponte/processar")
def processar_ponte(
    pedido: PedidoPonte,
):
    if not PONTE_API_SECRET:
        return {
            "success": False,
            "error": (
                "A chave da Ponte nao esta "
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
                    "A Ponte retornou uma resposta invalida."
                ),
                "status_code": resposta.status_code,
                "resposta": resposta.text[:2000],
            }

        return dados

    except requests.Timeout:
        return {
            "success": False,
            "error": (
                "A Ponte demorou muito para responder."
            ),
        }

    except requests.RequestException as erro:
        return {
            "success": False,
            "error": (
                "Nao foi possivel conectar a Ponte Alex v2."
            ),
            "detalhes": str(erro),
        }

    except Exception as erro:
        return {
            "success": False,
            "error": (
                "Erro inesperado ao acessar a Ponte Alex v2."
            ),
            "detalhes": str(erro),
        }


# ============================================================
# FIM DA API
# ============================================================
