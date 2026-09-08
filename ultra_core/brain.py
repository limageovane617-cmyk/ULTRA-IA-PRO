# ============================================================
# 🧠 ALEX IA ULTRA — BRAIN
# Cérebro central do Ultra Core
# ============================================================

from typing import Any, Dict, List, Optional
from uuid import uuid4

from .context import TaskContext
from .planner import TaskPlanner, planner
from .router import ToolRouter, router
from .executor import TaskExecutor, executor
from .verifier import ResultVerifier, verifier


class UltraBrain:
    """
    Coordenador central da Alex IA Ultra.

    O Brain conecta:

    - Contexto
    - Planejamento
    - Roteamento
    - Execução
    - Verificação

    Ele não implementa diretamente cada ferramenta.
    Ele coordena os componentes do Ultra Core.
    """

    def __init__(
        self,
        task_planner: TaskPlanner = planner,
        task_router: ToolRouter = router,
        task_executor: TaskExecutor = executor,
        result_verifier: ResultVerifier = verifier,
    ) -> None:

        self.planner = task_planner
        self.router = task_router
        self.executor = task_executor
        self.verifier = result_verifier

    # ========================================================
    # CRIAÇÃO DE TAREFA
    # ========================================================

    def create_task(
        self,
        user_request: str,
    ) -> TaskContext:
        """
        Cria um novo contexto para uma solicitação.
        """

        if not user_request or not user_request.strip():
            raise ValueError(
                "A solicitação do usuário não pode estar vazia."
            )

        context = TaskContext(
            user_request=user_request.strip(),
            task_id=str(uuid4()),
        )

        context.update_status("created")

        return context

    # ========================================================
    # PLANEJAMENTO
    # ========================================================

    def plan_task(
        self,
        context: TaskContext,
        steps: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Cria o plano de execução da tarefa.
        """

        return self.planner.create_plan(
            context,
            steps,
        )

    # ========================================================
    # INSPEÇÃO DAS FERRAMENTAS
    # ========================================================

    def available_tools(self) -> List[Dict[str, Any]]:
        """
        Retorna as ferramentas disponíveis.
        """

        return self.router.available_tools()

    # ========================================================
    # EXECUÇÃO
    # ========================================================

    def execute(
        self,
        context: TaskContext,
        *,
        stop_on_error: bool = True,
    ) -> Dict[str, Any]:
        """
        Executa o plano da tarefa.
        """

        if not context.plan:
            return {
                "success": False,
                "status": "no_plan",
                "message": (
                    "A tarefa ainda não possui um plano."
                ),
            }

        result = self.executor.execute_all(
            context,
            stop_on_error=stop_on_error,
        )

        return result

    # ========================================================
    # VERIFICAÇÃO
    # ========================================================

    def verify(
        self,
        context: TaskContext,
    ) -> Dict[str, Any]:
        """
        Verifica o resultado da tarefa.
        """

        return self.verifier.verify_context(
            context,
        )

    # ========================================================
    # CICLO COMPLETO
    # ========================================================

    def run(
        self,
        user_request: str,
        steps: Optional[List[Dict[str, Any]]] = None,
        *,
        stop_on_error: bool = True,
    ) -> Dict[str, Any]:
        """
        Executa o ciclo básico do Ultra Core.

        Fluxo:

        Pedido
          ↓
        Contexto
          ↓
        Plano
          ↓
        Execução
          ↓
        Verificação
        """

        context = self.create_task(
            user_request,
        )

        if not steps:
            context.update_status(
                "waiting_for_plan"
            )

            return {
                "success": False,
                "status": "waiting_for_plan",
                "task_id": context.task_id,
                "context": context.summary(),
                "message": (
                    "A tarefa foi criada, mas ainda "
                    "não possui um plano de execução."
                ),
            }

        self.plan_task(
            context,
            steps,
        )

        execution = self.execute(
            context,
            stop_on_error=stop_on_error,
        )

        verification = self.verify(
            context,
        )

        return {
            "success": (
                execution.get("success", False)
                and verification.get("success", False)
            ),
            "task_id": context.task_id,
            "status": context.status,
            "execution": execution,
            "verification": verification,
            "context": context.summary(),
        }


# ============================================================
# INSTÂNCIA PRINCIPAL
# ============================================================

brain = UltraBrain()


__all__ = [
    "UltraBrain",
    "brain",
]
