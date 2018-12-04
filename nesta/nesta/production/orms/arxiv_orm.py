'''
ArXiv ORM
=========

Note that Author fields have been flattened out from
Articles.
'''

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import VARCHAR, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DATE

Base = declarative_base()


class Article(Base):
    __tablename__ = 'arxiv_articles'

    id = Column(VARCHAR(20), primary_key=True)
    datestamp = Column(DATE)
    created = Column(DATE)
    updated = Column(DATE)
    title = Column(TEXT)
    journal_ref = Column(TEXT)
    doi = Column(VARCHAR(200))
    abstract = Column(TEXT)
    msc_class = Column(VARCHAR(200))


class Author(Base):
    __tablename__ = 'arxiv_authors'

    article_id = Column(VARCHAR(20), primary_key=True)
    keyname = Column(VARCHAR(50), primary_key=True)
    forenames = Column(VARCHAR(50), primary_key=True)
