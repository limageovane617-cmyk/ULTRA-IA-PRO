"""
Alex IA Ultra — Gerenciador de Vídeo

Motores:
1. Wan 2.2 14B FP8 — R3GM
2. Wan 2.2 14B I2V — Upsampler
3. LTX-2.3 — Hugging Face
4. Magic Hour — LTX-2.3

Sistema:
- Image-to-Video
- Fallback automático
- Detecção de quota ZeroGPU
- Pausa automática de motores indisponíveis
- Compatível com app.py
"""

from __future__ import annotations

import os
import re
import time
import random
from pathlib import Path
from typing import Any, Optional

import requests
import streamlit as st

try:
    from gradio_client import Client, handle_file
except Exception:
    Client = None
    handle_file = None


# ============================================================
# CONFIGURAÇÃO
# ============================================================

NOME_MODULO = "Alex IA Ultra — Gerenciador de Vídeo"

DURACAO_PADRAO = 5.0

R3GM_SPACE = "r3gm/wan2-2-fp8da-aoti-preview"

UPSAMPLER_SPACE = (
    "Upsampler/wan-2-2-14b-image-to-video"
)

LTX_HF_SPACE = (
    "https://lightricks-ltx-2-3.hf.space"
)

MAGIC_HOUR_BASE_URL = (
    "https://api.magichour.ai/v1"
)

MAGIC_HOUR_MODELO = "ltx-2.3"
MAGIC_HOUR_RESOLUCAO = "480p"
MAGIC_HOUR_DURACAO = 5


CAMERAS = [
    "Sony FX5",
    "Sony FX6",
    "Canon EOS C80",
    "ARRI Alexa Mini LF",
]


PROPORCOES = [
    "1:1",
    "16:9",
    "9:16",
]


MOTORES_VIDEO = [
    "Wan 2.2 — R3GM",
    "Wan 2.2 — Upsampler",
    "LTX-2.3 — Hugging Face",
    "Magic Hour — LTX-2.3",
]


# ============================================================
# PASTA DE SAÍDA
# ============================================================

PASTA = Path("videos_gerados")

PASTA.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONTROLE DE MOTORES
# ============================================================

# Quando um motor dá erro de quota, ele fica pausado.
#
# Isso evita que a Ultra tente o mesmo motor novamente
# em todas as solicitações.
#
# O tempo pode ser ajustado.
#
PAUSA_PADRAO_MINUTOS = 30

PAUSA_QUOTA_MINUTOS = 30

PAUSA_AUTORIZACAO_MINUTOS = 60

PAUSA_ERRO_TEMPORARIO_MINUTOS = 10


def _estado_motores():

    if "video_motores_bloqueados" not in st.session_state:

        st.session_state.video_motores_bloqueados = {}

    return st.session_state.video_motores_bloqueados


def _pausar_motor(
    nome: str,
    minutos: int,
    motivo: str
):

    estado = _estado_motores()

    estado[nome] = {
        "ate": time.time() + (
            minutos * 60
        ),
        "motivo": motivo,
    }


def _motor_pausado(nome: str) -> bool:

    estado = _estado_motores()

    dados = estado.get(nome)

    if not dados:
        return False

    ate = dados.get("ate", 0)

    if time.time() >= ate:

        estado.pop(
            nome,
            None
        )

        return False

    return True


def _motivo_pausa(nome: str) -> str:

    estado = _estado_motores()

    dados = estado.get(nome)

    if not dados:
        return ""

    return str(
        dados.get(
            "motivo",
            ""
        )
    )


def _tempo_restante(nome: str) -> int:

    estado = _estado_motores()

    dados = estado.get(nome)

    if not dados:
        return 0

    restante = (
        dados.get("ate", 0)
        - time.time()
    )

    return max(
        0,
        int(restante)
    )


# ============================================================
# SECRETS
# ============================================================

def _secret(nome: str) -> str:

    try:

        valor = st.secrets.get(
            nome,
            ""
        )

    except Exception:

        valor = ""

    if not valor:

        valor = os.environ.get(
            nome,
            ""
        )

    return str(
        valor or ""
    ).strip()


