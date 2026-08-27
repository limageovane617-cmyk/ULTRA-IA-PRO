import os
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# 🖼️ TESTE PIXAZO — FLUX 1 SCHNELL
# ============================================================

PIXAZO_URL = (
    "https://gateway.pixazo.ai/"
    "flux-1-schnell/v1/getData"
)

MODELO = "Flux 1 Schnell"


# ============================================================
# 🔐 OBTER API KEY
# ============================================================

def obter_api_key():

    try:
        chave = st.secrets.get(
            "PIXAZO_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "PIXAZO_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 📁 PASTA DAS IMAGENS
# ============================================================

def obter_pasta():

    pasta = Path(
        "/tmp/alex_ia_ultra_pixazo"
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# 🎨 GERAR IMAGEM
# ============================================================

def gerar_imagem(prompt):

    api_key = obter_api_key()

    if not api_key:

        raise RuntimeError(
            "PIXAZO_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    # --------------------------------------------------------
    # Cabeçalhos da Pixazo
    # --------------------------------------------------------

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key,
    }

    # --------------------------------------------------------
    # Dados da geração
    # --------------------------------------------------------

    dados = {
        "prompt": prompt.strip(),
        "num_steps": 4,
        "height": 1024,
        "width": 1024,
    }

    # --------------------------------------------------------
    # Fazer requisição
    # --------------------------------------------------------

    try:

        resposta = requests.post(
            PIXAZO_URL,
            headers=headers,
            json=dados,
            timeout=120,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro de conexão com a Pixazo: {erro}"
        )

    # --------------------------------------------------------
    # Verificar HTTP
    # --------------------------------------------------------

    if resposta.status_code != 200:

        try:
            detalhes = resposta.json()

        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Pixazo retornou HTTP "
            f"{resposta.status_code}:\n\n"
            f"{detalhes}"
        )

    # --------------------------------------------------------
    # Ler resposta
    # --------------------------------------------------------

    try:

        resultado = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            f"A Pixazo não retornou JSON válido: {erro}"
        )

    # --------------------------------------------------------
    # Mostrar resposta caso não encontremos imagem
    # --------------------------------------------------------

    if not resultado:

        raise RuntimeError(
            "A Pixazo retornou uma resposta vazia."
        )

    # --------------------------------------------------------
    # Procurar URL da imagem
    # --------------------------------------------------------

    imagem_url = None

    if isinstance(resultado, dict):

        imagem_url = (
            resultado.get("output")
            or resultado.get("image")
            or resultado.get("image_url")
            or resultado.get("url")
        )

    # --------------------------------------------------------
    # Caso a API retorne uma lista
    # --------------------------------------------------------

    if isinstance(resultado, list):

        if len(resultado) > 0:

            primeiro = resultado[0]

            if isinstance(primeiro, str):
                imagem_url = primeiro

            elif isinstance(primeiro, dict):

                imagem_url = (
                    primeiro.get("output")
                    or primeiro.get("image")
                    or primeiro.get("image_url")
                    or primeiro.get("url")
                )

    # --------------------------------------------------------
    # Verificar URL
    # --------------------------------------------------------

    if not imagem_url:

        raise RuntimeError(
            "A Pixazo respondeu corretamente, "
            "mas não encontramos a URL da imagem.\n\n"
            f"Resposta recebida:\n{resultado}"
        )

    # --------------------------------------------------------
    # Baixar imagem
    # --------------------------------------------------------

    try:

        imagem = requests.get(
            imagem_url,
            timeout=120,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao baixar a imagem: {erro}"
        )

    if imagem.status_code != 200:

        raise RuntimeError(
            "A Pixazo retornou a URL, "
            "mas não foi possível baixar "
            f"a imagem. HTTP {imagem.status_code}"
        )

    # --------------------------------------------------------
    # Salvar imagem
    # --------------------------------------------------------

    caminho = (
        obter_pasta()
        / "teste_pixazo_flux.png"
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
# 🧪 INTERFACE DO TESTE
# ============================================================

def mostrar_teste():

    st.title(
        "🧪 TESTE DE IMAGEM — PIXAZO"
    )

    st.write(
        "Teste isolado usando o Flux 1 Schnell."
    )

    st.info(
        "Modelo: Flux 1 Schnell"
    )

    prompt = st.text_area(
        "Digite o que você quer criar:",
        value=(
            "Um robô futurista caminhando "
            "em uma cidade cyberpunk à noite, "
            "cinematográfico, extremamente detalhado, "
            "iluminação profissional."
        ),
        height=130,
    )

    if st.button(
        "🎨 GERAR IMAGEM",
        use_container_width=True,
    ):

        if not prompt.strip():

            st.warning(
                "Digite uma descrição para a imagem."
            )

            return

        with st.spinner(
            "🎨 Pixazo está criando sua imagem..."
        ):

            try:

                caminho = gerar_imagem(
                    prompt
                )

                st.image(
                    caminho,
                    caption=(
                        "🖼️ Flux 1 Schnell — Pixazo"
                    ),
                    use_container_width=True,
                )

                st.success(
                    "✅ Imagem gerada com sucesso!"
                )

            except Exception as erro:

                st.error(
                    f"❌ Erro ao gerar imagem:\n\n{erro}"
                )


# ============================================================
# 🚀 EXECUTAR
# ============================================================

if __name__ == "__main__":

    mostrar_teste()
