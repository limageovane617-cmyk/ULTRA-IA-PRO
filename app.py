# ============================================================
# 🤖 ALEX IA ULTRA
# APP PRINCIPAL
# ============================================================
# Criado por: Geovani
# ============================================================

import base64
import os
import sys
import importlib
from pathlib import Path

import streamlit as st

from ponte_alex import (
    verificar_ponte,
    ponte_disponivel,
    obter_status_ponte,
    ClientePonteAlex,
    ErroPonteAlex,
)


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Alex IA Ultra",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# 📦 IMPORTAÇÕES DO PROJETO
# ============================================================

if "gerenciador_imagem" in sys.modules:
    importlib.reload(sys.modules["gerenciador_imagem"])
else:
    import gerenciador_imagem

from gerenciador_imagem import mostrar_imagem

from config_ultra import (
    SYSTEM_PROMPT,
    GEMINI_MODEL,
    AI_NAME,
    CREATOR_NAME
)

from servicos import (
    criar_cliente_gemini,
    verificar_servicos
)

from memoria import (
    salvar_memoria,
    carregar_memorias,
    apagar_memoria,
    apagar_todas_memorias
)

from personagens import (
    salvar_personagem,
    carregar_personagem,
    listar_personagens,
    apagar_personagem
)

from voz import (
    mostrar_audio,
    gerar_audio
)

import video

gerar_video = video.gerar_video
mostrar_configuracao_video = video.mostrar_configuracao_video
verificar_magic_hour = video.verificar_magic_hour

from arquivos import ler_arquivo

from codigo import (
    preparar_pedido_codigo,
    listar_linguagens
)


# ============================================================
# 🧠 SESSION STATE
# ============================================================

DEFAULTS = {
    "mensagens": [],
    "personagem_atual": None,
    "arquivo_contexto": "",
    "arquivo_nome": "",
    "imagem_contexto": None,
    "imagem_nome": "",
    "imagem_mime": "",
    "ferramenta_ativa": None,
    "usar_voz": False,
    "ultima_imagem_caminho": None,
}

for chave, valor in DEFAULTS.items():

    if chave not in st.session_state:
        st.session_state[chave] = valor
# ============================================================
# 🔐 SERVIÇOS
# ============================================================

servicos = verificar_servicos()

if not servicos.get("gemini"):

    st.error(
        "🔐 A chave GEMINI_API_KEY não está configurada "
        "nos Secrets do Streamlit."
    )

    st.stop()


cliente = criar_cliente_gemini()

if cliente is None:

    st.error(
        "❌ Não foi possível criar a conexão com o Gemini."
    )

    st.stop()


# ============================================================
# 🖼️ FUNDO DA ALEX IA ULTRA
# ============================================================

FUNDO_URL = (
    "https://i.supaimg.com/"
    "c4e94ec5-263e-44e5-b119-dca8baa8acad/"
    "9865081d-da93-4f67-a58d-f304f9feb1cb.jpg"
)

# ============================================================
# 🎨 CSS (substituído por painel dinâmico de cores)
# ============================================================

# --- Painel de cores dinâmico (substitui o CSS estático) ---
# Defaults de cores/fonte
DEFAULT_COLOR_SETTINGS = {
    "fundo_botao": "#0f172a",        # botão do popover "+"
    "nome_color": "#8fd8ff",        # cor do nome "Alex IA"
    "texto_color": "#ffffff",       # cor de texto geral / botões
    "painel_bg": "#08111d",         # fundo do painel de ferramentas
    "font_family": "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial"
}

# inicializa session_state para configurações de cor (mantém entre runs)
for k, v in DEFAULT_COLOR_SETTINGS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Painel de configuração (usuário pode abrir e ajustar)
with st.expander("🎨 Painel de Cores — ajustar aparência", expanded=False):
    st.markdown("Altere cores e fonte abaixo. As mudanças são aplicadas imediatamente.")
    st.session_state["fundo_botao"] = st.color_picker(
        "Cor do botão (+)",
        st.session_state["fundo_botao"],
        key="picker_fundo_botao"
    )
    st.session_state["nome_color"] = st.color_picker(
        "Cor do nome 'Alex IA'",
        st.session_state["nome_color"],
        key="picker_nome_color"
    )
    st.session_state["texto_color"] = st.color_picker(
        "Cor do texto / ícones",
        st.session_state["texto_color"],
        key="picker_texto_color"
    )
    st.session_state["painel_bg"] = st.color_picker(
        "Fundo do painel de ferramentas",
        st.session_state["painel_bg"],
        key="picker_painel_bg"
    )
    st.session_state["font_family"] = st.text_input(
        "Fonte (CSS font-family)",
        st.session_state["font_family"],
        key="input_font_family"
    )