def obter_api_key_magichour() -> str:

    return _secret(
        "MAGIC_HOUR_API_KEY"
    )


def obter_token_replicate() -> str:

    return _secret(
        "REPLICATE_API_TOKEN"
    )


def headers_magichour() -> dict:

    chave = (
        obter_api_key_magichour()
    )

    if not chave:

        raise RuntimeError(
            "MAGIC_HOUR_API_KEY não foi encontrada."
        )

    return {
        "Authorization":
            f"Bearer {chave}",

        "Accept":
            "application/json",

        "Content-Type":
            "application/json",
    }


# ============================================================
# UTILIDADES
# ============================================================

def _nome_saida(
    prefixo: str
) -> Path:

    return PASTA / (
        f"{prefixo}_"
        f"{int(time.time() * 1000)}.mp4"
    )


def _extensao_imagem(
    nome: str
) -> str:

    ext = (
        Path(nome)
        .suffix
        .lower()
    )

    if ext not in [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    ]:

        return ".jpg"

    return ext


def _salvar_imagem_temp(
    imagem_bytes: bytes,
    nome: str,
    prefixo: str
) -> Path:

    extensao = _extensao_imagem(
        nome
    )

    caminho = (
        PASTA
        /
        (
            f"{prefixo}_"
            f"{int(time.time() * 1000)}"
            f"{extensao}"
        )
    )

    caminho.write_bytes(
        imagem_bytes
    )

    return caminho


# ============================================================
# PROMPT
# ============================================================

def montar_prompt(
    movimento: str,
    camera: str = "Sony FX6"
) -> str:

    movimento = (
        movimento or ""
    ).strip()

    return f"""
Animate the provided reference image into a realistic
cinematic image-to-video sequence.

MAIN MOTION:
{movimento}

CAMERA:
{camera}

CHARACTER CONSISTENCY IS EXTREMELY IMPORTANT.

Keep exactly the same person/character from the input image.

Preserve:
- exact face
- facial identity
- hairstyle
- hair color
- clothing
- clothing colors
- body proportions
- accessories
- skin tone
- character identity
- environment whenever possible

The character must remain the same throughout the entire clip.

Do NOT:
- create another person
- change the face
- change the hairstyle
- change the clothes
- change the body
- duplicate the person
- create extra limbs
- change the character identity
- add another person

Only animate the requested movement.

The movement should be smooth, natural and physically plausible.

Maintain temporal consistency from the first frame to the last frame.

Use realistic cinematic lighting and natural motion.

Camera movement:
subtle and cinematic.

Do not add subtitles.
Do not add text.
Do not add logos.
Do not add watermarks.
""".strip()


def montar_negative_prompt() -> str:

    return (
        "static image, frozen character, "
        "blurry, low quality, distorted face, "
        "different person, different face, "
        "different clothes, changed hairstyle, "
        "duplicate person, duplicate body, "
        "extra person, extra arms, extra legs, "
        "extra fingers, deformed hands, "
        "bad anatomy, warped face, "
        "flickering, morphing, identity change, "
        "text, subtitles, watermark, logo"
    )


# ============================================================
# EXTRAIR VÍDEO
# ============================================================

def _extrair_video_gradio(
    resultado: Any
) -> Optional[str]:

    if resultado is None:

        return None

    if isinstance(
        resultado,
        str
    ):

        valor = resultado.strip()

        if not valor:

            return None

        if (
            valor.startswith(
                "http://"
            )
            or
            valor.startswith(
                "https://"
            )
            or
            valor.lower().endswith(
                ".mp4"
            )
        ):

            return valor

        return None

    if isinstance(
        resultado,
        dict
    ):

        for chave in [
            "video",
            "output",
            "path",
            "url",
            "video_path",
            "file",
            "file_path"
        ]:

            valor = resultado.get(
                chave
            )

            encontrado = (
                _extrair_video_gradio(
                    valor
                )
            )

            if encontrado:

                return encontrado

        return None

    if isinstance(
        resultado,
        (list, tuple)
    ):

        for item in resultado:

            encontrado = (
                _extrair_video_gradio(
                    item
                )
            )

            if encontrado:

                return encontrado

    return None


