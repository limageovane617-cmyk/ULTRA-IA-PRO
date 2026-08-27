# ============================================================
# 🧪 TESTE DE IMAGEM — FLUXPOOL
# ============================================================
# Teste isolado.
# NÃO altera a Alex IA Ultra principal.
# ============================================================

import os
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================

API_URL = "https://api.fluxpool.ai/v1/images/generations"

MODELO = "flux-1.1-pro"


# ============================================================
# OBTER API KEY
# ============================================================

def obter_api_key():

    try:
        chave = st.secrets.get(
            "FLUXPOOL_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "FLUXPOOL_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# PASTA
# ============================================================

def obter_pasta():

    pasta = Path(
        "/tmp/alex_ia_ultra_fluxpool"
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# GERAR IMAGEM
# ============================================================

def gerar_imagem(prompt):

    api_key = obter_api_key()

    # --------------------------------------------------------
    # VERIFICAR CHAVE
    # --------------------------------------------------------

    if not api_key:

        raise RuntimeError(
            "FLUXPOOL_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    # --------------------------------------------------------
    # PREPARAR REQUISIÇÃO
    # --------------------------------------------------------

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    dados = {
        "model": MODELO,
        "prompt": prompt.strip(),
        "size": "1024x1024",
    }

    # --------------------------------------------------------
    # ENVIAR
    # --------------------------------------------------------

    try:

        resposta = requests.post(
            API_URL,
            headers=headers,
            json=dados,
            timeout=180,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro de conexão com a Fluxpool: {erro}"
        )

    # --------------------------------------------------------
    # VERIFICAR HTTP
    # --------------------------------------------------------

    if resposta.status_code != 200:

        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Fluxpool retornou HTTP "
            f"{resposta.status_code}:\n\n"
            f"{detalhes}"
        )

    # --------------------------------------------------------
    # LER JSON
    # --------------------------------------------------------

    try:

        resultado = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            "A Fluxpool retornou uma resposta "
            f"que não é JSON: {erro}"
        )

    # --------------------------------------------------------
    # VERIFICAR DATA
    # --------------------------------------------------------

    dados_imagem = resultado.get(
        "data"
    )

    if not dados_imagem:

        raise RuntimeError(
            "A Fluxpool não retornou dados "
            "da imagem.\n\n"
            f"Resposta:\n{resultado}"
        )

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    imagem_url = dados_imagem[0].get(
        "url"
    )

    if not imagem_url:

        raise RuntimeError(
            "A Fluxpool não retornou "
            "a URL da imagem."
        )

    # --------------------------------------------------------
    # BAIXAR IMAGEM
    # --------------------------------------------------------

    try:

        imagem = requests.get(
            imagem_url,
            timeout=180,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao baixar a imagem: {erro}"
        )

    if imagem.status_code != 200:

        raise RuntimeError(
            "Erro ao baixar a imagem.\n"
            f"HTTP: {imagem.status_code}"
        )

    # --------------------------------------------------------
    # SALVAR
    # --------------------------------------------------------

    caminho = (
        obter_pasta()
        / "teste_fluxpool.png"
    )

    try:

        caminho.write_bytes(
            imagem.content
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao salvar a imagem: {erro}"
        )

    return str(caminho)


# ============================================================
# INTERFACE
# ============================================================

def mostrar_teste():

    st.title(
        "🧪 TESTE DE IMAGEM — FLUXPOOL"
    )

    st.write(
        "Teste isolado de geração de imagens."
    )

    st.info(
        f"Modelo: {MODELO}"
    )

    prompt = st.text_area(
        "Digite o que você quer criar:",
        value=(
            "Um robô futurista caminhando "
            "em uma cidade cyberpunk à noite, "
            "cinematográfico, extremamente "
            "detalhado, iluminação profissional."
        ),
        height=150,
    )

    if st.button(
        "🎨 GERAR IMAGEM",
        use_container_width=True,
    ):

        if not prompt.strip():

            st.warning(
                "Digite uma descrição "
                "para a imagem."
            )

            return

        with st.spinner(
            "🎨 Fluxpool está gerando..."
        ):

            try:

                caminho = gerar_imagem(
                    prompt
                )

                st.image(
                    caminho,
                    caption=(
                        "🖼️ Fluxpool / "
                        "Flux 1.1 Pro"
                    ),
                    use_container_width=True,
                )

                st.success(
                    "✅ Imagem gerada com sucesso!"
                )

            except Exception as erro:

                st.error(
                    "❌ Erro ao gerar imagem:"
                )

                st.code(
                    str(erro)
                )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    mostrar_teste()
