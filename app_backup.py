# ============================================================
# 🤖 ALEX IA ULTRA
# Aplicativo principal
# Criada por Geovani
# ============================================================

import streamlit as st

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

from imagem import mostrar_imagem
from voz import mostrar_audio

from video import (
    gerar_video,
    mostrar_configuracao_video
)

from arquivos import ler_arquivo

from codigo import (
    preparar_pedido_codigo,
    analisar_codigo,
    listar_linguagens
)


# ============================================================
# ⚙️ CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Alex IA Ultra",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# 🎨 ESTILO
# ============================================================

st.markdown("""
<style>

.chat-painel {
    max-width: 1000px;
    margin: auto;
}

.titulo-alex {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
}

.subtitulo-alex {
    text-align: center;
    opacity: 0.75;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 🤖 CABEÇALHO
# ============================================================

st.markdown(
    '<div class="titulo-alex">🤖 Alex IA Ultra</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="subtitulo-alex">'
    f'Criada por {CREATOR_NAME} • Sua inteligência artificial pessoal'
    f'</div>',
    unsafe_allow_html=True
)


# ============================================================
# 🧠 ESTADO DA CONVERSA
# ============================================================

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "personagem_atual" not in st.session_state:
    st.session_state.personagem_atual = None

if "arquivo_contexto" not in st.session_state:
    st.session_state.arquivo_contexto = ""

if "arquivo_nome" not in st.session_state:
    st.session_state.arquivo_nome = ""


# ============================================================
# 🔐 VERIFICAÇÃO DOS SERVIÇOS
# ============================================================

servicos = verificar_servicos()

gemini_disponivel = servicos["gemini"]
huggingface_disponivel = servicos["huggingface"]

if not gemini_disponivel:
    st.error(
        "🔐 A chave GEMINI_API_KEY não está configurada "
        "nos Secrets do Streamlit."
    )

    st.info(
        "Abra os Secrets do seu aplicativo e adicione "
        "GEMINI_API_KEY. Não coloque a chave dentro do app.py."
    )

    st.stop()


cliente = criar_cliente_gemini()

if cliente is None:
    st.error(
        "❌ Não foi possível criar a conexão com o Gemini."
    )
    st.stop()


# ============================================================
# 📚 SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Alex IA Ultra")
    st.caption("Painel de controle")

    # ========================================================
    # 🧹 LIMPAR CONVERSA
    # ========================================================

    if st.button(
        "🗑️ Limpar conversa",
        use_container_width=True
    ):
        st.session_state.mensagens = []
        st.rerun()

    st.divider()

    # ========================================================
    # 🎭 PERSONAGENS
    # ========================================================

    st.header("🎭 Personagens")

    personagens = listar_personagens()

    personagem_selecionado = st.selectbox(
        "Personagem salvo",
        ["Nenhum"] + personagens
    )

    dados_personagem = None

    if personagem_selecionado != "Nenhum":
        dados_personagem = carregar_personagem(
            personagem_selecionado
        )

        if dados_personagem:
            st.session_state.personagem_atual = dados_personagem

    nome_personagem = st.text_input(
        "Nome",
        value=(
            dados_personagem["nome"]
            if dados_personagem
            else ""
        )
    )

    idade_personagem = st.text_input(
        "Idade",
        value=(
            dados_personagem["idade"]
            if dados_personagem
            else ""
        )
    )

    aparencia_personagem = st.text_area(
        "Aparência",
        value=(
            dados_personagem["aparencia"]
            if dados_personagem
            else ""
        )
    )

    roupa_personagem = st.text_input(
        "Roupa",
        value=(
            dados_personagem["roupa"]
            if dados_personagem
            else ""
        )
    )

    personalidade_personagem = st.text_area(
        "Personalidade",
        value=(
            dados_personagem["personalidade"]
            if dados_personagem
            else ""
        )
    )

    if st.button(
        "💾 Salvar personagem",
        use_container_width=True
    ):

        if not nome_personagem.strip():
            st.warning(
                "Digite um nome para o personagem."
            )

        else:
            salvar_personagem(
                nome=nome_personagem,
                idade=idade_personagem,
                aparencia=aparencia_personagem,
                roupa=roupa_personagem,
                personalidade=personalidade_personagem
            )

            st.session_state.personagem_atual = {
                "nome": nome_personagem,
                "idade": idade_personagem,
                "aparencia": aparencia_personagem,
                "roupa": roupa_personagem,
                "personalidade": personalidade_personagem
            }

            st.success("✅ Personagem salvo!")
            st.rerun()

    if personagens:

        personagem_para_apagar = st.selectbox(
            "Apagar personagem",
            ["Nenhum"] + personagens,
            key="apagar_personagem"
        )

        if st.button(
            "🗑️ Apagar personagem",
            use_container_width=True
        ):

            if personagem_para_apagar != "Nenhum":
                apagar_personagem(
                    personagem_para_apagar
                )

                st.success("Personagem apagado.")
                st.rerun()

    st.divider()

    # ========================================================
    # 🧠 MEMÓRIA
    # ========================================================

    st.header("🧠 Memória")

    memorias = carregar_memorias()

    if memorias:

        st.caption(
            f"{len(memorias)} memória(s) salva(s)"
        )

        memoria_para_apagar = st.selectbox(
            "Escolha uma memória",
            ["Nenhuma"] + memorias,
            key="memoria_apagar"
        )

        if st.button(
            "🗑️ Apagar memória",
            use_container_width=True
        ):

            if memoria_para_apagar != "Nenhuma":
                apagar_memoria(memoria_para_apagar)
                st.rerun()

        if st.button(
            "🗑️ Apagar todas as memórias",
            use_container_width=True
        ):
            apagar_todas_memorias()
            st.rerun()

    else:
        st.caption("Nenhuma memória salva.")

    st.divider()

    # ========================================================
    # 📄 ARQUIVOS
    # ========================================================

    st.header("📄 Arquivos")

    arquivo = st.file_uploader(
        "Enviar arquivo",
        type=["pdf", "txt", "docx"]
    )

    if arquivo:

        if st.button(
            "📥 Ler arquivo",
            use_container_width=True
        ):

            texto_arquivo, erro_arquivo = ler_arquivo(arquivo)

            if erro_arquivo:
                st.error(f"❌ {erro_arquivo}")

            else:
                st.session_state.arquivo_contexto = (
                    texto_arquivo[:50000]
                )

                st.session_state.arquivo_nome = arquivo.name

                st.success("✅ Arquivo carregado!")

    if st.session_state.arquivo_contexto:

        st.caption(
            f"📎 {st.session_state.arquivo_nome}"
        )

        if st.button(
            "🗑️ Remover arquivo",
            use_container_width=True
        ):
            st.session_state.arquivo_contexto = ""
            st.session_state.arquivo_nome = ""
            st.rerun()

    st.divider()

    # ========================================================
    # 🖼️ IMAGEM
    # ========================================================

    st.header("🖼️ Imagens")

    if huggingface_disponivel:
        st.success("Hugging Face conectado")
    else:
        st.warning("HF_TOKEN não configurado")

    st.divider()

    # ========================================================
    # 🔊 VOZ
    # ========================================================

    st.header("🔊 Voz")

    usar_voz = st.checkbox(
        "🔊 Ler respostas da Alex",
        value=False
    )

    st.divider()

    # ========================================================
    # 🎬 VÍDEO
    # ========================================================

    st.header("🎬 Vídeo")

    camera_video, proporcao_video, duracao_video = (
        mostrar_configuracao_video()
    )

    st.divider()

    # ========================================================
    # 💻 CÓDIGO
    # ========================================================

    st.header("💻 Programação")

    linguagem_codigo = st.selectbox(
        "Linguagem",
        listar_linguagens()
    )


# ============================================================
# 💬 HISTÓRICO DA CONVERSA
# ============================================================

for mensagem in st.session_state.mensagens:

    if mensagem["role"] == "user":

        with st.chat_message("user"):
            st.write(mensagem["content"])

    elif mensagem["role"] == "assistant":

        with st.chat_message("assistant"):
            st.write(mensagem["content"])


# ============================================================
# 💬 CAMPO PRINCIPAL DE CHAT
# ============================================================

pergunta = st.chat_input(
    "Digite sua mensagem para a Alex..."
)


# ============================================================
# 🚀 PROCESSAMENTO
# ============================================================

if pergunta:

    pergunta = pergunta.strip()

    if not pergunta:
        st.stop()

    # --------------------------------------------------------
    # Guarda mensagem do usuário
    # --------------------------------------------------------

    st.session_state.mensagens.append({
        "role": "user",
        "content": pergunta
    })

    # --------------------------------------------------------
    # 🧠 COMANDO DE MEMÓRIA
    # --------------------------------------------------------

    if pergunta.lower().startswith("memorize:"):

        informacao = pergunta[len("memorize:"):].strip()

        if informacao:
            salvar_memoria(informacao)

            resposta_memoria = (
                "🧠 Pronto! Salvei essa informação "
                "na minha memória."
            )

        else:
            resposta_memoria = (
                "Digite depois de `memorize:` "
                "a informação que você quer salvar."
            )

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": resposta_memoria
        })

        st.rerun()

    # --------------------------------------------------------
    # 🖼️ COMANDO DE IMAGEM
    # --------------------------------------------------------

    if pergunta.lower().startswith("imagem:"):

        prompt_imagem = pergunta[len("imagem:"):].strip()

        if not huggingface_disponivel:

            resposta_imagem = (
                "❌ O HF_TOKEN ainda não está "
                "configurado nos Secrets."
            )

            st.session_state.mensagens.append({
                "role": "assistant",
                "content": resposta_imagem
            })

            st.rerun()

        if not prompt_imagem:

            resposta_imagem = (
                "Digite o que você quer gerar "
                "depois de `imagem:`."
            )

            st.session_state.mensagens.append({
                "role": "assistant",
                "content": resposta_imagem
            })

            st.rerun()

        with st.chat_message("assistant"):

            st.write("🖼️ Gerando sua imagem...")

            mostrar_imagem(prompt_imagem)

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": "🖼️ Imagem gerada pela Alex IA."
        })

        st.stop()

    # --------------------------------------------------------
    # 🎬 COMANDO DE VÍDEO
    # --------------------------------------------------------

    if pergunta.lower().startswith("video:"):

        descricao_video = pergunta[len("video:"):].strip()

        if not descricao_video:

            resposta_video = (
                "Digite a descrição depois de `video:`."
            )

            st.session_state.mensagens.append({
                "role": "assistant",
                "content": resposta_video
            })

            st.rerun()

        with st.chat_message("assistant"):

            st.write("🎬 Preparando seu vídeo cinematográfico...")

            with st.spinner(
                "🎬 O Veo 3.1 está gerando seu vídeo. "
                "Isso pode levar alguns minutos..."
            ):

                caminho_video, mensagem_video = gerar_video(
                    descricao=descricao_video,
                    camera=camera_video,
                    proporcao=proporcao_video,
                    duracao=duracao_video
                )

            if caminho_video:

                st.success("🎬 Vídeo gerado com sucesso!")

                st.video(caminho_video)

                with open(caminho_video, "rb") as arquivo_video:
                    st.download_button(
                        "⬇️ Baixar vídeo MP4",
                        data=arquivo_video.read(),
                        file_name="alex_ia_video.mp4",
                        mime="video/mp4",
                        key="baixar_video_chat"
                    )

                resposta_video = (
                    "🎬 Vídeo gerado com sucesso pelo Veo 3.1."
                )

            else:

                resposta_video = (
                    f"❌ Não foi possível gerar o vídeo.\\n\\n"
                    f"{mensagem_video}"
                )

                st.error(resposta_video)

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": resposta_video
        })

        # Não envia o pedido de vídeo para o chat normal do Gemini.
        # O módulo de vídeo já processou a solicitação.
        st.stop()

    # --------------------------------------------------------
    # 💻 COMANDO DE CÓDIGO
    # --------------------------------------------------------

    if pergunta.lower().startswith("codigo:"):

        pedido_codigo = pergunta[len("codigo:"):].strip()

        if not pedido_codigo:

            resposta_codigo = (
                "Digite o que você quer programar "
                "depois de `codigo:`."
            )

        else:

            prompt_codigo = preparar_pedido_codigo(
                pedido=pedido_codigo,
                linguagem=linguagem_codigo
            )

            try:

                resposta = cliente.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt_codigo
                )

                resposta_codigo = (
                    resposta.text
                    if resposta.text
                    else "Não consegui gerar o código."
                )

            except Exception as erro:

                resposta_codigo = (
                    f"❌ Erro ao gerar código: {erro}"
                )

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": resposta_codigo
        })

        st.rerun()

    # --------------------------------------------------------
    # 📄 ARQUIVO + CHAT
    # --------------------------------------------------------

    contexto_arquivo = ""

    if st.session_state.arquivo_contexto:

        contexto_arquivo = f"""
Arquivo enviado pelo usuário:

Nome:
{st.session_state.arquivo_nome}

Conteúdo:

{st.session_state.arquivo_contexto}
"""

    # --------------------------------------------------------
    # 🎭 PERSONAGEM
    # --------------------------------------------------------

    contexto_personagem = ""

    personagem = st.session_state.personagem_atual

    if personagem:

        contexto_personagem = f"""
Personagem atualmente selecionado:

Nome:
{personagem["nome"]}

Idade:
{personagem["idade"]}

Aparência:
{personagem["aparencia"]}

Roupa:
{personagem["roupa"]}

Personalidade:
{personagem["personalidade"]}

Use o personagem somente quando isso fizer sentido
para o pedido do usuário.
"""

    # --------------------------------------------------------
    # 🧠 MEMÓRIAS
    # --------------------------------------------------------

    memorias = carregar_memorias()

    contexto_memoria = ""

    if memorias:

        contexto_memoria = """
Memórias importantes do usuário:

""" + "\n".join(
            f"- {memoria}"
            for memoria in memorias
        )

    # --------------------------------------------------------
    # 📜 HISTÓRICO
    # --------------------------------------------------------

    historico = ""

    for mensagem in st.session_state.mensagens:

        if mensagem["role"] == "user":

            historico += (
                f"Geovani: "
                f"{mensagem['content']}\n"
            )

        elif mensagem["role"] == "assistant":

            historico += (
                f"{AI_NAME}: "
                f"{mensagem['content']}\n"
            )

    # --------------------------------------------------------
    # 🧠 INSTRUÇÃO FINAL
    # --------------------------------------------------------

    instrucao = f"""
{SYSTEM_PROMPT}

Regras adicionais:

- Responda sempre em português do Brasil.
- Você está conversando diretamente com Geovani.
- Mantenha continuidade com o histórico.
- Use as memórias quando forem relevantes.
- Use o personagem somente quando necessário.
- Se houver um arquivo enviado, analise seu conteúdo.
- Não invente informações sobre arquivos.
- Seja clara, inteligente e objetiva.
- Ajude Geovani a desenvolver a Alex IA Ultra.
- Quando não souber algo, diga claramente.

{contexto_memoria}

{contexto_personagem}

{contexto_arquivo}

Histórico da conversa:

{historico}

Pergunta atual:

{pergunta}
"""

    # --------------------------------------------------------
    # 🤖 GEMINI
    # --------------------------------------------------------

    try:

        with st.chat_message("assistant"):

            with st.spinner(
                "🤖 Alex IA está pensando..."
            ):

                resposta = cliente.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=instrucao
                )

                texto_resposta = (
                    resposta.text
                    if resposta.text
                    else "Não consegui gerar uma resposta."
                )

            st.write(texto_resposta)

            # ------------------------------------------------
            # 🔊 VOZ
            # ------------------------------------------------

            if usar_voz:

                with st.spinner(
                    "🔊 Gerando voz..."
                ):

                    mostrar_audio(texto_resposta)

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": texto_resposta
        })

    except Exception as erro:

        mensagem_erro = (
            f"❌ Erro ao conversar com o Gemini:\n\n"
            f"{erro}"
        )

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": mensagem_erro
        })

        st.error(mensagem_erro)
