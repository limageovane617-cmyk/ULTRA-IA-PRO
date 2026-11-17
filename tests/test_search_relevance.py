import unittest

from ultra_core.tool_bindings import filtrar_resultados_relevantes


class SearchRelevanceTests(unittest.TestCase):
    def test_rejects_unrelated_sao_jose_results(self):
        results = [
            {"titulo": "São José – Wikipédia", "snippet": "História e tradições católicas"},
            {"titulo": "Prefeitura Municipal de São José", "snippet": "Serviços municipais"},
        ]
        filtered = filtrar_resultados_relevantes(
            "notícias recentes sobre inteligência artificial", results
        )
        self.assertEqual(filtered, [])

    def test_keeps_results_about_artificial_intelligence(self):
        results = [
            {"titulo": "Inteligência artificial avança em 2026",
             "snippet": "Novas aplicações de inteligência artificial nas empresas"},
            {"titulo": "São José – Wikipédia", "snippet": "História da cidade"},
        ]
        filtered = filtrar_resultados_relevantes(
            "notícias sobre inteligência artificial", results
        )
        self.assertEqual(len(filtered), 1)
        self.assertIn("Inteligência artificial", filtered[0]["titulo"])

    def test_rejects_irrelevant_bing_rss_items(self):
        # Bing RSS usa exatamente os campos titulo/snippet/url.
        results = [
            {"titulo": "LATAM Airlines", "snippet": "Passagens e viagens aéreas",
             "url": "https://www.latamairlines.com/"},
            {"titulo": "São José – Wikipédia", "snippet": "História da cidade",
             "url": "https://pt.wikipedia.org/wiki/S%C3%A3o_Jos%C3%A9"},
        ]
        filtered = filtrar_resultados_relevantes(
            "novidades recentes sobre inteligência artificial em novembro de 2026",
            results,
        )
        self.assertEqual(filtered, [])

    def test_keeps_relevant_bing_rss_item_and_its_url(self):
        results = [
            {"titulo": "Inteligência artificial: novas pesquisas em 2026",
             "snippet": "Avanços recentes em inteligência artificial",
             "url": "https://example.com/ia"},
            {"titulo": "LATAM Airlines", "snippet": "Voos e passagens",
             "url": "https://www.latamairlines.com/"},
        ]
        filtered = filtrar_resultados_relevantes(
            "novidades recentes sobre inteligência artificial em novembro de 2026",
            results,
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["url"], "https://example.com/ia")


if __name__ == "__main__":
    unittest.main()
