# ============================================================
# ALEX IA ULTRA — GERENCIADOR DE IMAGENS
# BACKEND LOCAL: DIFFUSERS + CUDA MULTI-GPU
#
# Variaveis:
#   ALEX_IMAGE_MODEL_PATH=/caminho/modelo-diffusers
#   ALEX_IMAGE_DEVICE=auto | cuda:0 | cuda:1 | cpu
#   ALEX_IMAGE_WIDTH=768
#   ALEX_IMAGE_HEIGHT=768
#   ALEX_IMAGE_STEPS=25
#   ALEX_IMAGE_GUIDANCE=7.5
#   ALEX_IMAGE_OUTPUT_DIR=./alex_imagens
#   ALEX_IMAGE_FP16_VARIANT=auto | true | false
#
# O modulo nao baixa modelos e nao usa APIs remotas para inferencia.
# ============================================================

import os
import threading
import uuid
from pathlib import Path

import torch
from PIL import Image

try:
    import streamlit as st
except ImportError:
    st = None

MOTOR_IMAGEM = "ALEX IMAGE ENGINE — Diffusers local multi-GPU"
TIMEOUT_IMAGEM = 600

_PIPELINES = {}
_PIPELINE_LOCK = threading.Lock()
_GPU_LOCKS = {}
_GPU_LOCKS_LOCK = threading.Lock()
_DEVICE_STATE_LOCK = threading.Lock()
_NEXT_DEVICE = 0


def _modelo_path():
    valor = os.environ.get("ALEX_IMAGE_MODEL_PATH", "").strip()
    if not valor:
        raise RuntimeError(
            "ALEX_IMAGE_MODEL_PATH nao foi configurado. "
            "Aponte para a pasta local completa do modelo Diffusers."
        )
    caminho = Path(valor).expanduser()
    if not caminho.is_dir() or not (caminho / "model_index.json").is_file():
        raise RuntimeError(
            f"Modelo Diffusers invalido ou incompleto: {caminho}"
        )
    return str(caminho.resolve())


def _dispositivos():
    preferencia = os.environ.get("ALEX_IMAGE_DEVICE", "auto").strip().lower()
    if preferencia == "cpu":
        return ["cpu"]
    if preferencia.startswith("cuda:"):
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA foi solicitada, mas nao esta disponivel.")
        try:
            indice = int(preferencia.split(":", 1)[1])
        except (ValueError, IndexError) as erro:
            raise ValueError("ALEX_IMAGE_DEVICE deve ser cuda:N.") from erro
        if indice < 0 or indice >= torch.cuda.device_count():
            raise RuntimeError(f"GPU {indice} nao esta disponivel.")
        return [f"cuda:{indice}"]
    if preferencia != "auto":
        raise ValueError("ALEX_IMAGE_DEVICE deve ser auto, cuda:N ou cpu.")
    if torch.cuda.is_available():
        return [f"cuda:{i}" for i in range(torch.cuda.device_count())]
    return ["cpu"]


def _proximo_dispositivo(dispositivos):
    """Round-robin entre dispositivos; chamadas concorrentes nao disputam o contador."""
    global _NEXT_DEVICE
    with _DEVICE_STATE_LOCK:
        indice = _NEXT_DEVICE % len(dispositivos)
        _NEXT_DEVICE += 1
    return dispositivos[indice]


def _lock_gpu(device):
    with _GPU_LOCKS_LOCK:
        return _GPU_LOCKS.setdefault(device, threading.Lock())


def _carregar_pipeline(device):
    caminho = _modelo_path()
    chave = (device, caminho)

    with _PIPELINE_LOCK:
        if chave in _PIPELINES:
            return _PIPELINES[chave]

        try:
            from diffusers import StableDiffusionPipeline
        except ImportError as erro:
            raise RuntimeError(
                "Diffusers nao instalado. Instale diffusers, transformers, "
                "accelerate e safetensors."
            ) from erro

        dtype = torch.float16 if device.startswith("cuda") else torch.float32
        variant_cfg = os.environ.get("ALEX_IMAGE_FP16_VARIANT", "auto").lower()

        kwargs = {
            "torch_dtype": dtype,
            "local_files_only": True,
            "use_safetensors": True,
        }

        # Usa pesos fp16 dedicados quando disponiveis. Se o repositorio local
        # nao tiver essa variante, tenta o carregamento padrao em seguida.
        if device.startswith("cuda") and variant_cfg != "false":
            try:
                pipe = StableDiffusionPipeline.from_pretrained(
                    caminho, variant="fp16", **kwargs
                )
            except Exception:
                if variant_cfg == "true":
                    raise
                pipe = StableDiffusionPipeline.from_pretrained(
                    caminho, **kwargs
                )
        else:
            pipe = StableDiffusionPipeline.from_pretrained(
                caminho, **kwargs
            )

        pipe = pipe.to(device)
        pipe.set_progress_bar_config(disable=True)

        # Ativacoes conservadoras para placas com VRAM limitada.
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


def descarregar_pipelines():
    """Libera pipelines mantidos em cache. Chame somente sem geracoes em andamento."""
    with _PIPELINE_LOCK:
        _PIPELINES.clear()
    if torch.cuda.is_available():
        for indice in range(torch.cuda.device_count()):
            with torch.cuda.device(indice):
                torch.cuda.empty_cache()
    return True


def diagnostico_motor():
    dispositivos = _dispositivos()
    dados = {
        "motor": MOTOR_IMAGEM,
        "modelo": _modelo_path(),
        "cuda_disponivel": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "dispositivos": dispositivos,
        "pipelines_cache": [],
    }
    with _PIPELINE_LOCK:
        for (device, caminho), pipe in _PIPELINES.items():
            dados["pipelines_cache"].append({
                "device": device,
                "modelo": caminho,
                "classe": type(pipe).__name__,
                "dtype": str(pipe.unet.dtype),
            })
    return dados


