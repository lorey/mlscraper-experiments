from mlscraper.util import Page


class TestPage:
    def test_something(self):
        with open("tests/static/so.html") as file:
            page = Page(file.read())
        nodes = page.select(".answer .js-vote-count")
        assert [n.text for n in nodes] == ["20", "16", "0"]
