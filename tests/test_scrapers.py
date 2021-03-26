from mlscraper.scrapers import DictScraper, ListScraper, Scraper, ValueScraper
from mlscraper.util import Page, Sample


def test_value_scraper():
    page1_html = '<html><body><p class="test">test</p><p>bla</p></body></html>'
    page1 = Page(page1_html)

    page2_html = '<html><body><div></div><p class="test">hallo</p></body></html>'
    page2 = Page(page2_html)

    vs = ValueScraper()
    vs.samples = [Sample(page1, "test"), Sample(page2, "hallo")]
    vs.train()


def test_scraper_build():
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

    scraper = Scraper.build(samples)
    assert isinstance(scraper, ListScraper)
    print(scraper.samples)
    assert scraper.samples[0].item == item

    dict_scraper = scraper.scraper
    assert isinstance(dict_scraper, DictScraper)
    assert list(dict_scraper.scraper_per_key.keys()) == ["user", "upvotes", "when"]