# ============================================================
# SALVAR VÍDEO
# ============================================================

def _salvar_video_gradio(
    origem: str,
    destino: Path
) -> str:

    if not origem:

        raise RuntimeError(
            "Origem do vídeo está vazia."
        )

    origem = str(
        origem
    )

    if Path(origem).exists():

        destino.write_bytes(
            Path(origem).read_bytes()
        )

    elif origem.startswith(
        (
            "http://",
            "https://"
        )
    ):

        resposta = requests.get(
            origem,
            timeout=300
        )

        resposta.raise_for_status()

        destino.write_bytes(
            resposta.content
        )

    else:

        raise RuntimeError(
            f"Vídeo não acessível: {origem}"
        )

    if (
        not destino.exists()
        or destino.stat().st_size <= 0
    ):

        raise RuntimeError(
            "O vídeo retornado está vazio."
        )

    return str(
        destino
    )


# ============================================================
# DETECTAR QUOTA
# ============================================================

def _erro_e_quota(
    erro: Exception | str
) -> bool:

    texto = str(
        erro
    ).lower()

    palavras = [
        "zerogpu",
        "quota",
        "exceeded",
        "rate limit",
        "too many requests",
        "try again in",
        "requested vs.",
        "daily limit",
    ]

    return any(
        palavra in texto
        for palavra in palavras
    )


def _extrair_horas_quota(
    texto: str
) -> Optional[int]:

    texto = str(
        texto
    )

    encontrados = re.findall(
        r"try again in\s+(\d+):(\d+):(\d+)",
        texto,
        flags=re.IGNORECASE
    )

    if not encontrados:

        return None

    horas, minutos, segundos = (
        encontrados[0]
    )

    total_segundos = (
        int(horas) * 3600
        +
        int(minutos) * 60
        +
        int(segundos)
    )

    return max(
        1,
        int(
            total_segundos / 60
        )
        + 1
    )


def _registrar_erro_motor(
    nome: str,
    erro: Exception | str
):

    texto = str(
        erro
    )

    if _erro_e_quota(
        texto
    ):

        minutos = (
            _extrair_horas_quota(
                texto
            )
        )

        if minutos is None:

            minutos = (
                PAUSA_QUOTA_MINUTOS
            )

        _pausar_motor(
            nome,
            minutos,
            texto
        )

        return

    texto_lower = texto.lower()

    if (
        "401" in texto_lower
        or
        "unauthorized" in texto_lower
        or
        "api key" in texto_lower
        or
        "authentication" in texto_lower
    ):

        _pausar_motor(
            nome,
            PAUSA_AUTORIZACAO_MINUTOS,
            texto
        )

        return

    if (
        "timeout" in texto_lower
        or
        "temporarily" in texto_lower
        or
        "503" in texto_lower
        or
        "502" in texto_lower
        or
        "500" in texto_lower
    ):

        _pausar_motor(
            nome,
            PAUSA_ERRO_TEMPORARIO_MINUTOS,
            texto
        )


# ============================================================
# MOTOR 1
# WAN 2.2 — R3GM
# ============================================================

