import os
from pathlib import Path
import streamlit as st


# ============================================================
# 🖼️ TESTE ISOLADO — HUGGING FACE
# ============================================================

MODELO_IMAGEM = "black-forest-labs/FLUX.1-schnell"
PROVEDOR = "fal-ai"


# ============================================================
# 🔐 TOKEN HUGGING FACE
# ============================================================

def obter_token_huggingface():
    try:
        token = st.secrets.get("HF_TOKEN", "")
    except Exception:
        token = ""

    if not token:
        token = os.environ.get("HF_TOKEN", "")

    return str(token).strip()


# ============================================================
# 📁 PASTA DAS IMAGENS
# ============================================================

def obter_pasta_imagens():
    pasta = Path("/tmp/alex_ia_ultra_imagens_teste")
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


# ============================================================
# 💾 GUARDAR ÚLTIMA IMAGEM
# ============================================================

def guardar_ultima_imagem(
    imagem,
    prompt,
    caminho=None,
    motor=None
):
    st.session_state.ultima_imagem = imagem
    st.session_state.ultima_imagem_caminho = caminho
    st.session_state.ultimo_prompt_imagem = prompt
    st.session_state.ultimo_motor_imagem = motor

    return True


# ============================================================
# 🎨 GERAR IMAGEM
# ============================================================

def gerar_imagem_teste(prompt):

    token = obter_token_huggingface()

    if not token:
        raise RuntimeError(
            "HF_TOKEN não encontrado nos Secrets do Streamlit."
        )

    # --------------------------------------------------------
    # Importar biblioteca
    # --------------------------------------------------------

    try:
        from huggingface_hub import InferenceClient

    except Exception as erro:
        raise RuntimeError(
            "huggingface_hub não está instalado. "
            f"Detalhes: {erro}"
        )

    # --------------------------------------------------------
    # Criar cliente
    # --------------------------------------------------------

    try:
        cliente = InferenceClient(
            provider=PROVEDOR,
            api_key=token,
        )

    except Exception as erro:
        raise RuntimeError(
            f"Erro ao conectar ao Hugging Face: {erro}"
        )

    # --------------------------------------------------------
    # Gerar imagem
    # --------------------------------------------------------

    try:
        imagem = cliente.text_to_image(
            prompt.strip(),
            model=MODELO_IMAGEM,
        )

    except Exception as erro:
        raise RuntimeError(
            f"Erro na geração de imagem pelo Hugging Face: {erro}"
        )

    # --------------------------------------------------------
    # Verificar imagem
    # --------------------------------------------------------

    if imagem is None:
        raise RuntimeError(
            "O Hugging Face não retornou uma imagem."
        )

    # --------------------------------------------------------
    # Salvar imagem
    # --------------------------------------------------------

    caminho = (
        obter_pasta_imagens()
        / "teste_flux_schnell.png"
    )

    try:
        imagem.save(caminho)

    except Exception as erro:
        raise RuntimeError(
            f"Não foi possível salvar a imagem: {erro}"
        )

    # --------------------------------------------------------
    # Guardar informações
    # --------------------------------------------------------

    guardar_ultima_imagem(
        imagem=str(caminho),
        prompt=prompt,
        caminho=str(caminho),
        motor=(
            f"Hugging Face / "
            f"{PROVEDOR} / "
            f"{MODELO_IMAGEM}"
        ),
    )

    return str(caminho)


# ============================================================
# 🧪 TELA DE TESTE
# ============================================================

def mostrar_teste():

    st.title(
        "🧪 TESTE ISOLADO — HUGGING FACE"
    )

    st.write(
        "Este arquivo testa somente a geração "
        "de imagens."
    )

    st.info(
        f"Modelo: {MODELO_IMAGEM}\n\n"
        f"Provedor: {PROVEDOR}"
    )

    prompt = st.text_input(
        "Prompt",
        "Um robô futurista em uma cidade cinematográfica à noite",
    )

    if st.button(
        "🎨 Testar geração",
        use_container_width=True,
    ):

        if not prompt.strip():

            st.warning(
                "Digite um prompt."
            )

            return

        with st.spinner(
            "🎨 Gerando imagem..."
        ):

            try:

                caminho = gerar_imagem_teste(
                    prompt
                )

                st.image(
                    caminho,
                    caption=(
                        "FLUX.1-schnell — "
                        "teste isolado"
                    ),
                    use_container_width=True,
                )

                st.success(
                    "✅ Imagem gerada com sucesso!"
                )

            except Exception as erro:

                st.error(
                    f"❌ Erro:\n\n{erro}"
                )


# ============================================================
# 🚀 EXECUTAR
# ============================================================

if __name__ == "__main__":
    mostrar_teste()
