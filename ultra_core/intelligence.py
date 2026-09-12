# ============================================================
# 🧠 ALEX IA ULTRA — INTELLIGENCE BRIDGE
# Ponte entre o Ultra Core e o modelo de linguagem
# ============================================================

from typing import Any, Dict

from .context import TaskContext


class UltraIntelligence:
    """
    Ponte de inteligência do Ultra Core.

    Prepara o resultado processado pelo cérebro da Ultra
    para ser utilizado pelo modelo de linguagem.
    """

    def build_context(
        self,
        context: TaskContext,
    ) -> Dict[str, Any]:
        """
        Organiza o contexto completo da tarefa.
        """

        return {
            "user_request": context.user_request,
            "status": context.status,
            "plan": context.plan,
            "tool_results": context.tool_results,
            "errors": context.errors,
            "metadata": context.metadata,
        }

    def build_prompt(
        self,
        context: TaskContext,
    ) -> str:
        """
        Converte o contexto do Ultra Core em um prompt
        para o modelo de linguagem.
        """

        dados = self.build_context(context)

        return (
            "Você é a inteligência da Alex IA Ultra.\n\n"
            "O Ultra Core analisou e processou a solicitação "
            "do usuário.\n\n"

            "Use os resultados das ferramentas para construir "
            "a resposta final.\n\n"

            "SOLICITAÇÃO DO USUÁRIO:\n"
            f"{dados['user_request']}\n\n"

            "STATUS DA TAREFA:\n"
            f"{dados['status']}\n\n"

            "PLANO EXECUTADO:\n"
            f"{dados['plan']}\n\n"

            "RESULTADOS DAS FERRAMENTAS:\n"
            f"{dados['tool_results']}\n\n"

            "ERROS REGISTRADOS:\n"
            f"{dados['errors']}\n\n"

            "INSTRUÇÕES:\n"
            "- Responda em português do Brasil.\n"
            "- Seja clara e objetiva.\n"
            "- Use os resultados verificados pelo Ultra Core.\n"
            "- Não invente informações que não estejam disponíveis.\n"
        )


# Instância principal da inteligência
intelligence = UltraIntelligence()