def gerar_r3gm(
    imagem_bytes: bytes,
    nome_imagem: str,
    movimento: str,
    camera: str = "Sony FX6",
    duracao: float = 5.0
) -> dict:

    nome_motor = (
        "Wan 2.2 — R3GM"
    )

    if _motor_pausado(
        nome_motor
    ):

        raise RuntimeError(
            "Motor pausado temporariamente: "
            +
            _motivo_pausa(
                nome_motor
            )
        )

    if Client is None:

        raise RuntimeError(
            "gradio_client não está instalado."
        )

    if handle_file is None:

        raise RuntimeError(
            "handle_file não está disponível."
        )

    if not imagem_bytes:

        raise ValueError(
            "O R3GM precisa de uma imagem."
        )

    entrada = _salvar_imagem_temp(
        imagem_bytes,
        nome_imagem,
        "entrada_r3gm"
    )

    prompt = montar_prompt(
        movimento,
        camera
    )

    seed = random.randint(
        0,
        2147483647
    )

    duracao_segundos = max(
        0.5,
        min(
            float(duracao),
            5.0
        )
    )

    client = Client(
        R3GM_SPACE
    )

    try:

        resultado = client.predict(

            input_image=handle_file(
                str(entrada)
            ),

            last_image=None,

            prompt=prompt,

            steps=4,

            negative_prompt=(
                montar_negative_prompt()
            ),

            duration_seconds=(
                duracao_segundos
            ),

            guidance_scale=1.0,

            guidance_scale_2=1.0,

            seed=seed,

            randomize_seed=True,

            quality=5,

            scheduler=(
                "UniPCMultistep"
            ),

            flow_shift=3.0,

            # SOMENTE valores aceitos
            # pelo Space atual.
            frame_multiplier=16,

            video_component=True,

            api_name="/generate_video"
        )

    except Exception as erro:

        _registrar_erro_motor(
            nome_motor,
            erro
        )

        raise

    video = (
        _extrair_video_gradio(
            resultado
        )
    )

    if not video:

        raise RuntimeError(
            "R3GM não retornou vídeo."
        )

    destino = _nome_saida(
        "video_r3gm"
    )

    caminho = (
        _salvar_video_gradio(
            video,
            destino
        )
    )

    return {
        "sucesso": True,
        "motor": nome_motor,
        "video": caminho,
        "arquivo": caminho,
        "fallback": False,
        "erro": None,
    }


# ============================================================
# MOTOR 2
# WAN 2.2 — UPSAMPLER
# ============================================================

def gerar_upsampler(
    imagem_bytes: bytes,
    nome_imagem: str,
    movimento: str,
    camera: str = "Sony FX6",
    duracao: float = 5.0
) -> dict:

    nome_motor = (
        "Wan 2.2 — Upsampler"
    )

    if _motor_pausado(
        nome_motor
    ):

        raise RuntimeError(
            "Motor pausado temporariamente: "
            +
            _motivo_pausa(
                nome_motor
            )
        )

    if Client is None:

        raise RuntimeError(
            "gradio_client não está instalado."
        )

    if handle_file is None:

        raise RuntimeError(
            "handle_file não está disponível."
        )

    if not imagem_bytes:

        raise ValueError(
            "O Upsampler precisa de uma imagem."
        )

    entrada = _salvar_imagem_temp(
        imagem_bytes,
        nome_imagem,
        "entrada_upsampler"
    )

    prompt = montar_prompt(
        movimento,
        camera
    )

    duracao_segundos = max(
        0.5,
        min(
            float(duracao),
            5.0
        )
    )

    client = Client(
        UPSAMPLER_SPACE
    )

    try:

        # IMPORTANTE:
        #
        # O Upsampler da versão que você
        # estava usando rejeitou "last_image".
        #
        # Portanto não enviamos esse argumento.
        #
        resultado = client.predict(

            input_image=handle_file(
                str(entrada)
            ),

            prompt=prompt,

            steps=4,

            negative_prompt=(
                montar_negative_prompt()
            ),

            duration_seconds=(
                duracao_segundos
            ),

            guidance_scale=1.0,

            seed=random.randint(
                0,
                2147483647
            ),

            randomize_seed=True,

            api_name="/generate_video"
        )

    except Exception as erro:

        _registrar_erro_motor(
            nome_motor,
            erro
        )

        raise

    video = (
        _extrair_video_gradio(
            resultado
        )
    )

    if not video:

        raise RuntimeError(
            "Upsampler não retornou vídeo."
        )

    destino = _nome_saida(
        "video_upsampler"
    )

    caminho = (
        _salvar_video_gradio(
            video,
            destino
        )
    )

    return {
        "sucesso": True,
        "motor": nome_motor,
        "video": caminho,
        "arquivo": caminho,
        "fallback": True,
        "erro": None,
    }


# ============================================================
# MOTOR 3
# LTX 2.3 — HUGGING FACE
# ============================================================

