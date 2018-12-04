import pytest
import time
from unittest import mock
import xml.etree.ElementTree as ET

from nesta.packages.arxiv.collect_arxiv import _arxiv_request
from nesta.packages.arxiv.collect_arxiv import request_token
from nesta.packages.arxiv.collect_arxiv import total_articles
from nesta.packages.arxiv.collect_arxiv import arxiv_batch
from nesta.packages.arxiv.collect_arxiv import xml_to_json

import os

__location__ = os.path.realpath(os.path.join(os.getcwd(),
                                             os.path.dirname(__file__)))

@pytest.fixture
def mock_response():
    with open(os.path.join(__location__, "standard_api_response.xml")) as f:
        data = f.read()
    return data.encode("utf8")


@mock.patch('nesta.packages.arxiv.collect_arxiv.requests.get')
def test_arxiv_request_sends_valid_params(mocked_requests, mock_response):
    mocked_requests().text = mock_response

    _arxiv_request('test.url', delay=0, metadataPrefix='arXiv')
    assert mocked_requests.call_args[0] == ('test.url', )
    assert mocked_requests.call_args[1] == {'params': {'verb': 'ListRecords',
                                                       'metadataPrefix': 'arXiv'}}

    _arxiv_request('another_test.url', delay=0, resumptionToken='123456')
    assert mocked_requests.call_args[0] == ('another_test.url', )
    assert mocked_requests.call_args[1] == {'params': {'verb': 'ListRecords',
                                                       'resumptionToken': '123456'}}


@mock.patch('nesta.packages.arxiv.collect_arxiv.requests.get')
def test_arxiv_request_returns_xml_element(mocked_requests, mock_response):
    mocked_requests().text = mock_response
    response = _arxiv_request('test.url', delay=0, metadataPrefix='arXiv')
    assert type(response) == ET.Element


@mock.patch('nesta.packages.arxiv.collect_arxiv.requests.get')
def test_arxiv_request_implements_delay(mocked_requests, mock_response):
    """Fair use policy specifies wait of 3 seconds between each request:
        https://arxiv.org/help/api/user-manual#Quickstart
    """
    mocked_requests().text = mock_response

    start_time = time.time()
    _arxiv_request('test.url', delay=1, metadataPrefix='arXiv')
    assert time.time() - start_time > 1

    start_time = time.time()
    _arxiv_request('test.url', delay=3, metadataPrefix='arXiv')
    assert time.time() - start_time > 3


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_request_token_returns_correct_token(mocked_request, mock_response):
    mocked_request.return_value = ET.fromstring(mock_response)
    assert request_token() == '3132962'


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_request_token_doesnt_override_delay(mocked_request, mock_response):
    mocked_request.return_value = ET.fromstring(mock_response)
    request_token()
    if 'delay' in mocked_request.call_args[1]:
        assert mocked_request.call_args[1]['delay'] >= 3


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_total_articles_returns_correct_amount(mocked_request, mock_response):
    mocked_request.return_value = ET.fromstring(mock_response)
    assert total_articles() == 1463679


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_total_articles_doesnt_override_delay(mocked_request, mock_response):
    mocked_request.return_value = ET.fromstring(mock_response)
    total_articles()
    if 'delay' in mocked_request.call_args[1]:
        assert mocked_request.call_args[1]['delay'] >= 3


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_arxiv_batch_extracts_required_fields(mocked_request, mock_response):
    mocked_request.return_value = ET.fromstring(mock_response)
    batch, _ = arxiv_batch('111222444', 0)
    expected_fields = {'datestamp', 'id', 'created', 'updated', 'title', 'categories',
                       'journal_ref', 'doi', 'msc_class', 'abstract', 'authors'}
    assert set(batch[0]) == expected_fields


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_arxiv_batch_handles_missing_fields(mocked_request, mock_response):
    mocked_request.return_value = ET.fromstring(mock_response)
    batch, _ = arxiv_batch('111222444', 0)
    expected_fields = {'datestamp', 'id', 'title', 'categories', 'abstract', 'authors'}
    assert set(batch[1]) == expected_fields


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_arxiv_batch_author_json_conversion(mocked_request, mock_response):
    mocked_request.return_value = ET.fromstring(mock_response)
    batch, _ = arxiv_batch('111222444', 0)

    expected_authors = '[{"keyname": "Author", "forenames": "G."}]'
    assert batch[0]['authors'] == expected_authors

    expected_authors = ('[{"keyname": "AnotherAuthor", "forenames": "L. M.", "suffix": "II", '
                        '"affiliation": "CREST, Japan Science and Technology Agency"}, '
                        '{"keyname": "Surname", "forenames": "Some other"}, '
                        '{"keyname": "Collaboration", "forenames": "An important"}]')
    assert batch[1]['authors'] == expected_authors


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_arxiv_batch_converts_categories_to_list(mocked_request, mock_response):
    mocked_request.return_value = ET.fromstring(mock_response)
    batch, _ = arxiv_batch('111222444', 0)
    assert batch[0]['categories'] == ['math.PR', 'math.RT']
    assert batch[1]['categories'] == ['hep-ex']


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_arxiv_batch_converts_dates(mocked_request, mock_response):
    mocked_request.return_value = ET.fromstring(mock_response)
    batch, _ = arxiv_batch('111222444', 0)
    assert {'datestamp', 'created', 'updated'} < batch[0].keys()
    assert {'created', 'updated'}.isdisjoint(batch[1].keys())


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_arxiv_batch_returns_resumption_cursor(mocked_request, mock_response):
    mocked_request.return_value = ET.fromstring(mock_response)
    _, cursor = arxiv_batch('111222444', 0)
    assert cursor == 1001


@mock.patch('nesta.packages.arxiv.collect_arxiv._arxiv_request')
def test_arxiv_batch_returns_none_at_end_of_data(mocked_request):
    with open(os.path.join(__location__, "final_api_response.xml")) as f:
        mock_response = f.read().encode("utf-8")

    mocked_request.return_value = ET.fromstring(mock_response)
    _, cursor = arxiv_batch('7654321', 0)
    assert cursor is None


def test_xml_to_json_conversion():
    with open(os.path.join(__location__, "authors.xml")) as f:
        test_xml = f.read().encode("utf-8")
    expected_output = ('[{"keyname": "AnotherAuthor", "forenames": "L. M.", "suffix": "II", '
                       '"affiliation": "CREST, Japan Science and Technology Agency"}, '
                       '{"keyname": "Surname", "forenames": "Some other"}, '
                       '{"keyname": "Collaboration", "forenames": "An important"}]')

    root = ET.fromstring(test_xml)
    assert xml_to_json(root, 'author', '{http://arxiv.org/OAI/arXiv/}') == expected_output
