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


if __name__ == "__main__":
    unittest.main()
