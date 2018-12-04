"""
analyse_arxiv
=============

Analyse arXiv data.
"""


def term_appears_in_doc(term, doc):
    """Check whether the term appears in a processed document

    Args:
        term (str): A term to search for.
        doc (:obj:`list` of :obj:`list` of :obj:`str`): A doc to process.
    Returns:
        bool
    """
    return any(term in sent for sent in doc)


if __name__ == "__main__":
    from nesta.packages.nlp_utils.preprocess import tokenize_document
    import pandas as pd

    df = pd.read_json("/Users/jklinger/tmp-data/arxiv_test.json")
    quantum_appears = [term_appears_in_doc("quantum", abstract)
                       for abstract in df.abstract.apply(tokenize_document)]
    print(sum(quantum_appears), len(df))
