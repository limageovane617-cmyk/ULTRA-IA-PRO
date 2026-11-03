# ============================================================
# ALEX IA ULTRA — PLANNER
# Planejador de tarefas do Ultra Core
# ============================================================

from copy import deepcopy
from typing import Any, Dict, List, Optional

from .context import TaskContext


class TaskPlanner:
    """
    Cria e gerencia o plano de execução de uma tarefa.

    O Planner organiza as etapas.
    A execução fica sob responsabilidade do Executor.
    """

    VALID_STATUSES = {
        "pending",
        "running",
        "completed",
        "failed",
    }

    # ========================================================
    # NORMALIZAÇÃO DE ETAPAS
    # ========================================================

    @staticmethod
    def _normalize_step(
        step: Dict[str, Any],
        index: int,
    ) -> Dict[str, Any]:
        """
        Normaliza e valida uma etapa.
        """

        if not isinstance(step, dict):
            raise TypeError(
                f"A etapa {index} precisa ser um dicionário."
            )

        arguments = step.get("arguments", {})

        if arguments is None:
            arguments = {}

        if not isinstance(arguments, dict):
            raise TypeError(
                f"Os argumentos da etapa {index} precisam ser um dicionário."
            )

        name = str(
            step.get("name") or f"Etapa {index}"
        ).strip()

        description = str(
            step.get("description") or ""
        ).strip()

        tool = step.get("tool")

        if tool is not None:
            tool = str(tool).strip() or None

        return {
            "id": index,
            "name": name,
            "description": description,
            "tool": tool,
            "arguments": deepcopy(arguments),
            "status": "pending",
        }

    # ========================================================
    # CRIAÇÃO DO PLANO
    # ========================================================

    def create_plan(
        self,
        context: TaskContext,
        steps: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Cria um plano a partir de etapas previamente definidas.

        O Planner não executa as etapas.
        """

        if not isinstance(steps, list):
            raise TypeError(
                "As etapas do plano precisam estar em uma lista."
            )

        normalized_steps = []

        for index, step in enumerate(steps, start=1):

            normalized_step = self._normalize_step(
                step,
                index,
            )

            normalized_steps.append(
                normalized_step
            )

        # Só altera o contexto depois de validar
        # todas as etapas.
        context.plan.clear()

        for step in normalized_steps:
            context.add_plan_step(step)

        context.update_status("planned")

        return context.plan

    # ========================================================
    # ADICIONAR ETAPA
    # ========================================================

    def add_step(
        self,
        context: TaskContext,
        name: str,
        description: str = "",
        tool: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Adiciona uma nova etapa ao plano.
        """

        if arguments is None:
            arguments = {}

        if not isinstance(arguments, dict):
            raise TypeError(
                "Os argumentos da etapa precisam ser um dicionário."
            )

        step = {
            "id": len(context.plan) + 1,
            "name": str(name or f"Etapa {len(context.plan) + 1}").strip(),
            "description": str(description or "").strip(),
            "tool": (
                str(tool).strip()
                if tool is not None and str(tool).strip()
                else None
            ),
            "arguments": deepcopy(arguments),
            "status": "pending",
        }

        context.add_plan_step(step)

        return step

    # ========================================================
    # INICIAR ETAPA
    # ========================================================

    def start_step(
        self,
        context: TaskContext,
        step_id: int,
    ) -> Dict[str, Any]:
        """
        Marca uma etapa como em execução.
        """

        step = self._get_step(
            context,
            step_id,
        )

        if step.get("status") == "completed":
            raise ValueError(
                f"A etapa {step_id} já foi concluída."
            )

        step["status"] = "running"

        # Remove informações de uma tentativa anterior.
        step.pop("error", None)
        step.pop("result", None)

        context.update_status("executing")

        return step

    # ========================================================
    # CONCLUIR ETAPA
    # ========================================================

    def complete_step(
        self,
        context: TaskContext,
        step_id: int,
        result: Any = None,
    ) -> Dict[str, Any]:
        """
        Marca uma etapa como concluída.
        """

        step = self._get_step(
            context,
            step_id,
        )

        step["status"] = "completed"
        step["result"] = result

        # Evita manter erro antigo em uma etapa concluída.
        step.pop("error", None)

        context.touch()

        return step

    # ========================================================
    # FALHA NA ETAPA
    # ========================================================

    def fail_step(
        self,
        context: TaskContext,
        step_id: int,
        error: str,
    ) -> Dict[str, Any]:
        """
        Marca uma etapa como falha.
        """

        step = self._get_step(
            context,
            step_id,
        )

        step["status"] = "failed"
        step["error"] = str(error)

        # Evita manter resultado antigo em uma etapa falha.
        step.pop("result", None)

        context.update_status("failed")

        return step

    # ========================================================
    # ETAPAS PENDENTES
    # ========================================================

    def pending_steps(
        self,
        context: TaskContext,
    ) -> List[Dict[str, Any]]:
        """
        Retorna as etapas ainda não concluídas.

        Mantém o comportamento anterior:
        etapas pendentes, em execução e com falha
        continuam sendo consideradas não concluídas.
        """

        return [
            step
            for step in context.plan
            if step.get("status") != "completed"
        ]

    # ========================================================
    # VERIFICAR CONCLUSÃO
    # ========================================================

    def is_complete(
        self,
        context: TaskContext,
    ) -> bool:
        """
        Verifica se todas as etapas foram concluídas.
        """

        if not context.plan:
            return False

        return all(
            step.get("status") == "completed"
            for step in context.plan
        )

    # ========================================================
    # BUSCAR ETAPA
    # ========================================================

    def _get_step(
        self,
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
            f"Etapa {step_id} não encontrada no plano."
        )


# ============================================================
# INSTÂNCIA PADRÃO
# ============================================================

planner = TaskPlanner()


__all__ = [
    "TaskPlanner",
    "planner",
]
