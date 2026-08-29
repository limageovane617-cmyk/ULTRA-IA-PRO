#!/usr/bin/env python3
# -*- codificação: utf-8 -*-
"""
cliente_ponte_alex.py
Cliente Oficial da Ponte Alex v2 para integração externa segura via HTTPS.

Permite enviar scripts Python para a Ponte Alex v2, aplicar transformações,
validar a sintaxe, executar no interpretador Python e baixar o arquivo resultante.

Uso via Linha de Comando:
    python3 cliente_ponte_alex.py <arquivo.py> --instruction "<instrução>" [--output <saida.py>]

Uso via Módulo Python:
    de cliente_ponte_alex importar ClientePonteAlex
    cliente = ClientePonteAlex()
    resultado = cliente.processar_arquivo(
        caminho_arquivo="meu_script.py",
        instrucao="Substituir '[TESTE]' por '[PRODUÇÃO]'",
        arquivo_saida="meu_script_processado.py"
    )
"""

importar os
importar sys
importar json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_PONTE_URL = "https://ponte-alex-v2.dockhosting.dev"

classe ErroPonteAlex(Exceção):
    """Exceção base para erros de comunicação ou processamento na Ponte Alex v2."""
    def __init__(self, mensagem: str, status_http: Optional[int] = None, detalhes: Optional[Dict[str, Any]] = None):
        super().__init__(mensagem)
        self.status_http = status_http
        self.detalhes = detalhes ou {}


