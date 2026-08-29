#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
teste_cliente_ponte.py

Teste automatizado para o cliente oficial cliente_ponte_alex.py.

Valida:
1. Leitura segura do segredo de ambiente.
2. Conexao com a Ponte Alex v2 via HTTPS.
3. Teste do endpoint de ping.
4. Envio de arquivo Python para processamento.
5. Transformacao do codigo.
6. Validacao da sintaxe Python.
7. Execucao do codigo na Ponte.
8. Download do arquivo processado.
9. Validacao do arquivo baixado.
10. Execucao local do arquivo baixado.
"""

import os
import sys
import subprocess
from pathlib import Path

from cliente_ponte_alex import ClientePonteAlex, ErroPonteAlex


def executar_teste_automatizado():

    print("=" * 65)
    print("INICIANDO TESTE AUTOMATIZADO: cliente_ponte_alex.py")
    print("=" * 65)

    # ============================================================
    # 1. VERIFICAR SEGREDO
    # ============================================================

    segredo_presente = bool(
        os.environ.get("PONTE_API_SECRET", "").strip()
    )

    if not segredo_presente:
        print("ERRO: PONTE_API_SECRET nao esta configurada.")
        sys.exit(1)

    print(
        "1. PONTE_API_SECRET configurado com sucesso."
    )

    # ============================================================
    # 2. URL DA PONTE
    # ============================================================

    url_teste = (
        os.environ.get("PONTE_API_URL")
        or "https://ponte-alex-v2.dockhosting.dev"
    )

    print(f"2. Conectando a Ponte Alex v2 em: {url_teste}")

    cliente = ClientePonteAlex(base_url=url_teste)

    # ============================================================
    # 3. TESTE DE PING
    # ============================================================

    print()
    print("3. Testando Health Check:")
    print("   GET /api/ponte/v2/ping")

    try:

        dados_ping = cliente.ping()

        print(
            f"   Status: {dados_ping.get('status')}"
        )

        print(
            f"   Versao: {dados_ping.get('version')}"
        )

        print(
            f"   Runtime: {dados_ping.get('pythonRuntime')}"
        )

        assert (
            dados_ping.get("status") == "online"
        ), "Status do ping deve ser online."

        print("   Ping concluido com sucesso.")

    except Exception as e:

        print(f"   FALHA NO PING: {e}")
        sys.exit(1)

    # ============================================================
    # 4. CRIAR ARQUIVO TEMPORARIO
    # ============================================================

    arquivo_entrada = Path(
        "temp_script_teste_entrada.py"
    )

    arquivo_saida_esperada = Path(
        "temp_script_teste_saida.py"
    )

    codigo_original = (
        'def executar():\n'
        '    status = "TESTE_ORIGINAL_PENDENTE"\n'
        '    print(f"EXECUCAO_CLIENTE: {status}")\n'
        '    return 0\n'
        '\n'
        'if __name__ == "__main__":\n'
        '    executar()\n'
    )

    with open(
        arquivo_entrada,
        "w",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(codigo_original)

    print()
    print(
        "4. Arquivo de teste criado:"
    )

    print(
        f"   {arquivo_entrada.name}"
    )

    print(
        f"   Tamanho: {arquivo_entrada.stat().st_size} bytes"
    )

    # ============================================================
    # 5. INSTRUCAO DE TRANSFORMACAO
    # ============================================================

    instrucao_transformacao = (
        'Substituir "TESTE_ORIGINAL_PENDENTE" '
        'por "TESTE_INTEGRACAO_CLIENTE_SUCESSO"'
    )

    print()
    print(
        "5. Enviando arquivo para processamento:"
    )

    print(
        "   POST /api/ponte/v2/processar"
    )

    print(
        f"   Instrucao: {instrucao_transformacao}"
    )

    try:

        # ========================================================
        # 6. PROCESSAR ARQUIVO
        # ========================================================

        resultado = cliente.processar_arquivo(
            caminho_arquivo=str(
                arquivo_entrada
            ),
            instrucao=instrucao_transformacao,
            arquivo_saida=str(
                arquivo_saida_esperada
            ),
            destino_local=str(
                arquivo_saida_esperada
            )
        )

        print()
        print(
            "6. Resposta recebida da Ponte Alex v2:"
        )

        print(
            f"   HTTP Status: {resultado['status_http']}"
        )

        print(
            f"   Test Passed: {resultado['test_passed']}"
        )

        print(
            f"   Mensagem: {resultado['test_message']}"
        )

        print(
            "   Exit Code Python: "
            f"{resultado['execution'].get('exitCode')}"
        )

        print(
            "   Saida Python:"
        )

        print(
            resultado['execution']
            .get('stdout', '')
            .strip()
        )

        print(
            f"   Download URL: {resultado['download_url']}"
        )

        print(
            "   Arquivo salvo localmente: "
            f"{resultado['arquivo_salvo']}"
        )

        print(
            f"   Tamanho: {resultado['tamanho_bytes']} bytes"
        )

        # ========================================================
        # 7. VALIDACOES
        # ========================================================

        print()
        print(
            "7. Executando validacoes..."
        )

        assert (
            resultado["status_http"] == 200
        ), (
            "HTTP deve ser 200. "
            f"Recebido: {resultado['status_http']}"
        )

        assert (
            resultado["test_passed"] is True
        ), (
            "test_passed deve ser True."
        )

        assert (
            resultado["execution"].get("exitCode") == 0
        ), (
            "Exit Code Python deve ser 0."
        )

        stdout = (
            resultado["execution"]
            .get("stdout", "")
        )

        assert (
            "TESTE_INTEGRACAO_CLIENTE_SUCESSO"
            in stdout
        ), (
            "A saida Python deve conter "
            "o texto transformado."
        )

        assert (
            arquivo_saida_esperada.exists()
        ), (
            "O arquivo baixado deve existir."
        )

        assert (
            arquivo_saida_esperada.stat().st_size > 0
        ), (
            "O arquivo baixado nao pode estar vazio."
        )

        print(
            "   Validacoes da resposta: OK"
        )

        # ========================================================
        # 8. VERIFICAR CONTEUDO DO ARQUIVO
        # ========================================================

        conteudo_baixado = (
            arquivo_saida_esperada.read_text(
                encoding="utf-8"
            )
        )

        assert (
            "TESTE_INTEGRACAO_CLIENTE_SUCESSO"
            in conteudo_baixado
        ), (
            "O arquivo baixado nao contem "
            "o codigo transformado."
        )

        print(
            "   Conteudo do arquivo baixado: OK"
        )

        # ========================================================
        # 9. EXECUTAR ARQUIVO LOCALMENTE
        # ========================================================

        print()
        print(
            "8. Executando localmente "
            "o arquivo baixado..."
        )

        proc_local = subprocess.run(
            [
                sys.executable,
                str(arquivo_saida_esperada)
            ],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert (
            proc_local.returncode == 0
        ), (
            "Execucao local deve retornar "
            "Exit Code 0."
        )

        assert (
            "TESTE_INTEGRACAO_CLIENTE_SUCESSO"
            in proc_local.stdout
        ), (
            "A execucao local nao apresentou "
            "o texto transformado."
        )

        print(
            "   Execucao local: SUCESSO"
        )

        print(
            f"   Exit Code: {proc_local.returncode}"
        )

        print(
            f"   Saida: {proc_local.stdout.strip()}"
        )

        # ========================================================
        # 10. TESTE APROVADO
        # ========================================================

        print()
        print(
            "TESTE COMPLETO APROVADO!"
        )

    except ErroPonteAlex as e:

        print()
        print(
            "FALHA NA PONTE ALEX:"
        )

        print(
            str(e)
        )

        if e.detalhes:

            print(
                "Detalhes:"
            )

            print(
                e.detalhes
            )

        sys.exit(1)

    except AssertionError as e:

        print()
        print(
            "FALHA DE VALIDACAO:"
        )

        print(
            str(e)
        )

        sys.exit(1)

    except Exception as e:

        print()
        print(
            "ERRO INESPERADO:"
        )

        print(
            str(e)
        )

        sys.exit(2)

    finally:

        # ========================================================
        # LIMPEZA
        # ========================================================

        if arquivo_entrada.exists():

            arquivo_entrada.unlink()

        if arquivo_saida_esperada.exists():

            arquivo_saida_esperada.unlink()

    print()
    print("=" * 65)
    print(
        "TODOS OS TESTES DO CLIENTE OFICIAL "
        "FORAM APROVADOS COM SUCESSO!"
    )
    print("=" * 65)


if __name__ == "__main__":
    executar_teste_automatizado()