# Gera CSS usando as cores escolhidas
CSS = f"""
<style>
:root {{
    --fundo-botao: {st.session_state['fundo_botao']};
    --nome-color: {st.session_state['nome_color']};
    --texto-color: {st.session_state['texto_color']};
    --painel-bg: {st.session_state['painel_bg']};
    --app-font-family: {st.session_state['font_family']};
}}

.stApp {{
    font-family: var(--app-font-family);
    background-image: url("{FUNDO_URL}") !important;
    background-size: 100% 100% !important;
    background-position: center center !important;
    background-repeat: no-repeat !important;
    background-attachment: fixed !important;
    min-height: 100vh !important;
}}

.stApp::before {{
    content: "";
    position: fixed;
    inset: 0;
    background: rgba(2,8,16,.35);
    z-index: 0;
    pointer-events: none;
}}

.main .block-container {{
    max-width: 980px;
    padding-top: 1.2rem;
    padding-bottom: 8rem;
}}

/* BOTÃO DE FERRAMENTAS (+) */
div[data-testid="stElementContainer"]:has(
    div[data-testid="stPopover"]
),
div[data-testid="stPopover"] {{
    position: fixed !important;
    bottom: 14px !important;
    left: 1px !important;
    width: auto !important;
    z-index: 99999 !important;
}}

div[data-testid="stPopover"] > button {{
    padding: 0 !important;
    min-width: 36px !important;
    width: 36px !important;
    height: 36px !important;
    border-radius: 100% !important;
    border: 1px solid rgba(0,0,0,0.12) !important;
    background-color: var(--fundo-botao) !important;
    color: var(--texto-color) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}

/* PAINEL DE FERRAMENTAS */
.tool-panel {{
    margin: 0 auto .60rem;
    padding: .75rem;
    border-radius: 20px;
    background: var(--painel-bg);
    border: 1px solid rgba(130,210,255,.08);
    color: var(--texto-color);
}}

/* ESPAÇO DO INPUT DO CHAT */
div[data-testid="stChatInput"] {{
    padding-left: 55px !important;
}}

/* CHAT & MENSAGENS */
div[data-testid="stChatMessage"] {{
    background: transparent !important;
}}
div[data-testid="stChatMessage"] > div {{
    background: transparent !important;
}}

/* MENSAGEM DO USUÁRIO */
.user-message {{
    background: rgba(0,0,0,0.60);
    color: var(--texto-color);
    padding: 11px 15px;
    border-radius: 100px 100px 15px 100px;
    font-size: 16px;
    line-height: 1.45;
    word-break: break-word;
    width: fit-content;
    max-width: 75%;
    margin-left: auto;
}}

/* MENSAGEM DA ALEX */
.assistant-message {{
    background: rgba(0,0,0,0.10);
    color: var(--texto-color);
    padding: 12px 16px;
    border-radius: 100px 100px 100px 5px;
    font-size: 16px;
    line-height: 1.45;
    word-wrap: break-word;
    width: fit-content;
    max-width: 78%;
}}

.alex-name {{
    font-weight: bold;
    margin-bottom: 6px;
    color: var(--nome-color);
}}

/* BOTÕES (primários) */
div.stButton > button, button[kind="primary"] {{
    background-color: var(--fundo-botao) !important;
    color: var(--texto-color) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
}}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)
# --- fim do bloco de cores dinâmico ---


# ============================================================
# 🤖 CABEÇALHO
# ============================================================

st.markdown(
    f"## 🤖 {AI_NAME}"
)

st.caption(
    f"Criada por {CREATOR_NAME} • inteligência artificial pessoal"
)


# ============================================================
# 💬 HISTÓRICO
# ============================================================

for indice, mensagem in enumerate(
    st.session_state.mensagens
):

    role = mensagem.get(
        "role",
        "assistant"
    )

    tipo = mensagem.get(
        "tipo",
        "texto"
    )

    texto = mensagem.get(
        "content",
        ""
    )


    # ========================================================
    # 👤 USUÁRIO
    # ========================================================

    if role == "user":

        with st.chat_message(
            "user",
            avatar="👤"
        ):

            st.markdown(
                f"""
                <div class="user-message">
                    {texto}
                </div>
                """,
                unsafe_allow_html=True
            )


        continue


    # ========================================================
    # ✨ ALEX
    # ========================================================

    with st.chat_message(
        "assistant",
        avatar="✨"
    ):

        st.markdown(
            """
            <div class="alex-name">
                ✨ Alex IA
            </div>
            """,
            unsafe_allow_html=True
        )


        # ====================================================
        # 🖼️ IMAGEM
        # ====================================================

        if (
            tipo == "imagem"
            and mensagem.get("arquivo")
            and os.path.exists(
                mensagem["arquivo"]
            )
        ):

            st.image(
                mensagem["arquivo"],
                use_container_width=True
            )


        # ====================================================
        # 🎬 VÍDEO
        # ====================================================

        elif (
            tipo == "video"
            and mensagem.get("arquivo")
            and os.path.exists(
                mensagem["arquivo"]
            )
        ):

            st.video(
                mensagem["arquivo"]
            )


        # ====================================================
        # 💬 TEXTO
        # ====================================================

        if texto:

            st.markdown(
                texto,
                unsafe_allow_html=False
            )


        # ====================================================
        # 🔊 BOTÃO OUVIR
        # ====================================================

        if texto:

            audio_key = (
                "historico_audio_"
                + str(indice)
            )


            if st.button(
                "🔊 Ouvir",
                key=audio_key
            ):

                with st.spinner(
                    "🔊 Preparando a voz..."
                ):

                    audio, erro, formato = (
                        gerar_audio(texto)
                    )


                if audio:

                    st.audio(
                        audio,
                        format=formato
                    )

                else:

                    st.error(
                        "❌ Não foi possível gerar "
                        f"a voz: {erro}"
                    )
