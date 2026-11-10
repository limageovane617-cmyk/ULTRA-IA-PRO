
# ============================================================
# 🧭 ALEX IA ULTRA — ROUTER V10
# Sistema inteligente de roteamento do Ultra Core
# ============================================================

from typing import Any, Dict, List, Optional

from .tools import Tool, ToolRegistry, tool_registry


class ToolRouter:
    """
    Direcionador central de ferramentas da Alex IA Ultra.

    Responsabilidades:
    - Localizar ferramentas registradas.
    - Identificar ferramentas por nome.
    - Identificar ferramentas por palavras-chave.
    - Verificar disponibilidade.
    - Explicar decisões de roteamento.
    - Compartilhar o registry global do Ultra Core.
    """

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
    ) -> None:

        self.registry = (
            registry
            if registry is not None
            else tool_registry
        )

    # ========================================================
    # NORMALIZAÇÃO
    # ========================================================

    @staticmethod
    def _normalize_text(value: Any) -> str:
        """
        Normaliza valores textuais.
        """

        if value is None:
            return ""

        return str(value).strip().lower()

    @classmethod
    def _normalize_keywords(
        cls,
        keywords: Any,
    ) -> List[str]:
        """
        Normaliza palavras-chave sem tratar uma string
        como uma sequência de caracteres individuais.
        """

        if isinstance(keywords, str):
            keywords = [keywords]

        if not isinstance(keywords, (list, tuple, set)):
            return []

        normalized = []

        for keyword in keywords:

            value = cls._normalize_text(keyword)

            if value and value not in normalized:
                normalized.append(value)

        return normalized

    # ========================================================
    # LOCALIZAR FERRAMENTA
    # ========================================================

    def find_tool(
        self,
        requested_tool: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> Optional[Tool]:
        """
        Procura uma ferramenta disponível.

        Prioridade:
        1. Nome exato.
        2. Correspondência por palavras-chave.
        """

        # ----------------------------------------------------
        # BUSCA DIRETA
        # ----------------------------------------------------

        requested_name = self._normalize_text(
            requested_tool
        )

        if requested_name:

            tool = self.registry.get(
                requested_name
            )

            if tool is not None and tool.enabled:
                return tool

        # ----------------------------------------------------
        # BUSCA POR PALAVRAS-CHAVE
        # ----------------------------------------------------

        normalized_keywords = self._normalize_keywords(
            keywords
        )

        if not normalized_keywords:
            return None

        # ----------------------------------------------------
        # PERCORRER REGISTRO
        # ----------------------------------------------------

        for tool_info in self.registry.list_tools():

            if not isinstance(tool_info, dict):
                continue

            if not tool_info.get("enabled", False):
                continue

            tool_name = self._normalize_text(
                tool_info.get("name")
            )

            description = self._normalize_text(
                tool_info.get("description")
            )

            searchable_text = (
                f"{tool_name} {description}"
            )

            if any(
                keyword in searchable_text
                for keyword in normalized_keywords
            ):

                tool = self.registry.get(
                    tool_info.get("name")
                )

                if tool is not None and tool.enabled:
                    return tool

        return None

    # ========================================================
    # ROTEAR ETAPA
    # ========================================================

    def route(
        self,
        step: Dict[str, Any],
    ) -> Optional[Tool]:
        """
        Seleciona a ferramenta adequada para uma etapa.
        """

        if not isinstance(step, dict):
            return None

        requested_tool = step.get("tool")

        keywords = step.get(
            "keywords",
            [],
        )

        return self.find_tool(
            requested_tool=requested_tool,
            keywords=keywords,
        )

    # ========================================================
    # EXPLICAR ROTA
    # ========================================================

    def explain_route(
        self,
        step: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Explica qual ferramenta será utilizada.
        """

        if not isinstance(step, dict):

            return {
                "success": False,
                "tool": None,
                "reason": "A etapa informada é inválida.",
            }

        tool = self.route(step)

        if tool is None:

            requested_tool = step.get("tool")

            return {
                "success": False,
                "tool": None,
                "requested_tool": requested_tool,
                "reason": (
                    "Nenhuma ferramenta compatível "
                    "e habilitada foi encontrada."
                ),
            }

        return {
            "success": True,
            "tool": tool.name,
            "description": tool.description,
            "reason": (
                "Ferramenta encontrada e habilitada "
                "no registro da Alex IA Ultra."
            ),
        }

    # ========================================================
    # FERRAMENTAS DISPONÍVEIS
    # ========================================================

    def available_tools(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Retorna as ferramentas registradas.
        """

        return self.registry.list_tools()

    # ========================================================
    # VERIFICAR EXISTÊNCIA
    # ========================================================

    def has_tool(
        self,
        tool_name: str,
    ) -> bool:
        """
        Verifica se uma ferramenta está registrada
        e habilitada.
        """

        if not isinstance(tool_name, str):
            return False

        tool = self.registry.get(
            tool_name.strip()
        )

        return (
            tool is not None
            and tool.enabled is True
        )

    # ========================================================
    # CONTAGEM DE FERRAMENTAS
    # ========================================================

    def count_available_tools(self) -> int:
        """
        Conta as ferramentas habilitadas.
        """

        return sum(
            1
            for item in self.registry.list_tools()
            if isinstance(item, dict)
            and item.get("enabled") is True
        )


# ============================================================
# INSTÂNCIA PRINCIPAL
# ============================================================

# Compartilha exatamente o mesmo registro utilizado
# pelo Tool Loader e pelo restante do Ultra Core.

router = ToolRouter(
    registry=tool_registry
)


# ============================================================
# EXPORTAÇÕES
# ============================================================

__all__ = [
    "ToolRouter",
    "router",
]
