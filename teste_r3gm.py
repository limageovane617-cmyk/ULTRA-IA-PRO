import os
from pathlib import Path

import streamlit as st
from gradio_client import Client, handle_file


SPACE_ID = "r3gm/wan2-2-fp8da-aoti-preview"

PASTA = Path("videos")
PASTA.mkdir(exist_ok=True)


st.set_page_config(
    page_title="Teste Wan 2.2",
    page_icon="🎬"
)

st.title("🎬 Teste Wan 2.2 I2V")
st.write("r3gm/wan2-2-fp8da-aoti-preview")

imagem = st.file_uploader(
    "🖼️ Escolha a imagem",
    type=["png", "jpg", "jpeg", "webp"]
)

prompt = st.text_area(
    "✍️ Movimento",
    value=(
        "The character slowly walks toward the camera. "
        "The camera smoothly follows the character. "
        "Keep the exact same face, clothing, hairstyle and identity. "
        "Natural realistic movement and cinematic motion."
    )
)

if st.button("🎬 GERAR VÍDEO", type="primary"):

    if imagem is None:
        st.error("❌ Carregue uma imagem primeiro.")
        st.stop()

    arquivo_imagem = Path("imagem_r3gm.png")
    arquivo_imagem.write_bytes(imagem.getvalue())

    try:

        with st.status(
            "🔌 Conectando ao Wan 2.2...",
            expanded=True
        ) as status:

            st.write("Conectando ao Space...")

            client = Client(SPACE_ID)

            st.write("Enviando imagem...")

            # Parâmetros confirmados pelo OpenAPI
            resultado = client.predict(
                input_image=handle_file(
                    str(arquivo_imagem)
                ),
                last_image=None,
                prompt=prompt,
                steps=4,
                negative_prompt=(
                    "static, blurry, low quality, "
                    "distorted face, extra fingers, "
                    "deformed hands, duplicate person"
                ),
                duration_seconds=0.5,
                guidance_scale=1.0,
                guidance_scale_2=1.0,
                seed=42,
                randomize_seed=True,
                quality=5,
                scheduler="UniPCMultistep",
                flow_shift=6.0,
                frame_multiplier=16,
                video_component=True,
                safe_mode=True,
                enable_safety_checker=True,
                api_name="/generate_video"
            )

            st.write("Resposta recebida.")

            status.update(
                label="✅ Geração concluída!",
                state="complete"
            )

        st.write("Resultado bruto:")

        st.write(resultado)

        # O OpenAPI informa que a saída principal
        # possui um campo de vídeo.
        video = None

        if isinstance(resultado, dict):

            if "video" in resultado:
                video = resultado["video"]

            elif "output" in resultado:
                output = resultado["output"]

                if isinstance(output, dict):
                    video = output.get("video")

        elif isinstance(resultado, (list, tuple)):

            for item in resultado:

                if isinstance(item, dict):

                    if "video" in item:
                        video = item["video"]
                        break

        if video is None:
            st.warning(
                "⚠️ O Space respondeu, mas o formato "
                "da saída precisa ser analisado."
            )
            st.json(resultado)
            st.stop()

        caminho = None

        if isinstance(video, dict):
            caminho = video.get("path")

            if not caminho:
                caminho = video.get("url")

        elif isinstance(video, str):
            caminho = video

        if not caminho:
            st.error(
                "❌ Não encontrei o arquivo de vídeo "
                "na resposta."
            )
            st.json(resultado)
            st.stop()

        # Se o Gradio retornar um caminho local
        if Path(str(caminho)).exists():

            origem = Path(str(caminho))

            destino = (
                PASTA /
                "teste_r3gm_wan22.mp4"
            )

            destino.write_bytes(
                origem.read_bytes()
            )

            st.success("🎉 VÍDEO GERADO!")

            st.video(str(destino))

        else:

            # Se retornar uma URL
            if str(caminho).startswith(
                ("http://", "https://")
            ):

                import requests

                resposta = requests.get(
                    caminho,
                    timeout=180
                )

                resposta.raise_for_status()

                destino = (
                    PASTA /
                    "teste_r3gm_wan22.mp4"
                )

                destino.write_bytes(
                    resposta.content
                )

                st.success(
                    "🎉 VÍDEO GERADO!"
                )

                st.video(str(destino))

            else:

                st.warning(
                    "⚠️ O Space retornou um caminho "
                    "que não conseguimos acessar diretamente:"
                )

                st.code(str(caminho))

    except Exception as erro:

        st.error(
            "❌ Erro ao chamar o Wan 2.2:"
        )

        st.code(
            f"{type(erro).__name__}: {erro}"
        )

        st.info(
            "Esse teste não modifica o video.py."
          )
