# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS
# MOTOR ÚNICO: Z-IMAGE TURBO (HUGGING FACE)
# Sem Pixazo, sem motor pago e sem fallback pago.
# ============================================================

import os
import shutil
from io import BytesIO
from pathlib import Path

import requests
import streamlit as st
from PIL import Image


ZIMAGE_SPACE = "mrfakename/Z-Image-Turbo"
MOTOR_IMAGEM = "Z-Image Turbo / Hugging Face"
TIMEOUT_IMAGEM = 600


def obter_token_huggingface():
    """
    Obtém o token do Hugging Face sem expô-lo nos logs ou na interface.

    Prioridade:
    1. Variáveis de ambiente HF_TOKEN / HUGGINGFACE_TOKEN.
    2. Secrets do Streamlit com os mesmos nomes.
    """
    for nome in ("HF_TOKEN", "HUGGINGFACE_TOKEN"):
        token = os.environ.get(nome, "")
        if token and token.strip():
            return token.strip()

    try:
        for nome in ("HF_TOKEN", "HUGGINGFACE_TOKEN"):
            token = st.secrets.get(nome, "")
            if token and str(token).strip():
                return str(token).strip()
    except Exception:
        # Streamlit pode não ter secrets configurados (ex.: execução local/Kaggle).
        pass

    return None


def obter_pasta_imagens():
    pasta = Path("/tmp/alex_ia_ultra_imagens")
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def guardar_ultima_imagem(imagem, prompt, caminho=None, motor=None):
    try:
        st.session_state.ultima_imagem = imagem
        st.session_state.ultima_imagem_caminho = caminho
        st.session_state.ultimo_prompt_imagem = prompt
        st.session_state.ultimo_motor_imagem = motor or MOTOR_IMAGEM
        return True
    except Exception:
        return False


def normalizar_resultado(resultado):
    if isinstance(resultado, (tuple, list)):
        if not resultado:
            raise RuntimeError("O Z-Image Turbo retornou uma lista vazia.")
        return normalizar_resultado(resultado[0])

    if isinstance(resultado, dict):
        for chave in ("path", "image", "url", "image_url", "name"):
            if resultado.get(chave):
                return normalizar_resultado(resultado[chave])
        raise RuntimeError("Formato de imagem não reconhecido no retorno do Z-Image Turbo.")

    if isinstance(resultado, os.PathLike):
        return str(resultado)

    if isinstance(resultado, str) and resultado.strip():
        return resultado.strip()

    raise RuntimeError(f"Tipo de resultado não reconhecido: {type(resultado).__name__}")


def _salvar_como_png(origem):
    destino = obter_pasta_imagens() / "ultima_imagem.png"

    if isinstance(origem, bytes):
        entrada = BytesIO(origem)
        with Image.open(entrada) as imagem:
            imagem.load()
            imagem.convert("RGB" if imagem.mode not in ("RGBA", "LA") else "RGBA").save(
                destino, format="PNG"
            )
    else:
        caminho = Path(str(origem))
        if not caminho.is_file():
            raise RuntimeError(f"Arquivo de imagem não encontrado: {caminho}")

        with Image.open(caminho) as imagem:
            imagem.load()
            imagem.convert("RGB" if imagem.mode not in ("RGBA", "LA") else "RGBA").save(
                destino, format="PNG"
            )

    if not destino.is_file() or destino.stat().st_size == 0:
        raise RuntimeError("O arquivo de imagem gerado está vazio.")

    # Confirma que o arquivo pode realmente ser aberto como imagem.
    with Image.open(destino) as validacao:
        validacao.verify()

    return str(destino)


