
# ============================================================
# ⚙️ ALEX IA ULTRA — EXECUTOR
# Executor controlado do Ultra Core
# ============================================================

from typing import Any, Dict, Optional

from .context import TaskContext
from .planner import TaskPlanner, planner
from .router import ToolRouter, router
from .verifier import ResultVerifier


class TaskExecutor:
    """
    Executa as etapas planejadas pela Alex IA Ultra.

    Responsabilidades:
    - Executar ferramentas.
    - Validar resultados.
    - Registrar sucessos e falhas reais.
    - Preservar resultados originais.
    - Evitar repetição automática de etapas com falha.
    """

    def __init__(
        self,
        task_router: ToolRouter = router,
        task_planner: TaskPlanner = planner,
        result_verifier: Optional[ResultVerifier] = None,
    ) -> None:

        self.router = task_router
        self.planner = task_planner

        self.verifier = (
            result_verifier
            if result_verifier is not None
            else ResultVerifier()
        )

    # ========================================================
    # EXECUTAR UMA ETAPA
    # ========================================================

    def execute_step(
        self,
        context: TaskContext,
        step_id: int,
    ) -> Dict[str, Any]:

        step = self._get_step(
            context,
            step_id,
        )

        self.planner.start_step(
            context,
            step_id,
        )

        tool = None

        try:
            # Localizar ferramenta.
            tool = self.router.route(step)

            if tool is None:

                error_message = (
                    f"Nenhuma ferramenta disponível "
                    f"para a etapa {step_id}."
                )

                return self._register_failure(
                    context=context,
                    step_id=step_id,
                    error_message=error_message,
                    source="executor",
                )

            # Validar argumentos.
            arguments = step.get(
                "arguments",
                {},
            )

            if not isinstance(arguments, dict):

                raise TypeError(
                    "Os argumentos da ferramenta "
                    "precisam ser um dicionário."
                )

            # Executar ferramenta.
            result = tool.execute(
                **arguments,
            )

            # Validar resultado real.
            verification = self.verifier.verify_result(
                result
            )

            if not verification.success:

                error_message = (
                    verification.message
                    or "A ferramenta não confirmou o sucesso."
                )

                return self._register_failure(
                    context=context,
                    step_id=step_id,
                    error_message=error_message,
                    source=f"tool:{tool.name}",
                    tool_name=tool.name,
                    result=result,
                    verification=verification.to_dict(),
                )

            # Somente resultados aprovados são concluídos.
            self.planner.complete_step(
                context,
                step_id,
                result,
            )

            context.add_tool_result(
                tool=tool.name,
                success=True,
                result=result,
            )

            return {
                "success": True,
                "step_id": step_id,
                "tool": tool.name,
                "result": result,
                "verification": verification.to_dict(),
            }

        except Exception as exc:

            error_message = (
                f"{type(exc).__name__}: {exc}"
            )

            return self._register_failure(
                context=context,
                step_id=step_id,
                error_message=error_message,
                source=(
                    f"tool:{tool.name}"
                    if tool is not None
                    else "executor"
                ),
                tool_name=(
                    tool.name
                    if tool is not None
                    else None
                ),
            )

    # ========================================================
    # REGISTRAR FALHA
    # ========================================================

    def _register_failure(
        self,
        context: TaskContext,
        step_id: int,
        error_message: str,
        source: str,
        tool_name: Optional[str] = None,
        result: Any = None,
        verification: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        self.planner.fail_step(
            context,
            step_id,
            error_message,
        )

        context.add_error(
            source=source,
            message=error_message,
            details={
                "step_id": step_id,
                "verification": verification,
            },
        )

        if tool_name is not None:

            context.add_tool_result(
                tool=tool_name,
                success=False,
                result=result,
            )

        response = {
            "success": False,
            "step_id": step_id,
            "error": error_message,
        }

        if tool_name is not None:
            response["tool"] = tool_name

        if result is not None:
            response["result"] = result

        if verification is not None:
            response["verification"] = verification

        return response

    # ========================================================
    # EXECUTAR PRÓXIMA ETAPA
    # ========================================================

    def execute_next(
        self,
        context: TaskContext,
    ) -> Dict[str, Any]:

        pending = [
            step
            for step in self.planner.pending_steps(context)
            if step.get("status") == "pending"
        ]

        if not pending:

            return {
                "success": False,
                "message": (
                    "Não existem etapas novas pendentes. "
                    "Verifique se existem etapas com falha."
                ),
            }

        next_step = pending[0]

        return self.execute_step(
            context,
            next_step["id"],
        )

    # ========================================================
    # EXECUTAR TODAS AS ETAPAS
    # ========================================================

    def execute_all(
        self,
        context: TaskContext,
        stop_on_error: bool = True,
    ) -> Dict[str, Any]:

        results = []

        while not self.planner.is_complete(context):

            # Somente etapas realmente pendentes.
            # Etapas com falha não serão repetidas
            # automaticamente nesta execução.

            pending = [
                step
                for step in self.planner.pending_steps(context)
                if step.get("status") == "pending"
            ]

            if not pending:
                break

            step_id = pending[0]["id"]

            result = self.execute_step(
                context,
                step_id,
            )

            results.append(result)

            if not result.get("success") and stop_on_error:
                break

        # Verificar resultado final.
        if self.planner.is_complete(context):

            if context.has_errors():

                context.update_status("failed")

                return {
                    "success": False,
                    "status": "failed",
                    "results": results,
                    "errors": context.errors,
                }

            context.update_status("completed")

            return {
                "success": True,
                "status": "completed",
                "results": results,
            }

        # Existem erros registrados.
        if context.has_errors():

            context.update_status("failed")

            return {
                "success": False,
                "status": "failed",
                "results": results,
                "errors": context.errors,
            }

        return {
            "success": False,
            "status": context.status,
            "results": results,
        }

    # ========================================================
    # LOCALIZAR ETAPA
    # ========================================================

    @staticmethod
    def _get_step(
        context: TaskContext,
        step_id: int,
    ) -> Dict[str, Any]:

        for step in context.plan:

            if step.get("id") == step_id:
                return step

        raise KeyError(
            f"Etapa {step_id} não encontrada."
        )


# ============================================================
# INSTÂNCIA PADRÃO
# ============================================================

executor = TaskExecutor()


__all__ = [
    "TaskExecutor",
    "executor",
]
