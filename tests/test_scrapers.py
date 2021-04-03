import pytest

from mlscraper.scrapers import DictScraper, ListScraper, Scraper, ValueScraper
from mlscraper.util import Page, Sample


@pytest.fixture
def stackoverflow_samples():
    with open("tests/static/so.html") as file:
        page = Page(file.read())

    item = [
        {
            "user": "https://stackoverflow.com/users/624900/jterrace",
            "upvotes": "20",
            "when": "2011-06-16 19:45:11Z",
        },
        {
            "user": "https://stackoverflow.com/users/4044167/nico-knoll",
            "upvotes": "16",
            "when": "2017-09-06 15:27:16Z",
        },
        {
            "user": "https://stackoverflow.com/users/1275778/lorey",
            "upvotes": "0",
            "when": "2021-01-06 10:50:04Z",
        },
    ]
    samples = [Sample(page, item)]
    return samples


class TestScraper:
    def test_build(self, stackoverflow_samples):
        scraper = Scraper.build(stackoverflow_samples)
        assert isinstance(scraper, ListScraper)
        print(scraper.samples)
        assert scraper.samples[0].item == stackoverflow_samples[0].item

        dict_scraper = scraper.scraper
        assert isinstance(dict_scraper, DictScraper)
        assert list(dict_scraper.scraper_per_key.keys()) == ["user", "upvotes", "when"]

    @pytest.mark.skip
    def test_scrape(self, stackoverflow_samples):
        scraper = Scraper.build(stackoverflow_samples)
        scraper.train()

        so_page = stackoverflow_samples[0].page
        scraper_per_key = scraper.scraper.scraper_per_key
        for key, scraper in scraper_per_key.items():
            print(key, scraper.scrape(so_page))


class TestDictScraper:
    def test_scrape_matches(self):
        item_1 = {"h": "no 1", "t": "the first one"}
        item_2 = {"h": "no 2", "t": "the second one"}

        elem_temp = "<div><h1>%(h)s</h1><p>%(t)s</p></div>"
        elem_1 = elem_temp % item_1
        elem_2 = elem_temp % item_2
        html = f"<html><body>{elem_1}{elem_2}</body></html>"
        page = Page(html)
        ds = DictScraper()
        ds.add_sample(Sample(page, item_1))
        ds.add_sample(Sample(page, item_2))
        ds.train()
        match_dicts = list(ds.scrape_matches(page))
        matches_items = [
            {k: m.get_value() for k, m in md.items()} for md in match_dicts
        ]
        assert [item_1, item_2] == matches_items


def test_value_scraper():
    page1_html = '<html><body><p class="test">test</p><p>bla</p></body></html>'
    page1 = Page(page1_html)

    page2_html = '<html><body><div></div><p class="test">hallo</p></body></html>'
    page2 = Page(page2_html)

    vs = ValueScraper()
    vs.samples = [Sample(page1, "test"), Sample(page2, "hallo")]
    vs.train()

    for sample in vs.samples:
        assert vs.scrape(sample.page) == sample.item
