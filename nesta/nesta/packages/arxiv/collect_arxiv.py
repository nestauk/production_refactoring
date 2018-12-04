import datetime
import json
import logging
import requests
from retrying import retry
import time
import xml.etree.ElementTree as ET


OAI = "{http://www.openarchives.org/OAI/2.0/}"
ARXIV = "{http://arxiv.org/OAI/arXiv/}"
DELAY = 10  # seconds between requests
API_URL = 'http://export.arxiv.org/oai2'


@retry(stop_max_attempt_number=10)
def _arxiv_request(url, delay=DELAY, **kwargs):
    """Make a request and convert the result to xml elements.
     Args:
        url (str): endpoint of the api
        delay (int): time to wait after request in seconds
        kwargs (dict): any other arguments to pass as paramaters in the request
     Returns:
        (:obj:`xml.etree.ElementTree.Element`): converted response
    """
    params = dict(verb='ListRecords', **kwargs)
    r = requests.get(url, params=params)
    time.sleep(delay)
    try:
        root = ET.fromstring(r.text)
    except ET.ParseError as e:
        logging.error(r.text)
        raise e
    return root


def total_articles():
    """Make a request to the API and capture the total number of articles from the
    resumptionToken tag.
     Returns:
        (int): total number of articles
    """
    root = _arxiv_request(API_URL, metadataPrefix='arXiv')
    token = root.find(OAI+'ListRecords').find(OAI+"resumptionToken")
    list_size = token.attrib['completeListSize']
    return int(list_size)


def request_token():
    """Make a request to the API and capture the resumptionToken which will be
    used to a page through results. Not efficient as it also returns the first
    page of data which is slow and not required.
     Returns:
        (str): supplied resumtionToken
    """
    root = _arxiv_request(API_URL, metadataPrefix='arXiv')
    token = root.find(OAI+'ListRecords').find(OAI+"resumptionToken")
    resumption_token = token.text.split("|")[0]
    logging.info(f"resumptionToken: {resumption_token}")
    return resumption_token


def xml_to_json(element, tag, prefix=''):
    """Converts a layer of xml to a json string. Handles multiple instances of the
    specified tag and any schema prefix which they may have.
     Args:
        element (:obj:`xml.etree.ElementTree.Element`): xml element containing the data
        tag (str): target tag
        prefix (str): schema prefix on the name of the tag
     Returns:
        (str): json of the original object with the supplied tag as the key and a list
               of all instances of this tag as the value.
    """
    tag = ''.join([prefix, tag])
    all_data = [{field.tag[len(prefix):]: field.text
                 for field in fields.getiterator()
                 if field.tag != tag}
                for fields in element.getiterator(tag)]
    return json.dumps(all_data)


def arxiv_batch(token, cursor):
    """Retrieves a batch of data from the arXiv api (expect 1000).
     Args:
        token (str): resumptionToken issued from a prevous request
        cursor (int): record to start from
     Returns:
        (:obj:`list` of :obj:`dict`): retrieved records
    """
    resumption_token = '|'.join([token, str(cursor)])
    root = _arxiv_request(API_URL, resumptionToken=resumption_token)
    records = root.find(OAI+'ListRecords')
    output = []
    for record in records.findall(OAI+"record"):
        header = record.find(OAI+'header')
        header_id = header.find(OAI+'identifier').text
        row = dict(datestamp=header.find(OAI+'datestamp').text)
        logging.debug(f"article {header_id} datestamp: {row['datestamp']}")
        # collect all fields from the metadata section
        meta = record.find(OAI+'metadata')
        if meta is None:
            logging.warning(f"No metadata for article {header_id}")
        else:
            info = meta.find(ARXIV+'arXiv')
            fields = ['id', 'created', 'updated', 'title', 'categories',
                      'journal-ref', 'doi', 'msc-class', 'abstract']
            for field in fields:
                try:
                    row[field.replace('-', '_')] = info.find(ARXIV+field).text
                except AttributeError:
                    logging.debug(f"{field} not found in article {header_id}")
            for date_field in ['datestamp', 'created', 'updated']:
                try:
                    date = row[date_field]
                    row[date_field] = datetime.datetime.strptime(date, '%Y-%m-%d').date()
                except ValueError:
                    del row[date_field]  # date is not in the correct format
                except KeyError:
                    pass  # field not in this row
            # split categories into a list for the link table in sql
            try:
                row['categories'] = row['categories'].split(' ')
                row['title'] = row['title'].strip()
                row['authors'] = xml_to_json(info, 'author', prefix=ARXIV)
            except KeyError:
                pass  # field not in this row
        output.append(row)
    # extract cursor for next batch
    token = root.find(OAI+'ListRecords').find(OAI+"resumptionToken")
    if token.text is not None:
        resumption_cursor = int(token.text.split("|")[1])
        logging.info(f"next resumptionCursor: {resumption_cursor}")
    else:
        resumption_cursor = None
        logging.info("End of data")
    return output, resumption_cursor


if __name__ == "__main__":
    import pandas as pd
    outdir = "/Users/jklinger/tmp-data/arxiv_test.json"
    n = total_articles()
    token = request_token()
    output, _ = arxiv_batch(token, 0)
    pd.DataFrame(output).to_json(outdir, orient="records")