def gerar_ltx_huggingface(
    prompt: str,
    duration: float = 5.0,
    height: int = 512,
    width: int = 512,
    imagem_bytes: Optional[bytes] = None,
    nome_imagem: str = "imagem.png"
) -> dict:

    nome_motor = (
        "LTX-2.3 — Hugging Face"
    )

    if _motor_pausado(
        nome_motor
    ):

        raise RuntimeError(
            "Motor pausado temporariamente: "
            +
            _motivo_pausa(
                nome_motor
            )
        )

    if Client is None:

        raise RuntimeError(
            "gradio_client não está instalado."
        )

    if not prompt:

        raise ValueError(
            "O prompt está vazio."
        )

    caminho_imagem = None

    if imagem_bytes:

        caminho_imagem = (
            _salvar_imagem_temp(
                imagem_bytes,
                nome_imagem,
                "entrada_ltx"
            )
        )

    client = Client(
        LTX_HF_SPACE
    )

    duracao_segundos = max(
        0.5,
        min(
            float(duration),
            5.0
        )
    )

    try:

        resultado = client.predict(

            input_image=(
                str(caminho_imagem)
                if caminho_imagem
                else None
            ),

            prompt=prompt.strip(),

            duration=(
                duracao_segundos
            ),

            enhance_prompt=True,

            seed=0,

            randomize_seed=True,

            height=int(height),

            width=int(width),

            api_name="/generate_video"
        )

    except Exception as erro:

        _registrar_erro_motor(
            nome_motor,
            erro
        )

        raise

    video = (
        _extrair_video_gradio(
            resultado
        )
    )

    if not video:

        raise RuntimeError(
            "LTX não retornou vídeo."
        )

    # O LTX pode devolver um arquivo
    # temporário do Gradio.
    destino = _nome_saida(
        "video_ltx"
    )

    caminho = (
        _salvar_video_gradio(
            video,
            destino
        )
    )

    return {
        "sucesso": True,
        "motor": nome_motor,
        "video": caminho,
        "arquivo": caminho,
        "fallback": True,
        "erro": None,
    }


# ============================================================
# MAGIC HOUR
# ============================================================

def obter_url_upload(
    extensao: str
):

    ext = (
        str(extensao)
        .lower()
        .replace(
            ".",
            ""
        )
    )

    resposta = requests.post(

        (
            f"{MAGIC_HOUR_BASE_URL}"
            "/files/upload-urls"
        ),

        headers=headers_magichour(),

        json={
            "items": [
                {
                    "type": "image",
                    "extension": ext,
                }
            ]
        },

        timeout=60
    )

    if resposta.status_code != 200:

        raise RuntimeError(
            "Magic Hour HTTP "
            f"{resposta.status_code}: "
            f"{resposta.text}"
        )

    dados = resposta.json()

    itens = (
        dados.get(
            "items"
        )
        or []
    )

    if not itens:

        raise RuntimeError(
            "Magic Hour não retornou upload."
        )

    item = itens[0]

    return (
        item["upload_url"],
        item["file_path"]
    )


def enviar_imagem_magichour(
    imagem_bytes: bytes,
    nome: str
) -> str:

    ext = (
        Path(nome)
        .suffix
        .lower()
        .replace(
            ".",
            ""
        )
        or "png"
    )

    upload_url, file_path = (
        obter_url_upload(
            ext
        )
    )

    resposta = requests.put(
        upload_url,
        data=imagem_bytes,
        timeout=120
    )

    if resposta.status_code not in [
        200,
        201,
        204
    ]:

        raise RuntimeError(
            "Falha no upload Magic Hour."
        )

    return file_path


