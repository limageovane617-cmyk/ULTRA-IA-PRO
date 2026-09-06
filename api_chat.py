import os
import re
import base64
from pathlib import Path
from typing import List, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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


# ============================================================
# ALEX IA ULTRA API
# ============================================================

app = FastAPI(
    title="Alex IA Ultra API"
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
# CHAT - GEMINI
# ============================================================

@app.post("/api/chat")
def chat(pedido: PedidoChat):
    cliente = obter_cliente_gemini()

    if cliente is None:
        return {
            "success": False,
            "resposta": (
                "A chave da Gemini nao esta "
                "configurada no servidor."
            ),
        }

    partes = [
        SYSTEM_PROMPT
    ]

    if pedido.historico:
        partes.append(
            "\nHISTORICO DA CONVERSA:\n"
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
                "Nao consegui gerar uma resposta."
            )

        # ====================================================
        # DETECTAR ACAO DE GERACAO DE IMAGEM
        # ====================================================

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
                prompt_imagem = pedido.pergunta

            try:
                caminho_imagem = (
                    gerar_imagem_pixazo(
                        prompt_imagem
                    )
                )

                url_imagem = (
                    criar_url_imagem(
                        caminho_imagem
                    )
                )

                return {
                    "success": True,
                    "resposta": (
                        "Pronto! A imagem foi gerada."
                    ),
                    "imagem": url_imagem,
                    "imagem_url": url_imagem,
                    "arquivo_imagem": (
                        Path(
                            caminho_imagem
                        ).name
                    ),
                    "prompt": prompt_imagem,
                    "motor": (
                        "Pixazo / Flux 1 Schnell"
                    ),
                    "acao": "imagem",
                    "modelo": GEMINI_MODEL,
                }

            except Exception as erro_imagem:
                return {
                    "success": False,
                    "resposta": (
                        "Entendi que voce pediu "
                        "uma imagem, mas ocorreu "
                        "um erro ao gerar."
                    ),
                    "erro": str(
                        erro_imagem
                    ),
                    "acao": "imagem",
                    "modelo": GEMINI_MODEL,
                }

        # ====================================================
        # RESPOSTA NORMAL
        # ====================================================

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
# IMAGEM - PIXAZO
# ============================================================

@app.post("/api/imagem")
def imagem(pedido: PedidoImagem):
    try:
        caminho = gerar_imagem_pixazo(
            pedido.prompt
        )

        url_imagem = criar_url_imagem(
            caminho
        )

        return {
            "success": True,
            "imagem": url_imagem,
            "imagem_url": url_imagem,
            "arquivo_imagem": (
                Path(caminho).name
            ),
            "prompt": pedido.prompt,
            "motor": (
                "Pixazo / Flux 1 Schnell"
            ),
        }

    except Exception as erro:
        return {
            "success": False,
            "imagem": None,
            "imagem_url": None,
            "error": str(erro),
        }


# ============================================================
# VIDEO - GERENCIADOR DE VIDEO
# ============================================================

@app.post("/api/video")
def video(pedido: PedidoVideo):
    try:
        imagem_bytes = None

        # ====================================================
        # RECEBER IMAGEM BASE64
        # ====================================================

        if pedido.imagem:
            dados_imagem = pedido.imagem

            # Aceita:
            # data:image/png;base64,XXXXXX

            if "," in dados_imagem:
                dados_imagem = (
                    dados_imagem.split(
                        ",",
                        1,
                    )[1]
                )

            try:
                imagem_bytes = (
                    base64.b64decode(
                        dados_imagem,
                        validate=True,
                    )
                )

            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Imagem em base64 invalida."
                    ),
                )

        # ====================================================
        # GERAR VIDEO A PARTIR DE IMAGEM
        # ====================================================

        if imagem_bytes:
            resultado = gerar_video_imagem(
                imagem_bytes=imagem_bytes,
                nome_imagem="imagem_alex.png",
                prompt=pedido.prompt,
                duracao=float(
                    pedido.duracao or 5
                ),
            )

        # ====================================================
        # GERAR VIDEO A PARTIR DE TEXTO
        # ====================================================

        else:
            resultado = gerar_video_texto(
                prompt=pedido.prompt,
                duracao=float(
                    pedido.duracao or 5
                ),
            )

        # ====================================================
        # VERIFICAR RESULTADO
        # ====================================================

        if not resultado.get(
            "sucesso"
        ):
            return {
                "success": False,
                "sucesso": False,
                "motor": resultado.get(
                    "motor"
                ),
                "erro": resultado.get(
                    "erro"
                ),
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
                "motor": resultado.get(
                    "motor"
                ),
                "erro": (
                    "O video foi processado, "
                    "mas nenhum arquivo foi "
                    "retornado."
                ),
                "video": None,
                "video_url": None,
                "arquivo": None,
            }

        # ====================================================
        # NORMALIZAR CAMINHO
        # ====================================================

        caminho_video = Path(
            str(caminho_video)
        )

        nome_video = (
            caminho_video.name
        )

        # ====================================================
        # GARANTIR QUE O VIDEO FIQUE NA
        # PASTA PUBLICA DA API
        # ====================================================

        destino_video = (
            PASTA_VIDEOS
            / nome_video
        )

        if (
            caminho_video.resolve()
            != destino_video.resolve()
        ):
            try:
                if caminho_video.exists():
                    destino_video.write_bytes(
                        caminho_video.read_bytes()
                    )

            except Exception as erro_copia:
                return {
                    "success": False,
                    "sucesso": False,
                    "motor": resultado.get(
                        "motor"
                    ),
                    "erro": (
                        "O video foi gerado, "
                        "mas nao foi possivel "
                        "prepara-lo para o APK."
                    ),
                    "detalhes": str(
                        erro_copia
                    ),
                    "video": None,
                    "video_url": None,
                    "arquivo": None,
                }

        # ====================================================
        # VERIFICAR ARQUIVO FINAL
        # ====================================================

        if not destino_video.exists():
            return {
                "success": False,
                "sucesso": False,
                "motor": resultado.get(
                    "motor"
                ),
                "erro": (
                    "O arquivo de video "
                    "nao foi encontrado "
                    "apos a geracao."
                ),
                "video": None,
                "video_url": None,
                "arquivo": nome_video,
            }

        if not destino_video.is_file():
            return {
                "success": False,
                "sucesso": False,
                "motor": resultado.get(
                    "motor"
                ),
                "erro": (
                    "O caminho do video "
                    "nao corresponde a "
                    "um arquivo valido."
                ),
                "video": None,
                "video_url": None,
                "arquivo": nome_video,
            }

        # ====================================================
        # URL RELATIVA DA API
        # ====================================================

        url_video = criar_url_video(
            destino_video
        )

        # ====================================================
        # RESPOSTA COMPATIVEL COM O APK
        # ====================================================

        return {
            "success": True,
            "sucesso": True,
            "motor": resultado.get(
                "motor"
            ),
            "video": url_video,
            "video_url": url_video,
            "arquivo": nome_video,
            "arquivo_video": nome_video,
            "duracao": (
                pedido.duracao or 5
            ),
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
# VIDEO - DOWNLOAD / ABRIR NO APK
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
            detail=(
                "Video nao encontrado."
            ),
        )

    if not caminho.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "Arquivo de video invalido."
            ),
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
# PONTE ALEX V2 - PROXY SEGURO
# ============================================================

@app.post("/api/ponte/processar")
def processar_ponte(
    pedido: PedidoPonte
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
                    "A Ponte retornou uma "
                    "resposta invalida."
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
                "Nao foi possivel conectar "
                "a Ponte Alex v2."
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


# ============================================================
# FIM DA API
# ============================================================
