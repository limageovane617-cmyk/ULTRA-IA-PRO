import unittest
from unittest.mock import Mock, patch
from urllib.parse import quote

from ultra_core.web_search_fallback import pesquisar_bing_rss, _url_destino


class BingRssSearchTests(unittest.TestCase):
    @patch("ultra_core.web_search_fallback.requests.get")
    def test_parses_rss_results(self, get):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
          <item>
            <title>Notícia de teste</title>
            <link>https://example.com/noticia</link>
            <description>Resumo   da notícia</description>
            <pubDate>Sat, 14 Nov 2026 10:00:00 GMT</pubDate>
          </item>
        </channel></rss>"""
        response = Mock()
        response.content = xml.encode("utf-8")
        response.raise_for_status.return_value = None
        get.return_value = response

        result = pesquisar_bing_rss("notícia de teste")

        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "bing_rss")
        self.assertEqual(result["quantidade"], 1)
        self.assertEqual(result["resultados"][0]["url"], "https://example.com/noticia")
        self.assertFalse(result["verified"])

    def test_unwraps_bing_redirect(self):
        destination = "https://example.com/artigo?a=1"
        wrapped = "https://www.bing.com/news/apiclick.aspx?url=" + quote(destination, safe="")
        self.assertEqual(_url_destino(wrapped), destination)

    @patch("ultra_core.web_search_fallback.requests.get")
    def test_returns_failure_on_empty_feed(self, get):
        response = Mock()
        response.content = b"<rss><channel></channel></rss>"
        response.raise_for_status.return_value = None
        get.return_value = response

        result = pesquisar_bing_rss("consulta sem resultados")

        self.assertFalse(result["success"])
        self.assertEqual(result["resultados"], [])


if __name__ == "__main__":
    unittest.main()