def gerar_magichour(
    imagem_bytes: bytes,
    nome_arquivo: str,
    prompt: str
) -> dict:

    nome_motor = (
        "Magic Hour — LTX-2.3"
    )

    if _motor_pausado(
        nome_motor
    ):

        raise RuntimeError(
            "Motor pausado temporariamente: "
            +
            _motivo_pausa(
                nome_motor
            )
        )

    if not imagem_bytes:

        raise ValueError(
            "Magic Hour precisa de imagem."
        )

    file_path = (
        enviar_imagem_magichour(
            imagem_bytes,
            nome_arquivo
        )
    )

    dados = {

        "name":
            "Alex IA Ultra",

        "end_seconds":
            MAGIC_HOUR_DURACAO,

        "model":
            MAGIC_HOUR_MODELO,

        "resolution":
            MAGIC_HOUR_RESOLUCAO,

        "audio":
            False,

        "style": {
            "prompt":
                prompt
        },

        "assets": {
            "image_file_path":
                file_path
        }
    }

    try:

        resposta = requests.post(

            (
                f"{MAGIC_HOUR_BASE_URL}"
                "/image-to-video"
            ),

            headers=headers_magichour(),

            json=dados,

            timeout=120
        )

        if resposta.status_code not in [
            200,
            201,
            202
        ]:

            raise RuntimeError(
                "Magic Hour HTTP "
                f"{resposta.status_code}: "
                f"{resposta.text}"
            )

        resultado = (
            resposta.json()
        )

        projeto = resultado.get(
            "id"
        )

        if not projeto:

            raise RuntimeError(
                "Magic Hour não retornou ID."
            )

        inicio = time.time()

        while (
            time.time() - inicio
            < 300
        ):

            resposta = requests.get(

                (
                    f"{MAGIC_HOUR_BASE_URL}"
                    f"/video-projects/{projeto}"
                ),

                headers=headers_magichour(),

                timeout=60
            )

            if resposta.status_code == 200:

                dados_status = (
                    resposta.json()
                )

                url = (
                    encontrar_url_video(
                        dados_status
                    )
                )

                if url:

                    video = requests.get(
                        url,
                        timeout=180
                    )

                    video.raise_for_status()

                    caminho = (
                        _nome_saida(
                            "video_magichour"
                        )
                    )

                    caminho.write_bytes(
                        video.content
                    )

                    return {
                        "sucesso": True,
                        "motor":
                            nome_motor,
                        "video":
                            str(caminho),
                        "arquivo":
                            str(caminho),
                        "fallback":
                            True,
                        "erro":
                            None,
                    }

            time.sleep(5)

    except Exception as erro:

        _registrar_erro_motor(
            nome_motor,
            erro
        )

        raise

    raise RuntimeError(
        "Magic Hour demorou demais."
    )


def encontrar_url_video(
    dados: Any
) -> Optional[str]:

    if not isinstance(
        dados,
        dict
    ):

        return None

    for chave in [
        "video_url",
        "download_url",
        "output_url",
        "url"
    ]:

        valor = dados.get(
            chave
        )

        if (
            isinstance(
                valor,
                str
            )
            and
            valor.startswith(
                "http"
            )
        ):

            return valor

    # Procurar recursivamente
    # em respostas mais complexas.

    for valor in dados.values():

        if isinstance(
            valor,
            dict
        ):

            encontrado = (
                encontrar_url_video(
                    valor
                )
            )

            if encontrado:

                return encontrado

        elif isinstance(
            valor,
            list
        ):

            for item in valor:

                encontrado = (
                    encontrar_url_video(
                        item
                    )
                )

                if encontrado:

                    return encontrado

    return None


# ============================================================
# FALLBACK PRINCIPAL
# ============================================================

