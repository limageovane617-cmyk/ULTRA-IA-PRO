# ============================================================
# ALEX IA ULTRA — INTERPRETER
# Interpretador de linguagem natural do Ultra Core
# ============================================================

import re
import unicodedata

from typing import Any, Dict, List


class TaskInterpreter:
    """
    Interpretador central da Alex IA Ultra.

    Responsabilidades:
    - Normalizar o pedido.
    - Identificar a intenção principal.
    - Extrair palavras-chave relevantes.
    - Extrair o prompt principal.
    - Sugerir ferramentas.
    - Preparar informações para Brain e Planner.

    O Interpreter não executa ferramentas.
    """

    # ========================================================
    # CONFIGURAÇÕES
    # ========================================================

    CATEGORIAS = {
        "internet": [
            "pesquisar", "pesquise", "pesquisa",
            "buscar", "busque", "procure",
            "internet", "google",
            "noticia", "noticias",
            "informacao atual", "informacoes atuais",
            "dados atuais",
        ],

        "imagem": [
            "imagem", "imagens", "foto",
            "fotografia", "desenho",
            "ilustracao", "picture", "image",
            "gerar imagem", "criar imagem",
            "fazer imagem",
        ],

        "video": [
            "video", "videos", "filme",
            "animacao", "clipe", "clip",
            "gerar video", "criar video",
            "animar",
        ],

        "texto": [
            "texto", "escrever", "escreva",
            "redigir", "resumo", "resumir",
            "explicar", "explicacao",
            "traduzir", "traducao",
        ],

        "codigo": [
            "codigo", "programar",
            "programacao", "python",
            "javascript", "typescript",
            "funcao", "arquivo", "script",
            "classe", "bug", "erro",
            "corrigir codigo",
        ],
    }

    FERRAMENTAS = {
        "internet": [
            "pesquisa_internet",
        ],

        "imagem": [
            "imagem.gerar",
            "gerar_imagem",
            "image.generate",
            "image_generator",
        ],

        "video": [
            "video.gerar",
            "video.texto",
            "video.imagem",
            "video.fallback",
            "gerar_video",
        ],

        "texto": [
            "texto.gerar",
            "text.gerar",
            "gerar_texto",
        ],

        "codigo": [
            "codigo.gerar",
            "codigo.executar",
            "python.executar",
            "code.execute",
        ],

        "geral": [],
    }

    STOPWORDS = {
        "para", "com", "uma", "uns", "umas",
        "que", "qual", "quais", "como",
        "quero", "queria", "preciso",
        "faca", "fazer", "criar", "crie",
        "gerar", "gere", "sobre",
        "por", "dos", "das", "nos",
        "nas", "aos", "pelos", "pela",
        "pelo", "mais", "muito", "essa",
        "esse", "isso", "aquela", "aquele",
        "meu", "minha", "seu", "sua",
    }

    # ========================================================
    # NORMALIZAÇÃO
    # ========================================================

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza espaços, caixa e acentos.
        """

        texto = str(text or "").strip().lower()

        texto = unicodedata.normalize(
            "NFKD",
            texto,
        )

        texto = "".join(
            caractere
            for caractere in texto
            if not unicodedata.combining(caractere)
        )

        texto = re.sub(r"\s+", " ", texto)

        return texto.strip()

    # ========================================================
    # CORRESPONDÊNCIA DE TERMOS
    # ========================================================

    @staticmethod
    def contains_term(text: str, term: str) -> bool:
        """
        Procura uma palavra ou expressão completa,
        evitando correspondências dentro de outras palavras.
        """

        pattern = (
            r"(?<!\w)"
            + re.escape(term)
            + r"(?!\w)"
        )

        return re.search(pattern, text) is not None

    # ========================================================
    # DETECÇÃO DE INTENÇÃO
    # ========================================================

    def detect_intent(
        self,
        user_request: str,
    ) -> Dict[str, Any]:

        texto = self.normalize_text(user_request)

        if not texto:
            return {
                "intent": "unknown",
                "keywords": [],
                "confidence": 0.0,
                "suggested_tools": [],
            }

        # Perguntas factuais diretas também precisam de pesquisa,
        # mesmo quando o usuário não escreve "pesquise".
        padroes_pesquisa_factual = (
            r"\\bqual\\s+(?:e|foi|sera)\\s+(?:a\\s+)?capital\\b",
            r"\\bqual\\s+(?:e|foi)\\s+(?:a\\s+)?populacao\\b",
            r"\\bquem\\s+(?:e|foi)\\s+(?:o|a)?\\s*(?:presidente|primeiro ministro|premier)\\b",
            r"\\bquantos\\s+habitantes\\b",
            r"\\bonde\\s+fica\\b",
            r"\\bquando\\s+(?:foi|aconteceu|ocorreu)\\b",
        )

        if any(re.search(padrao, texto) for padrao in padroes_pesquisa_factual):
            return {
                "intent": "internet",
                "keywords": self.extract_keywords(texto),
                "confidence": 0.88,
                "suggested_tools": self.suggest_tools("internet"),
            }

        pontuacoes = {}

        for categoria, termos in self.CATEGORIAS.items():

            encontrados = [
                termo
                for termo in termos
                if self.contains_term(texto, termo)
            ]

            if encontrados:
                # Expressões específicas têm mais peso
                # do que palavras genéricas.
                pontuacao = sum(
                    2 if " " in termo else 1
                    for termo in encontrados
                )

                pontuacoes[categoria] = pontuacao

        if not pontuacoes:
            return {
                "intent": "geral",
                "keywords": self.extract_keywords(texto),
                "confidence": 0.40,
                "suggested_tools": [],
            }

        # Maior pontuação vence.
        # Em caso de empate, mantém a ordem das categorias.
        intent = max(
            pontuacoes,
            key=pontuacoes.get,
        )

        maior_pontuacao = pontuacoes[intent]

        total_sinais = sum(pontuacoes.values())

        # A confiança diminui quando há sinais concorrentes.
        confidence = min(
            0.55 + (maior_pontuacao * 0.08),
            0.95,
        )

        if total_sinais > maior_pontuacao:
            confidence *= (
                maior_pontuacao / total_sinais
            )

        return {
            "intent": intent,
            "keywords": self.build_keywords(
                texto,
                intent,
            ),
            "confidence": round(confidence, 2),
            "suggested_tools": self.suggest_tools(intent),
        }

    # ========================================================
    # EXTRAÇÃO DE PALAVRAS-CHAVE
    # ========================================================

    @classmethod
    def extract_keywords(
        cls,
        text: str,
        limit: int = 10,
    ) -> List[str]:

        texto = cls.normalize_text(text)

        palavras = re.findall(
            r"\b[\w-]+\b",
            texto,
        )

        resultado = []

        for palavra in palavras:

            if len(palavra) < 4:
                continue

            if palavra in cls.STOPWORDS:
                continue

            if palavra not in resultado:
                resultado.append(palavra)

            if len(resultado) >= limit:
                break

        return resultado

    # ========================================================
    # KEYWORDS POR INTENÇÃO
    # ========================================================

    def build_keywords(
        self,
        text: str,
        intent: str,
    ) -> List[str]:
        """
        Produz palavras-chave sem adicionar comandos
        genéricos que possam confundir o Router.
        """

        keywords = self.extract_keywords(
            text,
            limit=8,
        )

        # Evita palavras-chave artificiais como
        # "gerar", "buscar" e "criar".
        # A intenção e as ferramentas sugeridas
        # já identificam a categoria.
        resultado = []

        for keyword in keywords:

            keyword = self.normalize_text(keyword)

            if keyword and keyword not in resultado:
                resultado.append(keyword)

        return resultado[:12]

    # ========================================================
    # EXTRAÇÃO DO PROMPT
    # ========================================================

    def extract_prompt(
        self,
        user_request: str,
    ) -> str:
        """
        Remove comandos iniciais conhecidos,
        preservando o conteúdo principal.
        """

        texto = str(user_request or "").strip()

        if not texto:
            return ""

        prefixos = [
            # Imagem
            "gerar uma imagem de ",
            "gerar uma imagem ",
            "gerar imagem de ",
            "gerar imagem ",
            "criar uma imagem de ",
            "criar uma imagem ",
            "criar imagem de ",
            "criar imagem ",
            "fazer uma imagem de ",
            "fazer uma imagem ",
            "gere uma imagem de ",
            "gere uma imagem ",
            "crie uma imagem de ",
            "crie uma imagem ",

            # Vídeo
            "gerar um vídeo de ",
            "gerar um vídeo ",
            "gerar um video de ",
            "gerar um video ",
            "criar um vídeo de ",
            "criar um vídeo ",
            "criar um video de ",
            "criar um video ",
            "gere um vídeo de ",
            "gere um video de ",
            "gere um vídeo ",
            "gere um video ",
            "crie um vídeo de ",
            "crie um video de ",
            "animar ",

            # Internet
            "pesquisar sobre ",
            "pesquisar ",
            "pesquise sobre ",
            "pesquise ",
            "buscar sobre ",
            "buscar ",
            "busque sobre ",
            "busque ",
            "procurar sobre ",
            "procurar ",
            "procure sobre ",
            "procure ",

            # Texto
            "escrever sobre ",
            "escreva sobre ",
            "criar um texto sobre ",
            "criar um texto ",
            "fazer um texto sobre ",
            "fazer um texto ",
            "escreva um texto sobre ",
            "escreva um texto ",

            # Código
            "criar código para ",
            "criar codigo para ",
            "escrever código para ",
            "escrever codigo para ",
            "corrigir código ",
            "corrigir codigo ",
        ]

        texto_normalizado = self.normalize_text(texto)

        for prefixo in prefixos:

            prefixo_normalizado = self.normalize_text(
                prefixo
            )

            if texto_normalizado.startswith(
                prefixo_normalizado
            ):

                return texto[
                    len(prefixo):
                ].strip()

        return texto

    # ========================================================
    # SUGESTÃO DE FERRAMENTAS
    # ========================================================

    @classmethod
    def suggest_tools(
        cls,
        intent: str,
    ) -> List[str]:

        return list(
            cls.FERRAMENTAS.get(
                intent,
                [],
            )
        )

    # ========================================================
    # INTERPRETAÇÃO COMPLETA
    # ========================================================

    def interpret(
        self,
        user_request: str,
    ) -> Dict[str, Any]:
        """
        Executa a interpretação completa.
        """

        if not user_request or not str(
            user_request
        ).strip():

            return {
                "success": False,
                "intent": "unknown",
                "keywords": [],
                "confidence": 0.0,
                "prompt": "",
                "suggested_tools": [],
                "message": (
                    "A solicitação do usuário "
                    "está vazia."
                ),
            }

        detected = self.detect_intent(
            user_request
        )

        prompt = self.extract_prompt(
            user_request
        )

        return {
            "success": True,
            "intent": detected["intent"],
            "keywords": detected["keywords"],
            "confidence": detected["confidence"],
            "prompt": prompt,
            "suggested_tools": detected["suggested_tools"],
            "original_request": str(
                user_request
            ).strip(),
        }


# ============================================================
# INSTÂNCIA PADRÃO
# ============================================================

interpreter = TaskInterpreter()


__all__ = [
    "TaskInterpreter",
    "interpreter",
]
