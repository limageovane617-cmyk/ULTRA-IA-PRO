# ============================================================
# 🖼️ ALEX IA ULTRA — TESTE ISOLADO DE IMAGEM
# GOOGLE GEMINI / NANO BANANA 2
# Criado por Geovani
# ============================================================

import os
from pathlib import Path

import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

MODELO_IMAGEM = "gemini-3.1-flash-image"


# ============================================================
# 🔐 OBTER CHAVE GEMINI
# ============================================================

def obter_chave_gemini():

    try:
        chave = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "GEMINI_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 📁 PASTA DAS IMAGENS
# ============================================================

def obter_pasta_imagens():

    pasta = Path(
        "/tmp/alex_ia_ultra_gemini_imagens"
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# 🎨 GERAR IMAGEM COM GEMINI
# ============================================================

def gerar_imagem_gemini(prompt):

    chave = obter_chave_gemini()

    if not chave:
        raise RuntimeError(
            "GEMINI_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    # --------------------------------------------------------
    # Importar SDK
    # --------------------------------------------------------

    try:

        from google import genai
        from google.genai import types

    except Exception as erro:

        raise RuntimeError(
            "A biblioteca google-genai não está instalada.\n\n"
            "Adicione google-genai ao requirements.txt.\n\n"
            f"Detalhes: {erro}"
        )

    # --------------------------------------------------------
    # Criar cliente
    # --------------------------------------------------------

    try:

        cliente = genai.Client(
            api_key=chave
        )

    except Exception as erro:

        raise RuntimeError(
            f"Não foi possível iniciar o Gemini: {erro}"
        )

    # --------------------------------------------------------
    # Configuração da geração
    # --------------------------------------------------------

    configuracao = types.GenerateContentConfig(
        response_modalities=["IMAGE"]
    )

    # --------------------------------------------------------
    # Gerar imagem
    # --------------------------------------------------------

    try:

        resposta = cliente.models.generate_content(
            model=MODELO_IMAGEM,
            contents=prompt.strip(),
            config=configuracao
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro na geração de imagem pelo Gemini: {erro}"
        )

    # --------------------------------------------------------
    # Verificar resposta
    # --------------------------------------------------------

    if not resposta:
        raise RuntimeError(
            "O Gemini não retornou uma resposta."
        )

    if not resposta.parts:
        raise RuntimeError(
            "O Gemini não retornou nenhuma parte de imagem."
        )

    # --------------------------------------------------------
    # Procurar imagem
    # --------------------------------------------------------

    imagem = None

    for parte in resposta.parts:

        try:

            if parte.inline_data:

                imagem = parte.as_image()
                break

        except Exception:
            continue

    if imagem is None:

        raise RuntimeError(
            "O Gemini respondeu, mas não retornou "
            "uma imagem válida."
        )

    # --------------------------------------------------------
    # Salvar imagem
    # --------------------------------------------------------

    caminho = (
        obter_pasta_imagens()
        / "teste_gemini_imagem.png"
    )

    try:

        imagem.save(caminho)

    except Exception as erro:

        raise RuntimeError(
            f"Não foi possível salvar a imagem: {erro}"
        )

    return str(caminho)


# ============================================================
# 🧪 INTERFACE DO TESTE
# ============================================================

def mostrar_teste():

    st.title(
        "🧪 TESTE DE IMAGEM — GEMINI"
    )

    st.write(
        "Teste isolado de geração de imagens "
        "usando o Google Gemini."
    )

    st.info(
        f"Modelo utilizado: {MODELO_IMAGEM}"
    )

    prompt = st.text_area(
        "Digite o que você quer criar:",
        value=(
            "Um robô futurista caminhando "
            "em uma cidade cyberpunk à noite, "
            "cinematográfico, extremamente detalhado, "
            "iluminação profissional."
        ),
        height=120
    )

    if st.button(
        "🎨 GERAR IMAGEM",
        use_container_width=True
    ):

        if not prompt.strip():

            st.warning(
                "Digite uma descrição para a imagem."
            )

            return

        with st.spinner(
            "🎨 Gemini está criando sua imagem..."
        ):

            try:

                caminho = gerar_imagem_gemini(
                    prompt
                )

                st.image(
                    caminho,
                    caption=(
                        "🖼️ Imagem gerada pelo "
                        "Gemini — Nano Banana 2"
                    ),
                    use_container_width=True
                )

                st.success(
                    "✅ Imagem gerada com sucesso!"
                )

                st.caption(
                    f"Modelo: {MODELO_IMAGEM}"
                )

            except Exception as erro:

                st.error(
                    f"❌ Erro ao gerar imagem:\n\n{erro}"
                )


# ============================================================
# 🚀 EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    mostrar_teste()
