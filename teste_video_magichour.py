# ============================================================
# 🎬 TESTE DE VÍDEO — MAGIC HOUR
# IMAGE-TO-VIDEO
# Criado por Geovani
# ============================================================

import os
import time
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

BASE_URL = "https://api.magichour.ai/v1"

MODELO = "ltx-2.3"
RESOLUCAO = "480p"
DURACAO = 5

PASTA = Path(
    "/tmp/alex_ia_ultra_magichour"
)

PASTA.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 🔐 API KEY
# ============================================================

def obter_api_key():

    try:
        chave = st.secrets.get(
            "MAGIC_HOUR_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:

        chave = os.environ.get(
            "MAGIC_HOUR_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 🔐 CABEÇALHOS
# ============================================================

def headers_json():

    chave = obter_api_key()

    if not chave:

        raise RuntimeError(
            "MAGIC_HOUR_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    return {
        "Authorization": f"Bearer {chave}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


# ============================================================
# 📤 OBTER URL DE UPLOAD
# ============================================================

def obter_url_upload(extensao):

    extensao = extensao.lower().replace(".", "")

    if extensao not in [
        "png",
        "jpg",
        "jpeg",
        "webp",
        "jfif",
        "heic",
        "heif",
        "avif",
        "bmp",
        "tif",
        "tiff",
    ]:

        raise RuntimeError(
            f"Formato de imagem não suportado: {extensao}"
        )

    dados = {
        "items": [
            {
                "type": "image",
                "extension": extensao
            }
        ]
    }

    try:

        resposta = requests.post(
            f"{BASE_URL}/files/upload-urls",
            headers=headers_json(),
            json=dados,
            timeout=60
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro ao solicitar URL de upload:\n"
            f"{erro}"
        )

    if resposta.status_code != 200:

        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Magic Hour retornou HTTP "
            f"{resposta.status_code} ao solicitar upload:\n\n"
            f"{detalhes}"
        )

    try:

        resultado = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            "Resposta de upload não é JSON válido:\n"
            f"{erro}"
        )

    itens = resultado.get("items")

    if not itens:

        raise RuntimeError(
            "Magic Hour não retornou a lista de upload."
            f"\n\nResposta:\n{resultado}"
        )

    primeiro = itens[0]

    upload_url = primeiro.get(
        "upload_url"
    )

    file_path = primeiro.get(
        "file_path"
    )

    if not upload_url or not file_path:

        raise RuntimeError(
            "A resposta não contém "
            "upload_url e file_path.\n\n"
            f"Resposta:\n{resultado}"
        )

    return upload_url, file_path


# ============================================================
# 🖼️ ENVIAR IMAGEM
# ============================================================

def enviar_imagem(
    imagem_bytes,
    nome_arquivo
):

    extensao = Path(
        nome_arquivo
    ).suffix.lower().replace(
        ".",
        ""
    )

    upload_url, file_path = obter_url_upload(
        extensao
    )

    try:

        resposta = requests.put(
            upload_url,
            data=imagem_bytes,
            timeout=120
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro ao enviar a imagem para "
            f"o armazenamento do Magic Hour:\n{erro}"
        )

    if resposta.status_code not in [
        200,
        201,
        204
    ]:

        try:
            detalhes = resposta.text
        except Exception:
            detalhes = "Sem detalhes"

        raise RuntimeError(
            "Falha no upload da imagem.\n\n"
            f"HTTP {resposta.status_code}\n"
            f"{detalhes}"
        )

    return file_path


# ============================================================
# 🎬 CRIAR PROJETO DE VÍDEO
# ============================================================

def criar_video(
    file_path,
    prompt
):

    dados = {
        "name": "Teste Alex IA Ultra",
        "end_seconds": DURACAO,
        "model": MODELO,
        "resolution": RESOLUCAO,
        "audio": False,
        "style": {
            "prompt": prompt.strip()
        },
        "assets": {
            "image_file_path": file_path
        }
    }

    try:

        resposta = requests.post(
            f"{BASE_URL}/image-to-video",
            headers=headers_json(),
            json=dados,
            timeout=120
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro ao criar projeto de vídeo:\n"
            f"{erro}"
        )

    if resposta.status_code not in [
        200,
        201,
        202
    ]:

        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Magic Hour retornou HTTP "
            f"{resposta.status_code} ao criar vídeo:\n\n"
            f"{detalhes}"
        )

    try:

        resultado = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            "Resposta da geração não é JSON válido:\n"
            f"{erro}"
        )

    projeto_id = resultado.get("id")

    if not projeto_id:

        raise RuntimeError(
            "O Magic Hour não retornou o ID do vídeo.\n\n"
            f"Resposta:\n{resultado}"
        )

    return projeto_id, resultado


