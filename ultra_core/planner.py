
# ============================================================
# 🧠 ALEX IA ULTRA — PLANNER V10
# Planejador inteligente de tarefas do Ultra Core
# ============================================================

from copy import deepcopy
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone

from .context import TaskContext


class TaskPlanner:
    """
    Planejador central da Alex IA Ultra.

    Responsabilidades:
    - Criar planos de execução.
    - Gerenciar etapas.
    - Controlar dependências.
    - Controlar tentativas.
    - Registrar histórico de execução.
    - Permitir recuperação de falhas.
    - Preservar compatibilidade com Brain e Executor.
    """

    VALID_STATUSES = {
        "pending",
        "running",
        "completed",
        "failed",
    }

    DEFAULT_MAX_ATTEMPTS = 3

    # ========================================================
    # UTILITÁRIOS
    # ========================================================

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _validate_positive_integer(value: Any, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} precisa ser um inteiro positivo.")
        return value

    # ========================================================
    # NORMALIZAÇÃO
    # ========================================================

    @classmethod
    def _normalize_step(
        cls,
        step: Dict[str, Any],
        index: int,
    ) -> Dict[str, Any]:

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

        dependencies = step.get("dependencies", [])

        if dependencies is None:
            dependencies = []

        if not isinstance(dependencies, (list, tuple, set)):
            raise TypeError(
                f"As dependências da etapa {index} precisam ser uma coleção."
            )

        normalized_dependencies = []

        for dependency in dependencies:

            dependency_id = cls._validate_positive_integer(
                dependency,
                "ID da dependência",
            )

            if dependency_id not in normalized_dependencies:
                normalized_dependencies.append(dependency_id)

        if index in normalized_dependencies:
            raise ValueError(
                f"A etapa {index} não pode depender dela mesma."
            )

        max_attempts = cls._validate_positive_integer(
            step.get(
                "max_attempts",
                cls.DEFAULT_MAX_ATTEMPTS,
            ),
            "max_attempts",
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
            "dependencies": normalized_dependencies,
            "status": "pending",
            "attempts": 0,
            "max_attempts": max_attempts,
            "history": [],
            "created_at": cls._now(),
            "updated_at": cls._now(),
        }

    # ========================================================
    # VALIDAR DEPENDÊNCIAS
    # ========================================================

    @staticmethod
    def _validate_dependencies(
        steps: List[Dict[str, Any]],
    ) -> None:

        ids = {
            step["id"]
            for step in steps
        }

        graph = {
            step["id"]: step.get("dependencies", [])
            for step in steps
        }

        for step_id, dependencies in graph.items():

            for dependency in dependencies:

                if dependency not in ids:
                    raise ValueError(
                        f"A etapa {step_id} depende da etapa inexistente "
                        f"{dependency}."
                    )

        # Detectar ciclos.
        visited: Set[int] = set()
        visiting: Set[int] = set()

        def visit(step_id: int) -> None:

            if step_id in visiting:
                raise ValueError(
                    "Dependência circular detectada no plano."
                )

            if step_id in visited:
                return

            visiting.add(step_id)

            for dependency in graph[step_id]:
                visit(dependency)

            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in graph:
            visit(step_id)

    # ========================================================
    # CRIAÇÃO DO PLANO
    # ========================================================

    def create_plan(
        self,
        context: TaskContext,
        steps: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        if not isinstance(steps, list):
            raise TypeError(
                "As etapas do plano precisam estar em uma lista."
            )

        normalized_steps = []

        for index, step in enumerate(steps, start=1):

            normalized_steps.append(
                self._normalize_step(step, index)
            )

        # Valida tudo antes de modificar o contexto.
        self._validate_dependencies(normalized_steps)

        context.plan.clear()

        for step in normalized_steps:
            context.add_plan_step(step)

        context.update_status("planned")

        context.touch()

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
        dependencies: Optional[List[int]] = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> Dict[str, Any]:

        if arguments is None:
            arguments = {}

        if not isinstance(arguments, dict):
            raise TypeError(
                "Os argumentos precisam ser um dicionário."
            )

        step_id = len(context.plan) + 1

        step = self._normalize_step(
            {
                "name": name,
                "description": description,
                "tool": tool,
                "arguments": arguments,
                "dependencies": dependencies or [],
                "max_attempts": max_attempts,
            },
            step_id,
        )

        candidate_plan = list(context.plan) + [step]

        self._validate_dependencies(candidate_plan)

        context.add_plan_step(step)
        context.touch()

        return step

    # ========================================================
    # LOCALIZAR ETAPA
    # ========================================================

    def _get_step(
        self,
        context: TaskContext,
        step_id: int,
    ) -> Dict[str, Any]:

        for step in context.plan:

            if step.get("id") == step_id:
                return step

        raise KeyError(
            f"Etapa {step_id} não encontrada no plano."
        )

    # ========================================================
    # VERIFICAR DEPENDÊNCIAS
    # ========================================================

    def dependencies_satisfied(
        self,
        context: TaskContext,
        step_id: int,
    ) -> bool:

        step = self._get_step(context, step_id)

        dependencies = step.get("dependencies", [])

        for dependency_id in dependencies:

            dependency = self._get_step(
                context,
                dependency_id,
            )

            if dependency.get("status") != "completed":
                return False

        return True

    # ========================================================
    # INICIAR ETAPA
    # ========================================================

    def start_step(
        self,
        context: TaskContext,
        step_id: int,
    ) -> Dict[str, Any]:

        step = self._get_step(
            context,
            step_id,
        )

        status = step.get("status")

        if status == "completed":
            raise ValueError(
                f"A etapa {step_id} já foi concluída."
            )

        if status == "running":
            raise ValueError(
                f"A etapa {step_id} já está em execução."
            )

        if status not in {"pending", "failed"}:
            raise ValueError(
                f"Estado inválido para iniciar etapa: {status}."
            )

        if not self.dependencies_satisfied(
            context,
            step_id,
        ):
            raise ValueError(
                f"As dependências da etapa {step_id} "
                "ainda não foram concluídas."
            )

        attempts = step.get("attempts", 0)

        if attempts >= step.get(
            "max_attempts",
            self.DEFAULT_MAX_ATTEMPTS,
        ):
            raise ValueError(
                f"A etapa {step_id} atingiu o limite de tentativas."
            )

        step["attempts"] = attempts + 1
        step["status"] = "running"
        step["started_at"] = self._now()
        step["updated_at"] = self._now()

        step.pop("error", None)
        step.pop("result", None)

        step.setdefault("history", []).append({
            "attempt": step["attempts"],
            "status": "running",
            "started_at": step["started_at"],
        })

        context.update_status("executing")
        context.touch()

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

        step = self._get_step(
            context,
            step_id,
        )

        if step.get("status") != "running":
            raise ValueError(
                f"A etapa {step_id} não está em execução."
            )

        step["status"] = "completed"
        step["result"] = result
        step["completed_at"] = self._now()
        step["updated_at"] = self._now()

        step.pop("error", None)

        history = step.setdefault("history", [])

        if history:
            history[-1]["status"] = "completed"
            history[-1]["completed_at"] = step["completed_at"]

        context.touch()

        return step

    # ========================================================
    # REGISTRAR FALHA
    # ========================================================

    def fail_step(
        self,
        context: TaskContext,
        step_id: int,
        error: str,
    ) -> Dict[str, Any]:

        step = self._get_step(
            context,
            step_id,
        )

        if step.get("status") != "running":
            raise ValueError(
                f"A etapa {step_id} não está em execução."
            )

        step["status"] = "failed"
        step["error"] = str(error)
        step["failed_at"] = self._now()
        step["updated_at"] = self._now()

        step.pop("result", None)

        history = step.setdefault("history", [])

        if history:
            history[-1]["status"] = "failed"
            history[-1]["error"] = str(error)
            history[-1]["failed_at"] = step["failed_at"]

        context.update_status("failed")
        context.touch()

        return step

    # ========================================================
    # RETENTATIVA CONTROLADA
    # ========================================================

    def retry_step(
        self,
        context: TaskContext,
        step_id: int,
    ) -> Dict[str, Any]:

        step = self._get_step(
            context,
            step_id,
        )

        if step.get("status") != "failed":
            raise ValueError(
                "Somente etapas com falha podem ser reexecutadas."
            )

        if step.get("attempts", 0) >= step.get(
            "max_attempts",
            self.DEFAULT_MAX_ATTEMPTS,
        ):
            raise ValueError(
                "Limite máximo de tentativas atingido."
            )

        if not self.dependencies_satisfied(
            context,
            step_id,
        ):
            raise ValueError(
                "As dependências da etapa ainda não foram concluídas."
            )

        step["status"] = "pending"
        step.pop("error", None)
        step.pop("result", None)

        step["updated_at"] = self._now()

        context.update_status("planned")
        context.touch()

        return step

    # ========================================================
    # ETAPAS PENDENTES
    # ========================================================

    def pending_steps(
        self,
        context: TaskContext,
    ) -> List[Dict[str, Any]]:
        """
        Retorna etapas não concluídas e elegíveis.

        Mantém falhas visíveis para compatibilidade.
        Etapas pendentes com dependências incompletas
        não são liberadas para o Executor.
        """

        available = []

        for step in context.plan:

            status = step.get("status")

            if status == "completed":
                continue

            if status in {"failed", "running"}:
                available.append(step)
                continue

            if status == "pending":

                if self.dependencies_satisfied(
                    context,
                    step["id"],
                ):
                    available.append(step)

        return available

    # ========================================================
    # ETAPAS PRONTAS
    # ========================================================

    def ready_steps(
        self,
        context: TaskContext,
    ) -> List[Dict[str, Any]]:

        return [
            step
            for step in context.plan
            if (
                step.get("status") == "pending"
                and self.dependencies_satisfied(
                    context,
                    step["id"],
                )
                and step.get("attempts", 0)
                < step.get(
                    "max_attempts",
                    self.DEFAULT_MAX_ATTEMPTS,
                )
            )
        ]

    # ========================================================
    # VERIFICAR CONCLUSÃO
    # ========================================================

    def is_complete(
        self,
        context: TaskContext,
    ) -> bool:

        if not context.plan:
            return False

        return all(
            step.get("status") == "completed"
            for step in context.plan
        )

    # ========================================================
    # ESTATÍSTICAS
    # ========================================================

    def get_statistics(
        self,
        context: TaskContext,
    ) -> Dict[str, Any]:

        total = len(context.plan)

        completed = sum(
            step.get("status") == "completed"
            for step in context.plan
        )

        failed = sum(
            step.get("status") == "failed"
            for step in context.plan
        )

        running = sum(
            step.get("status") == "running"
            for step in context.plan
        )

        pending = sum(
            step.get("status") == "pending"
            for step in context.plan
        )

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "completion_percentage": (
                round(completed / total * 100, 2)
                if total
                else 0.0
            ),
            "is_complete": self.is_complete(context),
        }

    # ========================================================
    # EXPORTAR PLANO
    # ========================================================

    def export_plan(
        self,
        context: TaskContext,
    ) -> List[Dict[str, Any]]:

        return deepcopy(context.plan)


# ============================================================
# INSTÂNCIA PRINCIPAL
# ============================================================

planner = TaskPlanner()


__all__ = [
    "TaskPlanner",
    "planner",
]
