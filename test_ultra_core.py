# ============================================================
# 🧪 ALEX IA ULTRA — TESTE DO ULTRA CORE
# ============================================================

from ultra_core.brain import brain
from ultra_core.tools import tool_registry


# ============================================================
# FERRAMENTA DE TESTE
# ============================================================

def ferramenta_teste(mensagem: str) -> dict:
    """
    Ferramenta simples para validar o funcionamento
    do Ultra Core.
    """

    return {
        "status": "ok",
        "mensagem": mensagem,
    }


# ============================================================
# REGISTRAR FERRAMENTA
# ============================================================

tool_registry.register(
    name="teste",
    description="Ferramenta utilizada para testar o Ultra Core.",
    function=ferramenta_teste,
)


# ============================================================
# CRIAR PLANO
# ============================================================

steps = [
    {
        "name": "Executar ferramenta de teste",
        "description": "Executa uma ferramenta simples.",
        "tool": "teste",
        "arguments": {
            "mensagem": "Ultra Core funcionando!",
        },
    }
]


# ============================================================
# EXECUTAR ULTRA CORE
# ============================================================

resultado = brain.run(
    user_request="Teste completo do Ultra Core",
    steps=steps,
)


# ============================================================
# RESULTADO
# ============================================================

print()
print("=" * 60)
print("🧠 ALEX IA ULTRA — TESTE DO ULTRA CORE")
print("=" * 60)

print()
print("Resultado:")
print(resultado)

print()
print("Ferramentas registradas:")

for tool in brain.available_tools():
    print(
        f"- {tool['name']}: "
        f"{tool['description']} "
        f"[habilitada={tool['enabled']}]"
    )

print()
print("=" * 60)

if resultado.get("success"):
    print("✅ ULTRA CORE FUNCIONANDO")
else:
    print("❌ ULTRA CORE PRECISA DE CORREÇÃO")

print("=" * 60)
