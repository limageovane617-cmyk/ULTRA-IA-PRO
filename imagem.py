
# ============================================================
# ALEX IA ULTRA V13 — GERENCIADOR DE IMAGENS
# MOTOR PRINCIPAL: Z-IMAGE TURBO / HUGGING FACE
# SEM PIXAZO OU NVIDIA PAGOS
# ============================================================

import os
import shutil
from pathlib import Path

import requests
import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# ============================================================

ZIMAGE_SPACE = "mrfakename/Z-Image-Turbo"

MOTOR_IMAGEM = "Z-Image Turbo / Hugging Face"

TIMEOUT_IMAGEM = 600


# ============================================================
# PASTA DE IMAGENS
# ============================================================

def obter_pasta_imagens():

    pasta = Path("/tmp/alex_ia_ultra_imagens")
    pasta.mkdir(parents=True, exist_ok=True)

    return pasta


# ============================================================
# SALVAR ESTADO
# ============================================================

def guardar_ultima_imagem(
    imagem,
    prompt,
    caminho=None,
    motor=None
):

    try:
        st.session_state.ultima_imagem = imagem
        st.session_state.ultima_imagem_caminho = caminho
        st.session_state.ultimo_prompt_imagem = prompt
        st.session_state.ultimo_motor_imagem = motor

        return True

    except Exception:
        return False


# ============================================================
# NORMALIZAR RESULTADO DO HUGGING FACE
# ============================================================

def normalizar_resultado(resultado):

    if isinstance(resultado, (tuple, list)):

        if not resultado:
            raise RuntimeError("O motor retornou uma lista vazia.")

        return normalizar_resultado(resultado[0])

    if isinstance(resultado, dict):

        for chave in ("path", "image", "url", "name"):

            if resultado.get(chave):
                return normalizar_resultado(resultado[chave])

        raise RuntimeError(
            f"Formato de imagem não reconhecido: {resultado}"
        )

    if isinstance(resultado, os.PathLike):
        return str(resultado)

    if isinstance(resultado, str):
        return resultado

    raise RuntimeError(
        f"Tipo de resultado não reconhecido: {type(resultado)}"
    )


# ============================================================
# GERAR IMAGEM — Z IMAGE TURBO
# ============================================================

def gerar_imagem_zimage(prompt):

    if not prompt or not prompt.strip():
        raise ValueError("O prompt está vazio.")

    try:
        from gradio_client import Client

    except ImportError:
        raise RuntimeError(
            "gradio_client não instalado. "
            "Execute: pip install -U gradio_client"
        )

    try:

        cliente = Client(
            ZIMAGE_SPACE,
            verbose=False
        )

        resultado = cliente.predict(
            prompt.strip(),
            1024,
            1024,
            9,
            42,
            True,
            api_name="/generate_image"
        )

    except Exception as erro:

        raise RuntimeError(
            f"Falha ao conectar ao Z-Image Turbo: {erro}"
        )

    origem = normalizar_resultado(resultado)

    destino = obter_pasta_imagens() / "ultima_imagem.png"

    # Resultado em URL
    if origem.startswith(("http://", "https://")):

        try:

            resposta = requests.get(
                origem,
                timeout=120
            )

            resposta.raise_for_status()

            destino.write_bytes(resposta.content)

        except Exception as erro:

            raise RuntimeError(
                f"Erro ao baixar imagem: {erro}"
            )

    # Resultado em arquivo local
    else:

        arquivo = Path(origem)

        if not arquivo.is_file():

            raise RuntimeError(
                f"Arquivo de imagem não encontrado: {origem}"
            )

        shutil.copy2(
            arquivo,
            destino
        )

    if not destino.exists() or destino.stat().st_size == 0:

        raise RuntimeError("A imagem gerada está vazia.")

    return str(destino)


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def gerar_imagem(prompt):

    if not prompt or not prompt.strip():

        return None, "❌ Descrição da imagem vazia."

    try:

        caminho = gerar_imagem_zimage(prompt)

        guardar_ultima_imagem(
            imagem=caminho,
            prompt=prompt,
            caminho=caminho,
            motor=MOTOR_IMAGEM
        )

        return (
            caminho,
            "✅ Imagem gerada com sucesso pelo Z-Image Turbo."
        )

    except Exception as erro:

        mensagem = (
            f"❌ Falha na geração de imagem: {erro}"
        )

        print(mensagem)

        return None, mensagem


# ============================================================
# MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem(prompt):

    with st.spinner("🎨 Alex IA está criando sua imagem..."):

        imagem, mensagem = gerar_imagem(prompt)

    if imagem is None:

        st.error(mensagem)
        return False

    st.image(
        imagem,
        caption="🖼️ Imagem gerada pela Alex IA Ultra",
        use_container_width=True
    )

    st.success(mensagem)

    st.caption(
        f"Motor utilizado: {MOTOR_IMAGEM}"
    )

    return True


# ============================================================
# RECUPERAR ÚLTIMA IMAGEM
# ============================================================

def obter_ultima_imagem():

    return st.session_state.get("ultima_imagem")


def obter_caminho_ultima_imagem():

    return st.session_state.get("ultima_imagem_caminho")


def obter_prompt_ultima_imagem():

    return st.session_state.get(
        "ultimo_prompt_imagem",
        ""
    )


def obter_motor_ultima_imagem():

    return st.session_state.get(
        "ultimo_motor_imagem",
        ""
    )


# ============================================================
# LIMPAR IMAGEM
# ============================================================

def limpar_ultima_imagem():

    chaves = [
        "ultima_imagem",
        "ultima_imagem_caminho",
        "ultimo_prompt_imagem",
        "ultimo_motor_imagem"
    ]

    for chave in chaves:

        st.session_state.pop(
            chave,
            None
        )


# ============================================================
# COMPATIBILIDADE COM TOOL LOADER
# ============================================================

def gerar_imagem_pixazo(prompt):

    return gerar_imagem_zimage(prompt)


def gerar_imagem_nvidia(prompt):

    return gerar_imagem_zimage(prompt)