# ============================================================
# 🔎 CONSULTAR PROJETO
# ============================================================

def consultar_projeto(
    projeto_id
):

    urls = [
        f"{BASE_URL}/video-projects/{projeto_id}",
        f"{BASE_URL}/image-to-video/{projeto_id}",
    ]

    ultimo_erro = None

    for url in urls:

        try:

            resposta = requests.get(
                url,
                headers=headers_json(),
                timeout=60
            )

        except Exception as erro:

            ultimo_erro = str(erro)
            continue

        if resposta.status_code == 200:

            try:
                return resposta.json()
            except Exception:
                return {}

        ultimo_erro = (
            f"HTTP {resposta.status_code}: "
            f"{resposta.text}"
        )

    raise RuntimeError(
        "Não foi possível consultar o projeto.\n\n"
        f"{ultimo_erro}"
    )


# ============================================================
# 🔗 PROCURAR DOWNLOAD
# ============================================================

def encontrar_download(
    dados
):

    if not isinstance(
        dados,
        dict
    ):
        return None

    # Campos diretos
    campos = [
        "video_url",
        "download_url",
        "output_url",
        "url",
    ]

    for campo in campos:

        valor = dados.get(
            campo
        )

        if isinstance(
            valor,
            str
        ) and valor.startswith(
            "http"
        ):

            return valor

    # downloads
    downloads = dados.get(
        "downloads"
    )

    if isinstance(
        downloads,
        dict
    ):

        for valor in downloads.values():

            if isinstance(
                valor,
                str
            ) and valor.startswith(
                "http"
            ):

                return valor

            if isinstance(
                valor,
                dict
            ):

                for chave in [
                    "url",
                    "download_url"
                ]:

                    url = valor.get(
                        chave
                    )

                    if isinstance(
                        url,
                        str
                    ) and url.startswith(
                        "http"
                    ):

                        return url

    if isinstance(
        downloads,
        list
    ):

        for item in downloads:

            if isinstance(
                item,
                str
            ) and item.startswith(
                "http"
            ):

                return item

            if isinstance(
                item,
                dict
            ):

                for chave in [
                    "url",
                    "download_url"
                ]:

                    url = item.get(
                        chave
                    )

                    if isinstance(
                        url,
                        str
                    ) and url.startswith(
                        "http"
                    ):

                        return url

    # output
    output = dados.get(
        "output"
    )

    if isinstance(
        output,
        dict
    ):

        for valor in output.values():

            if isinstance(
                valor,
                str
            ) and valor.startswith(
                "http"
            ):

                return valor

    return None


# ============================================================
# ⬇️ BAIXAR VÍDEO
# ============================================================

def baixar_video(
    url
):

    caminho = (
        PASTA /
        "video_magichour.mp4"
    )

    try:

        resposta = requests.get(
            url,
            timeout=180
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro ao baixar o vídeo:\n"
            f"{erro}"
        )

    if resposta.status_code != 200:

        raise RuntimeError(
            "Falha ao baixar o vídeo.\n"
            f"HTTP {resposta.status_code}"
        )

    caminho.write_bytes(
        resposta.content
    )

    return str(caminho)


# ============================================================
# 🖥️ INTERFACE
# ============================================================

st.set_page_config(
    page_title="Teste Magic Hour",
    page_icon="🎬"
)

st.title(
    "🎬 TESTE DE VÍDEO — MAGIC HOUR"
)

st.caption(
    "Image-to-Video • LTX 2.3"
)

st.info(
    f"Motor: {MODELO} • "
    f"Resolução: {RESOLUCAO} • "
    f"Duração: {DURACAO}s"
)


