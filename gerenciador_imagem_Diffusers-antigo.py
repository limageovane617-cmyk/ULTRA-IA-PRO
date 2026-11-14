# ============================================================
# ALEX IA ULTRA — GERENCIADOR DE IMAGENS
# BACKEND LOCAL: DIFFUSERS + GPU CUDA (SEM API DE INFERÊNCIA)
#
# Configuração:
#   ALEX_IMAGE_MODEL_PATH=/caminho/para/modelo/diffusers
# Opcional:
#   ALEX_IMAGE_DEVICE=auto | cuda:0 | cuda:1 | cpu
#   ALEX_IMAGE_WIDTH=768
#   ALEX_IMAGE_HEIGHT=768
#   ALEX_IMAGE_STEPS=25
#   ALEX_IMAGE_GUIDANCE=7.5
#
# O diretório do modelo deve conter um pipeline Diffusers completo.
# Este módulo não baixa nem chama serviços de geração remotos.
# ============================================================

import os
import threading
import uuid
from pathlib import Path

import streamlit as st
import torch
from PIL import Image

MOTOR_IMAGEM = "ALEX IMAGE ENGINE — Diffusers local"
TIMEOUT_IMAGEM = 600

_PIPELINES = {}
_PIPELINE_LOCK = threading.Lock()
_GPU_LOCKS = {}
_GPU_LOCKS_LOCK = threading.Lock()


def _modelo_path():
    valor = os.environ.get("ALEX_IMAGE_MODEL_PATH", "").strip()
    if not valor:
        raise RuntimeError(
            "ALEX_IMAGE_MODEL_PATH não foi configurado. "
            "Informe a pasta local de um modelo Diffusers completo. "
            "Nenhum serviço remoto será usado como fallback."
        )
    caminho = Path(valor).expanduser()
    if not caminho.exists() or not caminho.is_dir():
        raise RuntimeError(f"Pasta do modelo não encontrada: {caminho}")
    return str(caminho)


def _dispositivos():
    preferencia = os.environ.get("ALEX_IMAGE_DEVICE", "auto").strip().lower()
    if preferencia == "cpu":
        return ["cpu"]
    if preferencia.startswith("cuda:"):
        if not torch.cuda.is_available():
            raise RuntimeError("Foi solicitado CUDA, mas CUDA não está disponível.")
        indice = int(preferencia.split(":", 1)[1])
        if indice >= torch.cuda.device_count():
            raise RuntimeError(f"GPU {indice} não está disponível.")
        return [f"cuda:{indice}"]
    if torch.cuda.is_available():
        return [f"cuda:{i}" for i in range(torch.cuda.device_count())]
    raise RuntimeError(
        "Nenhuma GPU CUDA disponível. O backend local foi configurado "
        "para não recorrer a serviços externos."
    )


def _lock_gpu(device):
    with _GPU_LOCKS_LOCK:
        return _GPU_LOCKS.setdefault(device, threading.Lock())


def _carregar_pipeline(device):
    chave = (device, _modelo_path())
    with _PIPELINE_LOCK:
        if chave in _PIPELINES:
            return _PIPELINES[chave]

        try:
            from diffusers import StableDiffusionPipeline, DEISMultistepScheduler
        except ImportError as erro:
            raise RuntimeError(
                "Diffusers não está instalado. Instale diffusers, transformers, "
                "accelerate e safetensors no ambiente local."
            ) from erro

        dtype = torch.float16 if device.startswith("cuda") else torch.float32
        try:
            pipe = StableDiffusionPipeline.from_pretrained(
                chave[1],
                torch_dtype=dtype,
                local_files_only=True,
                use_safetensors=True,
            )
            pipe.scheduler = DEISMultistepScheduler.from_config(
                pipe.scheduler.config
            )
            pipe = pipe.to(device)
            pipe.set_progress_bar_config(disable=True)

            # Reduz uso de VRAM em GPUs como a Tesla T4.
            try:
                pipe.enable_attention_slicing()
            except Exception:
                pass
            try:
                pipe.enable_vae_slicing()
            except Exception:
                pass

            _PIPELINES[chave] = pipe
            return pipe
        except Exception as erro:
            raise RuntimeError(
                f"Não foi possível carregar o modelo local em {device}: {erro}"
            ) from erro


def obter_token_huggingface():
    # Mantido apenas por compatibilidade com integrações antigas.
    # O backend local não usa token para inferência.
    return None


def obter_pasta_imagens():
    pasta = Path(os.environ.get(
        "ALEX_IMAGE_OUTPUT_DIR",
        str(Path.cwd() / "alex_imagens")
    )).expanduser()
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def guardar_ultima_imagem(imagem, prompt, caminho=None, motor=None):
    try:
        st.session_state.ultima_imagem = imagem
        st.session_state.ultima_imagem_caminho = caminho
        st.session_state.ultimo_prompt_imagem = prompt
        st.session_state.ultimo_motor_imagem = motor or MOTOR_IMAGEM
        return True
    except Exception:
        return False


