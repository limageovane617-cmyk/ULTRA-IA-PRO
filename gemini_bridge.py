
# ============================================================
# ALEX IA ULTRA — GEMINI BRIDGE V2
# Conexão resiliente com Google GenAI
# ============================================================

import logging
import os
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiBridge:

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.1-flash-lite",
        fallback_models=None,
    ):

        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("Chave Gemini não informada.")

        if not isinstance(model, str) or not model.strip():
            raise ValueError("Modelo Gemini não informado.")

        self.model = model.strip()

        # Modelos alternativos configuráveis pelo ambiente.
        if fallback_models is None:
            fallback_models = os.getenv(
                "GEMINI_FALLBACK_MODELS", ""
            ).split(",")

        self.fallback_models = [
            item.strip()
            for item in fallback_models
            if item.strip() and item.strip() != self.model
        ]

        # Retry configurado no SDK oficial.
        http_options = types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=4,
                initial_delay=1.0,
                max_delay=8.0,
                exp_base=2.0,
                jitter=1.0,
                http_status_codes=[
                    408, 429, 500, 502, 503, 504
                ],
            ),
            timeout=90000,
        )

        self.client = genai.Client(
            api_key=api_key.strip(),
            http_options=http_options,
        )

    # ========================================================
    # GERAÇÃO
    # ========================================================

    def gerar_resposta(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None,
        image_mime_type: Optional[str] = None,
    ) -> str:

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt vazio.")

        contents = [prompt]

        if image_bytes is not None:

            if not isinstance(image_bytes, (bytes, bytearray)):
                raise TypeError("Imagem precisa ser bytes.")

            if not image_bytes:
                raise ValueError("Imagem vazia.")

            mime_type = (
                image_mime_type or "image/jpeg"
            ).strip().lower()

            permitidos = {
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/heic",
                "image/heif",
            }

            if mime_type not in permitidos:
                raise ValueError("Formato de imagem inválido.")

            contents.append(
                types.Part.from_bytes(
                    data=bytes(image_bytes),
                    mime_type=mime_type,
                )
            )

        modelos = [self.model] + self.fallback_models

        ultimo_erro = None

        for modelo in modelos:

            try:

                logger.info(
                    "Solicitando resposta ao Gemini."
                )

                resposta = self.client.models.generate_content(
                    model=modelo,
                    contents=contents,
                )

                texto = getattr(resposta, "text", None)

                if texto and str(texto).strip():

                    logger.info(
                        "Resposta recebida do modelo Gemini."
                    )

                    return str(texto).strip()

                logger.warning(
                    "Modelo retornou resposta vazia."
                )

                ultimo_erro = RuntimeError(
                    "O Gemini retornou uma resposta vazia."
                )

            except Exception as erro:

                ultimo_erro = erro

                mensagem = str(erro).lower()

                temporario = any(
                    termo in mensagem
                    for termo in (
                        "503",
                        "429",
                        "502",
                        "500",
                        "504",
                        "408",
                        "unavailable",
                        "resource_exhausted",
                        "deadline_exceeded",
                        "timeout",
                    )
                )

                logger.warning(
                    "Falha no modelo Gemini durante geração."
                )

                # Erros permanentes não devem provocar
                # tentativas em outros modelos.
                if not temporario:
                    raise

                if modelo != modelos[-1]:
                    logger.warning(
                        "Tentando modelo alternativo."
                    )

        logger.error(
            "Todos os modelos Gemini configurados falharam."
        )

        raise RuntimeError(
            "O serviço Gemini está temporariamente indisponível."
        ) from ultimo_erro


# ============================================================
# FACTORY
# ============================================================

def criar_gemini_bridge(
    api_key: Optional[str],
    model: str = "gemini-3.1-flash-lite",
) -> Optional[GeminiBridge]:

    if not api_key:
        logger.warning(
            "GeminiBridge não criado: chave ausente."
        )
        return None

    try:
        return GeminiBridge(
            api_key=api_key,
            model=model,
        )

    except Exception:
        logger.exception(
            "Falha ao inicializar GeminiBridge."
        )
        return None


__all__ = [
    "GeminiBridge",
    "criar_gemini_bridge",
]
