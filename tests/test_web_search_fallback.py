import unittest
from unittest.mock import Mock, patch
from urllib.parse import quote

from ultra_core.web_search_fallback import (
    pesquisar_bing_rss, _url_destino,
    BING_RSS_URL, BING_NEWS_RSS_URL,
)


def _response(xml):
    response = Mock()
    response.content = xml.encode("utf-8")
    response.raise_for_status.return_value = None
    return response


class BingRssSearchTests(unittest.TestCase):
    @patch("ultra_core.web_search_fallback.requests.get")
    def test_parses_general_rss_results(self, get):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>Resultado de teste</title>
          <link>https://example.com/busca</link>
          <description>Resumo do resultado</description>
          <pubDate>Sat, 14 Nov 2026 10:00:00 GMT</pubDate>
        </item></channel></rss>"""
        get.return_value = _response(xml)

        result = pesquisar_bing_rss("capital do Brasil")

        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "bing_rss")
        self.assertEqual(result["quantidade"], 1)
        self.assertEqual(result["resultados"][0]["url"], "https://example.com/busca")
        self.assertFalse(result["verified"])
        self.assertEqual(get.call_args.args[0], BING_RSS_URL)

    @patch("ultra_core.web_search_fallback.requests.get")
    def test_news_queries_use_bing_news_rss(self, get):
        destination = "https://example.com/noticia"
        wrapped = "https://www.bing.com/news/apiclick.aspx?url=" + quote(destination, safe="")
        xml = f"""<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>Notícia sobre inteligência artificial</title>
          <link>{wrapped}</link>
          <description>Resumo da notícia</description>
        </item></channel></rss>"""
        get.return_value = _response(xml)

        result = pesquisar_bing_rss("notícias recentes sobre inteligência artificial")

        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "bing_news_rss")
        self.assertEqual(result["quantidade"], 1)
        self.assertEqual(result["resultados"][0]["url"], destination)
        self.assertEqual(get.call_args.args[0], BING_NEWS_RSS_URL)
        self.assertEqual(get.call_args.kwargs["params"]["mkt"], "pt-BR")

    def test_unwraps_bing_redirect(self):
        destination = "https://example.com/artigo?a=1"
        wrapped = "https://www.bing.com/news/apiclick.aspx?url=" + quote(destination, safe="")
        self.assertEqual(_url_destino(wrapped), destination)

    @patch("ultra_core.web_search_fallback.requests.get")
    def test_returns_failure_on_empty_feed(self, get):
        get.return_value = _response("<rss><channel></channel></rss>")
        result = pesquisar_bing_rss("consulta sem resultados")
        self.assertFalse(result["success"])
        self.assertEqual(result["resultados"], [])

    @patch("ultra_core.web_search_fallback.requests.get")
    def test_news_empty_feed_reports_news_provider(self, get):
        get.return_value = _response("<rss><channel></channel></rss>")
        result = pesquisar_bing_rss("notícias recentes de tecnologia")
        self.assertFalse(result["success"])
        self.assertEqual(result["provider"], "bing_news_rss")


if __name__ == "__main__":
    unittest.main()