# ============================================================
# 🖼️ IMAGEM
# ============================================================

imagem = st.file_uploader(
    "🖼️ Escolha uma imagem",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp"
    ]
)


if imagem:

    st.image(
        imagem,
        caption="Imagem de entrada",
        use_container_width=True
    )


# ============================================================
# 📝 PROMPT
# ============================================================

prompt = st.text_area(
    "📝 Movimento do personagem",
    value=(
        "O personagem começa a caminhar "
        "lentamente para frente. "
        "A câmera acompanha suavemente "
        "o personagem em um movimento "
        "cinematográfico. "
        "Manter o mesmo personagem, "
        "rosto, cabelo, roupa, aparência "
        "e identidade durante toda a cena. "
        "Movimento natural e estável."
    ),
    height=190
)


# ============================================================
# 🎬 GERAR
# ============================================================

if st.button(
    "🎬 GERAR VÍDEO",
    type="primary",
    use_container_width=True
):

    if imagem is None:

        st.warning(
            "⚠️ Escolha uma imagem primeiro."
        )

        st.stop()

    if not prompt.strip():

        st.warning(
            "⚠️ Digite o movimento do personagem."
        )

        st.stop()

    try:

        # ----------------------------------------------------
        # 1 — UPLOAD
        # ----------------------------------------------------

        with st.spinner(
            "📤 Enviando imagem..."
        ):

            file_path = enviar_imagem(
                imagem.getvalue(),
                imagem.name
            )

        st.success(
            "✅ Imagem enviada para o Magic Hour."
        )

        st.caption(
            f"Arquivo: {file_path}"
        )

        # ----------------------------------------------------
        # 2 — CRIAR VÍDEO
        # ----------------------------------------------------

        with st.spinner(
            "🎬 Criando projeto de vídeo..."
        ):

            projeto_id, resposta_inicial = criar_video(
                file_path,
                prompt
            )

        st.success(
            "🎬 Projeto criado!"
        )

        st.caption(
            f"ID: {projeto_id}"
        )

        # ----------------------------------------------------
        # 3 — PROCESSAMENTO
        # ----------------------------------------------------

        barra = st.progress(0)

        ultimo_resultado = {}

        video_url = None

        for tentativa in range(60):

            time.sleep(5)

            ultimo_resultado = consultar_projeto(
                projeto_id
            )

            status = str(
                ultimo_resultado.get(
                    "status",
                    "processing"
                )
            ).lower()

            barra.progress(
                min(
                    (tentativa + 1) / 60,
                    1.0
                )
            )

            st.caption(
                f"⏳ Status: {status}"
            )

            video_url = encontrar_download(
                ultimo_resultado
            )

            if video_url:

                break

            if status in [
                "failed",
                "error",
                "cancelled"
            ]:

                raise RuntimeError(
                    "A geração falhou.\n\n"
                    f"{ultimo_resultado}"
                )

        # ----------------------------------------------------
        # 4 — VERIFICAR
        # ----------------------------------------------------

        if not video_url:

            raise RuntimeError(
                "O vídeo ainda não possui "
                "um link de download.\n\n"
                "Última resposta da API:\n"
                f"{ultimo_resultado}"
            )

        # ----------------------------------------------------
        # 5 — DOWNLOAD
        # ----------------------------------------------------

        with st.spinner(
            "⬇️ Baixando vídeo..."
        ):

            caminho_video = baixar_video(
                video_url
            )

        # ----------------------------------------------------
        # 6 — RESULTADO
        # ----------------------------------------------------

        st.success(
            "🎉 VÍDEO GERADO COM SUCESSO!"
        )

        st.video(
            caminho_video
        )

        st.caption(
            "🎥 Magic Hour • LTX 2.3"
        )

        st.download_button(
            "⬇️ Baixar vídeo",
            data=Path(
                caminho_video
            ).read_bytes(),
            file_name="video_magichour.mp4",
            mime="video/mp4",
            use_container_width=True
        )

    except Exception as erro:

        st.error(
            "❌ Erro ao gerar vídeo:"
        )

        st.code(
            str(erro)
        )
