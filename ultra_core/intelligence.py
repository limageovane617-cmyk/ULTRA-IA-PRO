# ============================================================
# 🧠 ALEX IA ULTRA — INTELLIGENCE BRIDGE
# Ponte entre o Ultra Core e o modelo de linguagem
# ============================================================

from typing import Any, Dict, Optional

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
            "do usuário e executou as ferramentas necessárias.\n\n"

            "Sua função é transformar os resultados verificados "
            "pelo Ultra Core em uma resposta final útil, clara e "
            "fiel aos dados disponíveis.\n\n"

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

            "REGRAS IMPORTANTES:\n"
            "- Responda sempre em português do Brasil.\n"
            "- Seja clara, objetiva e útil.\n"
            "- Use prioritariamente os resultados fornecidos "
            "pelo Ultra Core.\n"
            "- Não invente fatos, resultados, fontes, títulos "
            "ou URLs.\n"
            "- Quando uma ferramenta de pesquisa fornecer "
            "resultados, use esses resultados como base da resposta.\n"
            "- Quando os resultados da pesquisa contiverem "
            "'fontes' ou 'resultados' com URLs, preserve essas "
            "URLs exatamente como foram fornecidas.\n"
            "- Se o usuário pedir fontes, referências, links ou "
            "citações, inclua explicitamente as fontes encontradas "
            "na resposta.\n"
            "- Mesmo quando o usuário não pedir fontes, se a resposta "
            "depender de uma pesquisa recente, inclua uma seção curta "
            "de 'Fontes' com as fontes utilizadas.\n"
            "- Não diga que pesquisou algo se não houver resultado "
            "de pesquisa.\n"
            "- Não transforme uma fonte em outra fonte diferente.\n"
            "- Se houver informações conflitantes entre fontes, "
            "informe claramente que existe divergência.\n"
            "- Não invente informações que não estejam disponíveis "
            "nos resultados ou que não possam ser sustentadas por eles.\n"
            "- Quando houver títulos e URLs nos resultados, associe "
            "cada fonte ao respectivo título quando isso for útil.\n\n"

            "FORMATO PARA PESQUISAS:\n"
            "Quando houver pesquisa na internet, responda primeiro "
            "à pergunta do usuário e depois apresente uma seção "
            "'Fontes utilizadas' contendo as fontes realmente "
            "fornecidas pela ferramenta.\n"
        )

    def generate_response(
        self,
        context: TaskContext,
        gemini_bridge: Optional[Any] = None,
    ) -> str:
        """
        Gera a resposta final usando o GeminiBridge.

        O Ultra Core continua funcionando mesmo quando
        o GeminiBridge não estiver disponível.
        """

        prompt = self.build_prompt(context)

        # Gemini é opcional.
        if gemini_bridge is None:
            return ""

        try:
            resposta = gemini_bridge.gerar_resposta(prompt)

            return resposta or ""

        except Exception as exc:
            context.add_error(
                source="gemini_bridge",
                message="Erro ao gerar resposta com Gemini",
                details=str(exc),
            )

            return ""


# Instância principal da inteligência
intelligence = UltraIntelligence()