def gerar_imagem_zimage(prompt):
    if not prompt or not prompt.strip():
        raise ValueError("O prompt da imagem está vazio.")

    token = obter_token_huggingface()
    if not token:
        raise RuntimeError(
            "HF_TOKEN não configurado. Adicione um token do Hugging Face "
            "nas variáveis de ambiente (HF_TOKEN) ou nos Secrets do Streamlit "
            "(HF_TOKEN). Não cole o token no código nem no repositório."
        )

    try:
        from gradio_client import Client
    except ImportError as erro:
        raise RuntimeError(
            "A biblioteca gradio_client não está instalada. "
            "Adicione gradio_client às dependências."
        ) from erro

    try:
        # O parâmetro correto do gradio_client é token.
        # Isso autentica a chamada ao Space com a conta Hugging Face do usuário.
        cliente = Client(
            ZIMAGE_SPACE,
            token=token,
            verbose=False,
        )
        resultado = cliente.predict(
            prompt.strip(),
            1024,
            1024,
            9,
            42,
            True,
            api_name="/generate_image",
        )
    except Exception as erro:
        raise RuntimeError(f"Falha ao chamar o Z-Image Turbo: {erro}") from erro

    origem = normalizar_resultado(resultado)

    if origem.startswith(("http://", "https://")):
        try:
            resposta = requests.get(origem, timeout=120)
            resposta.raise_for_status()
            caminho = _salvar_como_png(resposta.content)
        except Exception as erro:
            raise RuntimeError(f"Não foi possível baixar/validar a imagem: {erro}") from erro
    else:
        caminho = _salvar_como_png(origem)

    return caminho


def gerar_imagem(prompt):
    if not prompt or not prompt.strip():
        return None, "❌ A descrição da imagem está vazia."

    try:
        caminho = gerar_imagem_zimage(prompt)
        guardar_ultima_imagem(
            imagem=caminho,
            prompt=prompt.strip(),
            caminho=caminho,
            motor=MOTOR_IMAGEM,
        )
        return caminho, "✅ Imagem gerada e validada pelo Z-Image Turbo."
    except Exception as erro:
        mensagem = f"❌ Não foi possível gerar a imagem com o Z-Image Turbo: {erro}"
        print(mensagem)
        return None, mensagem


def mostrar_imagem(prompt):
    with st.spinner("🎨 Alex IA está criando sua imagem com o Z-Image Turbo..."):
        caminho, mensagem = gerar_imagem(prompt)

    if not caminho or not Path(caminho).is_file():
        st.error(mensagem)
        return False

    try:
        with Image.open(caminho) as imagem:
            imagem.verify()
        st.image(
            caminho,
            caption="🖼️ Imagem gerada pela Alex IA Ultra",
            use_container_width=True,
        )
    except Exception as erro:
        st.error(f"❌ A imagem foi retornada, mas não pôde ser exibida: {erro}")
        return False

    st.success(mensagem)
    st.caption(f"Motor utilizado: {MOTOR_IMAGEM}")
    return True


def obter_ultima_imagem():
    return st.session_state.get("ultima_imagem")


def obter_caminho_ultima_imagem():
    return st.session_state.get("ultima_imagem_caminho")


def obter_prompt_ultima_imagem():
    return st.session_state.get("ultimo_prompt_imagem", "")


def obter_motor_ultima_imagem():
    return st.session_state.get("ultimo_motor_imagem", "")


def limpar_ultima_imagem():
    for chave in (
        "ultima_imagem",
        "ultima_imagem_caminho",
        "ultimo_prompt_imagem",
        "ultimo_motor_imagem",
    ):
        st.session_state.pop(chave, None)


def executar_teste():
    st.title("🖼️ Teste de Geração de Imagem")
    st.write("Motor único: Z-Image Turbo / Hugging Face.")
    prompt = st.text_input(
        "Descreva a imagem:",
        value="Um beija-flor voando com as asas abertas",
    )
    if st.button("🎨 Gerar imagem", use_container_width=True):
        if not prompt.strip():
            st.warning("Digite uma descrição para gerar a imagem.")
        else:
            mostrar_imagem(prompt)


if __name__ == "__main__":
    executar_teste()