def gerar_imagem_local(prompt):
    if not prompt or not prompt.strip():
        raise ValueError("O prompt da imagem está vazio.")

    dispositivos = _dispositivos()
    largura = int(os.environ.get("ALEX_IMAGE_WIDTH", "768"))
    altura = int(os.environ.get("ALEX_IMAGE_HEIGHT", "768"))
    passos = int(os.environ.get("ALEX_IMAGE_STEPS", "25"))
    guidance = float(os.environ.get("ALEX_IMAGE_GUIDANCE", "7.5"))

    if largura < 256 or altura < 256 or largura % 8 or altura % 8:
        raise ValueError("Largura e altura devem ser >=256 e múltiplas de 8.")
    if not 1 <= passos <= 100:
        raise ValueError("ALEX_IMAGE_STEPS deve estar entre 1 e 100.")

    erros = []
    # Distribui chamadas entre as GPUs; cada pipeline é protegido por lock.
    for tentativa in range(len(dispositivos)):
        device = dispositivos[tentativa]
        lock = _lock_gpu(device)
        try:
            with lock:
                pipe = _carregar_pipeline(device)
                gerador = torch.Generator(device=device).manual_seed(
                    int.from_bytes(os.urandom(4), "big")
                )
                with torch.inference_mode():
                    resultado = pipe(
                        prompt=prompt.strip(),
                        width=largura,
                        height=altura,
                        num_inference_steps=passos,
                        guidance_scale=guidance,
                        generator=gerador,
                    )
                imagem = resultado.images[0]
                destino = obter_pasta_imagens() / f"alex_{uuid.uuid4().hex}.png"
                imagem.save(destino, format="PNG")
                with Image.open(destino) as validacao:
                    validacao.verify()
                return str(destino)
        except Exception as erro:
            erros.append(f"{device}: {erro}")
            if device.startswith("cuda"):
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass

    raise RuntimeError("Falha em todos os dispositivos locais: " + " | ".join(erros))


# Nome antigo mantido para não quebrar imports existentes.
def gerar_imagem_zimage(prompt):
    return gerar_imagem_local(prompt)


def gerar_imagem(prompt):
    if not prompt or not prompt.strip():
        return None, "❌ A descrição da imagem está vazia."
    try:
        caminho = gerar_imagem_local(prompt)
        guardar_ultima_imagem(
            imagem=caminho,
            prompt=prompt.strip(),
            caminho=caminho,
            motor=MOTOR_IMAGEM,
        )
        return caminho, "✅ Imagem gerada e validada pelo motor local da Alex."
    except Exception as erro:
        mensagem = f"❌ Falha no motor local de imagens: {erro}"
        print(mensagem)
        return None, mensagem


def mostrar_imagem(prompt):
    with st.spinner("🎨 Alex está gerando a imagem no motor local..."):
        caminho, mensagem = gerar_imagem(prompt)

    if not caminho or not Path(caminho).is_file():
        st.error(mensagem)
        return False

    try:
        with Image.open(caminho) as imagem:
            imagem.verify()
        st.image(
            caminho,
            caption="🖼️ Imagem gerada pelo ALEX IMAGE ENGINE local",
            use_container_width=True,
        )
    except Exception as erro:
        st.error(f"❌ A imagem não pôde ser exibida: {erro}")
        return False

    st.success(mensagem)
    st.caption(f"Motor utilizado: {MOTOR_IMAGEM}")
    return True


def obter_ultima_imagem():
    return st.session_state.get("ultima_imagem")


def obter_caminho_ultima_imagem():
    return st.session_state.get("ultima_imagem_caminho")


def obter_prompt_ultima_imagem():
    return st.session_state.get("ultimo_prompt_imagem", "")


def obter_motor_ultima_imagem():
    return st.session_state.get("ultimo_motor_imagem", "")


def limpar_ultima_imagem():
    for chave in (
        "ultima_imagem",
        "ultima_imagem_caminho",
        "ultimo_prompt_imagem",
        "ultimo_motor_imagem",
    ):
        st.session_state.pop(chave, None)


def executar_teste():
    st.title("🖼️ ALEX IMAGE ENGINE — TESTE LOCAL")
    st.caption("Inferência local com Diffusers; sem API externa de geração.")
    st.info(
        "Configure ALEX_IMAGE_MODEL_PATH apontando para a pasta local "
        "do modelo Diffusers antes de gerar."
    )
    prompt = st.text_input(
        "Descreva a imagem:",
        value="Um beija-flor voando com as asas abertas",
    )
    if st.button("🎨 Gerar imagem", use_container_width=True):
        if not prompt.strip():
            st.warning("Digite uma descrição para gerar a imagem.")
        else:
            mostrar_imagem(prompt)


if __name__ == "__main__":
    executar_teste()
