# ============================================================
# 🔍 ALEX IA ULTRA — VERIFIER
# Sistema de verificação do Ultra Core
# ============================================================

from typing import Any, Dict, List, Optional

from .context import TaskContext


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
        self.success = success
        self.message = message
        self.details = details or {}

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
    Verifica resultados produzidos pelas ferramentas da Ultra.
    """

    def verify_result(
        self,
        result: Any,
    ) -> VerificationResult:
        """
        Faz uma verificação básica do resultado.
        """

        if result is None:
            return VerificationResult(
                success=False,
                message="A ferramenta não retornou nenhum resultado.",
            )

        return VerificationResult(
            success=True,
            message="Resultado recebido.",
            details={
                "result_type": type(result).__name__,
            },
        )

    def verify_step(
        self,
        context: TaskContext,
        step_id: int,
    ) -> VerificationResult:
        """
        Verifica o resultado de uma etapa específica.
        """

        step = self._get_step(
            context,
            step_id,
        )

        if step.get("status") != "completed":
            return VerificationResult(
                success=False,
                message=(
                    f"A etapa {step_id} não está marcada "
                    "como concluída."
                ),
            )

        result = step.get("result")

        return self.verify_result(result)

    def verify_context(
        self,
        context: TaskContext,
    ) -> Dict[str, Any]:
        """
        Verifica o estado geral da tarefa.
        """

        checks: List[Dict[str, Any]] = []

        for step in context.plan:
            step_id = step.get("id")

            verification = self.verify_step(
                context,
                step_id,
            )

            checks.append(
                {
                    "step_id": step_id,
                    **verification.to_dict(),
                }
            )

        success = (
            bool(checks)
            and all(
                check["success"]
                for check in checks
            )
            and not context.has_errors()
        )

        return {
            "success": success,
            "status": (
                "verified"
                if success
                else "verification_failed"
            ),
            "checks": checks,
            "errors": context.errors,
        }

    @staticmethod
    def _get_step(
        context: TaskContext,
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
