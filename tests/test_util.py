from bs4 import BeautifulSoup

from mlscraper.util import AttributeExtractor, Page, get_attribute_extractor


class TestPage:
    def test_something(self):
        with open("tests/static/so.html") as file:
            page = Page(file.read())
        nodes = page.select(".answer .js-vote-count")
        assert [n.text for n in nodes] == ["20", "16", "0"]

    def test_find_all(self):
        with open("tests/static/so.html") as file:
            page = Page(file.read())
        nodes = page.find_all("/users/624900/jterrace")
        assert nodes


def test_attribute_extractor():
    soup = BeautifulSoup(
        '<html><body><a href="http://karllorey.com"></a><a>no link</a></body></html>',
        "lxml",
    )
    ue = AttributeExtractor("href")
    a_tags = soup.find_all("a")
    assert ue.extract(a_tags[0]) == "http://karllorey.com"
    assert ue.extract(a_tags[1]) is None


def test_extractor_factory():
    # we want to make sure that each extractor exists only once
    # as we need this to ensure extractor selection
    e1 = get_attribute_extractor("href")
    e2 = get_attribute_extractor("href")
    assert (
        e1 is e2
    ), "extractor factory return different instances for the same extractor"
