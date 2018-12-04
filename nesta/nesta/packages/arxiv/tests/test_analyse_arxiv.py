from unittest import TestCase
from nesta.packages.arxiv.analyse_arxiv import term_appears_in_doc


class TestAnalyseArxiv(TestCase):
    def test_term_appears_in_doc(self):
        doc = [["this", "is", "a", "sentence"], ["another"]]
        self.assertTrue(term_appears_in_doc("sentence", doc))
        self.assertFalse(term_appears_in_doc("joel", doc))
