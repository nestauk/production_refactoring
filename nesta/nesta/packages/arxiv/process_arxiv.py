"""
process_arxiv
=============

Intermediate processing of arXiv data.
"""

import json

AUTHOR_FIELDS = ["keyname", "forenames"]


def _parse_authors(id_, authors):
    """Extract the required author fields (from the global AUTHOR_FIELDS
    variable) and append the arXiv id to the row.

    Args:
        id_ (str): The arXiv id of article associated with this author.
        authors (str): A raw JSON string of authors information from arXiv.
    Returns:
        parsed (list): Record-oriented JSON.
    """
    parsed = []
    for author in json.loads(authors):
        row = {k: v for k, v in author.items()
               if k in AUTHOR_FIELDS}
        row['id'] = id_
        parsed.append(row)
    return parsed


def flatten_authors(ids, all_authors):
    """Flatten and process arXiv author information, associating
    each author with the arXiv id of their associated article.

    Args:
        ids (list): List of arXiv id matching the list of authors.
        all_authors (list): List of raw JSON strings of authors.
    Returns:
        parsed (list): Record-oriented JSON.
    """
    parsed = []
    for id_, authors in zip(ids, all_authors):
        parsed += _parse_authors(id_, authors)
        print(parsed)        
    return parsed


if __name__ == "__main__":
    import pandas as pd
    outdir = "/Users/jklinger/tmp-data/{}"
    df = pd.read_json(outdir.format("arxiv_test.json"))

    # Flatten out author information
    all_authors = df.pop("authors")
    flattened = flatten_authors(df["id"], all_authors)
    pd.DataFrame(flattened).to_json(outdir.format("arxiv_test_authors.json"),
                                    orient="records")
