# ============================================================
# 📄 ALEX IA ULTRA — SISTEMA DE ARQUIVOS
# Criada por Geovani
# ============================================================

from io import BytesIO

import PyPDF2
from docx import Document


def ler_txt(arquivo):
    """Lê um arquivo TXT."""

    try:
        conteudo = arquivo.read()

        if isinstance(conteudo, bytes):
            conteudo = conteudo.decode("utf-8", errors="ignore")

        return conteudo, None

    except Exception as erro:
        return None, str(erro)


def ler_pdf(arquivo):
    """Extrai texto de um arquivo PDF."""

    try:
        leitor = PyPDF2.PdfReader(arquivo)

        paginas = []

        for pagina in leitor.pages:
            texto = pagina.extract_text()

            if texto:
                paginas.append(texto)

        return "\n\n".join(paginas), None

    except Exception as erro:
        return None, str(erro)


def ler_docx(arquivo):
    """Extrai texto de um arquivo DOCX."""

    try:
        documento = Document(BytesIO(arquivo.read()))

        paragrafos = []

        for paragrafo in documento.paragraphs:

            if paragrafo.text.strip():
                paragrafos.append(paragrafo.text)

        return "\n".join(paragrafos), None

    except Exception as erro:
        return None, str(erro)


def ler_arquivo(arquivo):
    """
    Identifica o tipo do arquivo e extrai o texto.
    """

    if arquivo is None:
        return None, "Nenhum arquivo foi enviado."

    nome = arquivo.name.lower()

    if nome.endswith(".txt"):
        return ler_txt(arquivo)

    if nome.endswith(".pdf"):
        return ler_pdf(arquivo)

    if nome.endswith(".docx"):
        return ler_docx(arquivo)

    return None, (
        "Formato não suportado. "
        "Use PDF, TXT ou DOCX."
    )