def obter_token_huggingface():
    # Compatibilidade com integracoes antigas; inferencia local nao usa token.
    return None


def obter_pasta_imagens():
    pasta = Path(os.environ.get(
        "ALEX_IMAGE_OUTPUT_DIR",
        str(Path.cwd() / "alex_imagens")
    )).expanduser()
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _guardar_estado(imagem, prompt, caminho=None, motor=None):
    if st is None:
        return False
    try:
        st.session_state.ultima_imagem = imagem
        st.session_state.ultima_imagem_caminho = caminho
        st.session_state.ultimo_prompt_imagem = prompt
        st.session_state.ultimo_motor_imagem = motor or MOTOR_IMAGEM
        return True
    except Exception:
        return False


def guardar_ultima_imagem(imagem, prompt, caminho=None, motor=None):
    return _guardar_estado(imagem, prompt, caminho, motor)


def gerar_imagem_local(prompt):
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("O prompt da imagem esta vazio.")

    dispositivos = _dispositivos()
    largura = int(os.environ.get("ALEX_IMAGE_WIDTH", "768"))
    altura = int(os.environ.get("ALEX_IMAGE_HEIGHT", "768"))
    passos = int(os.environ.get("ALEX_IMAGE_STEPS", "25"))
    guidance = float(os.environ.get("ALEX_IMAGE_GUIDANCE", "7.5"))

    if largura < 256 or altura < 256 or largura % 8 or altura % 8:
        raise ValueError("Largura e altura devem ser >=256 e multiplas de 8.")
    if not 1 <= passos <= 100:
        raise ValueError("ALEX_IMAGE_STEPS deve estar entre 1 e 100.")
    if not 0 <= guidance <= 30:
        raise ValueError("ALEX_IMAGE_GUIDANCE deve estar entre 0 e 30.")

    erros = []
    # Comeca em GPUs alternadas. Em caso de erro, tenta os demais dispositivos.
    primeiro = _proximo_dispositivo(dispositivos)
    ordem = [primeiro] + [d for d in dispositivos if d != primeiro]

    for device in ordem:
        try:
            with _lock_gpu(device):
                pipe = _carregar_pipeline(device)
                seed = int.from_bytes(os.urandom(4), "big")
                generator = torch.Generator(device=device).manual_seed(seed)

                with torch.inference_mode():
                    resultado = pipe(
                        prompt=prompt.strip(),
                        width=largura,
                        height=altura,
                        num_inference_steps=passos,
                        guidance_scale=guidance,
                        generator=generator,
                    )

                imagem = resultado.images[0]
                destino = obter_pasta_imagens() / (
                    f"alex_{uuid.uuid4().hex}.png"
                )
                imagem.save(destino, format="PNG")

                with Image.open(destino) as validacao:
                    validacao.verify()

                return str(destino)

        except Exception as erro:
            erros.append(f"{device}: {type(erro).__name__}: {erro}")
            if device.startswith("cuda"):
                try:
                    indice = int(device.split(":")[1])
                    with torch.cuda.device(indice):
                        torch.cuda.empty_cache()
                except Exception:
                    pass

    raise RuntimeError(
        "Falha em todos os dispositivos locais: " + " | ".join(erros)
    )


def gerar_imagem_zimage(prompt):
    # Alias legado para preservar imports existentes.
    return gerar_imagem_local(prompt)


def gerar_imagem(prompt):
    if not isinstance(prompt, str) or not prompt.strip():
        return None, "❌ A descricao da imagem esta vazia."
    try:
        caminho = gerar_imagem_local(prompt)
        _guardar_estado(
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
    if st is None:
        caminho, mensagem = gerar_imagem(prompt)
        if not caminho:
            return False
        return caminho

    with st.spinner("🎨 Alex esta gerando no motor local..."):
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
        st.error(f"❌ A imagem nao pode ser exibida: {erro}")
        return False

    st.success(mensagem)
    st.caption(f"Motor utilizado: {MOTOR_IMAGEM}")
    return True


def obter_ultima_imagem():
    return st.session_state.get("ultima_imagem") if st else None


def obter_caminho_ultima_imagem():
    return st.session_state.get("ultima_imagem_caminho") if st else None


def obter_prompt_ultima_imagem():
    return st.session_state.get("ultimo_prompt_imagem", "") if st else ""


def obter_motor_ultima_imagem():
    return st.session_state.get("ultimo_motor_imagem", "") if st else ""


def limpar_ultima_imagem():
    if st is None:
        return
    for chave in (
        "ultima_imagem",
        "ultima_imagem_caminho",
        "ultimo_prompt_imagem",
        "ultimo_motor_imagem",
    ):
        st.session_state.pop(chave, None)


def executar_teste():
    if st is None:
        raise RuntimeError("Streamlit nao esta instalado neste ambiente.")
    st.title("🖼️ ALEX IMAGE ENGINE — TESTE LOCAL")
    st.caption("Inferencia local com Diffusers e distribuicao round-robin entre GPUs.")
    st.json(diagnostico_motor())
    prompt = st.text_input(
        "Descreva a imagem:",
        value="Um beija-flor voando com as asas abertas",
    )
    if st.button("🎨 Gerar imagem", use_container_width=True):
        if not prompt.strip():
            st.warning("Digite uma descricao para gerar a imagem.")
        else:
            mostrar_imagem(prompt)


if __name__ == "__main__":
    executar_teste()
