import streamlit as st
from gradio_client import Client

st.set_page_config(
    page_title="Teste Z Image Turbo",
    page_icon="🖼️"
)

st.title("🖼️ Teste Z Image Turbo")

prompt = st.text_area(
    "📝 Prompt",
    "Uma cidade futurista à noite, ruas molhadas refletindo luzes neon, estilo cinematográfico e realista."
)

if st.button("🖼️ Gerar imagem", type="primary"):

    try:

        with st.spinner("🎨 Gerando imagem..."):

            cliente = Client(
                "mrfakename/Z-Image-Turbo"
            )

            resultado = cliente.predict(
                prompt,
                1024,
                1024,
                9,
                42,
                True,
                api_name="/generate_image"
            )

        st.success("🎉 Geração concluída!")

        st.write("Resultado:")
        st.write(resultado)

        if isinstance(resultado, tuple):
            imagem = resultado[0]

            if imagem:
                st.image(
                    imagem,
                    caption="🖼️ Z Image Turbo",
                    use_container_width=True
                )

    except Exception as erro:

        st.error("❌ Erro ao chamar a Space.")

        st.code(str(erro))
