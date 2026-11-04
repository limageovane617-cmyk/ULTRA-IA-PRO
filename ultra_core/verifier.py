
# ============================================================
# 🔍 ALEX IA ULTRA — VERIFIER
# Sistema inteligente de verificação do Ultra Core
# ============================================================

from typing import Any, Dict, List, Optional


class VerificationResult:
    """
    Resultado de uma verificação.
    """

    def __init__(
        self,
        success: bool,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:

        self.success = success is True

        self.message = str(message)

        self.details = (
            details
            if isinstance(details, dict)
            else {}
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o resultado para dicionário.
        """

        return {
            "success": self.success,
            "message": self.message,
            "details": self.details,
        }


class ResultVerifier:
    """
    Verificador inteligente de resultados da Ultra.

    Responsabilidades:

    - Identificar resultados vazios.
    - Interpretar indicadores de sucesso e falha.
    - Detectar erros explícitos.
    - Verificar etapas executadas.
    - Verificar o contexto completo da tarefa.
    """

    # ========================================================
    # NORMALIZAR VALORES BOOLEANOS
    # ========================================================

    @staticmethod
    def _parse_boolean(
        value: Any,
    ) -> Optional[bool]:
        """
        Converte valores conhecidos para booleano.

        Retorna None quando o valor é ambíguo.
        """

        if isinstance(value, bool):
            return value

        if isinstance(value, int):
            if value == 1:
                return True

            if value == 0:
                return False

            return None

        if isinstance(value, float):
            if value == 1.0:
                return True

            if value == 0.0:
                return False

            return None

        if isinstance(value, str):

            normalized = value.strip().lower()

            true_values = {
                "true",
                "1",
                "yes",
                "y",
                "sim",
                "s",
                "success",
                "successful",
                "sucesso",
                "ok",
                "completed",
                "concluido",
                "concluído",
            }

            false_values = {
                "false",
                "0",
                "no",
                "n",
                "não",
                "nao",
                "failure",
                "failed",
                "falha",
                "falhou",
                "error",
                "erro",
                "null",
                "none",
                "",
            }

            if normalized in true_values:
                return True

            if normalized in false_values:
                return False

        return None

    # ========================================================
    # VERIFICAÇÃO BÁSICA
    # ========================================================

    def verify_result(
        self,
        result: Any,
    ) -> VerificationResult:
        """
        Analisa um resultado produzido por uma ferramenta.
        """

        # ----------------------------------------------------
        # RESULTADO INEXISTENTE
        # ----------------------------------------------------

        if result is None:

            return VerificationResult(
                False,
                "A ferramenta não retornou nenhum resultado.",
                {
                    "result_type": "NoneType",
                    "empty": True,
                },
            )

        # ----------------------------------------------------
        # BOOLEANO
        # ----------------------------------------------------

        if isinstance(result, bool):

            return VerificationResult(
                result,
                (
                    "Resultado booleano positivo."
                    if result
                    else "A ferramenta retornou False."
                ),
                {
                    "result_type": "bool",
                    "value": result,
                },
            )

        # ----------------------------------------------------
        # DICIONÁRIO
        # ----------------------------------------------------

        if isinstance(result, dict):

            return self._verify_dict(result)

        # ----------------------------------------------------
        # LISTA / TUPLA / CONJUNTO
        # ----------------------------------------------------

        if isinstance(result, (list, tuple, set)):

            if not result:

                return VerificationResult(
                    False,
                    "A ferramenta retornou uma coleção vazia.",
                    {
                        "result_type": type(result).__name__,
                        "empty": True,
                    },
                )

            return VerificationResult(
                True,
                "A ferramenta retornou uma coleção com dados.",
                {
                    "result_type": type(result).__name__,
                    "items": len(result),
                    "empty": False,
                },
            )

        # ----------------------------------------------------
        # STRING
        # ----------------------------------------------------

        if isinstance(result, str):

            texto = result.strip()

            if not texto:

                return VerificationResult(
                    False,
                    "A ferramenta retornou um texto vazio.",
                    {
                        "result_type": "str",
                        "empty": True,
                    },
                )

            if self._text_indicates_failure(texto):

                return VerificationResult(
                    False,
                    "O resultado contém indicadores de erro.",
                    {
                        "result_type": "str",
                        "value": texto,
                    },
                )

            return VerificationResult(
                True,
                "Resultado textual recebido.",
                {
                    "result_type": "str",
                    "length": len(texto),
                    "empty": False,
                },
            )

        # ----------------------------------------------------
        # BYTES
        # ----------------------------------------------------

        if isinstance(result, (bytes, bytearray)):

            if not result:

                return VerificationResult(
                    False,
                    "A ferramenta retornou dados binários vazios.",
                    {
                        "result_type": type(result).__name__,
                        "empty": True,
                    },
                )

            return VerificationResult(
                True,
                "Dados binários recebidos.",
                {
                    "result_type": type(result).__name__,
                    "size": len(result),
                },
            )

        # ----------------------------------------------------
        # OUTROS TIPOS
        # ----------------------------------------------------

        return VerificationResult(
            True,
            "Resultado recebido sem falha explícita.",
            {
                "result_type": type(result).__name__,
            },
        )

    # ========================================================
    # VERIFICAÇÃO DE DICIONÁRIO
    # ========================================================

    def _verify_dict(
        self,
        result: Dict[str, Any],
    ) -> VerificationResult:
        """
        Analisa dicionários retornados pelas ferramentas.
        """

        if not result:

            return VerificationResult(
                False,
                "A ferramenta retornou um dicionário vazio.",
                {
                    "result_type": "dict",
                    "empty": True,
                },
            )

        # ----------------------------------------------------
        # INDICADORES DE SUCESSO
        # ----------------------------------------------------

        success_values = []

        for key in ("success", "sucesso"):

            if key in result:

                parsed = self._parse_boolean(
                    result[key]
                )

                success_values.append(parsed)

        # ----------------------------------------------------
        # INDICADORES DE FALHA
        # ----------------------------------------------------

        failure_detected = False
        failure_details = {}

        for key in ("error", "erro", "exception"):

            if key not in result:
                continue

            value = result.get(key)

            if value is None:
                continue

            if isinstance(value, bool):

                if value is False:
                    continue

                failure_detected = True
                failure_details[key] = value
                continue

            if isinstance(value, (int, float)):

                if value == 0:
                    continue

                failure_detected = True
                failure_details[key] = value
                continue

            if isinstance(value, str):

                normalized = value.strip().lower()

                if normalized in {
                    "",
                    "false",
                    "0",
                    "none",
                    "null",
                    "no",
                    "não",
                    "nao",
                }:
                    continue

            failure_detected = True
            failure_details[key] = str(value)

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        status = str(
            result.get("status", "")
        ).strip().lower()

        failure_statuses = {
            "failed",
            "failure",
            "error",
            "erro",
            "falha",
            "falhou",
            "failed_task",
            "cancelled",
            "canceled",
            "cancelado",
            "rejected",
            "rejected_task",
        }

        success_statuses = {
            "success",
            "successful",
            "completed",
            "complete",
            "successfully",
            "concluido",
            "concluído",
            "verified",
            "ok",
        }

        status_failure = status in failure_statuses
        status_success = status in success_statuses

        # ----------------------------------------------------
        # FALHA TEM PRIORIDADE
        # ----------------------------------------------------

        if failure_detected or status_failure:

            return VerificationResult(
                False,
                "A ferramenta retornou uma indicação de falha.",
                {
                    "result_type": "dict",
                    "status": status or None,
                    "explicit_success": success_values,
                    "failure_detected": failure_detected,
                    "failure_details": failure_details,
                },
            )

        # ----------------------------------------------------
        # INDICADORES EXPLÍCITOS DE SUCESSO
        # ----------------------------------------------------

        if success_values:

            # Todos os indicadores precisam ser válidos.
            # Um indicador falso ou ambíguo reprova.
            success = all(
                value is True
                for value in success_values
            )

            return VerificationResult(
                success,
                (
                    "A ferramenta confirmou o sucesso."
                    if success
                    else "A ferramenta não confirmou o sucesso."
                ),
                {
                    "result_type": "dict",
                    "status": status or None,
                    "explicit_success": success_values,
                },
            )

        # ----------------------------------------------------
        # STATUS DE SUCESSO
        # ----------------------------------------------------

        if status_success:

            return VerificationResult(
                True,
                "O status da ferramenta indica conclusão.",
                {
                    "result_type": "dict",
                    "status": status,
                },
            )

        # ----------------------------------------------------
        # VERIFICAR DADOS ÚTEIS
        # ----------------------------------------------------

        payload_keys = (
            "result",
            "results",
            "data",
            "answer",
            "resposta",
            "content",
            "conteudo",
            "items",
            "sources",
            "fontes",
        )

        payload_found = False
        payload_empty = False

        for key in payload_keys:

            if key not in result:
                continue

            payload_found = True
            value = result[key]

            if value is None:
                payload_empty = True
                continue

            if isinstance(value, str) and not value.strip():
                payload_empty = True
                continue

            if isinstance(value, (list, tuple, dict, set)) and not value:
                payload_empty = True
                continue

            # Existe pelo menos um conteúdo útil.
            payload_empty = False
            break

        if payload_found and payload_empty:

            return VerificationResult(
                False,
                "O dicionário não contém dados úteis.",
                {
                    "result_type": "dict",
                    "keys": list(result.keys()),
                    "empty_payload": True,
                },
            )

        # ----------------------------------------------------
        # DICIONÁRIO COM DADOS
        # ----------------------------------------------------

        return VerificationResult(
            True,
            "Resultado recebido com dados.",
            {
                "result_type": "dict",
                "keys": list(result.keys()),
                "status": status or None,
                "payload_found": payload_found,
            },
        )

    # ========================================================
    # DETECTAR TEXTO DE ERRO
    # ========================================================

    @staticmethod
    def _text_indicates_failure(
        text: str,
    ) -> bool:
        """
        Detecta mensagens que indicam falha.
        """

        texto = str(text).strip().lower()

        error_prefixes = (
            "erro:",
            "error:",
            "exception:",
            "traceback",
            "failed:",
            "failure:",
            "falhou:",
            "falha:",
        )

        failure_phrases = (
            "não foi possível",
            "nao foi possivel",
            "não foi possível gerar",
            "nao foi possivel gerar",
            "ocorreu um erro",
            "an error occurred",
            "execution failed",
            "execução falhou",
        )

        return (
            texto.startswith(error_prefixes)
            or any(
                phrase in texto
                for phrase in failure_phrases
            )
        )

    # ========================================================
    # VERIFICAÇÃO DE ETAPA
    # ========================================================

    def verify_step(
        self,
        context: Any,
        step_id: int,
    ) -> VerificationResult:
        """
        Verifica o resultado de uma etapa específica.
        """

        step = self._get_step(
            context,
            step_id,
        )

        status = step.get("status")

        if status != "completed":

            return VerificationResult(
                False,
                f"A etapa {step_id} não foi concluída.",
                {
                    "step_id": step_id,
                    "status": status,
                },
            )

        result = step.get("result")

        verification = self.verify_result(result)

        verification.details.setdefault(
            "step_id",
            step_id,
        )

        return verification

    # ========================================================
    # VERIFICAÇÃO DO CONTEXTO
    # ========================================================

    def verify_context(
        self,
        context: Any,
    ) -> Dict[str, Any]:
        """
        Verifica todas as etapas de uma tarefa.
        """

        checks: List[Dict[str, Any]] = []

        if not context.plan:

            return {
                "success": False,
                "status": "verification_failed",
                "checks": [],
                "errors": context.errors,
                "message": (
                    "A tarefa não possui etapas para verificar."
                ),
            }

        # ----------------------------------------------------
        # VERIFICAR TODAS AS ETAPAS
        # ----------------------------------------------------

        for step in context.plan:

            step_id = step.get("id")

            try:

                verification = self.verify_step(
                    context,
                    step_id,
                )

                checks.append({
                    "step_id": step_id,
                    **verification.to_dict(),
                })

            except Exception as exc:

                checks.append({
                    "step_id": step_id,
                    "success": False,
                    "message": "Erro ao verificar etapa.",
                    "details": {
                        "error": str(exc),
                    },
                })

        # ----------------------------------------------------
        # RESULTADO GERAL
        # ----------------------------------------------------

        all_success = (
            bool(checks)
            and all(
                check.get("success") is True
                for check in checks
            )
        )

        no_errors = not context.has_errors()

        success = all_success and no_errors

        verified_steps = sum(
            1
            for check in checks
            if check.get("success") is True
        )

        failed_steps = len(checks) - verified_steps

        return {
            "success": success,

            "status": (
                "verified"
                if success
                else "verification_failed"
            ),

            "checks": checks,

            "errors": context.errors,

            "summary": {
                "total_steps": len(context.plan),
                "verified_steps": verified_steps,
                "failed_steps": failed_steps,
                "context_errors": len(context.errors),
            },
        }

    # ========================================================
    # LOCALIZAR ETAPA
    # ========================================================

    @staticmethod
    def _get_step(
        context: Any,
        step_id: int,
    ) -> Dict[str, Any]:
        """
        Localiza uma etapa pelo ID.
        """

        for step in context.plan:

            if step.get("id") == step_id:
                return step

        raise KeyError(
            f"Etapa {step_id} não encontrada."
        )


# ============================================================
# INSTÂNCIA PADRÃO
# ============================================================

verifier = ResultVerifier()


__all__ = [
    "VerificationResult",
    "ResultVerifier",
    "verifier",
]
