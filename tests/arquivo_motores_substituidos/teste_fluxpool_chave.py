import os
import streamlit as st


def obter_chave():

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


st.title("🔐 TESTE DA CHAVE — FLUXPOOL")

chave = obter_chave()

if not chave:
    st.error("❌ A chave NÃO está sendo encontrada.")
else:

    st.success("✅ O Streamlit encontrou a chave.")

    st.write(
        "Quantidade de caracteres:",
        len(chave)
    )

    st.write(
        "Começa com:",
        chave[:8] + "..."
    )

    st.write(
        "Termina com:",
        "..." + chave[-4:]
    )
