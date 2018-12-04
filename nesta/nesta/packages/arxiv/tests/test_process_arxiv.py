from nesta.packages.arxiv.process_arxiv import _parse_authors
from nesta.packages.arxiv.process_arxiv import flatten_authors
from nesta.packages.arxiv.process_arxiv import AUTHOR_FIELDS

import pytest
from unittest import mock

import os

__location__ = os.path.realpath(os.path.join(os.getcwd(),
                                             os.path.dirname(__file__)))


@pytest.fixture
def mock_input():
    with open(os.path.join(__location__, "authors.json")) as f:
        data = f.read()
    return data.encode("utf8")


def test_parse_authors(mock_input):
    response = _parse_authors(1, mock_input)
    assert len(response) == 2
    for author in response:
        assert all(k in author for k in AUTHOR_FIELDS)


@mock.patch("nesta.packages.arxiv.process_arxiv._parse_authors")
def test_flatten_authors(mocked_authors):
    ids = [None, None, None]
    authors = [None, None, None]
    mocked_authors.side_effect = [[None, None], [None], [None]]
    response = flatten_authors(ids, authors)
    assert len(response) == 4
