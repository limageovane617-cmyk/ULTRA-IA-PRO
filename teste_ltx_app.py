import streamlit as st
from gradio_client import Client

st.set_page_config(
    page_title="Teste LTX-2.3",
    page_icon="🎬"
)

st.title("🎬 Teste LTX-2.3")
st.write("Teste real da geração de vídeo através da Space oficial do LTX-2.3.")

prompt = st.text_area(
    "📝 Descrição do vídeo",
    "Uma bola vermelha rolando lentamente sobre uma mesa de madeira, iluminação cinematográfica, movimento suave de câmera."
)

if st.button("🎬 Gerar vídeo de teste"):

    try:

        with st.spinner("🔌 Conectando ao LTX-2.3..."):

            client = Client(
                "https://lightricks-ltx-2-3.hf.space"
            )

        st.success("✅ LTX-2.3 conectado!")

        with st.spinner("🎥 Gerando vídeo..."):

            resultado = client.predict(
                input_image=None,
                prompt=prompt,
                duration=1.0,
                enhance_prompt=True,
                seed=0,
                randomize_seed=True,
                height=512,
                width=512,
                api_name="/generate_video"
            )

        st.success("🎉 Vídeo gerado com sucesso!")

        # O LTX-2.3 retorna:
        # (caminho_do_video, seed)

        caminho_video = resultado[0]
        seed_usada = resultado[1]

        st.video(caminho_video)

        st.write("🎲 Seed utilizada:")
        st.code(str(seed_usada))

    except Exception as erro:

        st.error("❌ Erro durante a geração.")

        st.code(
            str(erro)
        )