def gerar_video_automatico(
    prompt: Optional[str] = None,
    imagem_bytes: Optional[bytes] = None,
    nome_imagem: str = "imagem.png",
    duracao: float = 5.0,
    width: int = 512,
    height: int = 512,
    descricao: Optional[str] = None,
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
    **kwargs
) -> dict:

    texto = (
        prompt
        or descricao
        or ""
    ).strip()

    if not texto:

        return {
            "sucesso":
                False,

            "video":
                None,

            "motor":
                None,

            "erro":
                "O movimento está vazio.",

            "erros":
                [],
        }

    erros = []

    # ========================================================
    # R3GM
    # ========================================================

    if imagem_bytes:

        if not _motor_pausado(
            "Wan 2.2 — R3GM"
        ):

            try:

                return gerar_r3gm(

                    imagem_bytes,

                    nome_imagem,

                    texto,

                    camera,

                    duracao

                )

            except Exception as erro:

                erros.append(
                    "R3GM: "
                    + str(erro)
                )

        else:

            erros.append(
                "R3GM: motor pausado — "
                +
                _motivo_pausa(
                    "Wan 2.2 — R3GM"
                )
            )

    else:

        erros.append(
            "R3GM: precisa de imagem."
        )

    # ========================================================
    # UPSAMPLER
    # ========================================================

    if imagem_bytes:

        if not _motor_pausado(
            "Wan 2.2 — Upsampler"
        ):

            try:

                resultado = (
                    gerar_upsampler(

                        imagem_bytes,

                        nome_imagem,

                        texto,

                        camera,

                        duracao

                    )
                )

                resultado[
                    "erros_anteriores"
                ] = erros

                return resultado

            except Exception as erro:

                erros.append(
                    "Upsampler: "
                    + str(erro)
                )

        else:

            erros.append(
                "Upsampler: motor pausado — "
                +
                _motivo_pausa(
                    "Wan 2.2 — Upsampler"
                )
            )

    # ========================================================
    # MAGIC HOUR
    # ========================================================

    if imagem_bytes:

        if not _motor_pausado(
            "Magic Hour — LTX-2.3"
        ):

            chave = (
                obter_api_key_magichour()
            )

            if chave:

                try:

                    resultado = (
                        gerar_magichour(

                            imagem_bytes,

                            nome_imagem,

                            montar_prompt(
                                texto,
                                camera
                            )

                        )
                    )

                    resultado[
                        "erros_anteriores"
                    ] = erros

                    return resultado

                except Exception as erro:

                    erros.append(
                        "Magic Hour: "
                        + str(erro)
                    )

            else:

                erros.append(
                    "Magic Hour: "
                    "MAGIC_HOUR_API_KEY não configurada."
                )

        else:

            erros.append(
                "Magic Hour: motor pausado — "
                +
                _motivo_pausa(
                    "Magic Hour — LTX-2.3"
                )
            )

    # ========================================================
    # LTX
    # ========================================================

    if not _motor_pausado(
        "LTX-2.3 — Hugging Face"
    ):

        try:

            resultado = (
                gerar_ltx_huggingface(

                    montar_prompt(
                        texto,
                        camera
                    ),

                    duration=min(
                        float(duracao),
                        5.0
                    ),

                    height=height,

                    width=width,

                    imagem_bytes=imagem_bytes,

                    nome_imagem=nome_imagem

                )
            )

            resultado[
                "erros_anteriores"
            ] = erros

            return resultado

        except Exception as erro:

            erros.append(
                "LTX-2.3: "
                + str(erro)
            )

    else:

        erros.append(
            "LTX-2.3: motor pausado — "
            +
            _motivo_pausa(
                "LTX-2.3 — Hugging Face"
            )
        )

    # ========================================================
    # NENHUM MOTOR
    # ========================================================

    return {

        "sucesso":
            False,

        "video":
            None,

        "motor":
            None,

        "erro":
            (
                "❌ NENHUM MOTOR DE VÍDEO "
                "CONSEGUIU GERAR O VÍDEO.\n\n"
                +
                "\n\n".join(
                    erros
                )
            ),

        "erros":
            erros,
    }


# ============================================================
# COMPATIBILIDADE COM APP.PY
# ============================================================

def gerar_video(
    prompt: Optional[str] = None,
    imagem_bytes: Optional[bytes] = None,
    nome_imagem: str = "imagem.png",
    duracao: float = 5.0,
    width: int = 512,
    height: int = 512,
    descricao: Optional[str] = None,
    **kwargs
) -> dict:

    return gerar_video_automatico(

        prompt=prompt,

        imagem_bytes=imagem_bytes,

        nome_imagem=nome_imagem,

        duracao=duracao,

        width=width,

        height=height,

        descricao=descricao,

        **kwargs
    )


def gerar_video_texto(
    prompt: str,
    duracao: float = 5.0,
    **kwargs
) -> dict:

    return gerar_ltx_huggingface(

        montar_prompt(
            prompt
        ),

        duration=duracao,

        **kwargs
    )