classe ClientePonteAlex:
    """
    Cliente oficial para integração com a API HTTPS da Ponte Alex v2.
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Inicializa o cliente da Ponte Alex v2.
        
        A URL base pode ser fornecida diretamente ou lida da variável PONTE_API_URL.
        O segredo de autenticação é o lido restrito de PONTE_API_SECRET.
        """
        # Determina uma URL base da Ponte Alex v2
        self.base_url = (base_url or os.environ.get("PONTE_API_URL") or DEFAULT_PONTE_URL).rstrip("/")

        # Valida a apresentação do segredo no ambiente sem nunca exibir seu conteúdo
        self._secret = os.environ.get("PONTE_API_SECRET", "").strip()

    def _obter_headers(self) -> Dict[str, str]:
        """Gera os cabeços HTTP necessários sem expor o segredo."""
        se não self._secret:
            levantar ErroPonteAlex(
                "O segredo de autenticação PONTE_API_SECRET não foi encontrado nas variáveis de ambiente. "
                "Configure uma variável PONTE_API_SECRET antes de executar o cliente."
            )
        retornar {
            "Content-Type": "application/json; charset=utf-8",
            "x-api-secret": self._secret,
            "User-Agent": "ClientePonteAlex/2.0"
        }

    def ping(self) -> Dict[str, Any]:
        """
        Executa verificação de status e saúde (health check) na Ponte Alex v2.
        Endpoint público GET /api/ponte/v2/ping.
        """
        url = f"{self.base_url}/api/ponte/v2/ping"
        req = urllib.request.Request(url, headers={"User-Agent": "ClientePonteAlex/2.0"}, method="GET")
        tentar:
            com urllib.request.urlopen(req, timeout=15) como resposta:
                dados = json.loads(response.read().decode("utf-8"))
                retornar dados
        exceto urllib.error.HTTPError como e:
            corpo = e.read().decode("utf-8", errors="replace")
            raise ErroPonteAlex(f"Erro HTTP {e.code} sem ping: {e.reason}", status_http=e.code)
        exceto urllib.error.URLError como e:
            raise ErroPonteAlex(f"Falha de conexão com a Ponte Alex v2 ({url}): {e.reason}")

    def._código(
        auto,
        conteudo_codigo: str,
        instrução: str,
        nome_arquivo:str = "script.py",
        nome_saida: Opcional[str] = Nenhum,
        destino_local: Opcional[str] = Nenhum
    ) -> Dict[str, Any]:
        """
        Envia código Python diretamente para processamento, execução e download do resultado.
        """
        se não conteudo_codigo.strip():
            raise ErroPonteAlex("O conteúdo do código Python não pode estar vazio.")

        se não nome_saida:
            nome_puro = Caminho(nome_arquivo).stem
            nome_saida = f"{nome_puro}_processado.py"

        url_processar = f"{self.base_url}/api/ponte/v2/processar"
        carga útil = {
            "nome do arquivo": nome_arquivo,
            "outputFilename": nome_saida,
            "instrução": instrução,
            "fileContent": conteudo_codigo
        }

        cabeçalhos = self._obter_cabeçalhos()
        dados_envio = json.dumps(carga útil).encode("utf-8")

        req = urllib.request.Request(url_processar, data=dados_envio, headers=headers, method="POST")

        tentar:
            com urllib.request.urlopen(req, timeout=30) como resposta:
                código_de_status = resposta.getcode()
                corpo_resposta = resposta.read().decode("utf-8")
                resultado_json = json.loads(corpo_resposta)
        exceto urllib.error.HTTPError como e:
            código_de_status = e.code
            corpo_erro = e.read().decode("utf-8", erros="replace")
            exceto = {}
            tentar:
                detalhes = json.loads(corpo_erro)
            exceto Exceção:
                detalhes = {"raw_error": corpo_erro}

            se o código de status for igual a 400:
                msg = detalhes.get("error") ou detalhes.get("testMessage") ou "Requisição inválida ou erro de sintaxe Python."
                raise ErroPonteAlex(f"Erro HTTP 400 (Bad Request): {msg}", status_http=400, detalhes=detalhes)
            elif status_code == 401:
                levantar ErroPonteAlex(
                    "Erro HTTP 401 (Não Autorizado): O segredo x-api-secret fornecido foi rejeitado ou está incorreto.",
                    status_http=401,
                    nenhum=detalhes
                )
            elif status_code == 500:
                msg = detalhes.get("error") ou "Erro interno no servidor da Ponte Alex v2."
                raise ErroPonteAlex(f"Erro HTTP 500 (Erro interno do servidor): {msg}", status_http=500, detalhes=detalhes)
            outro:
                raise ErroPonteAlex(f"Erro HTTP {status_code}: {e.reason}", status_http=status_code, detalhes=detalhes)
        exceto urllib.error.URLError como e:
            raise ErroPonteAlex(f"Falha de rede ao conectar a {url_processar}: {e.reason}")

        # Validações de integridade do retorno
        se não resultado_json.get("success"):
            levantar ErroPonteAlex(
                f"A operação não foi bem sucedida: {resultado_json.get('testMessage', 'Sem mensagem')}",
                anexo=resultado_json
            )

        processed_file_info = resultado_json.get("processedFile", {})
        download_url_relativa = processed_file_info.get("downloadUrl", "")

        se não download_url_relativa:
            raise ErroPonteAlex("A Ponte Alex v2 não retornou um downloadUrl válido para o arquivo processado.")

        # Construa URL completa para download
        se download_url_relativa.startswith("http://") ou download_url_relativa.startswith("https://"):
            url_download_completa = download_url_relativa
        outro:
            url_download_completa = urllib.parse.urljoin(self.base_url, download_url_relativa)

        # Realiza o download do arquivo processado
        caminho_salvar = Caminho(destino_local ou nome_saida)
        caminho_salvar.parent.mkdir(parents=True, exist_ok=True)

        req_download = urllib.request.Request(
            url_download_completa,
            headers={"User-Agent": "ClientePonteAlex/2.0"},
            método="GET"
        )

        tentar:
            com urllib.request.urlopen(req_download, timeout=30) como resp_down:
                conteúdo_baixado = resp_down.read()
                com open(caminho_salvar, "wb") como f_out:
                    f_out.write(conteudo_baixado)
        exceto urllib.error.HTTPError como e:
            raise ErroPonteAlex(f"Falha ao baixar arquivo processado ({url_download_completa}): HTTP {e.code}", status_http=e.code)
        exceto urllib.error.URLError como e:
            raise ErroPonteAlex(f"Falha de conexão ao baixar o arquivo: {e.reason}")

        tamanho_salvo = caminho_salvar.stat().st_size

        retornar {
            "status_http": código_de_status,
            "arquivo_salvo": str(caminho_salvar.resolve()),
            "nome_arquivo": caminho_salvar.nome,
            "tamanho_bytes": tamanho_salvo,
            "download_url": url_download_completa,
            "test_passed": resultado_json.get("testPassed", Falso),
            "test_message": resultado_json.get("testMessage", ""),
            "compile_check": resultado_json.get("compileCheck", {}),
            "execução": resultado_json.get("execução", {}),
            "original_sha256": resultado_json.get("originalFile", {}).get("sha256", ""),
            "processed_sha256": processed_file_info.get("sha256", ""),
            "resposta_completa": resultado_json
        }

    def feira_arquivo(
        auto,
        caminho_arquivo: str,
        instrução: str,
        arquivo_saida: Opcional[str] = Nenhum,
        destino_local: Opcional[str] = Nenhum
    ) -> Dict[str, Any]:
        """
        Lê um arquivo Python local e enviado para Ponte Alex v2.
        """
        caminho = Caminho(caminho_arquivo)
        se não caminho.exists():
            raise FileNotFoundError(f"Arquivo de entrada '{caminho_arquivo}' não encontrado.")

        se não caminho.is_file():
            raise ValueError(f"O caminho '{caminho_arquivo}' não é um arquivo regular.")

        com open(caminho, "r", encoding="utf-8", errors="replace") as f:
            conteúdo = f.read()

        nome_saida = arquivo_saida ou f"{caminho.stem}_processado.py"
        destino = destino_local ou nome_saida

        retornar self.processar_código(
            conteudo_codigo=conteudo,
            instrução=instrução,
            nome_arquivo=caminho.name,
            nome_saida=nome_saida,
            destino_local=destino
        )


