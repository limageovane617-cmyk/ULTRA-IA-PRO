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
    - Interpretação básica
    - Planejamento
    - Roteamento
    - Execução
    - Verificação

    O Brain não executa diretamente as ferramentas.

    Ele entende a solicitação, cria um plano e entrega
    a execução para o restante do Ultra Core.
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
    # NORMALIZAÇÃO
    # ========================================================

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:
        """
        Normaliza texto para facilitar a interpretação.
        """

        return " ".join(
            str(text or "")
            .lower()
            .strip()
            .split()
        )

    # ========================================================
    # IDENTIFICAÇÃO DE INTENÇÃO
    # ========================================================

    def detect_intent(
        self,
        user_request: str,
    ) -> Dict[str, Any]:
        """
        Detecta a intenção básica do usuário.

        Esta camada não utiliza IA externa.
        Ela funciona como primeira camada determinística
        do Ultra Core.

        Futuramente pode ser substituída ou complementada
        por um modelo de linguagem.
        """

        texto = self._normalize_text(
            user_request
        )

        if not texto:
            return {
                "intent": "unknown",
                "keywords": [],
                "confidence": 0.0,
            }

        palavras_imagem = [
            "imagem",
            "imagens",
            "foto",
            "fotografia",
            "desenho",
            "ilustração",
            "ilustracao",
            "picture",
            "image",
            "gerar imagem",
            "criar imagem",
            "fazer imagem",
        ]

        palavras_video = [
            "vídeo",
            "video",
            "vídeos",
            "videos",
            "filme",
            "animação",
            "animacao",
            "clipe",
            "clip",
            "gerar vídeo",
            "gerar video",
            "criar vídeo",
            "criar video",
            "animar",
        ]

        palavras_texto = [
            "texto",
            "escrever",
            "escreva",
            "redigir",
            "resumo",
            "resumir",
            "explicar",
            "explicação",
            "explicacao",
            "traduzir",
            "tradução",
            "traducao",
        ]

        imagem_encontrada = any(
            palavra in texto
            for palavra in palavras_imagem
        )

        video_encontrado = any(
            palavra in texto
            for palavra in palavras_video
        )

        texto_encontrado = any(
            palavra in texto
            for palavra in palavras_texto
        )

        if video_encontrado:
            intent = "video"
            confidence = 0.90

        elif imagem_encontrada:
            intent = "imagem"
            confidence = 0.90

        elif texto_encontrado:
            intent = "texto"
            confidence = 0.75

        else:
            intent = "geral"
            confidence = 0.40

        keywords = []

        if imagem_encontrada:
            keywords.extend(
                [
                    "imagem",
                    "image",
                    "foto",
                    "gerar",
                ]
            )

        if video_encontrado:
            keywords.extend(
                [
                    "video",
                    "vídeo",
                    "gerar",
                    "animar",
                ]
            )

        if texto_encontrado:
            keywords.extend(
                [
                    "texto",
                    "escrever",
                    "gerar",
                ]
            )

        if not keywords:
            keywords = [
                palavra
                for palavra in texto.split()
                if len(palavra) >= 4
            ][:8]

        return {
            "intent": intent,
            "keywords": keywords,
            "confidence": confidence,
        }

    # ========================================================
    # EXTRAÇÃO DO PEDIDO PRINCIPAL
    # ========================================================

    @staticmethod
    def extract_prompt(
        user_request: str,
    ) -> str:
        """
        Extrai o conteúdo principal do pedido.

        Não tenta reescrever o pedido.
        Apenas remove comandos muito comuns do início.
        """

        texto = str(
            user_request or ""
        ).strip()

        if not texto:
            return ""

        prefixos = [
            "gerar uma imagem de ",
            "gerar uma imagem ",
            "criar uma imagem de ",
            "criar uma imagem ",
            "fazer uma imagem de ",
            "fazer uma imagem ",
            "gere uma imagem de ",
            "gere uma imagem ",
            "crie uma imagem de ",
            "crie uma imagem ",
            "gerar um vídeo de ",
            "gerar um vídeo ",
            "gerar um video de ",
            "gerar um video ",
            "criar um vídeo de ",
            "criar um vídeo ",
            "criar um video de ",
            "criar um video ",
            "animar ",
        ]

        texto_lower = texto.lower()

        for prefixo in prefixos:

            if texto_lower.startswith(prefixo):

                return texto[
                    len(prefixo):
                ].strip()

        return texto

    # ========================================================
    # LOCALIZAÇÃO DE FERRAMENTA
    # ========================================================

    def _find_tool_for_intent(
        self,
        intent: str,
        keywords: List[str],
    ) -> Any:
        """
        Procura uma ferramenta compatível com a intenção.
        """

        tool_names = []

        if intent == "imagem":
            tool_names = [
                "imagem.gerar",
                "gerar_imagem",
                "image.generate",
                "image_generator",
            ]

        elif intent == "video":
            tool_names = [
                "video.gerar",
                "video.texto",
                "video.imagem",
                "video.fallback",
                "gerar_video",
            ]

        elif intent == "texto":
            tool_names = [
                "texto.gerar",
                "text.gerar",
                "gerar_texto",
            ]

        for nome in tool_names:

            try:

                tool = self.router.find_tool(
                    requested_tool=nome,
                )

                if tool is not None:
                    return tool

            except Exception:
                continue

        try:

            return self.router.find_tool(
                keywords=keywords,
            )

        except Exception:

            return None

    # ========================================================
    # ARGUMENTOS AUTOMÁTICOS
    # ========================================================

    def _build_tool_arguments(
        self,
        tool: Any,
        user_request: str,
        intent: str,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        Monta argumentos compatíveis com as ferramentas
        conhecidas pelo Ultra Core.

        O método mantém argumentos simples para evitar
        acoplamento excessivo entre Brain e ferramentas.
        """

        nome = str(
            getattr(
                tool,
                "name",
                "",
            )
        ).lower()

        argumentos: Dict[str, Any] = {}

        # ----------------------------------------------------
        # IMAGEM
        # ----------------------------------------------------

        if (
            intent == "imagem"
            or "imagem" in nome
            or "image" in nome
        ):

            argumentos["prompt"] = prompt

            return argumentos

        # ----------------------------------------------------
        # VÍDEO
        # ----------------------------------------------------

        if (
            intent == "video"
            or "video" in nome
        ):

            argumentos["prompt"] = prompt

            return argumentos

        # ----------------------------------------------------
        # TEXTO
        # ----------------------------------------------------

        if (
            intent == "texto"
            or "texto" in nome
            or "text" in nome
        ):

            argumentos["prompt"] = prompt

            return argumentos

        # ----------------------------------------------------
        # FERRAMENTA GENÉRICA
        # ----------------------------------------------------

        argumentos["prompt"] = prompt

        return argumentos

    # ========================================================
    # PLANEJAMENTO INTELIGENTE
    # ========================================================

    def create_intelligent_plan(
        self,
        context: TaskContext,
    ) -> List[Dict[str, Any]]:
        """
        Interpreta a solicitação e cria automaticamente
        um plano inicial.

        Esta é a primeira camada de inteligência autônoma
        do Ultra Core.
        """

        user_request = context.user_request

        detected = self.detect_intent(
            user_request
        )

        intent = detected["intent"]
        keywords = detected["keywords"]

        prompt = self.extract_prompt(
            user_request
        )

        tool = self._find_tool_for_intent(
            intent,
            keywords,
        )

        if tool is None:

            context.add_error(
                source="brain",
                message=(
                    "Não foi encontrada uma ferramenta "
                    f"compatível com a intenção '{intent}'."
                ),
            )

            context.update_status(
                "planning_failed"
            )

            return []

        arguments = self._build_tool_arguments(
            tool=tool,
            user_request=user_request,
            intent=intent,
            prompt=prompt,
        )

        step = {
            "name": (
                f"Executar tarefa de {intent}"
            ),
            "description": (
                f"Executar a solicitação do usuário "
                f"usando a ferramenta {tool.name}."
            ),
            "tool": tool.name,
            "keywords": keywords,
            "arguments": arguments,
        }

        plano = self.plan_task(
            context,
            [step],
        )

        context.touch()

        return plano

    # ========================================================
    # PLANEJAMENTO MANUAL
    # ========================================================

    def plan_task(
        self,
        context: TaskContext,
        steps: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Cria o plano de execução da tarefa.
        """

        if not steps:

            raise ValueError(
                "O plano precisa possuir pelo menos uma etapa."
            )

        return self.planner.create_plan(
            context,
            steps,
        )

    # ========================================================
    # INSPEÇÃO DAS FERRAMENTAS
    # ========================================================

    def available_tools(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Retorna as ferramentas disponíveis.
        """

        return self.router.available_tools()

    # ========================================================
    # EXPLICAÇÃO DO PLANO
    # ========================================================

    def explain_plan(
        self,
        context: TaskContext,
    ) -> Dict[str, Any]:
        """
        Retorna uma visão resumida do plano atual.
        """

        return {
            "task_id": context.task_id,
            "user_request": context.user_request,
            "status": context.status,
            "steps": context.plan,
        }

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

        return self.executor.execute_all(
            context,
            stop_on_error=stop_on_error,
        )

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
    # CICLO INTELIGENTE
    # ========================================================

    def run(
        self,
        user_request: str,
        steps: Optional[List[Dict[str, Any]]] = None,
        *,
        stop_on_error: bool = True,
        auto_plan: bool = True,
    ) -> Dict[str, Any]:
        """
        Executa o ciclo completo do Ultra Core.

        Fluxo:

        Pedido
          ↓
        Contexto
          ↓
        Interpretação
          ↓
        Plano automático
          ↓
        Router
          ↓
        Executor
          ↓
        Verifier
          ↓
        Resultado
        """

        try:

            context = self.create_task(
                user_request
            )

        except Exception as exc:

            return {
                "success": False,
                "status": "invalid_request",
                "task_id": None,
                "error": str(exc),
            }

        # ====================================================
        # PLANO MANUAL
        # ====================================================

        if steps:

            try:

                self.plan_task(
                    context,
                    steps,
                )

            except Exception as exc:

                context.add_error(
                    source="brain",
                    message=str(exc),
                )

                return {
                    "success": False,
                    "status": "planning_failed",
                    "task_id": context.task_id,
                    "context": context.summary(),
                    "error": str(exc),
                }

        # ====================================================
        # PLANO AUTOMÁTICO
        # ====================================================

        elif auto_plan:

            try:

                plano = (
                    self.create_intelligent_plan(
                        context
                    )
                )

            except Exception as exc:

                context.add_error(
                    source="brain",
                    message=str(exc),
                )

                context.update_status(
                    "planning_failed"
                )

                return {
                    "success": False,
                    "status": "planning_failed",
                    "task_id": context.task_id,
                    "context": context.summary(),
                    "error": str(exc),
                }

            if not plano:

                return {
                    "success": False,
                    "status": "planning_failed",
                    "task_id": context.task_id,
                    "intent": self.detect_intent(
                        user_request
                    ),
                    "context": context.summary(),
                    "message": (
                        "A Ultra entendeu a solicitação, "
                        "mas não encontrou uma ferramenta "
                        "compatível."
                    ),
                }

        # ====================================================
        # SEM PLANO
        # ====================================================

        else:

            context.update_status(
                "waiting_for_plan"
            )

            return {
                "success": False,
                "status": "waiting_for_plan",
                "task_id": context.task_id,
                "context": context.summary(),
                "message": (
                    "A tarefa foi criada, mas nenhum "
                    "plano foi fornecido."
                ),
            }

        # ====================================================
        # EXECUTAR
        # ====================================================

        execution = self.execute(
            context,
            stop_on_error=stop_on_error,
        )

        # ====================================================
        # VERIFICAR
        # ====================================================

        verification = self.verify(
            context,
        )

        sucesso_execucao = bool(
            execution.get(
                "success",
                False,
            )
        )

        sucesso_verificacao = bool(
            verification.get(
                "success",
                False,
            )
        )

        sucesso = (
            sucesso_execucao
            and
            sucesso_verificacao
        )

        # ====================================================
        # STATUS FINAL
        # ====================================================

        if sucesso:

            context.update_status(
                "completed"
            )

        elif context.has_errors():

            context.update_status(
                "failed"
            )

        return {
            "success": sucesso,
            "task_id": context.task_id,
            "status": context.status,
            "intent": self.detect_intent(
                user_request
            ),
            "plan": context.plan,
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
