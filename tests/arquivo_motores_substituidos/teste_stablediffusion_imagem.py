# ============================================================
# 🧪 TESTE DE IMAGEM — MODELSLAB / STABLE DIFFUSION
# ============================================================

import os
import time
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

API_URL = "https://modelslab.com/api/v6/images/text2img"

MODELO = "flux"


# ============================================================
# 🔐 API KEY
# ============================================================

def obter_api_key():

    try:
        chave = st.secrets.get(
            "STABLE_DIFFUSION_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "STABLE_DIFFUSION_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 📁 PASTA
# ============================================================

def obter_pasta():

    pasta = Path(
        "/tmp/alex_ia_ultra_stable_diffusion"
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
            "STABLE_DIFFUSION_API_KEY "
            "não foi encontrada nos Secrets "
            "do Streamlit."
        )

    dados = {
        "key": api_key,
        "model_id": MODELO,
        "prompt": prompt.strip(),
        "negative_prompt": (
            "blurry, low quality, distorted, "
            "bad anatomy, extra limbs, "
            "deformed, watermark"
        ),
        "width": "512",
        "height": "512",
        "samples": "1",
        "num_inference_steps": "20",
        "guidance_scale": 7.5,
        "enhance_prompt": "yes",
        "safety_checker": "yes",
    }

    try:

        resposta = requests.post(
            API_URL,
            json=dados,
            headers={
                "Content-Type": "application/json"
            },
            timeout=180,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro de conexão com a ModelsLab: {erro}"
        )

    if resposta.status_code != 200:

        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"ModelsLab retornou HTTP "
            f"{resposta.status_code}:\n\n"
            f"{detalhes}"
        )

    try:

        resultado = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            f"Resposta inválida da ModelsLab: {erro}"
        )

    # ========================================================
    # VERIFICAR ERRO DA API
    # ========================================================

    if resultado.get("status") == "error":

        mensagem = (
            resultado.get("message")
            or resultado.get("error")
            or resultado
        )

        raise RuntimeError(
            f"ModelsLab informou um erro:\n{mensagem}"
        )

    # ========================================================
    # PEGAR IMAGEM DIRETA
    # ========================================================

    output = resultado.get("output")

    if output:

        if isinstance(output, list):
            imagem_url = output[0]
        else:
            imagem_url = output

        return baixar_imagem(imagem_url)

    # ========================================================
    # PROCESSAMENTO ASSÍNCRONO
    # ========================================================

    fetch_url = resultado.get("fetch_result")

    if fetch_url:

        return aguardar_resultado(
            fetch_url
        )

    # ========================================================
    # RESULTADO DESCONHECIDO
    # ========================================================

    raise RuntimeError(
        "A ModelsLab respondeu, mas não "
        "encontramos a imagem.\n\n"
        f"Resposta:\n{resultado}"
    )


# ============================================================
# ⏳ AGUARDAR RESULTADO
# ============================================================

def aguardar_resultado(fetch_url):

    ultima_resposta = None

    for _ in range(30):

        try:

            resposta = requests.get(
                fetch_url,
                timeout=60,
            )

            ultima_resposta = resposta

        except Exception:
            time.sleep(2)
            continue

        if resposta.status_code != 200:

            time.sleep(2)
            continue

        try:

            resultado = resposta.json()

        except Exception:

            time.sleep(2)
            continue

        if resultado.get("status") == "error":

            raise RuntimeError(
                f"ModelsLab informou um erro:\n"
                f"{resultado}"
            )

        output = resultado.get("output")

        if output:

            if isinstance(output, list):
                imagem_url = output[0]
            else:
                imagem_url = output

            return baixar_imagem(
                imagem_url
            )

        time.sleep(2)

    raise RuntimeError(
        "A geração demorou mais que o esperado "
        "e não retornou uma imagem.\n\n"
        f"Última resposta: {ultima_resposta}"
    )


# ============================================================
# ⬇️ BAIXAR IMAGEM
# ============================================================

def baixar_imagem(imagem_url):

    if not imagem_url:
        raise RuntimeError(
            "A API não retornou uma URL de imagem."
        )

    try:

        resposta = requests.get(
            imagem_url,
            timeout=120,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao baixar a imagem: {erro}"
        )

    if resposta.status_code != 200:

        raise RuntimeError(
            "Não foi possível baixar a imagem. "
            f"HTTP {resposta.status_code}"
        )

    caminho = (
        obter_pasta()
        / "teste_modelslab.png"
    )

    try:

        caminho.write_bytes(
            resposta.content
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao salvar a imagem: {erro}"
        )

    return str(caminho)


# ============================================================
# 🧪 INTERFACE
# ============================================================

def mostrar_teste():

    st.title(
        "🧪 TESTE DE IMAGEM — MODELSLAB"
    )

    st.write(
        "Teste isolado de geração de imagens."
    )

    st.info(
        "Motor: ModelsLab / Stable Diffusion"
    )

    prompt = st.text_area(
        "Digite o que você quer criar:",
        value=(
            "Um robô futurista caminhando "
            "em uma cidade cyberpunk à noite, "
            "cinematográfico, extremamente "
            "detalhado, iluminação profissional."
        ),
        height=140,
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
            "🎨 Gerando imagem..."
        ):

            try:

                caminho = gerar_imagem(
                    prompt
                )

                st.image(
                    caminho,
                    caption=(
                        "🖼️ ModelsLab / "
                        "Stable Diffusion"
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
# 🚀 EXECUTAR
# ============================================================

if __name__ == "__main__":
    mostrar_teste()
