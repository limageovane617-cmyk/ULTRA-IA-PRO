import os
from typing import List, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

from config_ultra import SYSTEM_PROMPT, GEMINI_MODEL


app = FastAPI(title="Alex IA Ultra API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Mensagem(BaseModel):
    role: str
    content: str


class PedidoChat(BaseModel):
    pergunta: str
    historico: Optional[List[Mensagem]] = []
    contexto_arquivo: Optional[str] = ""
    nome_arquivo: Optional[str] = ""


def obter_cliente_gemini():
    chave = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )

    if not chave:
        return None

    return genai.Client(api_key=chave)


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
    }


@app.post("/api/chat")
def chat(pedido: PedidoChat):

    cliente = obter_cliente_gemini()

    if cliente is None:
        return {
            "success": False,
            "resposta": "A chave da Gemini não está configurada no servidor.",
        }

    partes = [SYSTEM_PROMPT]

    if pedido.historico:
        partes.append("\nHISTÓRICO DA CONVERSA:\n")

        for mensagem in pedido.historico[-20:]:
            partes.append(
                f"{mensagem.role}: {mensagem.content}"
            )

    if pedido.contexto_arquivo:
        partes.append("\nCONTEXTO DO ARQUIVO:\n")
        partes.append(pedido.contexto_arquivo)

    partes.append("\nNOVA PERGUNTA:\n")
    partes.append(pedido.pergunta)

    instrucao = "\n".join(partes)

    try:
        resultado = cliente.models.generate_content(
            model=GEMINI_MODEL,
            contents=instrucao,
        )

        resposta = getattr(resultado, "text", None)

        if not resposta:
            resposta = "Não consegui gerar uma resposta."

        return {
            "success": True,
            "resposta": resposta,
            "modelo": GEMINI_MODEL,
        }

    except Exception as erro:
        return {
            "success": False,
            "resposta": f"Erro ao consultar a Gemini: {erro}",
        }
