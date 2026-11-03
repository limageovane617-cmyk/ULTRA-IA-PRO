# ============================================================
# 🧠 ALEX IA ULTRA — BRAIN
# Cérebro central do Ultra Core
# ============================================================

from typing import Any, Dict, List, Optional
from uuid import uuid4

from .context import TaskContext
from .interpreter import TaskInterpreter, interpreter
from .planner import TaskPlanner, planner
from .router import ToolRouter, router
from .executor import TaskExecutor, executor
from .verifier import ResultVerifier, verifier
from .intelligence import UltraIntelligence, intelligence
from gemini_bridge import GeminiBridge


class UltraBrain:
    """
    Coordenador central da Alex IA Ultra.
    """

    def __init__(
        self,
        task_interpreter: TaskInterpreter = interpreter,
        task_planner: TaskPlanner = planner,
        task_router: ToolRouter = router,
        task_executor: TaskExecutor = executor,
        result_verifier: ResultVerifier = verifier,
        task_intelligence: UltraIntelligence = intelligence,
        gemini_bridge: Optional[GeminiBridge] = None,
    ) -> None:

        self.interpreter = task_interpreter
        self.planner = task_planner
        self.router = task_router
        self.executor = task_executor
        self.verifier = result_verifier
        self.intelligence = task_intelligence
        self.gemini_bridge = gemini_bridge

    # ========================================================
    # 🧠 INTERPRETAÇÃO
    # ========================================================

    def interpret(
        self,
        user_request: str,
    ) -> Dict[str, Any]:

        return self.interpreter.interpret(
            user_request
        )

    # ========================================================
    # 📝 CRIAÇÃO DE TAREFA
    # ========================================================

    def create_task(
        self,
        user_request: str,
    ) -> TaskContext:

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
    # 🧠 PREPARAÇÃO DA TAREFA
    # ========================================================

    def prepare_task(
        self,
        context: TaskContext,
    ) -> Dict[str, Any]:

        interpretation = self.interpret(
            context.user_request
        )

        if not interpretation.get("success"):

            context.add_error(
                source="interpreter",
                message=interpretation.get(
                    "message",
                    "Não foi possível interpretar o pedido.",
                ),
            )

            context.update_status(
                "interpretation_failed"
            )

            return interpretation

        context.set_metadata(
            "intent",
            interpretation.get("intent"),
        )

        context.set_metadata(
            "keywords",
            interpretation.get("keywords", []),
        )

        context.set_metadata(
            "confidence",
            interpretation.get("confidence", 0.0),
        )

        context.set_metadata(
            "prompt",
            interpretation.get("prompt", ""),
        )

        context.set_metadata(
            "suggested_tools",
            interpretation.get("suggested_tools", []),
        )

        context.set_metadata(
            "original_request",
            interpretation.get(
                "original_request",
                context.user_request,
            ),
        )

        # Marca que a interpretação já foi realizada.
        context.set_metadata(
            "_prepared",
            True,
        )

        context.update_status(
            "interpreted"
        )

        return interpretation

    # ========================================================
    # 📝 PLANEJAMENTO
    # ========================================================

    def plan_task(
        self,
        context: TaskContext,
        steps: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        plan = self.planner.create_plan(
            context,
            steps,
        )

        keywords = context.get_metadata(
            "keywords",
            [],
        )

        prompt = context.get_metadata(
            "prompt",
            "",
        )

        for step in plan:

            if "keywords" not in step:
                step["keywords"] = list(keywords)

            arguments = step.setdefault(
                "arguments",
                {},
            )

            if (
                prompt
                and "prompt" not in arguments
            ):
                arguments["prompt"] = prompt

        context.touch()

        return plan

    # ========================================================
    # 🤖 CRIAÇÃO AUTOMÁTICA DE PLANO
    # ========================================================

    def create_intelligent_plan(
        self,
        context: TaskContext,
    ) -> List[Dict[str, Any]]:

        # Evita executar o Interpreter duas vezes.
        if context.get_metadata("_prepared", False):

            interpretation = {
                "success": True,
                "intent": context.get_metadata(
                    "intent",
                    "geral",
                ),
                "keywords": context.get_metadata(
                    "keywords",
                    [],
                ),
                "suggested_tools": context.get_metadata(
                    "suggested_tools",
                    [],
                ),
                "prompt": context.get_metadata(
                    "prompt",
                    "",
                ),
            }

        else:

            interpretation = self.prepare_task(
                context
            )

        if not interpretation.get("success"):
            return []

        intent = interpretation.get(
            "intent",
            "geral",
        )

        keywords = interpretation.get(
            "keywords",
            [],
        )

        suggested_tools = interpretation.get(
            "suggested_tools",
            [],
        )

        prompt = interpretation.get(
            "prompt",
            "",
        )

        # Procura uma ferramenta sugerida e registrada.
        selected_tool = None

        for tool_name in suggested_tools:

            tool = self.router.registry.get(
                tool_name
            )

            if tool and tool.enabled:
                selected_tool = tool.name
                break

        step = {
            "name": f"Executar tarefa: {intent}",
            "description": (
                "Etapa criada automaticamente "
                "pelo cérebro da Ultra."
            ),
            "tool": selected_tool,
            "keywords": keywords,
            "arguments": {
                "prompt": prompt,
            },
        }

        return self.plan_task(
            context,
            [step],
        )

    # ========================================================
    # 🔧 FERRAMENTAS
    # ========================================================

    def available_tools(
        self,
    ) -> List[Dict[str, Any]]:

        return self.router.available_tools()

    # ========================================================
    # 🧭 EXPLICAR ROTA
    # ========================================================

    def explain_route(
        self,
        context: TaskContext,
    ) -> Dict[str, Any]:

        if not context.plan:

            return {
                "success": False,
                "tool": None,
                "reason": (
                    "A tarefa ainda não possui "
                    "um plano."
                ),
            }

        return self.router.explain_route(
            context.plan[0]
        )

    # ========================================================
    # ⚙️ EXECUÇÃO
    # ========================================================

    def execute(
        self,
        context: TaskContext,
        *,
        stop_on_error: bool = True,
    ) -> Dict[str, Any]:

        if not context.plan:

            return {
                "success": False,
                "status": "no_plan",
                "message": (
                    "A tarefa ainda não possui "
                    "um plano de execução."
                ),
            }

        return self.executor.execute_all(
            context,
            stop_on_error=stop_on_error,
        )

    # ========================================================
    # 🔍 VERIFICAÇÃO
    # ========================================================

    def verify(
        self,
        context: TaskContext,
    ) -> Dict[str, Any]:

        return self.verifier.verify_context(
            context
        )

    # ========================================================
    # 🧠 RESPOSTA FINAL
    # ========================================================

    def generate_response(
        self,
        context: TaskContext,
    ) -> str:

        if self.gemini_bridge is None:
            return ""

        return self.intelligence.generate_response(
            context=context,
            gemini_bridge=self.gemini_bridge,
        )

    # ========================================================
    # 🚀 CICLO COMPLETO
    # ========================================================

    def run(
        self,
        user_request: str,
        steps: Optional[List[Dict[str, Any]]] = None,
        *,
        stop_on_error: bool = True,
        history: Any = None,
        file_context: Optional[str] = None,
        file_name: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executa o ciclo completo da Ultra.

        Suporta:
        - Histórico da conversa.
        - Contexto de arquivos.
        - Nome do arquivo.
        - Imagens para análise visual.
        """

        context = self.create_task(
            user_request
        )

        # ----------------------------------------------------
        # CONTEXTO ADICIONAL
        # ----------------------------------------------------

        if history is not None:
            context.set_metadata(
                "history",
                history,
            )

        if file_context is not None:
            context.set_metadata(
                "file_context",
                file_context,
            )

        if file_name is not None:
            context.set_metadata(
                "file_name",
                file_name,
            )

        # ----------------------------------------------------
        # IMAGEM
        # ----------------------------------------------------

        if image_bytes is not None:

            if not isinstance(image_bytes, (bytes, bytearray)):
                raise TypeError(
                    "image_bytes precisa ser bytes ou bytearray."
                )

            if not image_bytes:
                raise ValueError(
                    "A imagem enviada está vazia."
                )

            context.set_metadata(
                "image_bytes",
                bytes(image_bytes),
            )

            context.set_metadata(
                "image_mime_type",
                image_mime_type or "image/jpeg",
            )

        # ----------------------------------------------------
        # INTERPRETAÇÃO
        # ----------------------------------------------------

        interpretation = self.prepare_task(
            context
        )

        if not interpretation.get("success"):

            return {
                "success": False,
                "status": context.status,
                "task_id": context.task_id,
                "interpretation": interpretation,
                "context": context.summary(),
            }

        # ----------------------------------------------------
        # PLANEJAMENTO
        # ----------------------------------------------------

        if steps:

            self.plan_task(
                context,
                steps,
            )

        else:

            self.create_intelligent_plan(
                context
            )

        if not context.plan:

            context.update_status(
                "waiting_for_plan"
            )

            return {
                "success": False,
                "status": "waiting_for_plan",
                "task_id": context.task_id,
                "interpretation": interpretation,
                "context": context.summary(),
                "message": (
                    "Não foi possível criar "
                    "um plano para esta tarefa."
                ),
            }

        # ----------------------------------------------------
        # EXECUÇÃO
        # ----------------------------------------------------

        execution = self.execute(
            context,
            stop_on_error=stop_on_error,
        )

        # ----------------------------------------------------
        # VERIFICAÇÃO
        # ----------------------------------------------------

        verification = self.verify(
            context
        )

        # ----------------------------------------------------
        # RESULTADO FINAL
        # ----------------------------------------------------

        success = (
            execution.get("success", False)
            and verification.get("success", False)
        )

        if success:

            context.update_status(
                "completed"
            )

        # ----------------------------------------------------
        # RESPOSTA FINAL
        # ----------------------------------------------------

        final_response = self.generate_response(
            context
        )

        return {
            "success": success,
            "task_id": context.task_id,
            "status": context.status,
            "interpretation": interpretation,
            "plan": context.plan,
            "execution": execution,
            "verification": verification,
            "final_response": final_response,
            "context": context.summary(),
        }


# ============================================================
# 🧠 INSTÂNCIA PRINCIPAL
# ============================================================

brain = UltraBrain()


__all__ = [
    "UltraBrain",
    "brain",
]
