#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
teste_ponte_alex.py

Teste da camada de integracao ponte_alex.py.

Este teste verifica:

1. Importacao correta do modulo.
2. Conexao com a Ponte Alex v2.
3. Health Check.
4. Status da Ponte.
5. Comunicacao HTTPS.
"""

import sys

from ponte_alex import (
    verificar_ponte,
    ponte_disponivel,
    obter_status_ponte,
)


def executar_teste():

    print("=" * 65)
    print("TESTE DA CAMADA DE INTEGRACAO - PONTE ALEX")
    print("=" * 65)

    # ============================================================
    # 1. TESTAR IMPORTACAO
    # ============================================================

    print()
    print("1. Modulo ponte_alex importado com sucesso.")

    # ============================================================
    # 2. TESTAR PING
    # ============================================================

    print()
    print("2. Testando comunicacao com a Ponte Alex v2...")

    try:

        dados = verificar_ponte()

        print(
            f"   Status: {dados.get('status')}"
        )

        print(
            f"   Ponte: {dados.get('ponte')}"
        )

        print(
            f"   Versao: {dados.get('version')}"
        )

        print(
            f"   Python: {dados.get('pythonRuntime')}"
        )

        if dados.get("status") != "online":

            print()
            print("ERRO: A Ponte nao esta online.")

            sys.exit(1)

        print(
            "   Comunicacao HTTPS: OK"
        )

    except Exception as erro:

        print()
        print("FALHA NA COMUNICACAO COM A PONTE:")
        print(erro)

        sys.exit(1)

    # ============================================================
    # 3. TESTAR ponte_disponivel
    # ============================================================

    print()
    print("3. Testando funcao ponte_disponivel()...")

    disponivel = ponte_disponivel()

    print(
        f"   Ponte disponivel: {disponivel}"
    )

    if not disponivel:

        print()
        print("ERRO: ponte_disponivel() retornou False.")

        sys.exit(1)

    print(
        "   Funcao ponte_disponivel(): OK"
    )

    # ============================================================
    # 4. TESTAR STATUS
    # ============================================================

    print()
    print("4. Testando obter_status_ponte()...")

    status = obter_status_ponte()

    print(
        f"   Online: {status.get('online')}"
    )

    print(
        f"   Status: {status.get('status')}"
    )

    print(
        f"   Ponte: {status.get('ponte')}"
    )

    print(
        f"   Versao: {status.get('version')}"
    )

    print(
        f"   Runtime: {status.get('pythonRuntime')}"
    )

    if not status.get("online"):

        print()
        print("ERRO: obter_status_ponte() indicou que a Ponte esta offline.")

        sys.exit(1)

    print(
        "   obter_status_ponte(): OK"
    )

    # ============================================================
    # 5. RESULTADO
    # ============================================================

    print()
    print("=" * 65)
    print("TESTE DA CAMADA DE INTEGRACAO APROVADO!")
    print("=" * 65)


if __name__ == "__main__":
    executar_teste()
