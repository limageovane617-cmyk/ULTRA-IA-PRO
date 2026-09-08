# ============================================================
# 🧭 ALEX IA ULTRA — ROUTER
# Direcionador de tarefas e ferramentas do Ultra Core
# ============================================================

from typing import Any, Dict, List, Optional

from .tools import Tool, ToolRegistry, tool_registry


class ToolRouter:
    """
    Decide qual ferramenta deve atender uma determinada tarefa.
    """

    def __init__(
        self,
        registry: ToolRegistry = tool_registry,
    ) -> None:
        self.registry = registry

    def find_tool(
        self,
        requested_tool: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> Optional[Tool]:
        """
        Procura uma ferramenta disponível.

        Primeiro tenta encontrar pelo nome exato.
        Se não encontrar, tenta localizar por palavras-chave.
        """

        if requested_tool:
            tool = self.registry.get(requested_tool)

            if tool and tool.enabled:
                return tool

        if not keywords:
            return None

        normalized_keywords = [
            keyword.lower().strip()
            for keyword in keywords
            if keyword
        ]

        for tool_info in self.registry.list_tools():
            if not tool_info["enabled"]:
                continue

            searchable_text = (
                f"{tool_info['name']} "
                f"{tool_info['description']}"
            ).lower()

            if any(
                keyword in searchable_text
                for keyword in normalized_keywords
            ):
                return self.registry.get(tool_info["name"])

        return None

    def route(
        self,
        step: Dict[str, Any],
    ) -> Optional[Tool]:
        """
        Escolhe a ferramenta para uma etapa do plano.
        """

        requested_tool = step.get("tool")

        keywords = step.get("keywords", [])

        return self.find_tool(
            requested_tool=requested_tool,
            keywords=keywords,
        )

    def explain_route(
        self,
        step: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Explica qual ferramenta foi escolhida para a etapa.
        """

        tool = self.route(step)

        if tool is None:
            return {
                "success": False,
                "tool": None,
                "reason": (
                    "Nenhuma ferramenta compatível "
                    "foi encontrada."
                ),
            }

        return {
            "success": True,
            "tool": tool.name,
            "description": tool.description,
            "reason": (
                "Ferramenta encontrada no registro "
                "da Ultra."
            ),
        }

    def available_tools(self) -> List[Dict[str, Any]]:
        """
        Retorna as ferramentas atualmente disponíveis.
        """

        return self.registry.list_tools()


# ============================================================
# INSTÂNCIA PADRÃO
# ============================================================

router = ToolRouter()


__all__ = [
    "ToolRouter",
    "router",
]
