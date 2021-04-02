from bs4 import BeautifulSoup

from mlscraper.util import HrefExtractor, Page


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


def test_url_extractor():
    soup = BeautifulSoup(
        '<html><body><a href="http://karllorey.com"></a><a>no link</a></body></html>',
        "lxml",
    )
    ue = HrefExtractor()
    a_tags = soup.find_all("a")
    assert ue.extract(a_tags[0]) == "http://karllorey.com"
    assert ue.extract(a_tags[1]) is None