def gerar_video_imagem(
    imagem_bytes: bytes,
    nome_imagem: str,
    prompt: str,
    duracao: float = 5.0,
    **kwargs
) -> dict:

    return gerar_video(

        prompt,

        imagem_bytes=imagem_bytes,

        nome_imagem=nome_imagem,

        duracao=duracao,

        **kwargs
    )


def gerar(
    prompt: str,
    **kwargs
) -> dict:

    return gerar_video(
        prompt,
        **kwargs
    )


def gerar_video_fallback(
    prompt: str,
    **kwargs
) -> Optional[str]:

    resultado = gerar_video(
        prompt,
        **kwargs
    )

    return (
        resultado.get(
            "video"
        )
        or
        resultado.get(
            "arquivo"
        )
    )


# ============================================================
# CONFIGURAÇÃO DO APP.PY
# ============================================================

def mostrar_configuracao_video():

    st.subheader(
        "🎬 Configuração de Vídeo"
    )

    camera_video = st.selectbox(

        "📷 Câmera",

        CAMERAS,

        index=1,

        key="video_camera"

    )

    proporcao_video = st.selectbox(

        "📐 Proporção",

        PROPORCOES,

        index=1,

        key="video_proporcao"

    )

    duracao_video = st.number_input(

        "⏱️ Duração do vídeo",

        min_value=0.5,

        max_value=5.0,

        value=5.0,

        step=0.5,

        key="video_duracao"

    )

    st.write(
        "**🎥 Motores disponíveis:**"
    )

    for motor in MOTORES_VIDEO:

        if _motor_pausado(
            motor
        ):

            restante = (
                _tempo_restante(
                    motor
                )
            )

            minutos = (
                restante // 60
            )

            st.write(
                f"• {motor} "
                f"⏸️ ({minutos} min)"
            )

        else:

            st.write(
                f"• {motor} ✅"
            )

    return (
        camera_video,
        proporcao_video,
        duracao_video
    )


# ============================================================
# STATUS
# ============================================================

def verificar_magic_hour():

    try:

        chave = (
            obter_api_key_magichour()
        )

        if chave:

            return (
                True,
                "✅ MAGIC_HOUR_API_KEY encontrada."
            )

        return (
            False,
            "❌ MAGIC_HOUR_API_KEY não encontrada."
        )

    except Exception as erro:

        return (
            False,
            f"❌ Erro: {erro}"
        )


def status_video() -> dict:

    status = {}

    for motor in MOTORES_VIDEO:

        status[motor] = {
            "disponivel":
                not _motor_pausado(
                    motor
                ),

            "tempo_restante":
                _tempo_restante(
                    motor
                ),

            "motivo":
                _motivo_pausa(
                    motor
                )
        }

    status[
        "gradio_client"
    ] = (
        Client is not None
    )

    status[
        "magic_hour"
    ] = bool(
        obter_api_key_magichour()
    )

    status[
        "replicate"
    ] = bool(
        obter_token_replicate()
    )

    status[
        "ltx"
    ] = LTX_HF_SPACE

    return status


# ============================================================
# LIMPAR PAUSAS
# ============================================================

def limpar_bloqueios_video():

    st.session_state[
        "video_motores_bloqueados"
    ] = {}


# ============================================================
# EXPORTAÇÕES
# ============================================================

__all__ = [

    "NOME_MODULO",

    "MOTORES_VIDEO",

    "CAMERAS",

    "PROPORCOES",

    "DURACAO_PADRAO",

    "gerar_video",

    "gerar_video_automatico",

    "gerar_video_fallback",

    "gerar",

    "gerar_video_texto",

    "gerar_video_imagem",

    "gerar_r3gm",

    "gerar_upsampler",

    "gerar_ltx_huggingface",

    "gerar_magichour",

    "mostrar_configuracao_video",

    "verificar_magic_hour",

    "obter_api_key_magichour",

    "obter_token_replicate",

    "status_video",

    "limpar_bloqueios_video",
    ]
