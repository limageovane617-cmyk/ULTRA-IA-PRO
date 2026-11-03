# ============================================================
# ALEX IA ULTRA — GEMINI BRIDGE
# Ponte entre o Ultra Core e o Google GenAI
# ============================================================

import logging

from typing import Optional

from google import genai
from google.genai import types


logger = logging.getLogger(__name__)


class GeminiBridge:
    """
    Ponte entre o Ultra Core e o Google GenAI.

    Responsabilidades:
    - Enviar prompts de texto.
    - Enviar imagens junto com o texto.
    - Retornar respostas do Gemini.
    - Tratar erros sem expor credenciais.

    O Ultra Core continua responsável pelo fluxo
    de interpretação, planejamento e execução.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.1-flash-lite",
    ):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError(
                "A chave da API do Gemini não foi informada."
            )

        if not isinstance(model, str) or not model.strip():
            raise ValueError(
                "O modelo Gemini não foi informado."
            )

        self.model = model.strip()

        # A chave é utilizada pelo cliente,
        # mas nunca deve aparecer em logs ou respostas.
        self.client = genai.Client(
            api_key=api_key.strip()
        )

    # ========================================================
    # GERAÇÃO DE RESPOSTA
    # ========================================================

    def gerar_resposta(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None,
        image_mime_type: Optional[str] = None,
    ) -> str:
        """
        Envia texto e, opcionalmente, uma imagem ao Gemini.

        A imagem é transmitida como conteúdo multimodal,
        sem conversão dos bytes para texto.
        """

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(
                "O prompt enviado ao Gemini está vazio."
            )

        contents = [prompt]

        # ----------------------------------------------------
        # IMAGEM OPCIONAL
        # ----------------------------------------------------

        if image_bytes is not None:

            if not isinstance(
                image_bytes,
                (bytes, bytearray),
            ):
                raise TypeError(
                    "Os dados da imagem precisam ser bytes."
                )

            if not image_bytes:
                raise ValueError(
                    "A imagem enviada está vazia."
                )

            mime_type = (
                image_mime_type or "image/jpeg"
            ).strip().lower()

            tipos_permitidos = {
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/heic",
                "image/heif",
            }

            if mime_type not in tipos_permitidos:
                raise ValueError(
                    "Formato de imagem não suportado: "
                    f"{mime_type}"
                )

            parte_imagem = types.Part.from_bytes(
                data=bytes(image_bytes),
                mime_type=mime_type,
            )

            contents.append(
                parte_imagem
            )

        # ----------------------------------------------------
        # CHAMADA AO MODELO
        # ----------------------------------------------------

        try:
            resposta = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )

            texto = getattr(
                resposta,
                "text",
                None,
            )

            if not texto:
                logger.warning(
                    "Gemini retornou uma resposta sem texto."
                )

                return ""

            return str(texto).strip()

        except Exception:
            logger.exception(
                "Falha ao solicitar resposta ao Gemini."
            )

            raise


# ============================================================
# FACTORY
# ============================================================

def criar_gemini_bridge(
    api_key: Optional[str],
    model: str = "gemini-3.1-flash-lite",
) -> Optional[GeminiBridge]:
    """
    Cria a ponte quando existe uma chave disponível.

    Retorna None quando a configuração não permite
    criar o cliente.
    """

    if not api_key:
        logger.warning(
            "GeminiBridge não criado: chave não configurada."
        )

        return None

    try:
        return GeminiBridge(
            api_key=api_key,
            model=model,
        )

    except Exception:
        logger.exception(
            "Não foi possível inicializar o GeminiBridge."
        )

        return None


__all__ = [
    "GeminiBridge",
    "criar_gemini_bridge",
]
