import pytest

from mlscraper.samples import (
    DictMatch,
    ItemStructureException,
    Sample,
    make_training_set,
)
from mlscraper.util import Page


class TestTrainingSet:
    def test_make_training_set(self):
        pages = [Page(""), Page("")]
        items = [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
        make_training_set(pages, items)

    def test_make_training_set_error(self):
        pages = [Page(""), Page("")]
        items = [{"a": "1", "b": "2"}, {"a": "3", "b": []}]
        with pytest.raises(ItemStructureException):
            make_training_set(pages, items)


class TestMatch:
    def test_get_matches_basic(self):
        page_html = "<html><body><h1>test</h1><p>2010</p><div class='footer'>2010</div></body></html>"
        s = Sample(Page(page_html), {"h": "test", "year": "2010"})
        matches = s.get_matches()
        assert len(matches) == 2
        assert all(isinstance(m, DictMatch) for m in matches)