def main():
    importar argparse

    analisador = argparse.ArgumentParser(
        description="Cliente Oficial da Ponte Alex v2 - Processamento e Execução Segura de Scripts Python"
    )
    parser.add_argument("arquivo", help="Caminho do arquivo Python de entrada a ser processado")
    parser.add_argument("--instruction", "-i", required=True, help="Instrução de modificação para a Ponte Alex v2")
    parser.add_argument("--output", "-o", default=None, help="Nome do arquivo de saída gerado")
    parser.add_argument("--url", "-u", default=None, help=f"URL base da Ponte Alex v2 (padrão: {DEFAULT_PONTE_URL})")
    parser.add_argument("--ping", action="store_true", help="Apenas testa a conectividade e status com a API")

    args = parser.parse_args()

    tentar:
        cliente = ClientePonteAlex(base_url=args.url)

        se args.ping:
            print("Executando ping na Ponte Alex v2...")
            res_ping = cliente.ping()
            print(f"Status: {res_ping.get('status')}")
            print(f"Ponte: {res_ping.get('ponte')} (v{res_ping.get('version')})")
            print(f"Tempo de execução: {res_ping.get('pythonRuntime')}")
            retornar 0

        print("=" * 60)
        print("ðŸš€ PONTE ALEX v2 - CLIENTE OFICIAL DE INTEGRAÇAO")
        print("=" * 60)
        print(f"Arquivo de entrada: {args.arquivo}")
        print(f"Instruções: {args.instruction}")
        print(f"Servidor: {cliente.base_url}")
        print(f"Autenticação: x-api-secret configurado no ambiente")
        imprimir("-" * 60)

        resultado = cliente.processar_arquivo(
            caminho_arquivo=args.arquivo,
            instrução=args.instrução,
            arquivo_saida=args.output
        )

        print("\nâœ… PROCESSAMENTO E EXECUÇÃO CONCLUÍDOS COM SUCESSO!")
        print(f"â€¢ Arquivo Local Salvo: {resultado['arquivo_salvo']}")
        print(f"â€¢ Tamanho do Arquivo: {resultado['tamanho_bytes']} bytes")
        print(f"â€¢ Teste Python: {'APROVADO (código de saída 0)' if resultado['test_passed'] else 'REPROVADO'}")
        print(f"â€¢ Mensagem: {resultado['test_message']}")
        
        exec_info = resultado.get("execução", {})
        se exec_info.get("stdout"):
            print("\n[Saída stdout da execução Python]:")
            print(exec_info['stdout'].strip())

        print("=" * 60)
        retornar 0

    exceto ErroPonteAlex como e:
        print(f"\nâ Œ ERRO NA PONTE ALEX v2: {e}", arquivo=sys.stderr)
        se e.detalhes:
            print(f"Detalhes: {json.dumps(e.detalhes, indent=2)}", arquivo=sys.stderr)
        retornar 1
    exceto Exception como e:
        print(f"\nâ Œ ERRO INESPERADO: {e}", arquivo=sys.stderr)
        retornar 2


se __name__ == "__main__":
    sys.exit(main())
