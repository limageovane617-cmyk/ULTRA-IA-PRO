import streamlit as st
from huggingface_hub import InferenceClient

st.set_page_config(
    page_title="Teste FLUX",
    page_icon="🖼️"
)

st.title("🖼️ Teste FLUX.1-schnell")

prompt = st.text_area(
    "📝 Descrição da imagem",
    "Uma cidade futurista à noite, ruas molhadas refletindo luzes neon, uma pessoa caminhando pela rua, aparência cinematográfica e realista."
)

if st.button("🖼️ Gerar imagem", type="primary"):

    try:

        token = st.secrets["HF_TOKEN"]

        cliente = InferenceClient(
            api_key=token,
            provider="auto"
        )

        with st.spinner("🎨 Gerando imagem..."):

            imagem = cliente.text_to_image(
                prompt=prompt.strip(),
                model="black-forest-labs/FLUX.1-schnell"
            )

        st.success("🎉 Imagem gerada com sucesso!")

        st.image(
            imagem,
            caption="🖼️ FLUX.1-schnell",
            use_container_width=True
        )

    except Exception as erro:

        st.error("❌ Erro ao gerar a imagem.")

        st.code(str(erro))
