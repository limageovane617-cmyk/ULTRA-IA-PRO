# ============================================================
# ALEX IA ULTRA — COMPATIBILIDADE DO MODULO DE IMAGEM
# Motor único: Z-Image Turbo / Hugging Face
# ============================================================

from gerenciador_imagem import (
    MOTOR_IMAGEM,
    gerar_imagem,
    gerar_imagem_zimage,
    mostrar_imagem,
    obter_ultima_imagem,
    obter_caminho_ultima_imagem,
    obter_prompt_ultima_imagem,
    obter_motor_ultima_imagem,
    limpar_ultima_imagem,
)

__all__ = [
    "MOTOR_IMAGEM",
    "gerar_imagem",
    "gerar_imagem_zimage",
    "mostrar_imagem",
    "obter_ultima_imagem",
    "obter_caminho_ultima_imagem",
    "obter_prompt_ultima_imagem",
    "obter_motor_ultima_imagem",
    "limpar_ultima_imagem",
]
