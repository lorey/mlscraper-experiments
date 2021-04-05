import pytest

from mlscraper.samples import ItemStructureException, make_training_set
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
